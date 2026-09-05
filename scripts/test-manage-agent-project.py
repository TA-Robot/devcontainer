#!/usr/bin/env python3
"""Black-box lifecycle checks. All disposable projects live in /tmp."""

import copy
import fcntl
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts/manage-agent-project"


def snapshot(root):
    """Observe bytes, modes, links and directories, including private metadata."""
    result = {}
    for path in sorted(root.rglob("*")):
        info = path.lstat()
        mode = stat.S_IMODE(info.st_mode)
        if path.is_symlink():
            value = ("symlink", os.readlink(path))
        elif path.is_file():
            value = ("file", mode, path.read_bytes())
        elif path.is_dir():
            value = ("directory", mode)
        else:
            value = ("special", mode)
        result[path.relative_to(root).as_posix()] = value
    return result


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="agent-project-test-", dir="/tmp")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.source = self.base / "source"
        self.target = self.base / "target"
        self.source.mkdir()
        self.target.mkdir()
        self.plan_file = self.base / "plan.json"

    def write(self, root, name, data=b"original\n", mode=0o644):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        path.chmod(mode)
        return path

    def cli(self, command, *args, ok=True):
        process = subprocess.run([str(CLI), command, "--target", str(self.target),
                                  *map(str, args), "--json"], capture_output=True, text=True)
        if ok:
            self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        else:
            self.assertNotEqual(process.returncode, 0, process.stdout + process.stderr)
        self.assertEqual(process.stderr, "")
        return json.loads(process.stdout)

    def plan(self, ok=True):
        before = snapshot(self.target)
        result = self.cli("plan", "--source", self.source, ok=ok)
        self.assertEqual(snapshot(self.target), before, "plan wrote target content")
        return result

    def apply(self, plan, ok=True):
        self.plan_file.write_text(json.dumps(plan), encoding="utf-8")
        before = snapshot(self.target)
        result = self.cli("apply", "--plan", self.plan_file, ok=ok)
        if not ok:
            self.assertEqual(snapshot(self.target), before, "rejected apply wrote target content")
        return result

    def install(self):
        plan = self.plan()
        self.assertEqual(plan["status"], "ready")
        result = self.apply(plan)
        self.assertEqual(result["status"], "applied")
        self.assertIsInstance(result["transaction_id"], str)
        return result

    def adopt(self, ok=True):
        before = snapshot(self.target)
        # Adoption must not even replace an identical file or chmod it.
        identity = {p: (p.stat().st_ino, p.stat().st_mtime_ns, p.stat().st_ctime_ns)
                    for p in self.target.rglob("*")
                    if p.is_file() and not p.is_symlink() and ".agent-project" not in p.parts}
        result = self.cli("adopt", "--source", self.source, ok=ok)
        after = snapshot(self.target)
        if not ok:
            self.assertEqual(after, before, "rejected adoption changed target")
        else:
            self.assertEqual({p: v for p, v in after.items() if not p.startswith(".agent-project")},
                             {p: v for p, v in before.items() if not p.startswith(".agent-project")})
            for path, prior in identity.items():
                info = path.stat()
                self.assertEqual((info.st_ino, info.st_mtime_ns, info.st_ctime_ns), prior)
        return result

    def kinds(self, plan):
        return {a["path"]: a["kind"] for a in plan["actions"]}

    def test_root_and_double_slash_overlap_are_rejected_before_inventory(self):
        self.write(self.source, "settings.txt")
        nested = self.source / "nested"
        nested.mkdir()
        before = snapshot(self.base)
        for target in ("/", "//" + str(self.source).lstrip("/"),
                       "//" + str(nested).lstrip("/")):
            with self.subTest(target=target):
                result = subprocess.run(
                    [str(CLI), "plan", "--source", str(self.source),
                     "--target", target, "--json"], capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn("source and target must be separate trees", result.stdout)
                self.assertEqual(snapshot(self.base), before)

    def test_private_metadata_is_git_ignored_without_editing_project_ignore(self):
        self.write(self.source, "settings.txt")
        project_ignore = self.write(self.target, ".gitignore", b"cache/\n")
        env = {**os.environ, "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1"}
        subprocess.run(["git", "-C", str(self.target), "init", "-q"], env=env,
                       check=True, capture_output=True)
        self.install()
        self.assertEqual(project_ignore.read_bytes(), b"cache/\n")
        private_ignore = self.target / ".agent-project/.gitignore"
        self.assertEqual(private_ignore.read_bytes(), b"*\n")
        self.assertEqual(stat.S_IMODE(private_ignore.stat().st_mode), 0o600)
        visible = subprocess.check_output(
            ["git", "-C", str(self.target), "ls-files", "--others", "--exclude-standard", "-z"],
            env=env).split(b"\0")
        self.assertIn(b"settings.txt", visible)
        self.assertFalse(any(path.startswith(b".agent-project/") for path in visible))

    def test_legacy_metadata_without_ignore_remains_unchanged_on_noop(self):
        self.write(self.source, "settings.txt")
        self.install()
        (self.target / ".agent-project/.gitignore").unlink()
        before = snapshot(self.target)
        self.cli("status")
        self.assertEqual(self.apply(self.plan())["status"], "noop")
        self.assertEqual(snapshot(self.target), before)

    def test_ignore_only_bootstrap_metadata_is_not_silently_adopted(self):
        self.write(self.target, ".agent-project/.gitignore", b"*\n", 0o600)
        before = snapshot(self.target)
        self.cli("status", ok=False)
        self.cli("recover", ok=False)
        self.assertEqual(snapshot(self.target), before)

    def test_failed_initial_apply_removes_new_private_ignore_and_metadata(self):
        if os.geteuid() == 0:
            self.skipTest("requires ordinary filesystem permission enforcement")
        self.write(self.source, "a")
        self.write(self.source, "locked/b")
        locked = self.target / "locked"
        locked.mkdir(mode=0o555)
        try:
            self.apply(self.plan(), ok=False)
            self.assertFalse((self.target / ".agent-project").exists())
            self.assertFalse((self.target / "a").exists())
        finally:
            locked.chmod(0o755)

    def test_adoption_and_update_preserve_stricter_non_executable_permissions(self):
        self.write(self.source, "settings.txt", b"original\n", 0o644)
        local = self.write(self.target, "settings.txt", b"original\n", 0o600)
        self.adopt()
        self.assertEqual(self.adopt()["status"], "noop")
        self.write(self.source, "settings.txt", b"updated\n", 0o644)
        self.apply(self.plan())
        self.assertEqual(local.read_bytes(), b"updated\n")
        self.assertEqual(stat.S_IMODE(local.stat().st_mode), 0o600)

    def test_real_template_and_native_contracts(self):
        self.source = ROOT / "project"
        self.write(self.target, "unrelated.txt", b"user content")
        self.write(self.target, ".git/config", b"git content")
        expected = snapshot(self.source)
        self.install()
        actual = snapshot(self.target)
        for name, value in expected.items():
            if value[0] == "file":
                self.assertEqual(actual[name], value, name)
            else:
                self.assertEqual(actual[name][0], value[0], name)
        self.assertEqual((self.target / "unrelated.txt").read_bytes(), b"user content")
        self.assertEqual((self.target / ".git/config").read_bytes(), b"git content")
        check = subprocess.run(["python3", str(ROOT / "scripts/validate-agent-contracts.py"),
                                "--template-root", str(self.target)], capture_output=True, text=True,
                               env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
        status = self.cli("status")
        self.assertEqual(status["managed_paths"], sorted(p for p, v in expected.items() if v[0] == "file"))
        self.assertEqual(status["local_changes"], [])
        before = snapshot(self.target)
        result = self.apply(self.plan())
        self.assertEqual(result, {"schema_version": 1, "status": "noop", "transaction_id": None})
        self.assertEqual(snapshot(self.target), before)

    def test_binary_unicode_spaces_modes_empty_directories(self):
        self.write(self.source, ".hidden/日本語 space/runner", bytes(range(256)), 0o751)
        self.write(self.source, "empty", b"", 0o640)
        (self.source / "empty directory").mkdir()
        self.install()
        self.assertEqual((self.target / ".hidden/日本語 space/runner").read_bytes(), bytes(range(256)))
        self.assertEqual(stat.S_IMODE((self.target / ".hidden/日本語 space/runner").stat().st_mode), 0o751)
        self.assertEqual(stat.S_IMODE((self.target / "empty").stat().st_mode), 0o640)
        self.assertTrue((self.target / "empty directory").is_dir())
        (self.source / ".hidden/日本語 space/runner").chmod(0o644)
        self.assertEqual(self.kinds(self.plan())[".hidden/日本語 space/runner"], "update")
        self.apply(self.plan())
        self.assertEqual(stat.S_IMODE((self.target / ".hidden/日本語 space/runner").stat().st_mode), 0o644)

    def test_unmanaged_identical_and_different_files_block_entire_install(self):
        for data in (b"template", b"user"):
            with self.subTest(data=data):
                self.write(self.source, "AGENTS.md", b"template")
                self.write(self.source, "another", b"new file")
                self.write(self.target, "AGENTS.md", data)
                plan = self.plan()
                self.assertEqual(plan["status"], "conflict")
                self.assertEqual(self.kinds(plan)["AGENTS.md"], "conflict")
                self.apply(plan, ok=False)
                self.assertFalse((self.target / "another").exists())
                self.assertFalse((self.target / ".agent-project").exists())

    def test_three_way_updates_local_retention_convergence_and_conflict(self):
        for name in ("clean", "local", "converged", "conflicted", "executable"):
            self.write(self.source, name)
        self.install()
        self.write(self.source, "clean", b"new")
        self.write(self.target, "local", b"customized")
        self.write(self.source, "converged", b"same new")
        self.write(self.target, "converged", b"same new")
        self.write(self.source, "conflicted", b"upstream")
        self.write(self.target, "conflicted", b"local")
        (self.target / "executable").chmod(0o755)
        plan = self.plan()
        self.assertEqual(self.kinds(plan), {"clean": "update", "local": "keep", "converged": "keep",
                                          "conflicted": "conflict", "executable": "keep"})
        self.apply(plan, ok=False)
        self.write(self.target, "conflicted")
        self.apply(self.plan())
        self.assertEqual((self.target / "clean").read_bytes(), b"new")
        self.assertEqual((self.target / "local").read_bytes(), b"customized")
        self.assertEqual((self.target / "converged").read_bytes(), b"same new")
        self.assertEqual((self.target / "conflicted").read_bytes(), b"upstream")
        status = self.cli("status")
        self.assertEqual([c["path"] for c in status["local_changes"]], ["executable", "local"])
        self.assertEqual(self.apply(self.plan())["status"], "noop")
        self.write(self.source, "local", b"next upstream")
        self.assertEqual(self.kinds(self.plan())["local"], "conflict")

    def test_existing_provider_config_blocks_real_template_install(self):
        self.source = ROOT / "project"
        self.write(self.target, ".codex/config.toml", b"user configuration")
        plan = self.plan()
        self.assertEqual(self.kinds(plan)[".codex/config.toml"], "conflict")
        self.apply(plan, ok=False)
        self.assertFalse((self.target / "AGENTS.md").exists())
        self.assertFalse((self.target / ".agent-project").exists())

    def test_deletion_preserves_unrelated_files_and_directories(self):
        self.write(self.source, "folder/clean")
        self.write(self.source, "folder/local")
        self.install()
        self.write(self.target, "folder/unrelated", b"keep")
        self.write(self.target, "folder/local", b"edited")
        shutil.rmtree(self.source / "folder")
        plan = self.plan()
        self.assertEqual(self.kinds(plan), {"folder/clean": "delete", "folder/local": "conflict"})
        self.apply(plan, ok=False)
        self.write(self.target, "folder/local")
        self.apply(self.plan())
        self.assertFalse((self.target / "folder/clean").exists())
        self.assertFalse((self.target / "folder/local").exists())
        self.assertEqual((self.target / "folder/unrelated").read_bytes(), b"keep")
        self.assertTrue((self.target / "folder").is_dir())
        self.assertEqual(self.cli("status")["managed_paths"], [])

    def test_locally_missing_managed_file(self):
        self.write(self.source, "file")
        self.install()
        (self.target / "file").unlink()
        self.assertEqual(self.kinds(self.plan())["file"], "keep")
        self.assertEqual(self.cli("status")["local_changes"][0]["reason"], "missing")
        self.assertEqual(self.apply(self.plan())["status"], "noop")
        self.write(self.source, "file", b"new")
        self.assertEqual(self.plan()["status"], "conflict")
        (self.source / "file").unlink()
        self.assertEqual(self.plan()["status"], "conflict")

    def test_stale_source_content_mode_inventory_and_root(self):
        self.write(self.source, "file")
        for mutation in ("bytes", "mode", "added", "removed", "root"):
            with self.subTest(mutation=mutation):
                plan = self.plan()
                if mutation == "bytes":
                    self.write(self.source, "file", b"changed")
                elif mutation == "mode":
                    (self.source / "file").chmod(0o755)
                elif mutation == "added":
                    self.write(self.source, "added")
                elif mutation == "removed":
                    (self.source / "added").unlink()
                else:
                    self.source.rename(self.base / "old-source")
                    shutil.copytree(self.base / "old-source", self.source)
                self.apply(plan, ok=False)

    def test_stale_target_content_mode_parent_metadata_and_replay(self):
        self.write(self.source, "folder/file")
        self.install()
        self.write(self.source, "folder/file", b"upstream")
        plan = self.plan()
        self.write(self.target, "folder/file", b"local")
        self.apply(plan, ok=False)
        self.write(self.target, "folder/file")
        plan = self.plan()
        (self.target / "folder/file").chmod(0o755)
        self.apply(plan, ok=False)
        (self.target / "folder/file").chmod(0o644)
        plan = self.plan()
        (self.target / "folder").rename(self.target / "moved-folder")
        shutil.copytree(self.target / "moved-folder", self.target / "folder")
        self.apply(plan, ok=False)
        plan = self.plan()
        state_path = self.target / ".agent-project/state.json"
        state_path.write_bytes(state_path.read_bytes() + b"\n")
        self.apply(plan, ok=False)
        plan = self.plan()
        self.apply(plan)
        self.apply(plan, ok=False)

    def test_unrelated_changes_do_not_invalidate_plan(self):
        self.write(self.source, "folder/file")
        plan = self.plan()
        self.write(self.target, "user-file", b"user")
        self.apply(plan)
        self.assertEqual((self.target / "user-file").read_bytes(), b"user")

    def test_target_root_replacement_invalidates_initial_plan(self):
        self.write(self.source, "file")
        plan = self.plan()
        self.target.rename(self.base / "old-target")
        self.target.mkdir()
        self.apply(plan, ok=False)

    def test_malformed_and_tampered_plans(self):
        self.write(self.source, "file")
        good = self.plan()
        variants = [None, [], {}, {**good, "schema_version": True}, {**good, "status": "conflict"},
                    {**good, "actions": []}, {**good, "extra": "ignored?"}]
        for path in ("../escape", "/tmp/escape", "a/../../escape", ".git/config",
                     "a/.agent-project/state.json", "", "a//b", "./file", "C:/file", "a\\b"):
            bad = copy.deepcopy(good)
            bad["actions"][0]["path"] = path
            variants.append(bad)
        bad = copy.deepcopy(good)
        bad["actions"].append(bad["actions"][0])
        variants.append(bad)
        bad = copy.deepcopy(good)
        bad["actions"][0]["kind"] = "delete"
        variants.append(bad)
        bad = copy.deepcopy(good)
        bad["next_state"]["files"] = {"../escape": {"mode": 420, "sha256": "0" * 64}}
        variants.append(bad)
        for bad in variants:
            with self.subTest(plan=bad):
                self.apply(bad, ok=False)
        for raw in (b"{", b'{"schema_version":1,"schema_version":1}', b"NaN", b"\xff"):
            self.plan_file.write_bytes(raw)
            before = snapshot(self.target)
            self.cli("apply", "--plan", self.plan_file, ok=False)
            self.assertEqual(snapshot(self.target), before)

    def test_plan_file_symlink_and_fifo_are_rejected(self):
        self.write(self.source, "file")
        valid = self.base / "valid-plan.json"
        valid.write_text(json.dumps(self.plan()))
        self.plan_file.symlink_to(valid)
        before = snapshot(self.target)
        self.cli("apply", "--plan", self.plan_file, ok=False)
        self.plan_file.unlink()
        os.mkfifo(self.plan_file)
        self.cli("apply", "--plan", self.plan_file, ok=False)
        self.assertEqual(snapshot(self.target), before)

    def test_reserved_source_paths_at_any_depth(self):
        for path in (".git/config", ".agent-project/state.json", "nested/.git/config",
                     "nested/.agent-project/state.json"):
            with self.subTest(path=path):
                self.write(self.source, path)
                self.plan(ok=False)
                shutil.rmtree(self.source)
                self.source.mkdir()

    def test_source_symlinks_special_types_and_root_aliases(self):
        outside = self.write(self.base, "outside", b"private")
        for destination in (outside, self.base):
            (self.source / "link").symlink_to(destination)
            self.plan(ok=False)
            (self.source / "link").unlink()
        os.mkfifo(self.source / "fifo")
        self.plan(ok=False)
        (self.source / "fifo").unlink()
        self.write(self.source, "special", mode=0o4755)
        self.plan(ok=False)
        (self.source / "special").unlink()
        alias = self.base / "alias"
        alias.symlink_to(self.source, target_is_directory=True)
        self.cli("plan", "--source", alias, ok=False)
        self.cli("plan", "--source", str(alias) + "/../source", ok=False)
        self.cli("plan", "--source", self.target, ok=False)
        nested = self.target / "nested-source"
        nested.mkdir()
        self.cli("plan", "--source", nested, ok=False)

    def test_target_symlinks_and_obstructions_never_touch_outside(self):
        self.write(self.source, "folder/file")
        outside = self.base / "outside"
        outside.mkdir()
        self.write(outside, "file", b"outside")
        plan = self.plan()
        (self.target / "folder").symlink_to(outside, target_is_directory=True)
        self.apply(plan, ok=False)
        self.plan(ok=False)
        self.assertEqual((outside / "file").read_bytes(), b"outside")
        (self.target / "folder").unlink()
        self.write(self.target, "folder", b"blocking file")
        plan = self.plan()
        self.assertEqual(plan["status"], "conflict")
        self.apply(plan, ok=False)
        (self.target / "folder").unlink()
        (self.target / "folder/file").mkdir(parents=True)
        self.assertEqual(self.plan()["status"], "conflict")
        alias = self.base / "target-alias"
        alias.symlink_to(self.target, target_is_directory=True)
        original = self.target
        self.target = alias
        self.cli("status", ok=False)
        self.target = original

    def test_managed_file_type_transitions_conflict(self):
        self.write(self.source, "file")
        self.install()
        (self.source / "file").unlink()
        self.write(self.source, "file/nested")
        plan = self.plan()
        self.assertEqual(plan["status"], "conflict")
        self.apply(plan, ok=False)

    def test_malformed_metadata_is_never_repaired(self):
        self.write(self.source, "file")
        self.install()
        state_path = self.target / ".agent-project/state.json"
        original = json.loads(state_path.read_text())
        saved_plan = self.plan()
        variants = [None, {}, {**original, "schema_version": True}, {**original, "files": []},
                    {**original, "files": {"../outside": {"sha256": "0" * 64, "mode": 420}}},
                    {**original, "files": {"file": {"sha256": "bad", "mode": 420}}},
                    {**original, "files": {"file": {"sha256": "0" * 64, "mode": True}}},
                    {**original, "directories": ["file"]}, {**original, "directories": ["a", "a"]},
                    {**original, "directories": ["missing/parent"]},
                    {**original, "transaction_id": "invalid"}]
        for value in variants:
            with self.subTest(state=value):
                state_path.write_text(json.dumps(value))
                before = snapshot(self.target)
                self.plan(ok=False)
                self.cli("status", ok=False)
                self.apply(saved_plan, ok=False)
                self.assertEqual(snapshot(self.target), before)
        state_path.write_text(json.dumps(original))
        pending = self.target / ".agent-project/transaction-interrupted"
        pending.mkdir()
        before = snapshot(self.target)
        self.plan(ok=False)
        self.cli("status", ok=False)
        self.assertEqual(snapshot(self.target), before)

    def test_metadata_symlinks_and_hardlinks(self):
        self.write(self.source, "file")
        outside = self.base / "outside-meta"
        outside.mkdir()
        (self.target / ".agent-project").symlink_to(outside, target_is_directory=True)
        self.plan(ok=False)
        self.cli("status", ok=False)
        self.assertEqual(list(outside.iterdir()), [])
        (self.target / ".agent-project").unlink()
        self.install()
        state_path = self.target / ".agent-project/state.json"
        backup = self.base / "state-backup"
        state_path.rename(backup)
        state_path.symlink_to(backup)
        self.plan(ok=False)
        self.cli("status", ok=False)
        state_path.unlink()
        os.link(backup, state_path)
        self.plan(ok=False)
        self.cli("status", ok=False)

    @unittest.skipIf(os.getuid() == 0, "requires normal POSIX permission enforcement")
    def test_io_failure_rolls_back_prior_updates(self):
        self.write(self.source, "a")
        self.write(self.source, "z/file")
        self.install()
        self.write(self.source, "a", b"new a")
        self.write(self.source, "z/file", b"new z")
        blocked = self.target / "z"
        blocked.chmod(0o555)
        try:
            plan = self.plan()
            self.apply(plan, ok=False)
            self.assertEqual((self.target / "a").read_bytes(), b"original\n")
            self.assertEqual((self.target / "z/file").read_bytes(), b"original\n")
            self.assertEqual(self.cli("status")["local_changes"], [])
        finally:
            blocked.chmod(0o755)
        self.apply(self.plan())
        self.assertEqual((self.target / "a").read_bytes(), b"new a")
        self.assertEqual((self.target / "z/file").read_bytes(), b"new z")

    def test_cooperative_apply_lock_has_no_metadata_side_effect(self):
        self.write(self.source, "file")
        plan = self.plan()
        handle = os.open(self.target, os.O_RDONLY | os.O_DIRECTORY)
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.apply(plan, ok=False)
            self.plan(ok=False)
            self.cli("status", ok=False)
            self.adopt(ok=False)
        finally:
            os.close(handle)
        self.apply(plan)

    def test_hardlinked_managed_file_update_does_not_modify_other_link(self):
        self.write(self.source, "file")
        self.install()
        outside = self.base / "outside-link"
        os.link(self.target / "file", outside)
        self.write(self.source, "file", b"new")
        self.apply(self.plan())
        self.assertEqual(outside.read_bytes(), b"original\n")
        self.assertEqual((self.target / "file").read_bytes(), b"new")

    def test_status_works_without_source_and_ignores_git_symlink(self):
        self.write(self.source, "file")
        self.install()
        shutil.rmtree(self.source)
        (self.target / ".git").symlink_to(self.base / "absent-git")
        before = snapshot(self.target)
        self.assertEqual(self.cli("status")["managed_paths"], ["file"])
        self.assertEqual(snapshot(self.target), before)

    def test_status_before_install_is_read_only(self):
        self.write(self.target, "user", b"preserve")
        before = snapshot(self.target)
        result = self.cli("status")
        self.assertEqual(result["managed_paths"], [])
        self.assertEqual(result["local_changes"], [])
        self.assertEqual(snapshot(self.target), before)

    def test_adoption_binary_modes_names_and_repeated_noop(self):
        self.write(self.source, ".hidden/日本語 space/run", bytes(range(256)), 0o751)
        self.write(self.source, "AGENTS.md", b"team instructions\n")
        shutil.copytree(self.source, self.target, dirs_exist_ok=True)
        # Only executable bits need match at adoption; all project modes are retained.
        (self.target / "AGENTS.md").chmod(0o600)
        self.write(self.target, ".git/config", b"never touch")
        self.write(self.target, "unrelated", b"private")
        self.assertEqual(self.plan()["status"], "conflict")
        result = self.adopt()
        self.assertEqual(result["status"], "applied")
        self.assertIsInstance(result["transaction_id"], str)
        status = self.cli("status")
        self.assertEqual(status["managed_paths"], [".hidden/日本語 space/run", "AGENTS.md"])
        self.assertEqual([c["path"] for c in status["local_changes"]], ["AGENTS.md"])
        before = snapshot(self.target)
        self.assertEqual(self.adopt(), {"schema_version": 1, "status": "noop", "transaction_id": None})
        self.assertEqual(self.apply(self.plan())["status"], "noop")
        self.assertEqual(snapshot(self.target), before)
        self.write(self.source, "AGENTS.md", b"updated instructions\n")
        self.apply(self.plan())
        self.assertEqual((self.target / "AGENTS.md").read_bytes(), b"updated instructions\n")
        self.assertEqual(stat.S_IMODE((self.target / "AGENTS.md").stat().st_mode), 0o600)

    def test_adoption_rejects_every_mismatch_without_partial_ownership(self):
        self.write(self.source, "a", b"matching")
        self.write(self.source, "z/file", b"original", 0o755)
        for mutation in ("bytes", "execute_mode", "missing", "directory", "parent_file"):
            with self.subTest(mutation=mutation):
                shutil.rmtree(self.target)
                shutil.copytree(self.source, self.target)
                path = self.target / "z/file"
                if mutation == "bytes":
                    path.write_bytes(b"customized")
                elif mutation == "execute_mode":
                    path.chmod(0o744)
                elif mutation == "missing":
                    path.unlink()
                elif mutation == "directory":
                    path.unlink()
                    path.mkdir()
                else:
                    shutil.rmtree(self.target / "z")
                    self.write(self.target, "z")
                self.adopt(ok=False)
                self.assertFalse((self.target / ".agent-project").exists())

    def test_adoption_rejects_conflicting_existing_ownership(self):
        self.write(self.source, "file")
        shutil.copytree(self.source, self.target, dirs_exist_ok=True)
        self.adopt()
        self.write(self.source, "added")
        self.write(self.target, "added")
        self.adopt(ok=False)
        self.assertEqual(self.cli("status")["managed_paths"], ["file"])
        (self.source / "added").unlink()
        self.write(self.source, "file", b"changed")
        self.write(self.target, "file", b"changed")
        self.adopt(ok=False)
        # Normal updates, including convergence, still work.
        self.apply(self.plan())
        self.assertEqual(self.cli("status")["local_changes"], [])
        other = self.base / "other-source"
        shutil.copytree(self.source, other)
        self.source = other
        self.adopt(ok=False)

    def test_adoption_symlinks_reserved_paths_and_metadata(self):
        self.write(self.source, "folder/file")
        shutil.copytree(self.source, self.target, dirs_exist_ok=True)
        for root in (self.source, self.target):
            for relative_path in ("folder/file", "folder"):
                with self.subTest(root=root, path=relative_path):
                    path = root / relative_path
                    moved = self.base / "moved"
                    path.rename(moved)
                    path.symlink_to(moved, target_is_directory=moved.is_dir())
                    self.adopt(ok=False)
                    path.unlink()
                    moved.rename(path)
        for reserved in (".git", ".agent-project"):
            (self.source / reserved).mkdir()
            self.adopt(ok=False)
            (self.source / reserved).rmdir()
        self.adopt()
        state_path = self.target / ".agent-project/state.json"
        old = self.base / "state"
        state_path.rename(old)
        state_path.symlink_to(old)
        self.adopt(ok=False)
        state_path.unlink()
        old.rename(state_path)
        state_path.write_text("{}")
        self.adopt(ok=False)

    def test_adoption_does_not_install_empty_directories(self):
        (self.source / "empty").mkdir()
        self.write(self.source, "file")
        self.write(self.target, "file")
        self.adopt()
        self.assertFalse((self.target / "empty").exists())
        self.apply(self.plan())
        self.assertTrue((self.target / "empty").is_dir())

    def test_adopted_v1_local_edits_v2_merge_v3_merge_and_deletion(self):
        v1 = b"first\nsecond\nthird\nfourth\nfifth\nlast\n"
        self.write(self.source, "team notes.txt", v1)
        shutil.copytree(self.source, self.target, dirs_exist_ok=True)
        self.adopt()
        self.write(self.target, "team notes.txt", v1.replace(b"first", b"local private first"))
        v2 = v1.replace(b"last", b"upstream last")
        self.write(self.source, "team notes.txt", v2)
        plan = self.plan()
        self.assertEqual(self.kinds(plan)["team notes.txt"], "update")
        self.assertNotIn("local private first", json.dumps(plan))
        # Unrelated creations AND edits inside an affected directory remain safe.
        self.write(self.target, "unrelated", b"new user file")
        self.write(self.target, ".git/config", b"git user data")
        self.apply(plan)
        expected_v2 = v2.replace(b"first", b"local private first")
        self.assertEqual((self.target / "team notes.txt").read_bytes(), expected_v2)
        status = self.cli("status")
        self.assertEqual([c["path"] for c in status["local_changes"]], ["team notes.txt"])
        self.assertNotIn("local private first", json.dumps(status))
        self.assertEqual(self.apply(self.plan())["status"], "noop")
        v3 = v2.replace(b"third", b"upstream third")
        self.write(self.source, "team notes.txt", v3)
        self.write(self.target, "team notes.txt", expected_v2.replace(b"fifth", b"local fifth"))
        self.apply(self.plan())
        self.assertEqual((self.target / "team notes.txt").read_bytes(),
                         v3.replace(b"first", b"local private first").replace(b"fifth", b"local fifth"))
        self.assertEqual((self.target / "unrelated").read_bytes(), b"new user file")
        self.assertEqual((self.target / ".git/config").read_bytes(), b"git user data")
        (self.source / "team notes.txt").unlink()
        self.apply(self.plan(), ok=False)

    def test_line_merge_boundaries_insertions_deletions_and_binary(self):
        cases = [
            (b"a\nb\nc\n", b"A\nb\nc\n", b"a\nb\nC\n", b"A\nb\nC\n"),
            (b"a\nb\nc\n", b"b\nc\n", b"a\nb\nC\n", b"b\nC\n"),
            (b"a\nb\nc\n", b"local\na\nb\nc\n", b"a\nb\nc\nup\n", b"local\na\nb\nc\nup\n"),
            (b"a\nb\nc\n", b"A\nb\nc\n", b"a\nB\nc\n", b"A\nB\nc\n"),
            (b"a\nb\nc\n", b"same\na\nb\nc\n", b"same\na\nb\nC\n", b"same\na\nb\nC\n"),
            (b"a\nb\nc\n", b"local\na\nb\nc\n", b"up\na\nb\nc\n", None),
            (b"a\nb\nc\n", b"a\nlocal\nb\nc\n", b"A\nb\nc\n", None),
            (b"a\nb\nc\n", b"a\nc\n", b"a\nB\nc\n", None),
            (b"a\nb\nc\n", b"A\nb\nc\n", b"UP\nb\nc\n", None),
            (b"a\r\nb\r\nc", b"A\r\nb\r\nc", b"a\r\nb\r\nC", b"A\r\nb\r\nC"),
            (b"a\nb\nc\n", b"A\nb\nc\n", b"a\nb\nc", b"A\nb\nc"),
            (b"a\x00\nb\nc\n", b"A\x00\nb\nc\n", b"a\x00\nb\nC\n", None),
            (b"a\xff\nb\nc\n", b"A\xff\nb\nc\n", b"a\xff\nb\nC\n", None),
            (b"a\x01\nb\nc\n", b"A\x01\nb\nc\n", b"a\x01\nb\nC\n", None),
            (b"a\x00", b"same\x00", b"same\x00", b"same\x00"),
        ]
        for number, (base, local, upstream, expected) in enumerate(cases):
            path = f"case-{number}"
            self.write(self.source, path, base)
        self.install()
        for number, (base, local, upstream, expected) in enumerate(cases):
            with self.subTest(number=number):
                path = f"case-{number}"
                self.write(self.target, path, local)
                self.write(self.source, path, upstream)
                plan = self.plan()
                if expected is None:
                    self.assertEqual(self.kinds(plan)[path], "conflict")
                    self.apply(plan, ok=False)
                    self.assertEqual((self.target / path).read_bytes(), local)
                    # Resolve this case before testing the next independent case.
                    self.write(self.target, path, base)
                    self.apply(self.plan())
                else:
                    self.apply(plan)
                    self.assertEqual((self.target / path).read_bytes(), expected)

    def test_content_and_modes_merge_independently(self):
        self.write(self.source, "local-mode")
        self.write(self.source, "upstream-mode")
        self.write(self.source, "competing-mode")
        self.install()
        (self.target / "local-mode").chmod(0o755)
        self.write(self.source, "local-mode", b"new upstream")
        self.write(self.target, "upstream-mode", b"new local")
        (self.source / "upstream-mode").chmod(0o755)
        (self.target / "competing-mode").chmod(0o754)
        (self.source / "competing-mode").chmod(0o744)
        self.apply(self.plan(), ok=False)
        (self.target / "competing-mode").chmod(0o644)
        self.apply(self.plan())
        self.assertEqual((self.target / "local-mode").read_bytes(), b"new upstream")
        self.assertEqual((self.target / "upstream-mode").read_bytes(), b"new local")
        for path in ("local-mode", "upstream-mode"):
            self.assertEqual(stat.S_IMODE((self.target / path).stat().st_mode), 0o755)

    def test_merge_plan_staleness_and_unrelated_nested_edits(self):
        base = b"first\nsecond\nlast\n"
        self.write(self.source, "nested/file", base)
        self.install()
        self.write(self.target, "nested/user", b"user v1")
        self.write(self.target, "nested/file", base.replace(b"first", b"local"))
        self.write(self.source, "nested/file", base.replace(b"last", b"upstream"))
        for root in (self.source, self.target):
            for mutation in ("bytes", "mode"):
                with self.subTest(root=root, mutation=mutation):
                    path = root / "nested/file"
                    original = path.read_bytes()
                    plan = self.plan()
                    if mutation == "bytes":
                        path.write_bytes(original + b"new\n")
                    else:
                        path.chmod(0o755)
                    self.apply(plan, ok=False)
                    path.write_bytes(original)
                    path.chmod(0o644)
        plan = self.plan()
        self.write(self.target, "nested/user", b"user v2")
        self.write(self.target, "nested/new user", b"preserve")
        self.apply(plan)
        self.assertEqual((self.target / "nested/file").read_bytes(), b"local\nsecond\nupstream\n")
        self.assertEqual((self.target / "nested/user").read_bytes(), b"user v2")
        self.assertEqual((self.target / "nested/new user").read_bytes(), b"preserve")

    def test_edited_conflicts_merge_results_and_target_redirection_rejected(self):
        base = b"a\nb\nc\n"
        self.write(self.source, "file", base)
        self.install()
        self.write(self.target, "file", b"local\nb\nc\n")
        self.write(self.source, "file", b"upstream\nb\nc\n")
        bad = self.plan()
        bad["status"] = "ready"
        bad["actions"][0]["kind"] = "update"
        self.apply(bad, ok=False)
        self.write(self.source, "file", b"a\nb\nupstream\n")
        good = self.plan()
        bad = copy.deepcopy(good)
        bad["actions"][0]["result"]["sha256"] = "0" * 64
        self.apply(bad, ok=False)
        bad = copy.deepcopy(good)
        bad["actions"].append({"path": "file/child", "kind": "add"})
        self.apply(bad, ok=False)
        other = self.base / "other-target"
        shutil.copytree(self.target, other)
        original = self.target
        self.target = other
        try:
            self.apply(good, ok=False)
            bad = copy.deepcopy(good)
            bad["target"] = str(other)
            self.apply(bad, ok=False)
        finally:
            self.target = original
        self.apply(good)
        self.assertEqual((self.target / "file").read_bytes(), b"local\nb\nupstream\n")

    def test_corrupt_common_bases_are_not_repaired_or_exposed(self):
        self.write(self.source, "file", b"private base\n")
        self.install()
        path = self.target / ".agent-project/state.json"
        original = json.loads(path.read_bytes())
        for bases in (None, [], {}, {"file": "%%%"}, {"file": "AA=="},
                      {"file": 123}, {"../escape": ""}):
            with self.subTest(bases=bases):
                path.write_text(json.dumps({**original, "bases": bases}))
                before = snapshot(self.target)
                self.plan(ok=False)
                self.cli("status", ok=False)
                self.adopt(ok=False)
                self.assertEqual(snapshot(self.target), before)
        path.write_text(json.dumps(original))
        self.assertNotIn("private base", json.dumps(self.cli("status")))

    def test_phase1_state_compatibility_and_base_capture_on_update(self):
        base = b"a\nb\nc\n"
        self.write(self.source, "file", base)
        self.install()
        path = self.target / ".agent-project/state.json"
        state = json.loads(path.read_bytes())
        del state["bases"]
        path.write_text(json.dumps(state))
        before = snapshot(self.target)
        self.assertFalse(self.cli("status")["common_base_available"])
        self.assertEqual(self.apply(self.plan())["status"], "noop")
        self.assertEqual(snapshot(self.target), before)
        self.write(self.target, "file", b"local\nb\nc\n")
        self.write(self.source, "file", b"a\nb\nupstream\n")
        self.apply(self.plan(), ok=False)
        self.write(self.target, "file", base)
        self.apply(self.plan())
        self.assertTrue(self.cli("status")["common_base_available"])
        self.write(self.target, "file", b"local\nb\nupstream\n")
        self.write(self.source, "file", b"a\nb\nupstream v3\n")
        self.apply(self.plan())
        self.assertEqual((self.target / "file").read_bytes(), b"local\nb\nupstream v3\n")

    def test_real_template_update_remains_valid_with_local_edit(self):
        shutil.copytree(ROOT / "project", self.source, dirs_exist_ok=True)
        self.install()
        name = "docs/agents/runbook.md"
        base = (self.source / name).read_bytes()
        self.write(self.target, name, b"Local team notes.\n\n" + base)
        self.write(self.source, name, base + b"\nUpstream maintenance notes.\n")
        self.apply(self.plan())
        self.assertEqual((self.target / name).read_bytes(),
                         b"Local team notes.\n\n" + base + b"\nUpstream maintenance notes.\n")
        check = subprocess.run(["python3", str(ROOT / "scripts/validate-agent-contracts.py"),
                                "--template-root", str(self.target)], capture_output=True, text=True,
                               env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)

    @unittest.skipIf(os.getuid() == 0, "requires normal POSIX permission enforcement")
    def test_failed_merge_transaction_restores_local_bytes_and_common_base(self):
        base = b"a\nb\nc\n"
        self.write(self.source, "a", base)
        self.write(self.source, "z/file", base)
        self.install()
        local = b"local\nb\nc\n"
        self.write(self.target, "a", local)
        self.write(self.source, "a", b"a\nb\nupstream\n")
        self.write(self.source, "z/file", b"updated\n")
        state_path = self.target / ".agent-project/state.json"
        original_state = state_path.read_bytes()
        (self.target / "z").chmod(0o555)
        try:
            self.apply(self.plan(), ok=False)
            self.assertEqual((self.target / "a").read_bytes(), local)
            self.assertEqual((self.target / "z/file").read_bytes(), base)
            self.assertEqual(state_path.read_bytes(), original_state)
        finally:
            (self.target / "z").chmod(0o755)
        self.apply(self.plan())
        self.assertEqual((self.target / "a").read_bytes(), b"local\nb\nupstream\n")

    @unittest.skipIf(os.getuid() == 0, "requires normal POSIX permission enforcement")
    def test_failed_adoption_metadata_creation_preserves_project(self):
        self.write(self.source, "file")
        self.write(self.target, "file")
        self.target.chmod(0o555)
        try:
            self.adopt(ok=False)
            self.assertFalse((self.target / ".agent-project").exists())
        finally:
            self.target.chmod(0o755)
        self.adopt()


class TransactionTests(unittest.TestCase):
    setUp = LifecycleTests.setUp
    write = LifecycleTests.write
    cli = LifecycleTests.cli
    plan = LifecycleTests.plan
    apply = LifecycleTests.apply
    install = LifecycleTests.install
    adopt = LifecycleTests.adopt
    kinds = LifecycleTests.kinds

    def crash(self, plan, count=1):
        self.plan_file.write_text(json.dumps(plan))
        result = subprocess.run([str(CLI), "apply", "--target", str(self.target),
                                 "--plan", str(self.plan_file), "--json"], capture_output=True,
                                env={**os.environ, "AGENT_PROJECT_TEST_CRASH_AFTER_REPLACE": str(count)})
        self.assertEqual(result.returncode, 99, result.stdout + result.stderr)
        self.assertEqual(result.stdout, b"")
        return self.cli("status")["pending_transaction"]

    def journal(self, identifier):
        return self.target / ".agent-project" / (identifier + ".json")

    def rollback(self, identifier, ok=True):
        before = snapshot(self.target)
        result = self.cli("rollback", "--transaction", identifier, ok=ok)
        if not ok:
            self.assertEqual(snapshot(self.target), before)
        return result

    def test_crashed_install_pending_refusal_recovery_and_repeat(self):
        self.write(self.source, "a", bytes(range(256)), 0o751)
        self.write(self.source, "nested/日本語 space", b"new")
        self.write(self.target, "unrelated", b"keep")
        plan = self.plan()
        identifier = self.crash(plan)
        self.assertIsInstance(identifier, str)
        self.assertEqual((self.target / "a").read_bytes(), bytes(range(256)))
        self.assertFalse((self.target / "nested/日本語 space").exists())
        before = snapshot(self.target)
        self.apply(plan, ok=False)
        self.adopt(ok=False)
        self.rollback(identifier, ok=False)
        self.plan(ok=False)
        self.assertEqual(snapshot(self.target), before)
        self.write(self.target, "nested/local", b"user after crash")
        shutil.rmtree(self.source)
        self.assertEqual(self.cli("recover")["status"], "recovered")
        self.assertFalse((self.target / "a").exists())
        self.assertEqual((self.target / "nested/local").read_bytes(), b"user after crash")
        self.assertEqual((self.target / "unrelated").read_bytes(), b"keep")
        self.assertEqual(self.cli("status")["managed_paths"], [])
        self.assertIsNone(self.cli("status")["pending_transaction"])
        before = snapshot(self.target)
        self.assertEqual(self.cli("recover")["status"], "noop")
        self.assertEqual(snapshot(self.target), before)

    def test_crash_each_replacement_and_deletion_recovers_exact_prior_state(self):
        for count in (1, 2, 3):
            with self.subTest(count=count):
                shutil.rmtree(self.source)
                shutil.rmtree(self.target)
                self.source.mkdir()
                self.target.mkdir()
                self.write(self.source, "a", b"a", 0o755)
                self.write(self.source, "b", b"b")
                self.write(self.source, "c", b"c")
                self.install()
                state = (self.target / ".agent-project/state.json").read_bytes()
                self.write(self.source, "a", b"new", 0o644)
                (self.source / "b").unlink()
                self.write(self.source, "c", b"new c")
                self.crash(self.plan(), count)
                self.cli("recover")
                self.assertEqual((self.target / "a").read_bytes(), b"a")
                self.assertEqual(stat.S_IMODE((self.target / "a").stat().st_mode), 0o755)
                self.assertEqual((self.target / "b").read_bytes(), b"b")
                self.assertEqual((self.target / "c").read_bytes(), b"c")
                self.assertEqual((self.target / ".agent-project/state.json").read_bytes(), state)
                self.apply(self.plan())
                self.assertFalse((self.target / "b").exists())

    def test_recovery_all_paths_preflight_preserves_post_crash_edits(self):
        self.write(self.source, "a")
        self.write(self.source, "z")
        self.install()
        self.write(self.source, "a", b"new a")
        self.write(self.source, "z", b"new z")
        self.crash(self.plan(), 2)
        self.write(self.target, "z", b"post crash user edit")
        before = snapshot(self.target)
        result = self.cli("recover", ok=False)
        self.assertIn("z", result["error"])
        self.assertEqual(snapshot(self.target), before)
        self.assertEqual((self.target / "a").read_bytes(), b"new a")
        self.write(self.target, "z", b"new z")
        self.cli("recover")
        self.assertEqual((self.target / "a").read_bytes(), b"original\n")

    def test_recovery_refuses_user_creation_at_unreached_path_and_mode_edits(self):
        self.write(self.source, "a")
        self.write(self.source, "z")
        self.crash(self.plan())
        self.write(self.target, "z", b"user creation")
        before = snapshot(self.target)
        self.cli("recover", ok=False)
        self.assertEqual(snapshot(self.target), before)
        (self.target / "z").unlink()
        (self.target / "a").chmod(0o755)
        before = snapshot(self.target)
        self.cli("recover", ok=False)
        self.assertEqual(snapshot(self.target), before)
        (self.target / "a").chmod(0o644)
        self.cli("recover")

    def test_corrupt_missing_backup_and_resigned_unsafe_journal_fail_closed(self):
        import hashlib
        self.write(self.source, "a")
        self.install()
        self.write(self.source, "a", b"new")
        identifier = self.crash(self.plan())
        path = self.journal(identifier)
        original = path.read_bytes()
        for mutation in ("checksum", "backup", "missing", "traversal", "duplicate", "target", "cursor"):
            with self.subTest(mutation=mutation):
                envelope = json.loads(original)
                record = envelope["record"]
                if mutation == "checksum":
                    envelope["sha256"] = "0" * 64
                elif mutation == "backup":
                    record["entries"][0]["before"]["data"] = "AA=="
                elif mutation == "missing":
                    del record["entries"][0]["before"]
                elif mutation == "traversal":
                    record["entries"][0]["path"] = "../outside"
                elif mutation == "duplicate":
                    record["entries"].append(record["entries"][0])
                elif mutation == "target":
                    record["target"] = str(self.base)
                else:
                    record["cursor"] = 99
                if mutation != "checksum":
                    body = (json.dumps(record, sort_keys=True, ensure_ascii=True, indent=2) + "\n").encode()
                    envelope["sha256"] = hashlib.sha256(body).hexdigest()
                path.write_text(json.dumps(envelope))
                before = snapshot(self.target)
                self.cli("recover", ok=False)
                self.cli("status", ok=False)
                self.assertEqual(snapshot(self.target), before)
        path.write_bytes(original)
        self.cli("recover")

    def test_recovery_symlink_file_parent_metadata_and_backup(self):
        self.write(self.source, "nested/a")
        identifier = self.crash(self.plan())
        outside = self.base / "outside"
        outside.mkdir()
        self.write(outside, "a", b"outside")
        for path in (self.target / "nested/a", self.target / "nested", self.journal(identifier),
                     self.target / ".agent-project"):
            with self.subTest(path=path):
                moved = self.base / "saved"
                path.rename(moved)
                path.symlink_to(outside if moved.is_dir() else outside / "a")
                before = snapshot(self.target)
                self.cli("recover", ok=False)
                self.assertEqual(snapshot(self.target), before)
                self.assertEqual((outside / "a").read_bytes(), b"outside")
                path.unlink()
                moved.rename(path)
        self.cli("recover")

    def test_rollback_merged_update_restores_local_content_modes_and_baseline(self):
        base = b"first\nsecond\nlast\n"
        self.write(self.source, "a", base)
        self.write(self.source, "deleted", b"delete me", 0o751)
        self.install()
        self.write(self.target, "a", b"local\nsecond\nlast\n", 0o755)
        prior = (self.target / ".agent-project/state.json").read_bytes()
        self.write(self.source, "a", b"first\nsecond\nupstream\n")
        (self.source / "deleted").unlink()
        self.write(self.source, "new/added", b"addition")
        identifier = self.apply(self.plan())["transaction_id"]
        self.write(self.target, "new/unrelated", b"keep")
        self.assertEqual((self.target / "a").read_bytes(), b"local\nsecond\nupstream\n")
        self.assertEqual(self.rollback(identifier)["status"], "rolled_back")
        self.assertEqual((self.target / "a").read_bytes(), b"local\nsecond\nlast\n")
        self.assertEqual(stat.S_IMODE((self.target / "a").stat().st_mode), 0o755)
        self.assertEqual((self.target / "deleted").read_bytes(), b"delete me")
        self.assertEqual(stat.S_IMODE((self.target / "deleted").stat().st_mode), 0o751)
        self.assertFalse((self.target / "new/added").exists())
        self.assertEqual((self.target / "new/unrelated").read_bytes(), b"keep")
        self.assertEqual((self.target / ".agent-project/state.json").read_bytes(), prior)
        before = snapshot(self.target)
        self.assertEqual(self.rollback(identifier)["status"], "noop")
        self.assertEqual(snapshot(self.target), before)
        self.apply(self.plan())

    def test_rollback_preflight_rejects_late_edit_before_any_write(self):
        self.write(self.source, "a")
        self.write(self.source, "z")
        self.install()
        self.write(self.source, "a", b"new a")
        self.write(self.source, "z", b"new z")
        identifier = self.apply(self.plan())["transaction_id"]
        self.write(self.target, "z", b"user")
        self.rollback(identifier, ok=False)
        self.assertEqual((self.target / "a").read_bytes(), b"new a")
        self.write(self.target, "z", b"new z", 0o755)
        self.rollback(identifier, ok=False)
        (self.target / "z").chmod(0o644)
        self.rollback(identifier)

    def test_rollback_latest_only_and_opaque_ids(self):
        self.write(self.source, "a")
        first = self.install()["transaction_id"]
        self.write(self.source, "a", b"v2")
        second = self.apply(self.plan())["transaction_id"]
        for identifier in (first, "../state.json", "/tmp/anything", "a/b", "0" * 32):
            self.rollback(identifier, ok=False)
        self.rollback(second)
        self.rollback(first, ok=False)
        third = self.apply(self.plan())["transaction_id"]
        self.rollback(second, ok=False)
        self.rollback(third)

    def test_rollback_adoption_removes_ownership_without_changing_project_files(self):
        self.write(self.source, "a")
        self.write(self.target, "a")
        identifier = self.adopt()["transaction_id"]
        self.write(self.target, "a", b"later user edit")
        self.rollback(identifier)
        self.assertEqual((self.target / "a").read_bytes(), b"later user edit")
        self.assertEqual(self.cli("status")["managed_paths"], [])
        self.assertEqual(self.plan()["status"], "conflict")

    def test_legacy_state_only_update_and_rollback(self):
        self.write(self.source, "a")
        self.install()
        state_path = self.target / ".agent-project/state.json"
        state = json.loads(state_path.read_bytes())
        del state["journal_version"]
        del state["bases"]
        for path in (self.target / ".agent-project").iterdir():
            if path.name != "state.json":
                path.unlink()
        state_path.write_text(json.dumps(state))
        before = snapshot(self.target)
        self.assertIsNone(self.cli("status")["pending_transaction"])
        self.assertEqual(self.apply(self.plan())["status"], "noop")
        self.assertEqual(snapshot(self.target), before)
        self.rollback(state["transaction_id"], ok=False)
        self.write(self.source, "a", b"v2")
        identifier = self.apply(self.plan())["transaction_id"]
        self.rollback(identifier)
        self.assertEqual(state_path.read_text(), json.dumps(state))
        self.assertEqual((self.target / "a").read_bytes(), b"original\n")

    def test_two_concurrent_clients_one_winner_and_independent_target(self):
        for index in range(25):
            self.write(self.source, f"file-{index:02d}", b"payload" * 100)
        self.plan_file.write_text(json.dumps(self.plan()))
        args = [str(CLI), "apply", "--target", str(self.target), "--plan", str(self.plan_file), "--json"]
        clients = [subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE) for _ in range(2)]
        outputs = [client.communicate(timeout=60) for client in clients]
        self.assertEqual(sorted(client.returncode for client in clients), [0, 1], outputs)
        self.assertIsNone(self.cli("status")["pending_transaction"])
        self.assertEqual(len(self.cli("status")["managed_paths"]), 25)
        for path in self.source.iterdir():
            self.assertEqual((self.target / path.name).read_bytes(), path.read_bytes())
        first = self.target
        handle = os.open(first, os.O_RDONLY | os.O_DIRECTORY)
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.target = self.base / "independent"
            self.target.mkdir()
            self.install()
        finally:
            os.close(handle)
        self.assertEqual(len(self.cli("status")["managed_paths"]), 25)

    def test_invalid_fault_setting_fails_without_writes(self):
        self.write(self.source, "a")
        self.plan_file.write_text(json.dumps(self.plan()))
        for value in ("0", "-1", "nan"):
            before = snapshot(self.target)
            result = subprocess.run([str(CLI), "apply", "--target", str(self.target), "--plan",
                                     str(self.plan_file)], capture_output=True,
                                    env={**os.environ, "AGENT_PROJECT_TEST_CRASH_AFTER_REPLACE": value})
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(snapshot(self.target), before)

    def test_interrupted_recovery_and_rollback_resume_durably(self):
        for operation in ("recover", "rollback"):
            with self.subTest(operation=operation):
                shutil.rmtree(self.source)
                shutil.rmtree(self.target)
                self.source.mkdir()
                self.target.mkdir()
                self.write(self.source, "a")
                self.write(self.source, "z")
                self.install()
                self.write(self.source, "a", b"new a")
                self.write(self.source, "z", b"new z")
                if operation == "recover":
                    identifier = self.crash(self.plan(), 2)
                    args = []
                else:
                    identifier = self.apply(self.plan())["transaction_id"]
                    args = ["--transaction", identifier]
                result = subprocess.run([str(CLI), operation, "--target", str(self.target),
                                         *args, "--json"], capture_output=True,
                                        env={**os.environ, "AGENT_PROJECT_TEST_CRASH_AFTER_RESTORE": "1"})
                self.assertEqual(result.returncode, 99, result.stdout + result.stderr)
                self.assertEqual((self.target / "a").read_bytes(), b"original\n")
                self.assertEqual((self.target / "z").read_bytes(), b"new z")
                self.assertEqual(self.cli("status")["pending_transaction"], identifier)
                self.rollback(identifier, ok=False)
                self.cli("recover")
                self.assertEqual((self.target / "z").read_bytes(), b"original\n")
                self.assertIsNone(self.cli("status")["pending_transaction"])

    def test_missing_pending_journal_fails_closed(self):
        self.write(self.source, "a")
        self.install()
        self.write(self.source, "a", b"new")
        identifier = self.crash(self.plan())
        self.journal(identifier).unlink()
        before = snapshot(self.target)
        self.cli("recover", ok=False)
        self.cli("status", ok=False)
        self.assertEqual(snapshot(self.target), before)
        self.assertEqual((self.target / "a").read_bytes(), b"new")

    def test_missing_completed_journal_fails_closed(self):
        self.write(self.source, "a")
        identifier = self.install()["transaction_id"]
        self.journal(identifier).unlink()
        before = snapshot(self.target)
        self.cli("recover", ok=False)
        self.cli("status", ok=False)
        self.rollback(identifier, ok=False)
        self.assertEqual(snapshot(self.target), before)

    def test_installed_layout_default_source_from_unrelated_cwd(self):
        prefix = self.base / "prefix"
        (prefix / "bin").mkdir(parents=True)
        installed = prefix / "bin/manage-agent-project"
        shutil.copy2(CLI, installed)
        template = prefix / "share/agent-project/template"
        shutil.copytree(ROOT / "project", template)
        args = [str(installed), "plan", "--target", str(self.target), "--json"]
        result = subprocess.run(args, cwd="/", capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        plan = json.loads(result.stdout)
        self.assertEqual(plan["source"], str(template))
        self.plan_file.write_text(json.dumps(plan))
        result = subprocess.run([str(installed), "apply", "--target", str(self.target), "--plan",
                                 str(self.plan_file), "--json"], cwd="/", capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for path, value in snapshot(template).items():
            if value[0] == "file":
                self.assertEqual(snapshot(self.target)[path], value)
        result = subprocess.run([str(installed), "adopt", "--target", str(self.target), "--json"],
                                cwd="/", capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "noop")


if __name__ == "__main__":
    unittest.main()
