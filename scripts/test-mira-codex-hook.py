#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / "scripts" / "mira-codex-hook.py"


class MiraCodexHookTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.state_dir = Path(self.temporary.name) / "state"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def emit(
        self, payload: dict[str, object], provider: str = "codex"
    ) -> dict[str, object]:
        environment = os.environ.copy()
        environment["MIRA_COMPANION_STATE_DIR"] = str(self.state_dir)
        command = ["python3", str(HOOK)]
        if provider != "codex":
            entrypoint = Path(self.temporary.name) / f"mira-{provider}-hook"
            if not entrypoint.exists():
                entrypoint.symlink_to(HOOK)
            command = [str(entrypoint)]
        result = subprocess.run(
            command,
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env=environment,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        return json.loads((self.state_dir / "state.json").read_text(encoding="utf-8"))

    def all_persisted_json(self) -> str:
        return "".join(
            path.read_text(encoding="utf-8")
            for path in self.state_dir.glob("*.json")
        )

    def test_prompt_content_is_not_persisted(self) -> None:
        secret = "do-not-store-this-prompt"
        state = self.emit(
            {
                "session_id": "session-a",
                "hook_event_name": "UserPromptSubmit",
                "prompt": secret,
                "cwd": "/workspace",
            }
        )
        self.assertEqual(state["status"], "thinking")
        serialized = self.all_persisted_json()
        self.assertNotIn(secret, serialized)
        self.assertNotIn("session-a", serialized)

    def test_tool_categories_are_sanitized(self) -> None:
        command = "pytest tests/private-customer-name"
        state = self.emit(
            {
                "session_id": "session-a",
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": command},
            }
        )
        self.assertEqual(state["status"], "testing")
        self.assertEqual(state["toolCategory"], "test")
        persisted = self.all_persisted_json()
        self.assertNotIn(command, persisted)

        state = self.emit(
            {
                "session_id": "session-a",
                "hook_event_name": "PreToolUse",
                "tool_name": "apply_patch",
                "tool_input": {"command": "private patch text"},
            }
        )
        self.assertEqual(state["status"], "typing")
        self.assertEqual(state["toolCategory"], "edit")

    def test_structured_test_outcomes_are_kept_without_tool_output(self) -> None:
        command = "pytest tests/private-customer-name"
        response_secret = "customer-output-must-not-persist"
        self.emit(
            {
                "session_id": "session-a",
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": command},
            }
        )
        state = self.emit(
            {
                "session_id": "session-a",
                "hook_event_name": "PostToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": command},
                "tool_response": {"exit_code": 1, "output": response_secret},
            }
        )
        latest = state["recentEvents"][-1]
        self.assertEqual(latest["category"], "test")
        self.assertEqual(latest["outcome"], "failure")

        state = self.emit(
            {
                "session_id": "session-a",
                "hook_event_name": "PostToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": command},
                "tool_response": {"exit_code": 0, "output": response_secret},
            }
        )
        self.assertEqual(state["recentEvents"][-1]["outcome"], "success")
        persisted = self.all_persisted_json()
        self.assertNotIn(command, persisted)
        self.assertNotIn(response_secret, persisted)

    def test_unstructured_tool_output_is_never_interpreted_or_stored(self) -> None:
        response = "exit_code=1 private-output"
        state = self.emit(
            {
                "session_id": "session-a",
                "hook_event_name": "PostToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "pytest"},
                "tool_response": response,
            }
        )
        self.assertEqual(state["recentEvents"][-1]["outcome"], "unknown")
        self.assertNotIn(response, self.all_persisted_json())

    def test_recent_event_ring_is_bounded(self) -> None:
        state: dict[str, object] = {}
        for index in range(30):
            state = self.emit(
                {
                    "session_id": "session-a",
                    "hook_event_name": "UserPromptSubmit",
                    "prompt": f"private-{index}",
                }
            )
        self.assertEqual(len(state["recentEvents"]), 24)
        timeline = json.loads(
            (self.state_dir / "timeline.json").read_text(encoding="utf-8")
        )
        self.assertEqual(len(timeline), 24)
        self.assertEqual(len({event["id"] for event in timeline}), 24)
        self.assertNotIn("private-29", self.all_persisted_json())

    def test_subagent_count_and_session_end(self) -> None:
        for agent_id in ("researcher", "reviewer"):
            state = self.emit(
                {
                    "session_id": "session-a",
                    "hook_event_name": "SubagentStart",
                    "agent_id": agent_id,
                    "agent_type": agent_id,
                }
            )
        self.assertEqual(state["status"], "delegating")
        self.assertEqual(state["activeSubagents"], 2)

        state = self.emit(
            {
                "session_id": "session-a",
                "hook_event_name": "SubagentStop",
                "agent_id": "researcher",
                "agent_type": "Explore",
            }
        )
        self.assertEqual(state["activeSubagents"], 1)

        state = self.emit(
            {"session_id": "session-a", "hook_event_name": "SessionEnd"}
        )
        self.assertEqual(state["status"], "idle")
        self.assertEqual(state["activeSubagents"], 0)

    def test_agentctl_jobs_are_provider_aware_and_sanitized(self) -> None:
        secret = "private-job-objective-must-not-persist"
        grok = self.emit(
            {
                "mira_source": "agentctl",
                "session_id": "private-grok-job-id",
                "attempt_id": "private-grok-attempt-id",
                "hook_event_name": "AgentJobStart",
                "provider": "grok",
                "role": "implementer",
                "objective": secret,
                "workspace": "/private/customer/workspace",
            }
        )
        self.assertEqual(grok["status"], "typing")
        self.assertEqual(grok["source"], "agentctl")
        self.assertEqual(grok["activeSubagents"], 1)
        self.assertEqual(grok["providerCounts"], {"codex": 0, "claude": 0, "grok": 1})
        self.assertEqual(grok["activeAgents"][0]["provider"], "grok")
        self.assertEqual(grok["activeAgents"][0]["role"], "implementer")

        mixed = self.emit(
            {
                "mira_source": "agentctl",
                "session_id": "private-claude-job-id",
                "attempt_id": "private-claude-attempt-id",
                "hook_event_name": "AgentJobStart",
                "provider": "claude",
                "role": "researcher",
            }
        )
        self.assertEqual(mixed["status"], "research")
        self.assertEqual(mixed["activeSubagents"], 2)
        self.assertEqual(mixed["providerCounts"], {"codex": 0, "claude": 1, "grok": 1})

        still_working = self.emit(
            {
                "mira_source": "agentctl",
                "session_id": "private-grok-job-id",
                "attempt_id": "private-grok-attempt-id",
                "hook_event_name": "AgentJobSucceeded",
                "provider": "grok",
                "role": "implementer",
            }
        )
        self.assertEqual(still_working["status"], "research")
        self.assertEqual(still_working["activeSubagents"], 1)
        self.assertEqual(still_working["recentEvents"][-1]["outcome"], "success")

        complete = self.emit(
            {
                "mira_source": "agentctl",
                "session_id": "private-claude-job-id",
                "attempt_id": "private-claude-attempt-id",
                "hook_event_name": "AgentJobSucceeded",
                "provider": "claude",
                "role": "researcher",
            }
        )
        self.assertEqual(complete["status"], "success")
        self.assertEqual(complete["activeSubagents"], 0)
        self.assertEqual(complete["activeAgents"], [])
        persisted = self.all_persisted_json()
        self.assertNotIn(secret, persisted)
        self.assertNotIn("private-grok-job-id", persisted)
        self.assertNotIn("private-grok-attempt-id", persisted)
        self.assertNotIn("/private/customer/workspace", persisted)

    def test_direct_claude_events_are_provider_aware_and_sanitized(self) -> None:
        prompt_secret = "private-claude-prompt"
        state = self.emit(
            {
                "session_id": "private-claude-session",
                "hook_event_name": "UserPromptSubmit",
                "prompt": prompt_secret,
                "cwd": "/private/claude/workspace",
            },
            provider="claude",
        )
        self.assertEqual(state["status"], "thinking")
        self.assertEqual(state["source"], "claude-hook")
        self.assertEqual(
            state["providerCounts"], {"codex": 0, "claude": 1, "grok": 0}
        )
        self.assertEqual(state["recentEvents"][-1]["provider"], "claude")

        delegated = self.emit(
            {
                "session_id": "private-claude-session",
                "hook_event_name": "SubagentStart",
                "agent_id": "private-claude-agent",
                "agent_type": "Explore",
                "prompt": "private-agent-task",
            },
            provider="claude",
        )
        self.assertEqual(delegated["activeSubagents"], 1)
        self.assertEqual(delegated["activeAgents"][0]["provider"], "claude")
        self.assertEqual(delegated["activeAgents"][0]["role"], "researcher")
        self.assertEqual(
            delegated["providerCounts"], {"codex": 0, "claude": 2, "grok": 0}
        )
        persisted = self.all_persisted_json()
        for secret in (
            prompt_secret,
            "private-claude-session",
            "private-claude-agent",
            "private-agent-task",
            "/private/claude/workspace",
        ):
            self.assertNotIn(secret, persisted)

    def test_grok_camel_case_wire_format_is_normalized(self) -> None:
        command_secret = "pytest tests/private-grok-customer"
        response_secret = "private-grok-tool-output"
        state = self.emit(
            {
                "hookEventName": "pre_tool_use",
                "sessionId": "private-grok-session",
                "toolName": "run_terminal_command",
                "toolInput": {"command": command_secret},
                "cwd": "/private/grok/workspace",
            },
            provider="grok",
        )
        self.assertEqual(state["status"], "testing")
        self.assertEqual(state["toolCategory"], "test")
        self.assertEqual(state["source"], "grok-hook")
        self.assertEqual(
            state["providerCounts"], {"codex": 0, "claude": 0, "grok": 1}
        )
        latest = state["recentEvents"][-1]
        self.assertEqual(latest["event"], "PreToolUse")
        self.assertEqual(latest["provider"], "grok")

        state = self.emit(
            {
                "hookEventName": "post_tool_use",
                "sessionId": "private-grok-session",
                "toolName": "run_terminal_command",
                "toolInput": {"command": command_secret},
                "toolResult": {"exitCode": 0, "output": response_secret},
            },
            provider="grok",
        )
        self.assertEqual(state["recentEvents"][-1]["outcome"], "success")

        approval = self.emit(
            {
                "hookEventName": "notification",
                "sessionId": "private-grok-session",
                "notificationType": "permission_prompt",
                "message": "private permission message",
            },
            provider="grok",
        )
        self.assertEqual(approval["status"], "approval")
        self.assertEqual(approval["event"], "PermissionRequest")
        persisted = self.all_persisted_json()
        for secret in (
            command_secret,
            response_secret,
            "private-grok-session",
            "/private/grok/workspace",
            "private permission message",
        ):
            self.assertNotIn(secret, persisted)

    def test_provider_failure_and_cancel_events_have_safe_states(self) -> None:
        failed = self.emit(
            {
                "session_id": "claude-failure-session",
                "hook_event_name": "PostToolUseFailure",
                "tool_name": "Bash",
                "tool_input": {"command": "pytest private-suite"},
                "error": "private failure detail",
            },
            provider="claude",
        )
        self.assertEqual(failed["status"], "error")
        self.assertEqual(failed["toolCategory"], "test")
        self.assertEqual(failed["recentEvents"][-1]["outcome"], "failure")

        stopped = self.emit(
            {
                "hookEventName": "stop_failure",
                "sessionId": "grok-failure-session",
                "errorDetails": "private API failure",
            },
            provider="grok",
        )
        self.assertEqual(stopped["status"], "error")
        self.assertEqual(stopped["recentEvents"][-1]["outcome"], "failure")

        cancelled = self.emit(
            {
                "hookEventName": "stop_cancelled",
                "sessionId": "grok-failure-session",
                "reasonDetails": "private cancel detail",
            },
            provider="grok",
        )
        self.assertEqual(cancelled["status"], "error")
        self.assertEqual(cancelled["recentEvents"][-1]["status"], "ready")
        persisted = self.all_persisted_json()
        self.assertNotIn("private failure detail", persisted)
        self.assertNotIn("private API failure", persisted)
        self.assertNotIn("private cancel detail", persisted)

    def test_grok_idle_notification_settles_interrupts_without_hiding_completion(self) -> None:
        self.emit(
            {
                "hookEventName": "user_prompt_submit",
                "sessionId": "grok-idle-session",
                "prompt": "private prompt",
            },
            provider="grok",
        )
        interrupted = self.emit(
            {
                "hookEventName": "notification",
                "sessionId": "grok-idle-session",
                "notificationType": "idle_prompt",
            },
            provider="grok",
        )
        self.assertEqual(interrupted["status"], "ready")
        self.assertEqual(interrupted["event"], "TurnIdle")

        complete = self.emit(
            {
                "hookEventName": "stop",
                "sessionId": "grok-idle-session",
            },
            provider="grok",
        )
        self.assertEqual(complete["status"], "success")
        settled = self.emit(
            {
                "hookEventName": "notification",
                "sessionId": "grok-idle-session",
                "notificationType": "idle_prompt",
            },
            provider="grok",
        )
        self.assertEqual(settled["status"], "success")
        self.assertEqual(settled["event"], "Stop")
        self.assertEqual(settled["recentEvents"][-1]["event"], "TurnIdle")
        self.assertNotIn("private prompt", self.all_persisted_json())

    def test_permission_has_priority_across_sessions(self) -> None:
        self.emit(
            {"session_id": "session-a", "hook_event_name": "UserPromptSubmit"}
        )
        state = self.emit(
            {
                "session_id": "session-b",
                "hook_event_name": "PermissionRequest",
                "tool_name": "Bash",
            }
        )
        self.assertEqual(state["status"], "approval")

    def test_explicit_disable_does_not_write_state(self) -> None:
        environment = os.environ.copy()
        environment["MIRA_COMPANION_STATE_DIR"] = str(self.state_dir)
        environment["MIRA_COMPANION_ENABLED"] = "0"
        result = subprocess.run(
            ["python3", str(HOOK)],
            input=json.dumps(
                {
                    "session_id": "session-a",
                    "hook_event_name": "UserPromptSubmit",
                }
            ),
            text=True,
            capture_output=True,
            env=environment,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.state_dir / "state.json").exists())

    def test_state_write_failure_is_provider_fail_open(self) -> None:
        blocked_state = Path(self.temporary.name) / "not-a-directory"
        blocked_state.write_text("occupied", encoding="utf-8")
        environment = os.environ.copy()
        environment["MIRA_COMPANION_STATE_DIR"] = str(blocked_state)
        result = subprocess.run(
            ["python3", str(HOOK)],
            input=json.dumps(
                {
                    "session_id": "session-a",
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Bash",
                }
            ),
            text=True,
            capture_output=True,
            env=environment,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")
        self.assertEqual(blocked_state.read_text(encoding="utf-8"), "occupied")

    def test_concurrent_subagent_events_do_not_lose_updates(self) -> None:
        environment = os.environ.copy()
        environment["MIRA_COMPANION_STATE_DIR"] = str(self.state_dir)

        def start_agent(index: int) -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                ["python3", str(HOOK)],
                input=json.dumps(
                    {
                        "session_id": "session-a",
                        "hook_event_name": "SubagentStart",
                        "agent_id": f"agent-{index}",
                    }
                ),
                text=True,
                capture_output=True,
                env=environment,
                check=False,
            )

        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(start_agent, range(8)))
        self.assertTrue(all(result.returncode == 0 for result in results))
        state = json.loads((self.state_dir / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["status"], "delegating")
        self.assertEqual(state["activeSubagents"], 8)


if __name__ == "__main__":
    unittest.main()
