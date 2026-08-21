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

    def emit(self, payload: dict[str, object]) -> dict[str, object]:
        environment = os.environ.copy()
        environment["MIRA_COMPANION_STATE_DIR"] = str(self.state_dir)
        result = subprocess.run(
            ["python3", str(HOOK)],
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
                "agent_type": "researcher",
            }
        )
        self.assertEqual(state["activeSubagents"], 1)

        state = self.emit(
            {"session_id": "session-a", "hook_event_name": "SessionEnd"}
        )
        self.assertEqual(state["status"], "idle")
        self.assertEqual(state["activeSubagents"], 0)

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
