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
    PROVIDER_EFFORTS,
    _classify_codex_failure,
    _validate_auth_file,
    probe_codex_agent_sandbox,
    run_codex_fixture,
    run_codex_study_once,
    run_isolated_provider_fixture,
    run_provider_study_once,
)
from agent_duration_study import DurationStudyError, validate_run_record  # noqa: E402


class AgentDurationLiveTests(unittest.TestCase):
    def make_fake_docker(
        self,
        directory: Path,
        *,
        hidden_exit: int = 0,
        grok_exit: int = 0,
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
    if arguments[-2:] == ["claude", "--version"]:
        print("2.1.220 (Claude Code)")
        raise SystemExit(0)
    if arguments[-2:] in (["/provider-bin/grok", "--version"], ["grok", "--version"]):
        print("grok 1.0.5 (fixture) [stable]")
        raise SystemExit(0)
    prompt = sys.stdin.buffer.read()
    stdin_log.write_text(str(len(prompt)), encoding="utf-8")
    is_codex = "exec" in arguments
    is_claude = "--print" in arguments and "claude" in arguments
    is_grok = "--prompt-file" in arguments
    if is_codex or is_claude or is_grok:
        workspace_mount = next(
            item
            for item in arguments
            if item.startswith("type=bind,src=") and ",dst=/case" in item
        )
        workspace = Path(workspace_mount.split(",dst=/case", 1)[0].split("src=", 1)[1])
        (workspace / ".fake-agent-change").write_text("changed\\n", encoding="utf-8")
        if is_codex:
            events = [
                {{"type": "thread.started", "thread_id": "private-thread-id"}},
                {{"type": "turn.started"}},
                {{"type": "item.completed", "item": {{"type": "agent_message", "text": "private final text"}}}},
                {{"type": "turn.completed", "usage": {{"input_tokens": 10, "cached_input_tokens": 2, "output_tokens": 3, "reasoning_output_tokens": 1}}}},
            ]
        elif is_claude:
            events = [
                {{"type": "system", "subtype": "init", "session_id": "private-claude-session", "model": "claude-opus-5"}},
                {{"type": "assistant", "session_id": "private-claude-session", "message": {{"role": "assistant", "model": "claude-opus-5", "content": [{{"type": "text", "text": "private claude answer"}}]}}}},
                {{"type": "result", "subtype": "success", "session_id": "private-claude-session", "result": "private final text", "usage": {{"input_tokens": 12, "cache_read_input_tokens": 4, "output_tokens": 5}}, "modelUsage": {{"claude-opus-5": {{"costUSD": 0.0}}}}}},
            ]
        else:
            home_mount = next(
                item
                for item in arguments
                if item.startswith("type=bind,src=") and ",dst=/agent-home" in item
            )
            agent_home = Path(home_mount.split(",dst=/agent-home", 1)[0].split("src=", 1)[1])
            summary = agent_home / ".grok" / "sessions" / "fixture-session" / "summary.json"
            summary.parent.mkdir(parents=True, exist_ok=True)
            requested_effort = arguments[arguments.index("--reasoning-effort") + 1]
            requested_model = arguments[arguments.index("--model") + 1]
            summary.write_text(json.dumps({{"current_model_id": requested_model, "reasoning_effort": requested_effort, "sandbox_profile": "duration-fixture"}}), encoding="utf-8")
            events = [
                {{"jsonrpc": "2.0", "method": "session/update", "params": {{"sessionId": "private-grok-session", "update": {{"sessionUpdate": "agent_message_chunk", "content": {{"type": "text", "text": "private grok answer"}}}}}}}},
                {{"type": "completed", "sessionId": "private-grok-session", "usage": {{"inputTokens": 14, "cachedInputTokens": 3, "outputTokens": 6}}}},
            ]
        for event in events:
            print(json.dumps(event))
        if is_grok and {grok_exit} != 0:
            print("unknown effort requested", file=sys.stderr)
            raise SystemExit({grok_exit})
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

    def write_provider_auth(self, directory: Path, provider: str) -> Path:
        if provider == "codex":
            path = directory / "auth.json"
            value = {
                "auth_mode": "chatgpt",
                "tokens": {
                    "access_token": "e30.eyJleHAiOjQxMDI0NDQ4MDB9.signature",
                    "refresh_token": "private-refresh",
                },
            }
        elif provider == "claude":
            path = directory / ".credentials.json"
            value = {
                "claudeAiOauth": {
                    "accessToken": "private-access",
                    "refreshToken": "private-refresh",
                    "expiresAt": 4102444800000,
                }
            }
        elif provider == "grok":
            path = directory / "auth.json"
            value = {
                "fixture-account": {
                    "key": "private-key",
                    "refresh_token": "private-refresh",
                    "expires_at": "2100-01-01T00:00:00Z",
                }
            }
        else:
            self.fail(f"unsupported fixture auth provider: {provider}")
        path.write_text(json.dumps(value) + "\n", encoding="utf-8")
        path.chmod(0o600)
        return path

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
            auth = self.write_provider_auth(root, "codex")

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
            self.assertNotIn("private-", serialized_result)
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

    def test_claude_runner_keeps_xhigh_request_isolated_and_content_free(self) -> None:
        with tempfile.TemporaryDirectory(prefix="duration-live-claude-") as raw_temp:
            root = Path(raw_temp)
            fixture_dir = self.build_s_fixture(root)
            fake_docker, call_log, _ = self.make_fake_docker(root)
            auth = self.write_provider_auth(root, "claude")

            result = run_isolated_provider_fixture(
                "claude",
                fixture_dir,
                image="provider-fixture:locked",
                model="opus",
                effort="xhigh",
                auth_file=auth,
                live_generation_authorized=True,
                docker_bin=str(fake_docker),
                timeout_seconds=2,
                output_bytes_cap=16 * 1024,
            )
            self.assertEqual(result["infrastructure"], "success")
            self.assertEqual(
                result["model_identity"],
                {
                    "requested_alias": "opus",
                    "requested_source": "flag",
                    "resolved_id": "claude-opus-5",
                    "identity_confidence": "exact",
                },
            )
            self.assertEqual(
                result["generation_settings"],
                [
                    {
                        "namespace": "claude.reasoning",
                        "key": "effort",
                        "requested_value": "xhigh",
                        "status": "unknown",
                    }
                ],
            )
            self.assertEqual(result["events"]["usage"]["cached_input_tokens"], 4)
            self.assertTrue(result["events"]["final_message_observed"])

            serialized_result = json.dumps(result, sort_keys=True)
            self.assertNotIn("private-claude-session", serialized_result)
            self.assertNotIn("private claude answer", serialized_result)
            self.assertNotIn("private-", serialized_result)
            self.assertNotIn(str(auth), serialized_result)

            calls = [
                json.loads(line)
                for line in call_log.read_text(encoding="utf-8").splitlines()
            ]
            run = next(call for call in calls if "--print" in call)
            serialized_run = json.dumps(run)
            self.assertIn("--safe-mode", run)
            self.assertIn("--no-session-persistence", run)
            self.assertIn("--strict-mcp-config", run)
            self.assertIn("xhigh", run)
            self.assertIn(
                "dst=/agent-home/.claude/.credentials.json,readonly",
                serialized_run,
            )
            self.assertNotIn(".claude.json", serialized_run)
            self.assertNotIn(str(ROOT), serialized_run)

    def test_grok_runner_observes_max_effort_from_ephemeral_metadata(self) -> None:
        with tempfile.TemporaryDirectory(prefix="duration-live-grok-") as raw_temp:
            root = Path(raw_temp)
            fixture_dir = self.build_s_fixture(root)
            fake_docker, call_log, _ = self.make_fake_docker(root)
            auth = self.write_provider_auth(root, "grok")

            result = run_isolated_provider_fixture(
                "grok",
                fixture_dir,
                image="provider-fixture:locked",
                model="grok-4.6",
                effort="max",
                auth_file=auth,
                live_generation_authorized=True,
                docker_bin=str(fake_docker),
                timeout_seconds=2,
                output_bytes_cap=16 * 1024,
                provider_binary=fake_docker,
            )
            self.assertEqual(result["infrastructure"], "success")
            self.assertEqual(result["model_identity"]["resolved_id"], "grok-4.6")
            self.assertEqual(result["model_identity"]["identity_confidence"], "exact")
            self.assertEqual(
                result["generation_settings"][0],
                {
                    "namespace": "grok.reasoning",
                    "key": "effort",
                    "requested_value": "max",
                    "status": "applied",
                    "applied_value": "max",
                },
            )
            self.assertEqual(result["events"]["usage"]["input_tokens"], 14)
            self.assertTrue(result["events"]["final_message_observed"])

            serialized_result = json.dumps(result, sort_keys=True)
            self.assertNotIn("private-grok-session", serialized_result)
            self.assertNotIn("private grok answer", serialized_result)
            self.assertNotIn("private-", serialized_result)
            self.assertNotIn(str(auth), serialized_result)

            calls = [
                json.loads(line)
                for line in call_log.read_text(encoding="utf-8").splitlines()
            ]
            run = next(call for call in calls if "--prompt-file" in call)
            serialized_run = json.dumps(run)
            self.assertIn("duration-fixture", run)
            self.assertIn("--disable-web-search", run)
            self.assertIn("--no-subagents", run)
            self.assertIn("--no-memory", run)
            self.assertIn("max", run)
            self.assertIn(
                "dst=/agent-home/.grok/auth.json,readonly",
                serialized_run,
            )
            self.assertIn("dst=/provider-bin/grok,readonly", serialized_run)
            self.assertNotIn(str(ROOT), serialized_run)

    def test_grok_rejection_wins_over_pre_run_session_default(self) -> None:
        with tempfile.TemporaryDirectory(prefix="duration-live-grok-reject-") as raw_temp:
            root = Path(raw_temp)
            fixture_dir = self.build_s_fixture(root)
            fake_docker, _, _ = self.make_fake_docker(root, grok_exit=2)
            auth = self.write_provider_auth(root, "grok")

            result = run_isolated_provider_fixture(
                "grok",
                fixture_dir,
                image="provider-fixture:locked",
                model="grok-4.6",
                effort="max",
                auth_file=auth,
                live_generation_authorized=True,
                docker_bin=str(fake_docker),
                timeout_seconds=2,
                output_bytes_cap=16 * 1024,
                provider_binary=fake_docker,
            )
            self.assertEqual(result["infrastructure"], "failure")
            self.assertEqual(result["failure_class"], "generation-setting-rejected")
            self.assertEqual(
                result["generation_settings"][0],
                {
                    "namespace": "grok.reasoning",
                    "key": "effort",
                    "requested_value": "max",
                    "status": "rejected",
                },
            )

    def test_provider_effort_ladders_include_deep_reasoning_levels(self) -> None:
        core = {"medium", "high", "xhigh", "max"}
        self.assertTrue(core <= PROVIDER_EFFORTS["codex"])
        self.assertTrue(core <= PROVIDER_EFFORTS["claude"])
        self.assertTrue(core <= PROVIDER_EFFORTS["grok"])
        self.assertIn("ultra", PROVIDER_EFFORTS["codex"])
        self.assertNotIn("ultra", PROVIDER_EFFORTS["claude"])

    def test_expired_credential_is_rejected_before_provider_or_refresh(self) -> None:
        with tempfile.TemporaryDirectory(prefix="duration-live-expired-") as raw_temp:
            root = Path(raw_temp)
            fixture_dir = self.build_s_fixture(root)
            fake_docker, call_log, _ = self.make_fake_docker(root)
            auth = root / ".credentials.json"
            auth.write_text(
                json.dumps(
                    {
                        "claudeAiOauth": {
                            "accessToken": "private-access",
                            "refreshToken": "private-refresh",
                            "expiresAt": 0,
                        }
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            auth.chmod(0o600)

            with self.assertRaisesRegex(
                DurationStudyError,
                "credential expires inside the live-run safety window",
            ):
                run_isolated_provider_fixture(
                    "claude",
                    fixture_dir,
                    image="provider-fixture:locked",
                    model="opus",
                    effort="max",
                    auth_file=auth,
                    live_generation_authorized=True,
                    docker_bin=str(fake_docker),
                    timeout_seconds=2,
                )
            self.assertFalse(call_log.exists())

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
            auth = self.write_provider_auth(root, "codex")
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
            self.assertNotIn("private-", serialized)
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

    def test_generic_claude_study_records_criterion_score_and_configured_boundary(self) -> None:
        with tempfile.TemporaryDirectory(prefix="duration-live-claude-study-") as raw_temp:
            root = Path(raw_temp)
            fake_docker, _, _ = self.make_fake_docker(root)
            auth = self.write_provider_auth(root, "claude")
            output_dir = root / "records"

            record, record_path = run_provider_study_once(
                "claude",
                "F04-S-PY-001",
                output_dir,
                image="provider-fixture:locked",
                model="opus",
                effort="xhigh",
                auth_file=auth,
                live_generation_authorized=True,
                run_id="claude-fixture-xhigh-pass",
                docker_bin=str(fake_docker),
                timeout_seconds=2,
                evaluator_timeout_seconds=2,
                output_bytes_cap=16 * 1024,
            )
            validate_run_record(record)
            self.assertEqual(record_path, output_dir / "claude-fixture-xhigh-pass.json")
            self.assertTrue(record["outcome"]["quality_pass"])
            self.assertEqual(record["diagnostics"]["evaluator"]["score"]["passed"], 5)
            self.assertEqual(record["diagnostics"]["evaluator"]["score"]["total"], 5)
            participant = record["participants"][0]
            self.assertEqual(participant["runtime_identity"]["provider"], "claude")
            self.assertEqual(participant["runtime_identity"]["cli_source"], "container-image")
            self.assertEqual(
                participant["generation_settings"][0]["requested_value"],
                "xhigh",
            )
            preflight = record["diagnostics"]["provider"]["sandbox_preflight"]
            self.assertEqual(preflight["assurance"], "configured")
            self.assertEqual(preflight["workspace_write"], "configured")
            self.assertEqual(
                record["diagnostics"]["provider"]["task_network"],
                "denied-by-provider-sandbox",
            )
            serialized = json.dumps(record, sort_keys=True)
            self.assertNotIn("private-", serialized)
            self.assertNotIn(str(auth), serialized)

    def test_generic_grok_study_records_host_sync_and_applied_max(self) -> None:
        with tempfile.TemporaryDirectory(prefix="duration-live-grok-study-") as raw_temp:
            root = Path(raw_temp)
            fake_docker, _, _ = self.make_fake_docker(root)
            auth = self.write_provider_auth(root, "grok")

            record, _ = run_provider_study_once(
                "grok",
                "F04-S-PY-001",
                root / "records",
                image="provider-fixture:locked",
                model="grok-4.6",
                effort="max",
                auth_file=auth,
                live_generation_authorized=True,
                run_id="grok-fixture-max-pass",
                docker_bin=str(fake_docker),
                timeout_seconds=2,
                evaluator_timeout_seconds=2,
                output_bytes_cap=16 * 1024,
                provider_binary=fake_docker,
            )
            validate_run_record(record)
            participant = record["participants"][0]
            self.assertEqual(participant["runtime_identity"]["provider"], "grok")
            self.assertEqual(participant["runtime_identity"]["cli_source"], "host-sync")
            self.assertEqual(participant["model_identity"]["resolved_id"], "grok-4.6")
            self.assertEqual(
                participant["generation_settings"][0],
                {
                    "namespace": "grok.reasoning",
                    "key": "effort",
                    "requested_value": "max",
                    "status": "applied",
                    "applied_value": "max",
                },
            )


if __name__ == "__main__":
    unittest.main()
