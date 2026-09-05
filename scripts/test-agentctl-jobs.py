#!/usr/bin/env python3

from __future__ import annotations

import contextlib
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import signal
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent.parent
AGENTCTL = Path(os.environ.get("AGENTCTL_TEST_BIN", ROOT / "scripts/agentctl"))
TEMPLATE_ROOT = Path(os.environ.get("AGENTCTL_TEST_TEMPLATE", ROOT / "project"))
sys.path.insert(0, os.environ.get("AGENTCTL_TEST_LIBRARY", str(ROOT / "scripts")))
from agentctl_jobs import _redact_log_text


FAKE_PROVIDER = r'''#!/usr/bin/env python3
import json
import os
from pathlib import Path
import subprocess
import sys

sys.stdin.read()  # Consume the prompt before reporting a synthetic result.
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
        if os.environ.get("FAKE_DELIVERY_TEXT"):
            with (workspace / relative).open("a") as delivered:
                delivered.write(os.environ["FAKE_DELIVERY_TEXT"] + "\n")
        changed = [relative]
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    if mode == "head-mismatch":
        head = "0" * 40
    status = (
        "blocked"
        if mode == "blocked"
        else "completed"
        if mode == "read-success"
        else "ready_for_commit"
    )
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
        "followups": [],
        "artifacts": None,
        "blocked_reason": None,
        "error": None
    }
    if os.environ.get("FAKE_ACCEPTANCE_COMMANDS"):
        result["checks"] = [
            {"command": command, "status": "passed", "exit_code": 0,
             "summary": "Synthetic claim only; command was never executed."}
            for command in json.loads(os.environ["FAKE_ACCEPTANCE_COMMANDS"])
        ]
    if status == "blocked":
        result["blocked_reason"] = "Synthetic blocker."

if kind == "codex":
    arguments = sys.argv[1:]
    index = arguments.index("--output-last-message")
    output_path = Path(arguments[index + 1])
    output_path.write_text(json.dumps(result), encoding="utf-8")
    print(json.dumps({"argv": arguments}))
elif kind == "claude":
    print(json.dumps({"structured_output": result, "argv": sys.argv[1:]}))
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


class LogRedactionTests(unittest.TestCase):
    def setUp(self) -> None:
        environment = patch.dict(os.environ, {}, clear=True)
        environment.start()
        self.addCleanup(environment.stop)

    def redact(self, text: str) -> tuple[str, int]:
        result, count = _redact_log_text(text)
        self.assertIsInstance(count, int)
        self.assertGreaterEqual(count, 0)
        return result, count

    def test_json_secret_names_are_case_insensitive_and_use_existing_rule(self) -> None:
        for key in (
            "api_key", "Api-Key", "APIKEY", "access_TOKEN", "clientSecret",
            "PASSWORD", "passwd", "credentials", "private-key", "PRIVATE_KEY",
            "privatekey", "aUtHoRiZaTiOn",
        ):
            with self.subTest(key=key):
                value = {key: "fixture-private-value-123", "message": "表示は残す 🌟"}
                result, count = self.redact(json.dumps(value, ensure_ascii=False))
                self.assertEqual(json.loads(result), {**value, key: "[REDACTED]"})
                self.assertNotIn("fixture-private-value-123", result)
                self.assertGreater(count, 0)

    def test_json_escaped_keys_and_values(self) -> None:
        source = (
            r'{"api\u005fkey":"fixture-\"quoted\"-\\path\nline\t\u79d8",'
            r'"Authoriz\u0061tion":"fixture\/auth\rvalue",'
            r'"ordinary":"quote: \"; slash: \\; Unicode: \u79d8"}'
        )
        result, count = self.redact(source)
        self.assertEqual(json.loads(result), {
            "api_key": "[REDACTED]", "Authorization": "[REDACTED]",
            "ordinary": json.loads(source)["ordinary"],
        })
        self.assertNotIn("fixture", result)
        self.assertEqual(count, 2)

    def test_nested_objects_arrays_and_non_string_secret_values(self) -> None:
        source = [
            {"nested": [{"token": "fixture-nested-value"}, ["ordinary", 2, False, None]]},
            {"secret": {"password": "fixture-inner-value", "ok": True}},
            {"api_key": ["ordinary", {"credential": "fixture-array-value"}]},
            {"password": 123, "token": False, "secret": None, "api_key": ""},
        ]
        expected = json.loads(json.dumps(source))
        expected[0]["nested"][0]["token"] = "[REDACTED]"
        expected[1]["secret"]["password"] = "[REDACTED]"
        expected[2]["api_key"][1]["credential"] = "[REDACTED]"
        result, count = self.redact(json.dumps(source, indent=2))
        self.assertEqual(json.loads(result), expected)
        self.assertEqual(count, 3)

    def test_prefixed_payloads_and_neighboring_lines(self) -> None:
        source = (
            'starting normally\n[INFO] request {"api_key":"fixture-first", "ok":true}'
            ' next [{"TOKEN":"fixture-second"}, "visible"]\n'
            'DEBUG {\n "Authorization": "fixture-third",\n "count": 3\n}\n'
            'finished normally\n'
        )
        expected = source
        for secret in ("fixture-first", "fixture-second", "fixture-third"):
            expected = expected.replace(secret, "[REDACTED]")
        result, count = self.redact(source)
        self.assertEqual(result, expected)
        self.assertEqual(count, 3)

    def test_existing_formats_in_plain_text_and_json_strings(self) -> None:
        secrets = [
            "sk-" + "a" * 20, "sk-ant-" + "b" * 20, "sk-proj-" + "c" * 20,
            "xai-" + "d" * 20, "ghp_" + "e" * 20, "github_pat_" + "f" * 20,
            "AKIA" + "A" * 16, "eyJheader12345.eyJpayload12345.signature12345",
            "fixture-assigned", "fixture-bearer", "fixture-basic", "fixture-env-value",
        ]
        source = "\n".join([
            *secrets[:8], f"PASSWORD={secrets[8]}; still visible",
            f"Authorization: Bearer {secrets[9]}",
            f"Authorization=Basic {secrets[10]}", f"environment says {secrets[11]}",
        ])
        with patch.dict(os.environ, {"SERVICE_SECRET": secrets[11]}):
            for encoded in (False, True):
                with self.subTest(json=encoded):
                    result, count = self.redact(
                        json.dumps({"message": source}) if encoded else source
                    )
                    message = json.loads(result)["message"] if encoded else result
                    for secret in secrets:
                        self.assertNotIn(secret, message)
                    self.assertIn("still visible", message)
                    self.assertEqual(message.count("[REDACTED]"), len(secrets))
                    self.assertGreaterEqual(count, len(secrets))

    def test_environment_values_with_json_escapes_preserve_structure(self) -> None:
        secret = 'fixture-"quoted"-\\path\n秘密'
        with patch.dict(os.environ, {"SERVICE_PRIVATE_KEY": secret}):
            result, count = self.redact(json.dumps({"message": f"before {secret} after"}))
        self.assertEqual(json.loads(result), {"message": "before [REDACTED] after"})
        self.assertEqual(count, 1)

    def test_known_tokens_and_environment_values_in_json_keys_and_arrays(self) -> None:
        token = "ghp_" + "g" * 20
        environment_secret = "fixture-environment-key"
        source = [{token: "ordinary field value"}, {environment_secret: True}, token]
        with patch.dict(os.environ, {"SERVICE_SECRET": environment_secret}):
            result, count = self.redact(json.dumps(source))
        self.assertEqual(json.loads(result), [
            {"[REDACTED]": "ordinary field value"}, {"[REDACTED]": True}, "[REDACTED]",
        ])
        self.assertEqual(count, 3)

    def test_duplicate_keys_and_numeric_lexemes_are_preserved(self) -> None:
        source = (
            '{"token":"fixture-one", "token":"fixture-two", '
            '"big":1e400, "precise":1.234567890123456789, "token_count":12345678}'
        )
        with patch.dict(os.environ, {"SERVICE_SECRET": "12345678"}):
            result, count = self.redact(source)
        self.assertEqual(
            result, source.replace("fixture-one", "[REDACTED]").replace("fixture-two", "[REDACTED]")
        )
        self.assertEqual(count, 2)

    def test_no_sensitive_content_and_complete_scalar_json(self) -> None:
        for source in ('', 'ordinary log\n', '{"secret":"", "ok":"日本語"}',
                       '[1, true, null, "ordinary"]', '123', 'false', 'null'):
            with self.subTest(source=source):
                self.assertEqual(self.redact(source), (source, 0))
        result, count = self.redact('"PASSWORD=fixture-scalar"')
        self.assertEqual(json.loads(result), "PASSWORD=[REDACTED]")
        self.assertGreater(count, 0)

    def test_long_integer_does_not_disable_neighbor_secret_redaction(self) -> None:
        number = "9" * 5000
        source = '{"number":' + number + ',"api_key":"fixture-secret"}'
        result, count = self.redact(source)
        self.assertEqual(result, source.replace("fixture-secret", "[REDACTED]"))
        self.assertEqual(count, 1)

    def test_redacted_escaped_surrogate_remains_utf8_printable(self) -> None:
        token = "sk-proj-" + "a" * 20
        source = '{"message":"\\ud800 ' + token + '","ordinary":"日本語"}'
        result, count = self.redact(source)
        decoded = json.loads(result.encode("utf-8"))
        self.assertEqual(decoded, {"message": "\ud800 [REDACTED]", "ordinary": "日本語"})
        self.assertEqual(count, 1)


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
        shutil.copytree(TEMPLATE_ROOT / ".agent", self.workspace / ".agent")
        shutil.copytree(TEMPLATE_ROOT / ".codex", self.workspace / ".codex")
        shutil.copytree(TEMPLATE_ROOT / ".claude", self.workspace / ".claude")
        shutil.copytree(TEMPLATE_ROOT / ".grok", self.workspace / ".grok")
        shutil.copy2(TEMPLATE_ROOT / "AGENTS.md", self.workspace / "AGENTS.md")
        shutil.copy2(TEMPLATE_ROOT / "CLAUDE.md", self.workspace / "CLAUDE.md")
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
        collaboration: dict[str, object] | None = None,
        lane: str = "write",
        role: str = "implementer",
        acceptance: list[dict[str, str]] | None = None,
    ) -> Path:
        task = {
            "schema_version": 1,
            "objective": "Create one deterministic result file.",
            "role": role,
            "lane": lane,
            "permission_profile": permission_profile,
            "resource_class": resource_class,
            "scope": {
                "allowed_paths": ["result.txt"],
                "forbidden_paths": ["forbidden.txt", ".devcontainer/"],
            },
            "acceptance": acceptance if acceptance is not None else [{"kind": "command", "value": "fake-provider"}],
            "constraints": ["Do not push or merge."],
            "dependency_job_ids": dependency_job_ids or [],
        }
        if priority is not None:
            task["priority"] = priority
        if collaboration is not None:
            task["collaboration"] = collaboration
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

    def check_fixture(self, commands: list[str], *, acceptance=None, **options):
        entries = acceptance if acceptance is not None else [
            {"kind": "command", "value": command} for command in commands
        ]
        self.extra_environment["FAKE_ACCEPTANCE_COMMANDS"] = json.dumps(commands)
        job = self.create(acceptance=entries, **options)
        # Lane R shares the checkout; remove the caller's transient input packet.
        (self.workspace / "task.json").unlink()
        result = self.invoke("job", "run", job["job_id"], "--provider", "codex", "--json",
                             mode="read-success" if options.get("lane") == "read" else "success")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        job = json.loads(result.stdout)
        return job, Path(job["attempts"][-1]["workspace_path"])

    def check_report(self, job, *arguments):
        result = self.invoke("job", "check", job["job_id"], "--json", *arguments, mode="exit")
        self.assertTrue(result.stdout, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0 if report["status"] == "passed" else 1, result.stderr)
        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(report["job_id"], job["job_id"])
        self.assertEqual(report["attempt_id"], job["attempts"][-1]["attempt_id"])
        self.assertEqual(report["head_sha"], job["attempts"][-1]["head_sha"])
        for check in report["checks"]:
            self.assertTrue(math.isfinite(check["elapsed_seconds"]))
            self.assertGreaterEqual(check["elapsed_seconds"], 0)
            self.assertLessEqual(len(check["stdout_tail"].encode()) +
                                 len(check["stderr_tail"].encode()), 65536)
            if check["status"] == "unexecuted":
                self.assertIsNone(check["exit_code"])
                self.assertEqual(check["elapsed_seconds"], 0)
                self.assertEqual(check["stdout_tail"], "")
                self.assertEqual(check["stderr_tail"], "")
        return report

    def checks_view(self, job):
        result = self.invoke("job", "checks", job["job_id"], "--json", mode="exit")
        self.assertEqual(result.returncode, 0, result.stderr)
        view = json.loads(result.stdout)
        self.assertEqual(view["schema_version"], 1)
        self.assertEqual(view["job_id"], job["job_id"])
        if not view["fresh"]:
            self.assertTrue(view["stale_reasons"])
        return view

    def strict_rejection(self, job):
        before = self.invoke("job", "show", job["job_id"], "--json").stdout
        result = self.invoke("job", "validate", job["job_id"], "--require-checks", "--json", mode="exit")
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("independent", result.stderr)
        self.assertEqual(self.invoke("job", "show", job["job_id"], "--json").stdout, before)
        self.assertFalse(Path(job["attempts"][-1]["result_path"]).with_name("validation.json").exists())
        return result

    def wait_for_check_marker(self, path, checker):
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            if path.exists() and path.stat().st_size:
                return
            if checker.poll() is not None:
                stdout, stderr = checker.communicate(timeout=2)
                self.fail(f"checker exited before command marker: {stdout} {stderr}")
            time.sleep(0.01)
        self.fail("checker did not reach its command marker")

    def stop_checker(self, checker):
        if checker.poll() is None:
            checker.terminate()
        checker.communicate(timeout=8)
        checker.stdout.close()
        checker.stderr.close()

    def bounded_check_invocation(self, *arguments):
        process = self.popen(*arguments, mode="exit")
        try:
            stdout, stderr = process.communicate(timeout=3)
            return subprocess.CompletedProcess(arguments, process.returncode, stdout, stderr)
        finally:
            self.stop_checker(process)

    def assert_check_process_stopped(self, pid):
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            proc = Path(f"/proc/{pid}/stat")
            if not proc.exists() or proc.read_text().rsplit(")", 1)[1].split()[0] == "Z":
                return
            time.sleep(0.02)
        self.fail(f"check child {pid} still running")

    def test_check_ownership_rejects_overlap_and_validation_promptly(self):
        gate, started, calls = (self.root / name for name in ("gate", "started", "calls"))
        command = (f"printf x >> '{calls}'; if test -f '{gate}'; then "
                   f"echo $$ > '{started}'; sleep 30; fi")
        job, _ = self.check_fixture([command])
        passed = self.check_report(job)
        gate.touch()
        checker = self.popen("job", "check", job["job_id"], "--json")
        try:
            self.wait_for_check_marker(started, checker)
            live = self.checks_view(job)
            self.assertTrue(live["in_progress"])
            self.assertFalse(live["fresh"])
            self.assertEqual(live["latest"]["status"], "incomplete")
            for arguments in (("check", "--recover-incomplete"), ("validate", "--require-checks"),
                              ("validate",)):
                denied = self.bounded_check_invocation("job", arguments[0], job["job_id"],
                                                       *arguments[1:], "--json")
                self.assertNotEqual(denied.returncode, 0, denied.stdout)
                self.assertIn("in progress", denied.stderr)
            self.assertEqual(calls.read_text(), "xx")
            with sqlite3.connect(self.state_dir / "state.db") as connection:
                self.assertEqual(connection.execute("SELECT count(*) FROM command_verifications").fetchone()[0], 2)
                self.assertEqual(connection.execute("SELECT count(*) FROM validations").fetchone()[0], 0)
            self.assertEqual(json.loads(Path(passed["report_path"]).read_text()), passed)
        finally:
            self.stop_checker(checker)
        self.assertFalse(self.checks_view(job)["in_progress"])

    def test_check_ownership_before_observation_overrides_previous_pass(self):
        from agentctl_jobs import StatePaths, _attempt_check_lock
        job, _ = self.check_fixture(["true"])
        passed = self.check_report(job)
        with _attempt_check_lock(StatePaths.from_value(self.state_dir), job["attempts"][-1]["attempt_id"]):
            view = self.checks_view(job)
            self.assertEqual(view["latest"], passed)
            self.assertTrue(view["in_progress"])
            self.assertFalse(view["fresh"])
            denied = self.bounded_check_invocation("job", "validate", job["job_id"], "--require-checks", "--json")
            self.assertNotEqual(denied.returncode, 0)
        self.assertTrue(self.checks_view(job)["fresh"])

    def test_check_different_attempts_execute_concurrently(self):
        gate = self.root / "gate"
        gate.touch()
        markers = [self.root / f"started-{i}" for i in range(2)]
        jobs = [self.check_fixture([f"echo ready > '{marker}'; while test -f '{gate}'; do sleep 0.05; done"])[0]
                for marker in markers]
        checkers = []
        try:
            for job, marker in zip(jobs, markers):
                checker = self.popen("job", "check", job["job_id"], "--timeout", "20", "--json")
                checkers.append(checker)
                self.wait_for_check_marker(marker, checker)
            self.assertTrue(all(checker.poll() is None for checker in checkers))
            self.assertTrue(all(self.checks_view(job)["in_progress"] for job in jobs))
            gate.unlink()
            for checker in checkers:
                stdout, stderr = checker.communicate(timeout=8)
                self.assertEqual(checker.returncode, 0, stderr)
                self.assertEqual(json.loads(stdout)["status"], "passed")
        finally:
            for checker in checkers:
                self.stop_checker(checker)
        self.assertTrue(all(self.checks_view(job)["fresh"] for job in jobs))

    def test_check_signals_preserve_bounded_evidence_clean_children_and_recheck(self):
        for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
            with self.subTest(signal=sig):
                gate = self.root / f"gate-{sig}"
                marker = self.root / f"child-{sig}"
                later = self.root / f"later-{sig}"
                gate.touch()
                self.extra_environment["CHECK_SECRET"] = "synthetic-secret"
                command = (f"if test -f '{gate}'; then "
                           "printf 'password=%s\\n' \"$CHECK_SECRET\"; printf diagnostic >&2; "
                           f"sleep 30 & echo $! > '{marker}'; wait; fi")
                job, _ = self.check_fixture(["printf first", command, f"touch '{later}'"])
                checker = self.popen("job", "check", job["job_id"], "--json")
                try:
                    self.wait_for_check_marker(marker, checker)
                    checker.send_signal(sig)
                    stdout, stderr = checker.communicate(timeout=8)
                    self.assertEqual(checker.returncode, 1, stderr)
                    report = json.loads(stdout)
                    self.assertEqual(report["status"], "interrupted")
                    self.assertEqual(report["interruption_signal"], sig)
                    self.assertEqual([c["status"] for c in report["checks"]],
                                     ["passed", "interrupted", "unexecuted"])
                    self.assertEqual(report["checks"][1]["exit_code"], -9)
                    self.assertIn("[REDACTED]", report["checks"][1]["stdout_tail"])
                    self.assertNotIn("synthetic-secret", json.dumps(report))
                    self.assertEqual(report["checks"][1]["stderr_tail"], "diagnostic")
                    self.assertFalse(later.exists())
                    self.assert_check_process_stopped(int(marker.read_text()))
                    view = self.checks_view(job)
                    self.assertEqual(view["latest"], report)
                    self.assertFalse(view["in_progress"])
                    self.assertFalse(view["fresh"])
                    self.strict_rejection(job)
                finally:
                    self.stop_checker(checker)
                gate.unlink()
                self.assertEqual(self.check_report(job)["status"], "passed")
                sealed = self.invoke("job", "validate", job["job_id"], "--require-checks", "--json")
                self.assertEqual(sealed.returncode, 0, sealed.stderr)

    def test_check_abrupt_death_keeps_incomplete_and_requires_explicit_recovery(self):
        gate, marker = self.root / "gate", self.root / "group"
        command = f"if test -f '{gate}'; then echo $$ > '{marker}'; sleep 30 & wait; fi"
        job, _ = self.check_fixture([command])
        passed = self.check_report(job)
        gate.touch()
        checker = self.popen("job", "check", job["job_id"], "--json")
        group = None
        try:
            self.wait_for_check_marker(marker, checker)
            group = int(marker.read_text())
            checker.kill()
            checker.wait(timeout=3)
            view = self.checks_view(job)
            self.assertEqual(view["latest"]["status"], "incomplete")
            self.assertTrue(view["in_progress"], "descendants must retain inherited ownership")
            denied = self.bounded_check_invocation("job", "check", job["job_id"], "--recover-incomplete", "--json")
            self.assertNotEqual(denied.returncode, 0)
            self.assertIn("in progress", denied.stderr)
            os.killpg(group, signal.SIGKILL)
            self.assert_check_process_stopped(group)
            checker.communicate(timeout=3)
            self.assertFalse(self.checks_view(job)["in_progress"])
            self.strict_rejection(job)
            gate.unlink()
            denied = self.invoke("job", "check", job["job_id"], "--json")
            self.assertNotEqual(denied.returncode, 0)
            self.assertIn("--recover-incomplete", denied.stderr)
            recovered = self.check_report(job, "--recover-incomplete")
            self.assertEqual(recovered["status"], "passed")
            self.assertNotEqual(recovered["verification_id"], passed["verification_id"])
            with sqlite3.connect(self.state_dir / "state.db") as connection:
                statuses = [r[0] for r in connection.execute("SELECT status FROM command_verifications ORDER BY sequence")]
            self.assertEqual(statuses, ["passed", "incomplete", "passed"])
        finally:
            if group is not None:
                try:
                    os.killpg(group, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            self.stop_checker(checker)

    def test_check_success_cleans_background_children_with_closed_pipes(self):
        marker = self.root / "child"
        command = f"sleep 30 </dev/null >/dev/null 2>&1 & echo $! > '{marker}'"
        job, _ = self.check_fixture([command])
        self.assertEqual(self.check_report(job)["status"], "passed")
        self.assert_check_process_stopped(int(marker.read_text()))
        self.assertFalse(self.checks_view(job)["in_progress"])

    def test_checks_signal_during_publication_cannot_publish_success(self):
        import agentctl_jobs as jobs
        job, _ = self.check_fixture(["true"])
        passed = self.check_report(job)
        original_write = jobs.write_json_private

        def interrupt_publication(path, report):
            original_write(path, report)
            os.kill(os.getpid(), signal.SIGTERM)

        with jobs.Store(jobs.StatePaths.from_value(self.state_dir)) as store:
            with patch("agentctl_jobs.write_json_private", side_effect=interrupt_publication):
                with self.assertRaisesRegex(jobs.AgentctlJobError, "interrupted during report publication"):
                    jobs.check_job(store, job["job_id"])
        view = self.checks_view(job)
        self.assertFalse(view["in_progress"])
        self.assertFalse(view["fresh"])
        self.assertEqual(view["latest"]["status"], "incomplete")
        self.assertNotEqual(view["latest"]["verification_id"], passed["verification_id"])
        # The atomically written JSON alone claims success; its metadata does not.
        artifact = json.loads(Path(view["latest"]["report_path"]).read_text())
        self.assertEqual(artifact["status"], "passed")
        self.strict_rejection(job)
        self.assertEqual(self.check_report(job, "--recover-incomplete")["status"], "passed")

    def test_checks_signal_during_metadata_update_rolls_back_success(self):
        import agentctl_jobs as jobs
        job, _ = self.check_fixture(["true"])
        self.check_report(job)
        with jobs.Store(jobs.StatePaths.from_value(self.state_dir)) as store:
            original_transaction = store.transaction

            class InterruptedConnection:
                def __init__(self, connection):
                    self.connection = connection

                def execute(self, query, parameters):
                    result = self.connection.execute(query, parameters)
                    if query.startswith("UPDATE command_verifications"):
                        os.kill(os.getpid(), signal.SIGTERM)
                    return result

            @contextlib.contextmanager
            def interrupted_transaction():
                with original_transaction() as connection:
                    yield InterruptedConnection(connection)

            with patch.object(store, "transaction", interrupted_transaction):
                with self.assertRaisesRegex(jobs.AgentctlJobError, "interrupted during report publication"):
                    jobs.check_job(store, job["job_id"])
        view = self.checks_view(job)
        self.assertEqual(view["latest"]["status"], "incomplete")
        self.assertFalse(view["in_progress"])
        self.assertFalse(view["fresh"])
        self.strict_rejection(job)

    def test_checks_absence_readonly_and_no_provider_fabrication(self):
        absent = self.invoke("job", "checks", "0" * 26, "--json")
        self.assertNotEqual(absent.returncode, 0)
        self.assertFalse(self.state_dir.exists())
        job, workspace = self.check_fixture(["echo real"])
        result_path = Path(job["attempts"][-1]["result_path"])
        provider = json.loads(result_path.read_text())
        provider["verification_id"] = "fake-provider-evidence"
        provider["independent_checks"] = {"status": "passed"}
        result_path.write_text(json.dumps(provider))
        before = {str(p): (p.read_bytes(), p.stat().st_mode) for p in self.state_dir.rglob("*")
                  if p.is_file() and p.suffix not in {".db", ".db-wal", ".db-shm"}}
        view = self.checks_view(job)
        self.assertIsNone(view["latest"])
        self.assertFalse(view["fresh"])
        self.strict_rejection(job)
        after = {str(p): (p.read_bytes(), p.stat().st_mode) for p in self.state_dir.rglob("*")
                 if p.is_file() and p.suffix not in {".db", ".db-wal", ".db-shm"}}
        self.assertEqual(before, after)
        self.assertEqual((workspace / "tracked.txt").read_text(), "base\n")

    def test_checks_persist_pass_and_strict_validation_never_executes(self):
        marker = self.root / "execution-count"
        job, workspace = self.check_fixture([f"printf x >> '{marker}'"])
        report = self.check_report(job)
        artifact = Path(report["report_path"])
        self.assertEqual(artifact.stat().st_mode & 0o777, 0o600)
        self.assertEqual(artifact.parent.stat().st_mode & 0o777, 0o700)
        self.assertEqual(json.loads(artifact.read_text()), report)
        self.assertRegex(report["verification_id"], r"^[0-9a-f]{32}$")
        for key in ("task_digest", "source_fingerprint"):
            self.assertRegex(report[key], r"^sha256:[0-9a-f]{64}$")
        with sqlite3.connect(self.state_dir / "state.db") as connection:
            digest, = connection.execute("SELECT report_digest FROM command_verifications").fetchone()
        self.assertEqual(digest, "sha256:" + hashlib.sha256(artifact.read_bytes()).hexdigest())
        for _ in range(2):
            view = self.checks_view(job)
            self.assertTrue(view["fresh"], view)
            self.assertEqual(view["latest"], report)
        result = self.invoke("job", "validate", job["job_id"], "--require-checks", "--json", mode="exit")
        self.assertEqual(result.returncode, 0, result.stderr)
        validation = json.loads(result.stdout)["validation"]
        self.assertEqual(validation["command_evidence"], "independently-executed")
        self.assertEqual(validation["verification_id"], report["verification_id"])
        self.assertEqual(marker.read_text(), "x")
        self.assertTrue(self.checks_view(job)["fresh"])
        retry = self.invoke("job", "run", job["job_id"], "--clean-retry", "--provider", "codex")
        self.assertNotEqual(retry.returncode, 0)

    def test_checks_later_failure_supersedes_pass_and_recheck_is_explicit(self):
        toggle = self.root / "toggle"
        toggle.touch()
        job, _ = self.check_fixture([f"test -f '{toggle}'", "echo later"])
        passed = self.check_report(job)
        original = Path(passed["report_path"]).read_bytes()
        toggle.unlink()
        failed = self.check_report(job)
        self.assertEqual(failed["status"], "failed")
        self.assertNotEqual(passed["verification_id"], failed["verification_id"])
        self.assertEqual(Path(passed["report_path"]).read_bytes(), original)
        view = self.checks_view(job)
        self.assertEqual(view["latest"], failed)
        self.assertTrue(view["fresh"], view)  # Fresh observation does not mean passing.
        self.strict_rejection(job)
        toggle.touch()
        self.assertEqual(self.checks_view(job)["latest"], failed)
        rechecked = self.check_report(job)
        self.assertEqual(rechecked["status"], "passed")
        self.assertEqual(len(list(Path(passed["report_path"]).parent.glob("*.json"))), 3)

    def test_checks_failed_timeout_no_checks_and_source_changed_cannot_seal(self):
        cases = [(["exit 9"], "failed"), (["sleep 2"], "timed-out"),
                 ([], "no-checks"), (["echo edited > tracked.txt"], "source-changed")]
        for commands, status in cases:
            with self.subTest(status=status):
                job, _ = self.check_fixture(commands, acceptance=(None if commands else [
                    {"kind": "manual", "value": "operator review"}]))
                report = self.check_report(job, "--timeout", "0.15")
                self.assertEqual(report["status"], status)
                self.assertEqual(self.checks_view(job)["latest"], report)
                self.strict_rejection(job)

    def test_checks_detect_changed_source_and_task_without_repair(self):
        mutations = ["printf edited > tracked.txt", "chmod +x tracked.txt", "chmod 600 tracked.txt",
                     "touch new.py", "git add -N new.py", "git update-index --assume-unchanged tracked.txt",
                     "git update-index --skip-worktree tracked.txt",
                     "git commit --allow-empty -qm updated"]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                job, workspace = self.check_fixture(["true"])
                self.check_report(job)
                if mutation == "git add -N new.py":
                    (workspace / "new.py").touch()
                subprocess.run(["/bin/sh", "-c", mutation], cwd=workspace, check=True)
                self.assertFalse(self.checks_view(job)["fresh"])
                self.strict_rejection(job)
        for flag in ("--assume-unchanged", "--skip-worktree"):
            job, workspace = self.check_fixture(["true"])
            subprocess.run(["git", "-C", str(workspace), "update-index", flag, "tracked.txt"], check=True)
            self.check_report(job)
            (workspace / "tracked.txt").write_text("hidden mutation\n")
            self.assertFalse(self.checks_view(job)["fresh"])
            self.strict_rejection(job)
            self.assertEqual((workspace / "tracked.txt").read_text(), "hidden mutation\n")
        job, _ = self.check_fixture(["true"])
        self.check_report(job)
        task = Path(job["task_path"])
        stored = json.loads(task.read_text())
        stored["objective"] = "altered immutable task"
        task.write_text(json.dumps(stored))
        view = self.checks_view(job)
        self.assertFalse(view["fresh"])
        self.assertIn("task", str(view["stale_reasons"]))
        self.strict_rejection(job)
        self.assertNotEqual(self.invoke("job", "check", job["job_id"]).returncode, 0)

    def test_checks_ignore_cache_and_reject_missing_or_symlinked_workspace(self):
        job, workspace = self.check_fixture(["true"])
        git_dir = Path(subprocess.check_output(["git", "-C", str(workspace), "rev-parse", "--git-common-dir"], text=True).strip())
        (git_dir / "info/exclude").write_text("cache/\n")
        self.check_report(job)
        (workspace / "cache").mkdir()
        (workspace / "cache/test.pyc").write_bytes(b"ignored")
        self.assertTrue(self.checks_view(job)["fresh"])
        moved = workspace.with_name("moved")
        workspace.rename(moved)
        self.assertFalse(self.checks_view(job)["fresh"])
        self.strict_rejection(job)
        workspace.symlink_to(moved)
        self.assertFalse(self.checks_view(job)["fresh"])
        self.strict_rejection(job)

    def test_checks_report_tampering_missing_metadata_and_incomplete_evidence(self):
        job, _ = self.check_fixture(["true", "echo checked"])
        report = self.check_report(job)
        artifact = Path(report["report_path"])
        original = artifact.read_bytes()
        for mutation in (b'{"status":"passed"}', b'not json', original + b'\n'):
            artifact.write_bytes(mutation)
            view = self.checks_view(job)
            self.assertFalse(view["fresh"])
            self.assertEqual(view["latest"]["status"], "corrupted")
            self.strict_rejection(job)
            self.assertEqual(artifact.read_bytes(), mutation)
        artifact.unlink()
        self.assertFalse(self.checks_view(job)["fresh"])
        self.strict_rejection(job)
        target = self.root / "substituted.json"
        target.write_bytes(original)
        artifact.symlink_to(target)
        self.assertFalse(self.checks_view(job)["fresh"])
        artifact.unlink()
        artifact.write_bytes(original)
        # Even a self-consistent report file cannot complete pending DB metadata.
        with sqlite3.connect(self.state_dir / "state.db") as connection:
            connection.execute("UPDATE command_verifications SET finished_at = NULL")
        self.assertEqual(self.checks_view(job)["latest"]["status"], "incomplete")
        self.strict_rejection(job)
        # An unregistered JSON artifact is never evidence.
        with sqlite3.connect(self.state_dir / "state.db") as connection:
            connection.execute("DELETE FROM command_verifications")
        self.assertIsNone(self.checks_view(job)["latest"])
        self.strict_rejection(job)
        self.assertEqual(artifact.read_bytes(), original)

    def test_checks_interrupted_later_execution_blocks_prior_pass(self):
        marker = self.root / "started"
        job, _ = self.check_fixture([f"if test -f '{marker}'; then sleep 1; else touch '{marker}'; fi"])
        passed = self.check_report(job)
        # Simulate failure to publish a finished artifact after commands completed.
        from agentctl_jobs import Store, StatePaths, check_job, AgentctlJobError
        with Store(StatePaths.from_value(self.state_dir)) as store:
            with patch("agentctl_jobs.write_json_private", side_effect=OSError("synthetic interrupted write")):
                with self.assertRaises(OSError):
                    check_job(store, job["job_id"], timeout=0.1)
        view = self.checks_view(job)
        self.assertFalse(view["fresh"])
        self.assertEqual(view["latest"]["status"], "incomplete")
        self.assertNotEqual(view["latest"]["verification_id"], passed["verification_id"])
        self.assertTrue(Path(passed["report_path"]).is_file())
        self.strict_rejection(job)

    def test_checks_inspects_incomplete_execution_without_waiting_or_reexecution(self):
        marker = self.root / "live-check-started"
        job, _ = self.check_fixture([f"touch '{marker}'; sleep 3"])
        checker = self.popen("job", "check", job["job_id"], "--timeout", "1", "--json")
        try:
            deadline = time.monotonic() + 5
            while not marker.exists() and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertTrue(marker.exists())
            view = self.checks_view(job)
            self.assertFalse(view["fresh"])
            self.assertEqual(view["latest"]["status"], "incomplete")
            self.assertIsNone(checker.poll())
            stdout, stderr = checker.communicate(timeout=10)
            self.assertEqual(checker.returncode, 1, stderr)
            report = json.loads(stdout)
            self.assertEqual(report["status"], "timed-out")
            self.assertEqual(self.checks_view(job)["latest"], report)
        finally:
            if checker.poll() is None:
                checker.wait(timeout=10)
            checker.stdout.close()
            checker.stderr.close()

    def test_checks_rejects_incomplete_fields_even_with_matching_integrity_metadata(self):
        job, _ = self.check_fixture(["true"])
        report = self.check_report(job)
        artifact = Path(report["report_path"])
        for field, value in (("elapsed_seconds", None), ("elapsed_seconds", float("nan")),
                             ("elapsed_seconds", -1), ("stdout_tail", None),
                             ("exit_code", None), ("status", "unexecuted")):
            with self.subTest(field=field, value=value):
                incomplete = json.loads(json.dumps(report))
                incomplete["checks"][0][field] = value
                raw = json.dumps(incomplete).encode()
                artifact.write_bytes(raw)
                # Emulate a partial older writer/corruption, not provider authority.
                with sqlite3.connect(self.state_dir / "state.db") as connection:
                    connection.execute("UPDATE command_verifications SET report_digest = ?",
                                       ("sha256:" + hashlib.sha256(raw).hexdigest(),))
                self.assertFalse(self.checks_view(job)["fresh"])
                self.strict_rejection(job)

    def test_checks_clean_retry_requires_new_evidence_for_new_source(self):
        job, workspace = self.check_fixture(["test -f result.txt"])
        passed = self.check_report(job)
        (workspace / "result.txt").write_text("user edit after delivery\n")
        self.strict_rejection(job)
        # Keep the existing retry state machine: legacy post-validation fails first.
        legacy = self.invoke("job", "validate", job["job_id"], "--json")
        self.assertNotEqual(legacy.returncode, 0)
        failed = json.loads(self.invoke("job", "show", job["job_id"], "--json").stdout)
        self.assertEqual(failed["state"], "failed")
        self.assertEqual(failed["attempts"][-1]["exit_reason"], "post_validation")
        # A legitimate provider delivery on the next existing workflow attempt.
        self.extra_environment["FAKE_DELIVERY_TEXT"] = "new-source-delivery"
        retry = self.invoke("job", "run", job["job_id"], "--provider", "codex", "--clean-retry", "--json")
        self.assertEqual(retry.returncode, 0, retry.stderr)
        retried = json.loads(retry.stdout)
        self.assertNotEqual(retried["attempts"][-1]["attempt_id"], passed["attempt_id"])
        self.assertNotEqual(retried["attempts"][-1]["head_sha"], passed["head_sha"])
        view = self.checks_view(retried)
        self.assertFalse(view["fresh"])
        self.assertEqual(view["latest"], passed)
        self.strict_rejection(retried)
        rechecked = self.check_report(retried)
        self.assertEqual(rechecked["status"], "passed")
        self.assertNotEqual(rechecked["source_fingerprint"], passed["source_fingerprint"])
        result = self.invoke("job", "validate", job["job_id"], "--require-checks", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((workspace / "result.txt").read_text(), "user edit after delivery\n")

    def test_checks_legacy_validation_explicitly_labels_provider_claims(self):
        job, _ = self.check_fixture(["exit 7"])
        result = self.invoke("job", "validate", job["job_id"], "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)["validation"]
        self.assertEqual(report["command_evidence"], "provider-reported")
        self.assertIsNone(report["verification_id"])
        self.assertIsNone(self.checks_view(job)["latest"])

    def test_checks_upgrade_actual_earlier_database_and_jobs(self):
        reproduced = subprocess.run(
            [sys.executable, str(ROOT / "scripts/fixtures/agentctl-history/reproduce-baseline-upgrade.py")],
            capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(reproduced.returncode, 0, reproduced.stdout + reproduced.stderr)
        self.assertIn("actual old database upgraded", reproduced.stdout)

    def test_checks_upgrade_actual_phase2_evidence_and_interruption(self):
        reproduced = subprocess.run(
            [sys.executable, str(ROOT / "scripts/fixtures/agentctl-history/reproduce-phase2-upgrade.py")],
            capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(reproduced.returncode, 0, reproduced.stdout + reproduced.stderr)
        self.assertIn("actual phase-2", reproduced.stdout)

    def test_check_runs_original_task_in_attempt_and_does_not_validate_job(self):
        commands = ["test -f result.txt && printf 'submitted\\n'", "pwd"]
        acceptance = [{"kind": "manual", "value": "Must be reviewed by an operator"},
                      {"kind": "command", "value": commands[0]},
                      {"kind": "file", "value": "result.txt"},
                      {"kind": "command", "value": commands[1], "cwd": ".agent"}]
        job, workspace = self.check_fixture(commands, acceptance=acceptance)
        attempt = job["attempts"][-1]
        # Result evidence is provider-owned; a substituted command must never run.
        result_path = Path(attempt["result_path"])
        result = json.loads(result_path.read_text())
        result["checks"] = [{"command": "touch wrong-result-command", "status": "passed", "exit_code": 0}]
        result_path.write_text(json.dumps(result))
        # Editing the caller input also cannot replace the immutable command list.
        (self.workspace / "task.json").write_text('{"acceptance": []}')
        task_path = Path(job["task_path"])
        original_task = task_path.read_bytes()
        report = self.check_report(job)
        self.assertEqual(report["status"], "passed")
        self.assertEqual([c["command"] for c in report["checks"]], commands)
        self.assertEqual(report["checks"][0]["stdout_tail"], "submitted\n")
        self.assertEqual(report["checks"][0]["cwd"], str(workspace))
        self.assertEqual(report["checks"][1]["cwd"], str(workspace / ".agent"))
        self.assertEqual(report["checks"][1]["stdout_tail"].strip(), str(workspace / ".agent"))
        self.assertFalse((workspace / "wrong-result-command").exists())
        self.assertEqual(task_path.read_bytes(), original_task)
        shown = json.loads(self.invoke("job", "show", job["job_id"], "--json").stdout)
        self.assertEqual(shown["state"], "succeeded")
        self.assertIsNone(shown.get("validation"))
        self.assertFalse(result_path.with_name("validation.json").exists())

    def test_check_failing_command_overrules_provider_pass_claim_and_stops(self):
        job, workspace = self.check_fixture(["printf passed; printf problem >&2; exit 7", "touch later"])
        report = self.check_report(job)
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["checks"][0]["exit_code"], 7)
        self.assertEqual(report["checks"][0]["stdout_tail"], "passed")
        self.assertEqual(report["checks"][0]["stderr_tail"], "problem")
        self.assertEqual(report["checks"][1]["status"], "unexecuted")
        self.assertFalse((workspace / "later").exists())

    def test_check_read_lane_and_validated_attempt(self):
        job, workspace = self.check_fixture(["test -f tracked.txt"], lane="read", role="reviewer", resource_class="light")
        self.assertEqual(workspace, self.workspace)
        validated = self.invoke("job", "validate", job["job_id"], "--json")
        self.assertEqual(validated.returncode, 0, validated.stderr)
        report = self.check_report(job)
        self.assertEqual(report["status"], "passed")

    def test_check_no_commands_is_not_verification(self):
        job, _ = self.check_fixture([], acceptance=[{"kind": "manual", "value": "Review behavior"}])
        report = self.check_report(job)
        self.assertEqual(report["status"], "no-checks")
        self.assertEqual(report["checks"], [])

    def test_check_timeout_is_one_budget_and_kills_children(self):
        pid_path = self.root / "child.pid"
        command = ("python3 -c 'import os,signal,time; "
                   "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
                   f"open(\"{pid_path}\",\"w\").write(str(os.getpid())); time.sleep(30)' & wait")
        job, _ = self.check_fixture(["sleep 0.6", command, "echo later"])
        started = time.monotonic()
        report = self.check_report(job, "--timeout", "1")
        self.assertLess(time.monotonic() - started, 3)
        self.assertEqual(report["status"], "timed-out")
        self.assertEqual(report["checks"][0]["status"], "passed")
        self.assertEqual(report["checks"][1]["status"], "timed-out")
        self.assertLess(report["checks"][1]["elapsed_seconds"], 0.8)
        self.assertEqual(report["checks"][1]["exit_code"], -9)
        self.assertEqual(report["checks"][2]["status"], "unexecuted")
        pid = int(pid_path.read_text())
        for _ in range(50):
            proc = Path(f"/proc/{pid}/stat")
            if not proc.exists() or proc.read_text().rsplit(")", 1)[1].split()[0] == "Z":
                break
            time.sleep(0.02)
        else:
            self.fail(f"timed-out child {pid} remains running")

    def test_check_timeout_with_exited_shell_and_inherited_pipes(self):
        job, _ = self.check_fixture(["sleep 30 & exit 0"])
        report = self.check_report(job, "--timeout", "0.2")
        self.assertEqual(report["status"], "timed-out")
        self.assertEqual(report["checks"][0]["exit_code"], 0)

    def test_check_large_output_is_drained_bounded_and_redacted(self):
        secret = "sk-" + "s" * 24
        command = ("python3 -c 'import os; "
                   "[(os.write(1,b\"x\"*65536),os.write(2,b\"y\"*65536)) for _ in range(160)]; "
                   f"os.write(1,b\"\\n{secret}\\nstdout-end\\n\"); "
                   "os.write(2,b\"\\nPASSWORD=fixture-password\\nstderr-end\\n\")'")
        job, _ = self.check_fixture([command])
        report = self.check_report(job, "--timeout", "10")
        self.assertEqual(report["status"], "passed")
        check = report["checks"][0]
        self.assertNotIn(secret, check["stdout_tail"])
        self.assertNotIn("fixture-password", check["stderr_tail"])
        self.assertIn("[REDACTED]", check["stdout_tail"])
        self.assertTrue(check["stdout_tail"].endswith("stdout-end\n"))
        self.assertTrue(check["stderr_tail"].endswith("stderr-end\n"))
        artifacts = list(self.state_dir.glob("projects/*/jobs/*/checks/*"))
        self.assertEqual(artifacts, [Path(report["report_path"])])
        self.assertLess(artifacts[0].stat().st_size, 100000)

    def test_check_source_mutations_invalidate_without_repair(self):
        mutations = [
            "printf changed > tracked.txt",
            "chmod +x tracked.txt",
            "touch introduced.py",
            "git update-index --assume-unchanged tracked.txt; printf hidden > tracked.txt",
            "git update-index --skip-worktree tracked.txt; printf hidden > tracked.txt",
            "git update-index --assume-unchanged tracked.txt",
            "git -c user.name=test -c user.email=test@example.invalid commit --allow-empty -qm changed",
        ]
        for number, command in enumerate(mutations):
            with self.subTest(command=command):
                # Each fixture is a real independent job from the same clean base.
                self.extra_environment["FAKE_ACCEPTANCE_COMMANDS"] = json.dumps([command, "echo later"])
                job = self.create(name=f"mutate-{number}.json", acceptance=[
                    {"kind": "command", "value": command}, {"kind": "command", "value": "echo later"}])
                run = self.invoke("job", "run", job["job_id"], "--provider", "codex", "--json")
                self.assertEqual(run.returncode, 0, run.stderr)
                job = json.loads(run.stdout)
                report = self.check_report(job)
                self.assertEqual(report["status"], "source-changed")
                self.assertTrue(report["source_changed"])
                self.assertEqual(report["checks"][0]["exit_code"], 0)
                self.assertEqual(report["checks"][1]["status"], "unexecuted")
                workspace = Path(job["attempts"][-1]["workspace_path"])
                if "printf" in command:
                    self.assertNotEqual((workspace / "tracked.txt").read_text(), "base\n")

    def test_check_failure_with_source_change_stays_failed(self):
        job, workspace = self.check_fixture(["printf changed > tracked.txt; exit 4"])
        report = self.check_report(job)
        self.assertEqual(report["status"], "failed")
        self.assertTrue(report["source_changed"])
        self.assertEqual((workspace / "tracked.txt").read_text(), "changed")

    def test_check_detects_byte_changes_under_existing_index_flags(self):
        for number, flag in enumerate(("--assume-unchanged", "--skip-worktree")):
            with self.subTest(flag=flag):
                command = "printf hidden > tracked.txt"
                self.extra_environment["FAKE_ACCEPTANCE_COMMANDS"] = json.dumps([command])
                job = self.create(name=f"hidden-{number}.json", acceptance=[
                    {"kind": "command", "value": command}])
                run = self.invoke("job", "run", job["job_id"], "--provider", "codex", "--json")
                self.assertEqual(run.returncode, 0, run.stderr)
                job = json.loads(run.stdout)
                workspace = Path(job["attempts"][-1]["workspace_path"])
                subprocess.run(["git", "-C", str(workspace), "update-index", flag, "tracked.txt"], check=True)
                report = self.check_report(job)
                self.assertEqual(report["status"], "source-changed")
                self.assertEqual(report["checks"][0]["status"], "passed")

    def test_check_rejects_symlinked_workspace_and_foreign_repository(self):
        marker = self.root / "ran"
        job, workspace = self.check_fixture([f"touch {marker}"])
        moved = workspace.with_name("moved")
        workspace.rename(moved)
        workspace.symlink_to(moved, target_is_directory=True)
        result = self.invoke("job", "check", job["job_id"], "--json")
        self.assertEqual(result.returncode, 2)
        self.assertIn("symlinked", result.stderr)
        workspace.unlink()
        workspace.mkdir()
        subprocess.run(["git", "init", "-q", str(workspace)], check=True)
        result = self.invoke("job", "check", job["job_id"], "--json")
        self.assertEqual(result.returncode, 2)
        self.assertIn("Git identity", result.stderr)
        self.assertFalse(marker.exists())

    def test_check_revalidates_later_cwd_after_trusted_command(self):
        (self.workspace / ".gitignore").write_text(".cache/\n")
        subprocess.run(["git", "-C", str(self.workspace), "add", ".gitignore"], check=True)
        subprocess.run(["git", "-C", str(self.workspace), "commit", "-qm", "ignore cache"], check=True)
        marker = self.root / "ran"
        commands = [f"rmdir .cache/work; ln -s {self.root} .cache/work", f"touch {marker}"]
        job, workspace = self.check_fixture(commands, acceptance=[
            {"kind": "command", "value": commands[0]},
            {"kind": "command", "value": commands[1], "cwd": ".cache/work"}])
        (workspace / ".cache/work").mkdir(parents=True)
        report = self.check_report(job)
        self.assertEqual(report["status"], "source-changed")
        self.assertEqual(report["checks"][1]["status"], "unexecuted")
        self.assertFalse(marker.exists())

    def test_check_rejects_escaping_cwd_at_job_creation(self):
        marker = self.root / "ran"
        for cwd in ("../outside", str(self.root), "nested/../../outside"):
            path = self.write_task("bad-cwd.json", acceptance=[
                {"kind": "command", "value": f"touch {marker}", "cwd": cwd}])
            result = self.invoke("job", "create", "--workspace", str(self.workspace),
                                 "--task", str(path), "--base", "HEAD", "--json")
            self.assertEqual(result.returncode, 2)
            self.assertFalse(marker.exists())

    def test_check_ignored_cache_is_allowed(self):
        (self.workspace / ".gitignore").write_text(".cache/\n")
        subprocess.run(["git", "-C", str(self.workspace), "add", ".gitignore"], check=True)
        subprocess.run(["git", "-C", str(self.workspace), "commit", "-qm", "ignore cache"], check=True)
        job, workspace = self.check_fixture(["mkdir -p .cache; echo cache > .cache/test"])
        report = self.check_report(job)
        self.assertEqual(report["status"], "passed")
        self.assertTrue((workspace / ".cache/test").exists())

    def test_check_rejects_bad_options_before_execution(self):
        marker = self.root / "ran"
        job, _ = self.check_fixture([f"touch {marker}"])
        for value in ("0", "-1", "nan", "inf", "-inf", "1e309", "not-a-number"):
            with self.subTest(timeout=value):
                result = self.invoke("job", "check", job["job_id"], f"--timeout={value}", "--json")
                self.assertEqual(result.returncode, 2)
                self.assertFalse(marker.exists())
        result = self.invoke("job", "check", job["job_id"], "--unknown", "--json")
        self.assertEqual(result.returncode, 2)
        self.assertFalse(marker.exists())

    def test_check_rejects_unknown_absent_and_active_attempts(self):
        from agentctl_jobs import StatePaths, Store, prepare_attempt
        marker = self.root / "ran"
        self.extra_environment["FAKE_ACCEPTANCE_COMMANDS"] = json.dumps([f"touch {marker}"])
        job = self.create(acceptance=[{"kind": "command", "value": f"touch {marker}"}])
        unknown = self.invoke("job", "id").stdout.strip()
        for job_id in (unknown, job["job_id"]):
            result = self.invoke("job", "check", job_id, "--json")
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        with Store(StatePaths.from_value(self.state_dir)) as store:
            prepare_attempt(store, job["job_id"], "codex")
        result = self.invoke("job", "check", job["job_id"], "--json")
        self.assertEqual(result.returncode, 2)
        self.assertFalse(marker.exists())

    def test_check_preflight_rejects_dirty_hidden_files_head_and_missing_workspace(self):
        marker = self.root / "ran"
        job, workspace = self.check_fixture([f"touch {marker}"])
        for flag in ("--assume-unchanged", "--skip-worktree"):
            subprocess.run(["git", "-C", str(workspace), "update-index", flag, "tracked.txt"], check=True)
            (workspace / "tracked.txt").write_text("hidden dirt\n")
            result = self.invoke("job", "check", job["job_id"], "--json")
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertFalse(marker.exists())
            (workspace / "tracked.txt").write_text("base\n")
            subprocess.run(["git", "-C", str(workspace), "update-index", flag.replace("--", "--no-", 1), "tracked.txt"], check=True)
        (workspace / "extra.py").touch()
        self.assertEqual(self.invoke("job", "check", job["job_id"], "--json").returncode, 2)
        (workspace / "extra.py").unlink()
        subprocess.run(["git", "-C", str(workspace), "commit", "--allow-empty", "-qm", "unexpected"], check=True)
        result = self.invoke("job", "check", job["job_id"], "--json")
        self.assertEqual(result.returncode, 2)
        self.assertIn("unexpected HEAD", result.stderr)
        shutil.rmtree(workspace)
        self.assertEqual(self.invoke("job", "check", job["job_id"], "--json").returncode, 2)
        self.assertFalse(marker.exists())

    def test_check_validates_all_cwds_before_first_command(self):
        marker = self.root / "ran"
        for number, cwd in enumerate(("missing", "linked", "nested/linked/child")):
            with self.subTest(cwd=cwd):
                commands = [f"touch {marker}", "pwd"]
                self.extra_environment["FAKE_ACCEPTANCE_COMMANDS"] = json.dumps(commands)
                job = self.create(name=f"cwd-{number}.json", acceptance=[
                    {"kind": "command", "value": commands[0]},
                    {"kind": "command", "value": commands[1], "cwd": cwd}])
                result = self.invoke("job", "run", job["job_id"], "--provider", "codex", "--json")
                self.assertEqual(result.returncode, 0, result.stderr)
                job = json.loads(result.stdout)
                workspace = Path(job["attempts"][-1]["workspace_path"])
                if cwd != "missing":
                    link = workspace / ("linked" if cwd == "linked" else "nested/linked")
                    link.parent.mkdir(exist_ok=True)
                    link.symlink_to(self.root, target_is_directory=True)
                result = self.invoke("job", "check", job["job_id"], "--json")
                self.assertEqual(result.returncode, 2)
                self.assertFalse(marker.exists())

    def write_collaboration_decision(self, name: str = "collaboration-decision.json") -> Path:
        decision = json.loads(
            (ROOT / "project/.agent/examples/collaboration-decision.example.json").read_text(
                encoding="utf-8"
            )
        )
        decision["base_sha"] = self.base_sha
        path = self.workspace / name
        path.write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
        return path

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

    def test_job_create_derives_collaboration_projection_from_validated_decision(self) -> None:
        task = self.write_task("derived-collaboration-task.json")
        decision = self.write_collaboration_decision()
        result = self.invoke(
            "job",
            "create",
            "--workspace",
            str(self.workspace),
            "--task",
            str(task),
            "--base",
            "HEAD",
            "--collaboration-decision",
            str(decision),
            "--json",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        job = json.loads(result.stdout)
        self.assertTrue(job["collaboration_correlated"])
        stored = json.loads(Path(job["task_path"]).read_text(encoding="utf-8"))
        annotation = stored["collaboration"]
        self.assertEqual(annotation["plan_id"], "plan-parser-regression-001")
        self.assertEqual(annotation["candidate_id"], "delegate-tests")
        self.assertEqual(annotation["relation"], "delegate")
        self.assertEqual(annotation["expected_mechanisms"], ["latency-overlap", "context-partitioning"])
        self.assertEqual(
            annotation["decision_digest"],
            "sha256:" + hashlib.sha256(decision.read_bytes()).hexdigest(),
        )

    def test_job_create_rejects_decision_for_another_base(self) -> None:
        task = self.write_task("wrong-base-collaboration-task.json")
        decision = self.write_collaboration_decision("wrong-base-decision.json")
        payload = json.loads(decision.read_text(encoding="utf-8"))
        payload["base_sha"] = "0" * 40
        decision.write_text(json.dumps(payload), encoding="utf-8")
        result = self.invoke(
            "job",
            "create",
            "--workspace",
            str(self.workspace),
            "--task",
            str(task),
            "--base",
            "HEAD",
            "--collaboration-decision",
            str(decision),
            "--json",
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("base_sha does not match", result.stderr)

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

    def test_safe_read_jobs_are_structured_across_all_providers(self) -> None:
        expected_arguments = {
            "codex": ("--sandbox", "read-only"),
            "claude": ("--permission-mode", "plan"),
            "grok": ("--sandbox", "read-only"),
        }
        for provider, expected in expected_arguments.items():
            with self.subTest(provider=provider):
                task = self.write_task(
                    f"read-{provider}.json",
                    lane="read",
                    role="researcher",
                    resource_class="light",
                )
                subprocess.run(
                    ["git", "-C", str(self.workspace), "add", task.name], check=True
                )
                subprocess.run(
                    [
                        "git",
                        "-C",
                        str(self.workspace),
                        "commit",
                        "-qm",
                        f"add {provider} read task",
                    ],
                    check=True,
                )
                created = self.invoke(
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
                self.assertEqual(created.returncode, 0, created.stdout + created.stderr)
                job = json.loads(created.stdout)
                result = self.invoke(
                    "job",
                    "run",
                    str(job["job_id"]),
                    "--provider",
                    provider,
                    "--json",
                    mode="read-success",
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                payload = json.loads(result.stdout)
                self.assertEqual(payload["state"], "succeeded")
                attempt = payload["attempts"][0]
                self.assertEqual(Path(attempt["workspace_path"]), self.workspace)
                self.assertIsNone(attempt["branch_name"])
                self.assertFalse((self.workspace / "result.txt").exists())
                process_log = json.loads(
                    Path(attempt["log_path"]).read_text(encoding="utf-8")
                )
                arguments = process_log["argv"]
                index = arguments.index(expected[0])
                self.assertEqual(arguments[index + 1], expected[1])
                if provider == "codex":
                    schema_index = arguments.index("--output-schema")
                    transport_schema = json.loads(
                        Path(arguments[schema_index + 1]).read_text(encoding="utf-8")
                    )
                else:
                    schema_index = arguments.index("--json-schema")
                    transport_schema = json.loads(arguments[schema_index + 1])
                encoded_schema = json.dumps(transport_schema)
                for omitted in (
                    "$schema",
                    "$id",
                    "uniqueItems",
                    "allOf",
                    "if",
                    "then",
                ):
                    self.assertNotIn(f'"{omitted}"', encoded_schema)
                self.assertNotIn('"oneOf"', encoded_schema)
                self.assertIn('"anyOf"', encoded_schema)
                self.assertEqual(
                    transport_schema["properties"]["schema_version"]["type"],
                    "integer",
                )
                self.assertEqual(
                    transport_schema["properties"]["status"]["type"], "string"
                )
                self.assertEqual(
                    set(transport_schema["required"]),
                    set(transport_schema["properties"]),
                )
                self.assertIn(
                    {"type": "null"},
                    transport_schema["properties"]["artifacts"]["anyOf"],
                )
                canonical_schema = (
                    Path(attempt["workspace_path"])
                    / ".agent/schemas/result.schema.json"
                ).read_text(encoding="utf-8")
                self.assertIn('"uniqueItems"', canonical_schema)
                self.assertIn('"$schema"', canonical_schema)

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
                "MIRA_COMPANION_EPISODE_DIR": str(mira_state),
                "MIRA_COMPANION_EPISODES_ENABLED": "1",
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

    def test_collaboration_decision_is_opaquely_correlated_to_mira_episode(self) -> None:
        mira_state = self.root / "mira-correlation-state"
        self.extra_environment.update(
            {
                "AGENTCTL_MIRA_BRIDGE_BIN": str(ROOT / "scripts/mira-codex-hook.py"),
                "MIRA_COMPANION_ENABLED": "1",
                "MIRA_COMPANION_STATE_DIR": str(mira_state),
                "MIRA_COMPANION_EPISODE_DIR": str(mira_state),
                "MIRA_COMPANION_EPISODES_ENABLED": "1",
            }
        )
        raw_plan_id = "private-plan-parser-001"
        raw_candidate_id = "private-candidate-consult-001"
        digest = "sha256:" + "c" * 64
        collaboration = {
            "plan_id": raw_plan_id,
            "candidate_id": raw_candidate_id,
            "decision_digest": digest,
            "relation": "consult",
            "lifecycle": "bounded-exchange",
            "expected_mechanisms": ["coverage", "error-decorrelation"],
            "binding_constraint": "evaluator",
            "annotation_source": "primary-plan",
        }
        job = self.create("mira-correlated-task.json", collaboration=collaboration)
        result = self.invoke(
            "job", "run", str(job["job_id"]), "--provider", "claude", "--json"
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        ledger = json.loads(
            (mira_state / "collaboration-episodes.json").read_text(encoding="utf-8")
        )
        self.assertEqual(len(ledger["episodes"]), 1)
        semantics = ledger["episodes"][0]["semantics"]
        self.assertEqual(semantics["relation"], "consult")
        self.assertEqual(semantics["lifecycle"], "bounded-exchange")
        self.assertEqual(semantics["bindingConstraint"], "evaluator")
        self.assertEqual(
            semantics["expectedMechanisms"], ["coverage", "error-decorrelation"]
        )
        self.assertTrue(semantics["correlation"]["available"])
        self.assertEqual(semantics["correlation"]["decisionDigest"], digest)
        persisted = "".join(
            path.read_text(encoding="utf-8") for path in mira_state.glob("*.json")
        )
        self.assertNotIn(raw_plan_id, persisted)
        self.assertNotIn(raw_candidate_id, persisted)
        self.assertNotIn(str(job["job_id"]), persisted)

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

    def test_structured_log_view_redacts_without_changing_raw_logs(self) -> None:
        job = self.create("structured-logs.json")
        run = self.invoke("job", "run", str(job["job_id"]), "--provider", "codex", "--json")
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        log_path = Path(json.loads(run.stdout)["attempts"][0]["log_path"])
        raw = (
            'before\nINFO {"api\\u005fkey":"fixture-private-value-123",'
            '"ordinary":"日本語", "nested":[{"Authorization":"fixture-auth-value"},42]}\n'
            'after\n'
        ).encode("utf-8")
        for source in (log_path, log_path.with_name("runner.log")):
            with self.subTest(source=source.name):
                source.write_bytes(raw)
                flags = ["--runner"] if source.name == "runner.log" else []
                for output_flags in (["--json"], []):
                    viewed = self.invoke("job", "logs", str(job["job_id"]), *flags, *output_flags)
                    self.assertEqual(viewed.returncode, 0, viewed.stdout + viewed.stderr)
                    content = viewed.stdout
                    if output_flags:
                        log = json.loads(content)
                        self.assertIsInstance(log["redaction_count"], int)
                        self.assertGreater(log["redaction_count"], 0)
                        content = log["content"]
                    self.assertNotIn("fixture-private-value-123", content)
                    self.assertNotIn("fixture-auth-value", content)
                    self.assertIn("before\nINFO ", content)
                    self.assertIn("\nafter\n", content)
                    line = next(line for line in content.splitlines() if line.startswith("INFO "))
                    self.assertEqual(json.loads(line[5:]), {
                        "api_key": "[REDACTED]", "ordinary": "日本語",
                        "nested": [{"Authorization": "[REDACTED]"}, 42],
                    })
                    self.assertEqual(source.read_bytes(), raw)

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

        # A same-parent cherry-pick within the same timestamp second may have
        # exactly the worker commit's SHA. Give integration a distinct parent
        # so this test really exercises patch-ID recognition, not ancestry.
        subprocess.run(
            ["git", "-C", str(self.workspace), "commit", "--allow-empty", "-m", "integration checkpoint"],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        )
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
