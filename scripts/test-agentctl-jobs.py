#!/usr/bin/env python3

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parent.parent
AGENTCTL = ROOT / "scripts/agentctl"


FAKE_PROVIDER = r'''#!/usr/bin/env python3
import json
import os
from pathlib import Path
import subprocess
import sys

kind = __PROVIDER_KIND__
mode = os.environ.get("FAKE_PROVIDER_MODE", "success")
if mode == "exit":
    print("synthetic provider failure")
    raise SystemExit(42)
if mode == "slow-success":
    import time
    time.sleep(0.4)
if mode == "noisy-success":
    print("NOISE_BEGIN" + "x" * (9 * 1024 * 1024))

workspace = Path.cwd()
job_id = os.environ["AGENTCTL_JOB_ID"]

if mode == "invalid":
    result = {"schema_version": 1}
else:
    changed = []
    if mode in {"success", "slow-success", "noisy-success", "scope", "head-mismatch", "grok-duplicate", "grok-conflict"}:
        relative = "forbidden.txt" if mode == "scope" else "result.txt"
        (workspace / relative).write_text(
            f"job={job_id}\n"
            f"resource={os.environ.get('AGENTCTL_RESOURCE_CLASS', '')}\n"
            f"compose={os.environ.get('COMPOSE_PROJECT_NAME', '')}\n"
            f"label={os.environ.get('AGENTCTL_DOCKER_LABEL', '')}\n"
            f"port={os.environ.get('AGENTCTL_PORT', '')}\n"
            f"memory={os.environ.get('GROK_MEMORY', '')}\n",
            encoding="utf-8",
        )
        changed = [relative]
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    if mode == "head-mismatch":
        head = "0" * 40
    status = "blocked" if mode == "blocked" else "ready_for_commit"
    result = {
        "schema_version": 1,
        "job_id": job_id,
        "status": status,
        "summary": "Synthetic provider result.",
        "head_sha": head,
        "changed_paths": changed,
        "dirty_state": {"is_dirty": bool(changed), "paths": changed},
        "checks": [
            {
                "command": "fake-provider",
                "status": "passed",
                "exit_code": 0,
                "summary": "Synthetic check passed."
            }
        ],
        "risks": [],
        "followups": []
    }
    if status == "blocked":
        result["blocked_reason"] = "Synthetic blocker."

if kind == "codex":
    arguments = sys.argv[1:]
    index = arguments.index("--output-last-message")
    output_path = Path(arguments[index + 1])
    output_path.write_text(json.dumps(result), encoding="utf-8")
    print(json.dumps({"argv": arguments}))
elif kind == "claude":
    print(json.dumps({"structured_output": result}))
else:
    if mode == "grok-duplicate":
        encoded = json.dumps(result)
        progress = dict(result)
        progress["changed_paths"] = []
        progress["checks"] = []
        progress["dirty_state"] = {"is_dirty": False, "paths": []}
        progress["summary"] = "Synthetic progress object."
        print(json.dumps({
            "text": json.dumps(progress) + encoded,
            "structuredOutput": None,
            "structuredOutputError": "model did not produce structured output",
            "argv": sys.argv[1:]
        }))
    elif mode == "grok-conflict":
        other = dict(result)
        other["checks"] = []
        other["summary"] = "Incomplete final result."
        print(json.dumps({
            "text": json.dumps(result) + json.dumps(other),
            "structuredOutput": None,
            "structuredOutputError": "model did not produce structured output",
            "argv": sys.argv[1:]
        }))
    else:
        print(json.dumps({"structuredOutput": result, "argv": sys.argv[1:]}))
'''


class AgentctlJobTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="agentctl-jobs-")
        self.root = Path(self.temp.name)
        self.workspace = self.root / "workspace"
        self.workspace.mkdir()
        subprocess.run(["git", "init", "-q", str(self.workspace)], check=True)
        subprocess.run(
            ["git", "-C", str(self.workspace), "config", "user.email", "test@example.invalid"],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(self.workspace), "config", "user.name", "test"], check=True
        )
        shutil.copytree(ROOT / "project/.agent", self.workspace / ".agent")
        shutil.copytree(ROOT / "project/.codex", self.workspace / ".codex")
        shutil.copytree(ROOT / "project/.claude", self.workspace / ".claude")
        shutil.copytree(ROOT / "project/.grok", self.workspace / ".grok")
        shutil.copy2(ROOT / "project/AGENTS.md", self.workspace / "AGENTS.md")
        shutil.copy2(ROOT / "project/CLAUDE.md", self.workspace / "CLAUDE.md")
        (self.workspace / "tracked.txt").write_text("base\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.workspace), "add", "."], check=True)
        subprocess.run(["git", "-C", str(self.workspace), "commit", "-qm", "base"], check=True)
        self.base_sha = subprocess.check_output(
            ["git", "-C", str(self.workspace), "rev-parse", "HEAD"], text=True
        ).strip()

        self.state_dir = self.root / "state"
        self.bin_dir = self.root / "bin"
        self.bin_dir.mkdir()
        self.codex = self.make_provider("codex", "codex")
        self.claude = self.make_provider("claude", "claude")
        self.grok = self.make_provider("grok", "grok")
        self.extra_environment: dict[str, str] = {"MIRA_COMPANION_ENABLED": "0"}

    def tearDown(self) -> None:
        self.temp.cleanup()

    def make_provider(self, filename: str, kind: str) -> Path:
        path = self.bin_dir / filename
        path.write_text(
            FAKE_PROVIDER.replace("__PROVIDER_KIND__", repr(kind)), encoding="utf-8"
        )
        path.chmod(0o755)
        return path

    def invoke(
        self,
        *arguments: str,
        mode: str = "success",
    ) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment.update(
            {
                "AGENTCTL_CODEX_BIN": str(self.codex),
                "AGENTCTL_CODEX_TRUSTED_BIN": str(self.codex),
                "AGENTCTL_CLAUDE_BIN": str(self.claude),
                "AGENTCTL_CLAUDE_TRUSTED_BIN": str(self.claude),
                "AGENTCTL_GROK_BIN": str(self.grok),
                "AGENTCTL_GROK_TRUSTED_BIN": str(self.grok),
                "FAKE_PROVIDER_MODE": mode,
            }
        )
        environment.update(self.extra_environment)
        return subprocess.run(
            [
                sys.executable,
                str(AGENTCTL),
                "--state-dir",
                str(self.state_dir),
                *arguments,
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=environment,
            check=False,
        )

    def popen(self, *arguments: str, mode: str = "success") -> subprocess.Popen[str]:
        environment = os.environ.copy()
        environment.update(
            {
                "AGENTCTL_CODEX_BIN": str(self.codex),
                "AGENTCTL_CLAUDE_BIN": str(self.claude),
                "AGENTCTL_GROK_BIN": str(self.grok),
                "FAKE_PROVIDER_MODE": mode,
            }
        )
        environment.update(self.extra_environment)
        return subprocess.Popen(
            [
                sys.executable,
                str(AGENTCTL),
                "--state-dir",
                str(self.state_dir),
                *arguments,
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=environment,
        )

    def write_task(
        self,
        name: str,
        *,
        permission_profile: str = "safe",
        dependency_job_ids: list[str] | None = None,
        resource_class: str = "write",
        priority: str | None = None,
    ) -> Path:
        task = {
            "schema_version": 1,
            "objective": "Create one deterministic result file.",
            "role": "implementer",
            "lane": "write",
            "permission_profile": permission_profile,
            "resource_class": resource_class,
            "scope": {
                "allowed_paths": ["result.txt"],
                "forbidden_paths": ["forbidden.txt", ".devcontainer/"],
            },
            "acceptance": [{"kind": "command", "value": "fake-provider"}],
            "constraints": ["Do not push or merge."],
            "dependency_job_ids": dependency_job_ids or [],
        }
        if priority is not None:
            task["priority"] = priority
        path = self.workspace / name
        path.write_text(json.dumps(task), encoding="utf-8")
        return path

    def create(self, name: str = "task.json", **task_options: object) -> dict[str, object]:
        task = self.write_task(name, **task_options)
        result = self.invoke(
            "job",
            "create",
            "--workspace",
            str(self.workspace),
            "--task",
            str(task),
            "--base",
            "HEAD",
            "--json",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def test_project_identity_is_stable_and_job_base_is_immutable(self) -> None:
        first = self.invoke("project", "register", "--workspace", str(self.workspace), "--json")
        second = self.invoke("project", "register", "--workspace", str(self.workspace), "--json")
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(json.loads(first.stdout)["project_id"], json.loads(second.stdout)["project_id"])

        job = self.create()
        self.assertRegex(str(job["job_id"]), r"^[0-9A-HJKMNP-TV-Z]{26}$")
        self.assertEqual(job["base_sha"], self.base_sha)
        stored_task = json.loads(Path(str(job["task_path"])).read_text(encoding="utf-8"))
        self.assertEqual(stored_task["job_id"], job["job_id"])
        self.assertEqual(stored_task["base_sha"], self.base_sha)
        self.assertEqual(stored_task["priority"], "normal")
        self.assertEqual(job["priority"], "normal")

    def test_schema_v1_database_is_migrated_in_place(self) -> None:
        self.state_dir.mkdir(mode=0o700)
        database = self.state_dir / "state.db"
        with sqlite3.connect(database) as connection:
            connection.executescript(
                """
                CREATE TABLE schema_meta (
                    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                    version INTEGER NOT NULL
                );
                INSERT INTO schema_meta(singleton, version) VALUES (1, 1);
                CREATE TABLE jobs (
                    job_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    base_sha TEXT NOT NULL,
                    role TEXT NOT NULL,
                    lane TEXT NOT NULL,
                    permission_profile TEXT NOT NULL,
                    resource_class TEXT NOT NULL,
                    task_path TEXT NOT NULL,
                    state TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )
        result = self.invoke("job", "show", "0" * 26, "--json")
        self.assertEqual(result.returncode, 2)
        self.assertIn("unknown job", result.stderr)
        with sqlite3.connect(database) as connection:
            version = connection.execute(
                "SELECT version FROM schema_meta WHERE singleton = 1"
            ).fetchone()[0]
            columns = {
                row[1] for row in connection.execute("PRAGMA table_info(jobs)").fetchall()
            }
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            }
        self.assertEqual(version, 2)
        self.assertTrue({"priority", "queue_reason", "queued_at"} <= columns)
        self.assertIn("validations", tables)

    def test_codex_foreground_job_uses_separate_worktree_and_validates(self) -> None:
        job = self.create()
        job_id = str(job["job_id"])
        (self.workspace / "later.txt").write_text("primary advanced\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.workspace), "add", "later.txt"], check=True)
        subprocess.run(["git", "-C", str(self.workspace), "commit", "-qm", "advance primary"], check=True)
        run = self.invoke("job", "run", job_id, "--provider", "codex", "--json")
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        completed = json.loads(run.stdout)
        self.assertEqual(completed["state"], "succeeded")
        attempt = completed["attempts"][0]
        self.assertEqual(attempt["state"], "succeeded")
        self.assertIn(job_id.lower(), str(attempt["branch_name"]))
        self.assertFalse((self.workspace / "result.txt").exists())
        self.assertTrue((Path(str(attempt["workspace_path"])) / "result.txt").is_file())
        self.assertFalse((Path(str(attempt["workspace_path"])) / "later.txt").exists())
        final_result = json.loads(Path(str(attempt["result_path"])).read_text(encoding="utf-8"))
        provider_result = json.loads(
            Path(str(attempt["result_path"])).with_name("provider-result.json").read_text(encoding="utf-8")
        )
        self.assertEqual(provider_result["status"], "ready_for_commit")
        self.assertEqual(final_result["status"], "completed")
        self.assertEqual(final_result["head_sha"], attempt["head_sha"])
        self.assertEqual(final_result["dirty_state"], {"is_dirty": False, "paths": []})
        self.assertEqual(final_result["checks"][-1]["command"], "agentctl broker commit")
        commit_subject = subprocess.check_output(
            ["git", "-C", str(attempt["workspace_path"]), "log", "-1", "--format=%s"],
            text=True,
        ).strip()
        self.assertTrue(commit_subject.startswith(f"agentctl({job_id.lower()}):"))
        process_log = Path(str(attempt["log_path"]))
        self.assertEqual(process_log.stat().st_mode & 0o777, 0o600)
        argv_record = json.loads(process_log.read_text(encoding="utf-8"))
        self.assertIn("--ask-for-approval", argv_record["argv"])
        self.assertIn("workspace-write", argv_record["argv"])
        process_leases = [lease for lease in completed["leases"] if lease["kind"] == "process"]
        self.assertEqual(len(process_leases), 1)
        self.assertIsNotNone(process_leases[0]["released_at"])

        validated = self.invoke("job", "validate", job_id, "--json")
        self.assertEqual(validated.returncode, 0, validated.stdout + validated.stderr)
        validated_payload = json.loads(validated.stdout)
        self.assertEqual(validated_payload["state"], "validated")
        self.assertEqual(validated_payload["validation"]["status"], "passed")
        validation_path = Path(validated_payload["validations"][0]["report_path"])
        self.assertTrue(validation_path.is_file())
        self.assertEqual(validation_path.stat().st_mode & 0o777, 0o600)

    def test_two_jobs_from_one_base_can_run_concurrently_without_checkout_contamination(self) -> None:
        first = self.create("parallel-1.json")
        second = self.create("parallel-2.json")
        processes = [
            self.popen(
                "job",
                "run",
                str(job["job_id"]),
                "--provider",
                "codex",
                "--json",
                mode="slow-success",
            )
            for job in (first, second)
        ]
        results = [process.communicate(timeout=20) for process in processes]
        for process, (stdout, stderr) in zip(processes, results):
            self.assertEqual(process.returncode, 0, stdout + stderr)
        payloads = [json.loads(stdout) for stdout, _ in results]
        worktrees = {payload["attempts"][0]["workspace_path"] for payload in payloads}
        branches = {payload["attempts"][0]["branch_name"] for payload in payloads}
        self.assertEqual(len(worktrees), 2)
        self.assertEqual(len(branches), 2)
        self.assertFalse((self.workspace / "result.txt").exists())

    def test_claude_structured_output_uses_the_same_result_contract(self) -> None:
        job = self.create("claude-task.json")
        result = self.invoke(
            "job", "run", str(job["job_id"]), "--provider", "claude", "--json"
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["state"], "succeeded")
        stored = json.loads(Path(payload["attempts"][0]["result_path"]).read_text(encoding="utf-8"))
        self.assertEqual(stored["job_id"], job["job_id"])

    def test_grok_structured_output_uses_safe_headless_contract(self) -> None:
        job = self.create("grok-task.json")
        result = self.invoke(
            "job", "run", str(job["job_id"]), "--provider", "grok", "--json"
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["state"], "succeeded")
        attempt = payload["attempts"][0]
        stored = json.loads(Path(attempt["result_path"]).read_text(encoding="utf-8"))
        self.assertEqual(stored["job_id"], job["job_id"])
        provider_log = json.loads(Path(attempt["log_path"]).read_text(encoding="utf-8"))
        arguments = provider_log["argv"]
        self.assertIn("--prompt-file", arguments)
        self.assertIn("/dev/stdin", arguments)
        self.assertIn("--no-subagents", arguments)
        max_turns_index = arguments.index("--max-turns")
        self.assertEqual(arguments[max_turns_index + 1], "64")
        self.assertIn("dontAsk", arguments)
        self.assertIn("workspace", arguments)
        self.assertIn("Glob", arguments)
        self.assertIn("Bash(git push*)", arguments)
        self.assertIn(
            "memory=0",
            (Path(attempt["workspace_path"]) / "result.txt").read_text(encoding="utf-8"),
        )

    def test_provider_lifecycle_reaches_mira_without_job_content(self) -> None:
        mira_state = self.root / "mira-state"
        self.extra_environment.update(
            {
                "AGENTCTL_MIRA_BRIDGE_BIN": str(ROOT / "scripts/mira-codex-hook.py"),
                "MIRA_COMPANION_ENABLED": "1",
                "MIRA_COMPANION_STATE_DIR": str(mira_state),
            }
        )
        job = self.create("mira-grok-task.json")
        result = self.invoke(
            "job", "run", str(job["job_id"]), "--provider", "grok", "--json"
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        state = json.loads((mira_state / "state.json").read_text(encoding="utf-8"))
        timeline = json.loads((mira_state / "timeline.json").read_text(encoding="utf-8"))
        lifecycle = [
            event
            for event in timeline
            if event["event"] in {"AgentJobStart", "AgentJobSucceeded"}
        ]
        self.assertEqual([event["event"] for event in lifecycle], [
            "AgentJobStart",
            "AgentJobSucceeded",
        ])
        self.assertTrue(all(event["provider"] == "grok" for event in lifecycle))
        self.assertTrue(all(event["role"] == "implementer" for event in lifecycle))
        self.assertEqual(state["status"], "success")
        self.assertEqual(state["activeSubagents"], 0)

        persisted = "".join(
            path.read_text(encoding="utf-8") for path in mira_state.glob("*.json")
        )
        self.assertNotIn(str(job["job_id"]), persisted)
        self.assertNotIn("Create one deterministic result file.", persisted)
        self.assertNotIn(str(self.workspace), persisted)

        failed_job = self.create("mira-failed-job.json")
        failed = self.invoke(
            "job",
            "run",
            str(failed_job["job_id"]),
            "--provider",
            "codex",
            mode="exit",
        )
        self.assertEqual(failed.returncode, 2)
        failed_timeline = json.loads(
            (mira_state / "timeline.json").read_text(encoding="utf-8")
        )
        self.assertEqual(failed_timeline[-1]["event"], "AgentJobFailed")
        self.assertEqual(failed_timeline[-1]["provider"], "codex")
        self.assertEqual(failed_timeline[-1]["outcome"], "failure")
        self.assertNotIn(
            str(failed_job["job_id"]),
            "".join(
                path.read_text(encoding="utf-8")
                for path in mira_state.glob("*.json")
            ),
        )

        self.extra_environment["AGENTCTL_MIRA_BRIDGE_BIN"] = str(
            self.root / "missing-mira-bridge"
        )
        fail_open_job = self.create("mira-fail-open.json")
        fail_open = self.invoke(
            "job",
            "run",
            str(fail_open_job["job_id"]),
            "--provider",
            "codex",
            "--json",
        )
        self.assertEqual(fail_open.returncode, 0, fail_open.stdout + fail_open.stderr)

    def test_grok_text_fallback_uses_only_a_fully_valid_final_document(self) -> None:
        recovered_job = self.create("grok-duplicate.json")
        recovered = self.invoke(
            "job",
            "run",
            str(recovered_job["job_id"]),
            "--provider",
            "grok",
            "--json",
            mode="grok-duplicate",
        )
        self.assertEqual(recovered.returncode, 0, recovered.stdout + recovered.stderr)
        self.assertEqual(json.loads(recovered.stdout)["state"], "succeeded")

        conflicting_job = self.create("grok-conflict.json")
        conflicting = self.invoke(
            "job",
            "run",
            str(conflicting_job["job_id"]),
            "--provider",
            "grok",
            "--json",
            mode="grok-conflict",
        )
        self.assertEqual(conflicting.returncode, 2)
        self.assertIn("required acceptance command was not reported as passed", conflicting.stderr)

    def test_provider_exit_never_becomes_success_and_retry_is_explicit(self) -> None:
        job = self.create("retry-task.json")
        job_id = str(job["job_id"])
        failed = self.invoke("job", "run", job_id, "--provider", "codex", mode="exit")
        self.assertEqual(failed.returncode, 2)
        shown = self.invoke("job", "show", job_id, "--json")
        payload = json.loads(shown.stdout)
        self.assertEqual(payload["state"], "failed")
        self.assertEqual(payload["attempts"][0]["exit_code"], 42)

        implicit = self.invoke("job", "run", job_id, "--provider", "codex")
        self.assertEqual(implicit.returncode, 2)
        self.assertIn("--clean-retry", implicit.stderr)
        shown_again = json.loads(self.invoke("job", "show", job_id, "--json").stdout)
        self.assertEqual(len(shown_again["attempts"]), 1)

        retried = self.invoke(
            "job",
            "run",
            job_id,
            "--provider",
            "codex",
            "--clean-retry",
            "--json",
        )
        self.assertEqual(retried.returncode, 0, retried.stdout + retried.stderr)
        retried_payload = json.loads(retried.stdout)
        self.assertEqual(len(retried_payload["attempts"]), 2)
        self.assertEqual(retried_payload["attempts"][1]["number"], 2)
        self.assertNotEqual(
            retried_payload["attempts"][0]["workspace_path"],
            retried_payload["attempts"][1]["workspace_path"],
        )

    def test_invalid_result_and_scope_escape_are_failed_states(self) -> None:
        for index, mode in enumerate(("invalid", "head-mismatch", "scope"), start=1):
            with self.subTest(mode=mode):
                job = self.create(f"invalid-{index}.json")
                result = self.invoke(
                    "job", "run", str(job["job_id"]), "--provider", "codex", mode=mode
                )
                self.assertEqual(result.returncode, 2)
                shown = json.loads(
                    self.invoke("job", "show", str(job["job_id"]), "--json").stdout
                )
                self.assertEqual(shown["state"], "failed")
                self.assertEqual(shown["attempts"][0]["exit_reason"], "result_validation")

    def test_trusted_fast_requires_a_second_explicit_opt_in(self) -> None:
        job = self.create("trusted-task.json", permission_profile="trusted-fast")
        job_id = str(job["job_id"])
        denied = self.invoke("job", "run", job_id, "--provider", "codex")
        self.assertEqual(denied.returncode, 2)
        self.assertIn("--allow-trusted-fast", denied.stderr)
        shown = json.loads(self.invoke("job", "show", job_id, "--json").stdout)
        self.assertEqual(shown["state"], "created")
        self.assertEqual(shown["attempts"], [])

        allowed = self.invoke(
            "job",
            "run",
            job_id,
            "--provider",
            "codex",
            "--allow-trusted-fast",
            "--json",
        )
        self.assertEqual(allowed.returncode, 0, allowed.stdout + allowed.stderr)

    def test_dependency_must_be_explicitly_validated_before_dispatch(self) -> None:
        parent = self.create("dependency-parent.json")
        child = self.create(
            "dependency-child.json", dependency_job_ids=[str(parent["job_id"])]
        )
        blocked = self.invoke(
            "job", "run", str(child["job_id"]), "--provider", "codex"
        )
        self.assertEqual(blocked.returncode, 2)
        self.assertIn("dependencies are not validated", blocked.stderr)
        child_state = json.loads(
            self.invoke("job", "show", str(child["job_id"]), "--json").stdout
        )
        self.assertEqual(child_state["state"], "created")
        self.assertEqual(child_state["attempts"], [])

        parent_run = self.invoke(
            "job", "run", str(parent["job_id"]), "--provider", "codex"
        )
        self.assertEqual(parent_run.returncode, 0, parent_run.stdout + parent_run.stderr)
        parent_validate = self.invoke("job", "validate", str(parent["job_id"]))
        self.assertEqual(
            parent_validate.returncode, 0, parent_validate.stdout + parent_validate.stderr
        )
        child_run = self.invoke(
            "job", "run", str(child["job_id"]), "--provider", "codex"
        )
        self.assertEqual(child_run.returncode, 0, child_run.stdout + child_run.stderr)
        child_validate = self.invoke("job", "validate", str(child["job_id"]))
        self.assertEqual(
            child_validate.returncode, 0, child_validate.stdout + child_validate.stderr
        )
        collected = self.invoke("job", "collect", str(child["job_id"]), "--json")
        self.assertEqual(collected.returncode, 0, collected.stdout + collected.stderr)
        report = json.loads(collected.stdout)
        self.assertEqual(
            report["dependency_order"], [parent["job_id"], child["job_id"]]
        )
        self.assertEqual(
            [entry["job_id"] for entry in report["candidate_commits"]],
            [parent["job_id"], child["job_id"]],
        )
        self.assertEqual(report["integration_assessment"], "review_required")
        self.assertEqual(report["inter_job_path_overlaps"][0]["paths"], ["result.txt"])

    def test_collect_requires_validation_and_writes_immutable_reports(self) -> None:
        job = self.create("collect.json")
        job_id = str(job["job_id"])
        run = self.invoke("job", "run", job_id, "--provider", "codex")
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        premature = self.invoke("job", "collect", job_id)
        self.assertEqual(premature.returncode, 2)
        self.assertIn("requires validated state", premature.stderr)
        validated = self.invoke("job", "validate", job_id)
        self.assertEqual(validated.returncode, 0, validated.stdout + validated.stderr)

        unsafe_target = self.invoke("job", "collect", job_id, "--onto=--help")
        self.assertEqual(unsafe_target.returncode, 2)
        self.assertIn("unsafe Git revision", unsafe_target.stderr)

        first = self.invoke("job", "collect", job_id, "--json")
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        first_report = json.loads(first.stdout)
        self.assertEqual(first_report["status"], "ready")
        self.assertEqual(first_report["integration_assessment"], "clean_candidate")
        self.assertFalse(first_report["automatic_integration_performed"])
        self.assertEqual(len(first_report["candidate_commits"]), 1)
        first_path = Path(first_report["report_path"])
        self.assertTrue(first_path.is_file())
        self.assertEqual(first_path.stat().st_mode & 0o777, 0o600)

        head_sha = first_report["candidate_commits"][0]["head_sha"]
        integrated = self.invoke(
            "job", "collect", job_id, "--onto", head_sha, "--json"
        )
        self.assertEqual(integrated.returncode, 0, integrated.stdout + integrated.stderr)
        second_report = json.loads(integrated.stdout)
        self.assertEqual(
            second_report["integration_assessment"], "already_integrated_or_no_change"
        )
        self.assertEqual(second_report["candidate_commits"], [])
        self.assertNotEqual(first_report["collection_id"], second_report["collection_id"])
        self.assertNotEqual(first_report["report_path"], second_report["report_path"])

        shown = json.loads(self.invoke("job", "show", job_id, "--json").stdout)
        self.assertEqual(
            [entry["profile"] for entry in shown["validations"]],
            ["job", "integration", "integration"],
        )

    def test_foreground_refuses_to_oversubscribe_capacity_without_queueing(self) -> None:
        self.extra_environment["AGENTCTL_CAPACITY_WRITE"] = "0"
        job = self.create("no-capacity.json")
        result = self.invoke("job", "run", str(job["job_id"]), "--provider", "codex")
        self.assertEqual(result.returncode, 2)
        self.assertIn("use --detach to queue", result.stderr)
        shown = json.loads(
            self.invoke("job", "show", str(job["job_id"]), "--json").stdout
        )
        self.assertEqual(shown["state"], "created")
        self.assertEqual(shown["attempts"], [])

    def test_integration_attempt_gets_compose_namespace_and_port_lease(self) -> None:
        job = self.create("integration.json", resource_class="integration")
        result = self.invoke(
            "job", "run", str(job["job_id"]), "--provider", "codex", "--json"
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        attempt = payload["attempts"][0]
        evidence = (Path(attempt["workspace_path"]) / "result.txt").read_text(
            encoding="utf-8"
        )
        self.assertIn(f"resource=integration\n", evidence)
        self.assertIn(f"compose=agent_{str(job['job_id']).lower()}\n", evidence)
        self.assertIn(f"label=dev.agentctl.job={job['job_id']}\n", evidence)
        port_line = next(line for line in evidence.splitlines() if line.startswith("port="))
        self.assertRegex(port_line, r"^port=\d+$")
        runtime_leases = [
            lease
            for lease in payload["leases"]
            if lease["kind"] in {"capacity", "port"}
        ]
        self.assertEqual({lease["kind"] for lease in runtime_leases}, {"capacity", "port"})
        self.assertTrue(all(lease["released_at"] for lease in runtime_leases))

    def test_log_view_is_bounded_redacted_and_path_confined(self) -> None:
        job = self.create("logs.json")
        run = self.invoke(
            "job", "run", str(job["job_id"]), "--provider", "codex", "--json"
        )
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        payload = json.loads(run.stdout)
        attempt = payload["attempts"][0]
        log_path = Path(attempt["log_path"])
        openai_secret = "sk-proj-" + "x" * 32
        xai_secret = "xai-" + "g" * 32
        bearer_secret = "bearer-value-that-must-not-leak"
        basic_secret = "basic-value-that-must-not-leak"
        jwt_secret = "eyJheader12345.eyJpayload12345.signature12345"
        log_path.write_text(
            "discarded line\n"
            f"OPENAI_API_KEY={openai_secret}\n"
            f"provider-token={xai_secret}\n"
            f"Authorization: Bearer {bearer_secret}\n"
            f"Authorization: Basic {basic_secret}\n"
            f"standalone={jwt_secret}\n",
            encoding="utf-8",
        )
        viewed = self.invoke(
            "job",
            "logs",
            str(job["job_id"]),
            "--lines",
            "5",
            "--bytes",
            "1024",
            "--json",
        )
        self.assertEqual(viewed.returncode, 0, viewed.stdout + viewed.stderr)
        log = json.loads(viewed.stdout)
        self.assertNotIn(openai_secret, log["content"])
        self.assertNotIn(xai_secret, log["content"])
        self.assertNotIn(bearer_secret, log["content"])
        self.assertNotIn(basic_secret, log["content"])
        self.assertNotIn(jwt_secret, log["content"])
        self.assertEqual(log["content"].count("[REDACTED]"), 5)
        self.assertGreaterEqual(log["redaction_count"], 5)
        self.assertNotIn("discarded line", log["content"])

        log_path.unlink()
        log_path.symlink_to(log_path.with_name("result.json"))
        linked = self.invoke("job", "logs", str(job["job_id"]))
        self.assertEqual(linked.returncode, 2)
        self.assertIn("symbolic link", linked.stderr)
        log_path.unlink()
        log_path.write_text("restored\n", encoding="utf-8")

        with sqlite3.connect(self.state_dir / "state.db") as connection:
            connection.execute(
                "UPDATE attempts SET log_path = '/etc/passwd' WHERE attempt_id = ?",
                (attempt["attempt_id"],),
            )
        escaped = self.invoke("job", "logs", str(job["job_id"]))
        self.assertEqual(escaped.returncode, 2)
        self.assertIn("canonical attempt evidence path", escaped.stderr)

        with sqlite3.connect(self.state_dir / "state.db") as connection:
            connection.execute(
                "UPDATE attempts SET log_path = ?, result_path = '/etc/passwd' "
                "WHERE attempt_id = ?",
                (str(log_path), attempt["attempt_id"]),
            )
        redirected_result = self.invoke("job", "logs", str(job["job_id"]))
        self.assertEqual(redirected_result.returncode, 2)
        self.assertIn("recorded result path", redirected_result.stderr)

    def test_terminal_provider_log_retention_is_bounded_and_recorded(self) -> None:
        job = self.create("noisy-log.json")
        run = self.invoke(
            "job",
            "run",
            str(job["job_id"]),
            "--provider",
            "codex",
            "--json",
            mode="noisy-success",
        )
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        attempt = json.loads(run.stdout)["attempts"][0]
        log_path = Path(attempt["log_path"])
        self.assertLessEqual(log_path.stat().st_size, 8 * 1024 * 1024)
        self.assertTrue(
            log_path.read_bytes().startswith(
                b"[agentctl: earlier provider output discarded by retention policy]\n"
            )
        )
        retention_path = log_path.with_name("log-retention.json")
        retention = json.loads(retention_path.read_text(encoding="utf-8"))
        self.assertTrue(retention["truncated"])
        self.assertGreater(retention["original_bytes"], retention["max_bytes"])
        self.assertFalse(retention["raw_log_redacted"])
        viewed = self.invoke("job", "logs", str(job["job_id"]), "--json")
        self.assertEqual(viewed.returncode, 0, viewed.stdout + viewed.stderr)
        self.assertTrue(json.loads(viewed.stdout)["retention"]["truncated"])

    def test_gc_dry_run_requires_explicit_integration_proof_and_never_deletes(self) -> None:
        job = self.create("gc.json")
        job_id = str(job["job_id"])
        run = self.invoke("job", "run", job_id, "--provider", "codex", "--json")
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        run_payload = json.loads(run.stdout)
        worktree = Path(run_payload["attempts"][0]["workspace_path"])
        head_sha = run_payload["attempts"][0]["head_sha"]
        self.assertEqual(self.invoke("job", "validate", job_id).returncode, 0)
        self.assertEqual(self.invoke("job", "collect", job_id).returncode, 0)

        refused = self.invoke("gc", "--job", job_id)
        self.assertEqual(refused.returncode, 2)
        self.assertIn("destructive GC is not implemented", refused.stderr)
        before = self.invoke("gc", "--dry-run", "--job", job_id, "--json")
        self.assertEqual(before.returncode, 0, before.stdout + before.stderr)
        before_job = json.loads(before.stdout)["jobs"][0]
        self.assertFalse(before_job["eligible"])
        self.assertIn(
            "job_commit_not_integrated_in_registered_head",
            {reason["kind"] for reason in before_job["reasons"]},
        )
        self.assertTrue(worktree.is_dir())

        cherry_pick = subprocess.run(
            ["git", "-C", str(self.workspace), "cherry-pick", str(head_sha)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(cherry_pick.returncode, 0, cherry_pick.stdout + cherry_pick.stderr)
        collected = self.invoke(
            "job", "collect", job_id, "--onto", "HEAD", "--json"
        )
        self.assertEqual(collected.returncode, 0, collected.stdout + collected.stderr)
        collected_report = json.loads(collected.stdout)
        self.assertEqual(
            collected_report["integration_assessment"],
            "already_integrated_or_no_change",
        )
        self.assertEqual(collected_report["members"][0]["integration_match"], "patch_id")

        after = self.invoke("gc", "--dry-run", "--job", job_id, "--json")
        self.assertEqual(after.returncode, 0, after.stdout + after.stderr)
        inventory = json.loads(after.stdout)
        after_job = inventory["jobs"][0]
        self.assertTrue(after_job["eligible"])
        self.assertEqual(inventory["summary"]["eligible"], 1)
        self.assertIn(
            "remove_worktree",
            {action["kind"] for action in after_job["candidate_actions"]},
        )
        self.assertEqual(after_job["evidence_policy"], "retain")
        self.assertTrue(worktree.is_dir())

        with sqlite3.connect(self.state_dir / "state.db") as connection:
            connection.execute(
                "UPDATE attempts SET workspace_path = ? WHERE attempt_id = ?",
                (str(self.workspace), run_payload["attempts"][0]["attempt_id"]),
            )
        tampered = self.invoke("gc", "--dry-run", "--job", job_id, "--json")
        self.assertEqual(tampered.returncode, 0, tampered.stdout + tampered.stderr)
        tampered_job = json.loads(tampered.stdout)["jobs"][0]
        self.assertFalse(tampered_job["eligible"])
        self.assertIn(
            "worktree_path_mismatch",
            {reason["kind"] for reason in tampered_job["reasons"]},
        )
        self.assertEqual(tampered_job["candidate_actions"], [])

    def test_gc_global_inventory_survives_a_moved_registered_workspace(self) -> None:
        job = self.create("gc-moved.json")
        with sqlite3.connect(self.state_dir / "state.db") as connection:
            connection.execute(
                "UPDATE projects SET registered_path = ? WHERE project_id = ?",
                (str(self.root / "missing-workspace"), job["project_id"]),
            )
        inventory = self.invoke("gc", "--dry-run", "--json")
        self.assertEqual(inventory.returncode, 0, inventory.stdout + inventory.stderr)
        payload = json.loads(inventory.stdout)
        self.assertEqual(payload["summary"]["jobs"], 1)
        self.assertIn(
            "registered_workspace_unavailable",
            {reason["kind"] for reason in payload["jobs"][0]["reasons"]},
        )

    def test_gc_inventories_only_the_exact_job_compose_project(self) -> None:
        docker = self.bin_dir / "docker-inventory"
        docker.write_text(
            "#!/bin/sh\n"
            "case \" $* \" in\n"
            "  *\" --filter label=com.docker.compose.project=$FAKE_DOCKER_PROJECT \"*) ;;\n"
            "  *) exit 8 ;;\n"
            "esac\n"
            "case \"$1\" in\n"
            "  ps) echo container-for-job ;;\n"
            "  network) echo network-for-job ;;\n"
            "  volume) echo volume-for-job ;;\n"
            "  *) exit 9 ;;\n"
            "esac\n",
            encoding="utf-8",
        )
        docker.chmod(0o755)
        self.extra_environment["AGENTCTL_DOCKER_BIN"] = str(docker)
        job = self.create("gc-docker.json", resource_class="integration")
        job_id = str(job["job_id"])
        self.extra_environment["FAKE_DOCKER_PROJECT"] = f"agent_{job_id.lower()}"
        run = self.invoke("job", "run", job_id, "--provider", "codex")
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        validated = self.invoke("job", "validate", job_id)
        self.assertEqual(validated.returncode, 0, validated.stdout + validated.stderr)

        inventory = self.invoke("gc", "--dry-run", "--job", job_id, "--json")
        self.assertEqual(inventory.returncode, 0, inventory.stdout + inventory.stderr)
        payload = json.loads(inventory.stdout)["jobs"][0]
        self.assertEqual(payload["docker"]["status"], "available")
        self.assertEqual(payload["docker"]["residual_count"], 3)
        self.assertEqual(
            payload["docker"]["project_name"], f"agent_{job_id.lower()}"
        )
        self.assertIn(
            "docker_resources_remain",
            {reason["kind"] for reason in payload["reasons"]},
        )


if __name__ == "__main__":
    unittest.main()
