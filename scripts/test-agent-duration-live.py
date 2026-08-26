#!/usr/bin/env python3

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from agent_duration_fixtures import build_fixture  # noqa: E402
from agent_duration_live import (  # noqa: E402
    CODEX_SANDBOX_PROBE_SCRIPT,
    CODEX_PROFILE,
    _classify_codex_failure,
    _validate_auth_file,
    probe_codex_agent_sandbox,
    run_codex_fixture,
    run_codex_study_once,
)
from agent_duration_study import DurationStudyError, validate_run_record  # noqa: E402


class AgentDurationLiveTests(unittest.TestCase):
    def make_fake_docker(
        self,
        directory: Path,
        *,
        hidden_exit: int = 0,
    ) -> tuple[Path, Path, Path]:
        executable = directory / "fake-docker"
        call_log = directory / "fake-docker.calls"
        stdin_log = directory / "fake-docker.stdin-size"
        program = f'''#!/usr/bin/env python3
import json
from pathlib import Path
import sys

call_log = Path({str(call_log)!r})
stdin_log = Path({str(stdin_log)!r})
arguments = sys.argv[1:]
with call_log.open("a", encoding="utf-8") as handle:
    handle.write(json.dumps(arguments) + "\\n")
if arguments[:2] == ["image", "inspect"]:
    print("sha256:" + "b" * 64)
    raise SystemExit(0)
if arguments[:1] == ["run"]:
    if arguments[-2:] == ["codex", "--version"]:
        print("codex-cli 9.8.7")
        raise SystemExit(0)
    prompt = sys.stdin.buffer.read()
    stdin_log.write_text(str(len(prompt)), encoding="utf-8")
    if "exec" in arguments:
        workspace_mount = next(
            item
            for item in arguments
            if item.startswith("type=bind,src=") and ",dst=/case" in item
        )
        workspace = Path(workspace_mount.split(",dst=/case", 1)[0].split("src=", 1)[1])
        (workspace / ".fake-agent-change").write_text("changed\\n", encoding="utf-8")
        events = [
            {{"type": "thread.started", "thread_id": "private-thread-id"}},
            {{"type": "turn.started"}},
            {{"type": "item.completed", "item": {{"type": "agent_message", "text": "private final text"}}}},
            {{"type": "turn.completed", "usage": {{"input_tokens": 10, "cached_input_tokens": 2, "output_tokens": 3, "reasoning_output_tokens": 1}}}},
        ]
        for event in events:
            print(json.dumps(event))
    if "/harness/hidden_tests.py" in arguments:
        raise SystemExit({hidden_exit})
    raise SystemExit(0)
if arguments[:1] == ["rm"]:
    raise SystemExit(0)
raise SystemExit(125)
'''
        executable.write_text(program, encoding="utf-8")
        executable.chmod(0o700)
        return executable, call_log, stdin_log

    def build_s_fixture(self, directory: Path) -> Path:
        fixture_dir = directory / "fixture"
        build_fixture(
            "F04-S-PY-001",
            fixture_dir,
            fixture_id="live-fixture-s",
            now=datetime(2026, 8, 26, 14, 0, tzinfo=timezone.utc),
        )
        return fixture_dir

    def test_codex_profile_is_primary_only_workspace_only_and_offline_for_commands(self) -> None:
        compile(CODEX_SANDBOX_PROBE_SCRIPT, "<sandbox-probe>", "exec")
        profile = CODEX_PROFILE.read_text(encoding="utf-8")
        self.assertIn('default_permissions = "duration-fixture"', profile)
        self.assertIn('":root" = "deny"', profile)
        self.assertIn('":minimal" = "read"', profile)
        self.assertIn('"/opt/devcontainer-ai-cli" = "read"', profile)
        self.assertIn('"." = "write"', profile)
        self.assertIn("enabled = false", profile)
        self.assertIn("multi_agent = false", profile)
        self.assertIn('web_search = "disabled"', profile)
        self.assertIn('inherit = "none"', profile)
        self.assertNotRegex(profile.lower(), r"token|api[_-]?key|password")
        self.assertEqual(
            _classify_codex_failure("failed to parse strict config"),
            "configuration",
        )
        self.assertEqual(
            _classify_codex_failure("authentication is required"),
            "authentication",
        )
        self.assertEqual(
            _classify_codex_failure("No prompt provided via stdin."),
            "prompt-input-missing",
        )

    def test_no_generation_sandbox_probe_uses_only_owned_mounts(self) -> None:
        with tempfile.TemporaryDirectory(prefix="duration-live-sandbox-") as raw_temp:
            root = Path(raw_temp)
            fixture_dir = self.build_s_fixture(root)
            fake_docker, call_log, _ = self.make_fake_docker(root)
            result = probe_codex_agent_sandbox(
                fixture_dir,
                image="codex-fixture:locked",
                docker_bin=str(fake_docker),
                timeout_seconds=2,
            )
            self.assertEqual(result["status"], "pass")
            self.assertFalse(result["generation_request_performed"])
            self.assertEqual(result["unrelated_read"], "denied")
            self.assertEqual(result["command_network"], "denied")

            calls = [
                json.loads(line)
                for line in call_log.read_text(encoding="utf-8").splitlines()
            ]
            run = next(call for call in calls if call[0] == "run")
            serialized = json.dumps(run)
            self.assertIn("sandbox", run)
            self.assertIn("duration-fixture", run)
            self.assertIn("--interactive", run)
            self.assertIn("seccomp=unconfined", run)
            self.assertIn(f"uid={os.getuid()},gid={os.getgid()}", serialized)
            self.assertIn("/case", serialized)
            self.assertIn("/agent-home", serialized)
            self.assertNotIn("auth.json", serialized)
            self.assertNotIn(str(ROOT), serialized)

    def test_live_codex_runner_is_explicit_bounded_and_content_free(self) -> None:
        with tempfile.TemporaryDirectory(prefix="duration-live-run-") as raw_temp:
            root = Path(raw_temp)
            fixture_dir = self.build_s_fixture(root)
            fake_docker, call_log, stdin_log = self.make_fake_docker(root)
            auth = root / "auth.json"
            auth.write_text('{"fixture":"credential-value"}\n', encoding="utf-8")
            auth.chmod(0o600)

            with self.assertRaises(DurationStudyError):
                run_codex_fixture(
                    fixture_dir,
                    image="codex-fixture:locked",
                    model="gpt-fixture",
                    effort="low",
                    auth_file=auth,
                    live_generation_authorized=False,
                    docker_bin=str(fake_docker),
                    timeout_seconds=2,
                )

            result = run_codex_fixture(
                fixture_dir,
                image="codex-fixture:locked",
                model="gpt-fixture",
                effort="low",
                auth_file=auth,
                live_generation_authorized=True,
                docker_bin=str(fake_docker),
                timeout_seconds=2,
                output_bytes_cap=16 * 1024,
            )
            self.assertEqual(result["infrastructure"], "success")
            self.assertIsNone(result["failure_class"])
            self.assertEqual(result["model_identity"]["identity_confidence"], "alias-only")
            self.assertEqual(result["generation_settings"][0]["status"], "unknown")
            self.assertEqual(result["events"]["event_counts"]["turn.completed"], 1)
            self.assertEqual(result["events"]["usage"]["input_tokens"], 10)
            self.assertRegex(result["events"]["thread_id_digest"], r"^sha256:[0-9a-f]{64}$")
            self.assertGreater(int(stdin_log.read_text(encoding="utf-8")), 0)

            serialized_result = json.dumps(result, sort_keys=True)
            self.assertNotIn("private-thread-id", serialized_result)
            self.assertNotIn("private final text", serialized_result)
            self.assertNotIn("credential-value", serialized_result)
            self.assertNotIn(str(auth), serialized_result)
            self.assertFalse(result["runtime"]["prompt_persisted"])
            self.assertFalse(result["runtime"]["raw_output_persisted"])
            self.assertFalse(result["runtime"]["credential_path_persisted"])

            calls = [
                json.loads(line)
                for line in call_log.read_text(encoding="utf-8").splitlines()
            ]
            run = next(call for call in calls if call[0] == "run" and "exec" in call)
            self.assertIn("--strict-config", run)
            self.assertIn("--ephemeral", run)
            self.assertIn("--ignore-rules", run)
            self.assertIn("readonly", json.dumps(run))
            self.assertNotIn(str(ROOT), json.dumps(run))

    def test_auth_source_must_be_private_regular_json(self) -> None:
        with tempfile.TemporaryDirectory(prefix="duration-live-auth-") as raw_temp:
            root = Path(raw_temp)
            auth = root / "auth.json"
            auth.write_text("{}\n", encoding="utf-8")
            auth.chmod(0o600)
            self.assertEqual(_validate_auth_file(auth), auth.resolve())

            auth.chmod(0o644)
            with self.assertRaises(DurationStudyError):
                _validate_auth_file(auth)
            auth.chmod(0o600)
            link = root / "linked-auth.json"
            link.symlink_to(auth)
            with self.assertRaises(DurationStudyError):
                _validate_auth_file(link)

    def test_one_shot_study_joins_provider_time_and_hidden_failure(self) -> None:
        with tempfile.TemporaryDirectory(prefix="duration-live-study-") as raw_temp:
            root = Path(raw_temp)
            fake_docker, call_log, _ = self.make_fake_docker(root, hidden_exit=1)
            auth = root / "auth.json"
            auth.write_text('{"fixture":"credential-value"}\n', encoding="utf-8")
            auth.chmod(0o600)
            output_dir = root / "records"

            record, record_path = run_codex_study_once(
                "F04-S-PY-001",
                output_dir,
                image="codex-fixture:locked",
                model="gpt-fixture",
                effort="low",
                auth_file=auth,
                live_generation_authorized=True,
                run_id="codex-fixture-hidden-fail",
                docker_bin=str(fake_docker),
                timeout_seconds=2,
                evaluator_timeout_seconds=2,
                output_bytes_cap=16 * 1024,
            )
            validate_run_record(record)
            self.assertEqual(record_path, output_dir / "codex-fixture-hidden-fail.json")
            self.assertEqual(json.loads(record_path.read_text(encoding="utf-8")), record)
            self.assertEqual(stat.S_IMODE(record_path.stat().st_mode), 0o600)
            self.assertEqual(record["schema_version"], 2)
            self.assertEqual(record["outcome"]["infrastructure"], "success")
            self.assertEqual(record["outcome"]["online_acceptance"], "fail")
            self.assertFalse(record["outcome"]["quality_pass"])
            self.assertEqual(
                record["outcome"]["failure_class"],
                "online-validation-failed",
            )
            self.assertEqual(record["diagnostics"]["provider"]["status"], "success")
            self.assertEqual(record["diagnostics"]["evaluator"]["status"], "fail")
            self.assertEqual(
                record["diagnostics"]["evaluator"]["score"],
                {
                    "resolution": "criterion",
                    "passed": 1,
                    "total": 5,
                    "ratio": 0.2,
                    "public_passed": 1,
                    "public_total": 1,
                    "hidden_passed": 0,
                    "hidden_total": 4,
                    "failed_check_ids": [
                        "hidden-separator-normalization",
                        "hidden-ascii-filtering",
                        "hidden-empty-result",
                        "hidden-length-bound",
                    ],
                    "all_checks_required": True,
                },
            )
            self.assertEqual(record["landmarks"]["T2"]["status"], "not-observed")
            self.assertIn("online_validation", record["durations_ms"])

            serialized = json.dumps(record, sort_keys=True)
            self.assertNotIn("private-thread-id", serialized)
            self.assertNotIn("private final text", serialized)
            self.assertNotIn("credential-value", serialized)
            self.assertNotIn(str(auth), serialized)
            calls_before_duplicate = call_log.read_text(encoding="utf-8").splitlines()
            self.assertEqual(
                sum('"exec"' in line for line in calls_before_duplicate),
                1,
            )
            with self.assertRaises(DurationStudyError):
                run_codex_study_once(
                    "F04-S-PY-001",
                    output_dir,
                    image="codex-fixture:locked",
                    model="gpt-fixture",
                    effort="low",
                    auth_file=auth,
                    live_generation_authorized=True,
                    run_id="codex-fixture-hidden-fail",
                    docker_bin=str(fake_docker),
                    timeout_seconds=2,
                    evaluator_timeout_seconds=2,
                )
            self.assertEqual(
                call_log.read_text(encoding="utf-8").splitlines(),
                calls_before_duplicate,
            )


if __name__ == "__main__":
    unittest.main()
