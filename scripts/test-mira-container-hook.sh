#!/usr/bin/env bash
set -euo pipefail

image="${1:-devcontainer-smoke:latest}"

docker image inspect "$image" >/dev/null

docker run --rm -i \
  --entrypoint python3 \
  -e MIRA_COMPANION_STATE_DIR=/tmp/mira-companion-state \
  "$image" - <<'PY'
from __future__ import annotations

import json
import os
import pathlib
import subprocess


EXPECTED_EVENTS = {
    "sessionStart",
    "sessionEnd",
    "userPromptSubmit",
    "preToolUse",
    "postToolUse",
    "permissionRequest",
    "subagentStart",
    "subagentStop",
    "stop",
}


def send(process: subprocess.Popen[str], message: dict[str, object]) -> None:
    assert process.stdin is not None
    process.stdin.write(json.dumps(message, separators=(",", ":")) + "\n")
    process.stdin.flush()


def read_response(
    process: subprocess.Popen[str], request_id: int
) -> dict[str, object]:
    assert process.stdout is not None
    while True:
        line = process.stdout.readline()
        if not line:
            stderr = process.stderr.read() if process.stderr is not None else ""
            raise RuntimeError(f"app-server exited before response {request_id}: {stderr}")
        message = json.loads(line)
        if message.get("id") == request_id:
            return message


server = subprocess.Popen(
    ["codex", "app-server", "--stdio"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    cwd="/workspace",
)
try:
    send(
        server,
        {
            "id": 1,
            "method": "initialize",
            "params": {
                "clientInfo": {
                    "name": "mira-container-smoke",
                    "title": "Mira container smoke",
                    "version": "1",
                },
                "capabilities": None,
            },
        },
    )
    initialize = read_response(server, 1)
    if "error" in initialize:
        raise RuntimeError(f"initialize failed: {initialize['error']}")

    send(server, {"method": "initialized"})
    send(
        server,
        {"id": 2, "method": "hooks/list", "params": {"cwds": ["/workspace"]}},
    )
    response = read_response(server, 2)
    if "error" in response:
        raise RuntimeError(f"hooks/list failed: {response['error']}")

    entries = response["result"]["data"]
    if len(entries) != 1:
        raise AssertionError(f"expected one cwd entry, got {len(entries)}")
    entry = entries[0]
    if entry["errors"] or entry["warnings"]:
        raise AssertionError(
            f"hook discovery diagnostics: errors={entry['errors']} warnings={entry['warnings']}"
        )
    hooks = entry["hooks"]
    actual_events = {hook["eventName"] for hook in hooks}
    if actual_events != EXPECTED_EVENTS:
        raise AssertionError(
            f"unexpected managed hook events: {sorted(actual_events)}"
        )
    for hook in hooks:
        if not hook["enabled"] or not hook["isManaged"]:
            raise AssertionError(f"hook is not enabled and managed: {hook}")
        if hook["trustStatus"] == "untrusted":
            raise AssertionError(f"managed hook unexpectedly requires trust: {hook}")
        if hook["sourcePath"] not in {
            "/etc/codex/requirements.toml",
            "/usr/local/lib/mira-companion",
        }:
            raise AssertionError(f"unexpected hook source: {hook['sourcePath']}")
finally:
    server.terminate()
    server.wait(timeout=5)


hook_path = pathlib.Path("/usr/local/lib/mira-companion/mira-codex-hook.py")
requirements_path = pathlib.Path("/etc/codex/requirements.toml")
if not hook_path.is_file() or not os.access(hook_path, os.X_OK):
    raise AssertionError("managed Mira hook is missing or not executable")
if not requirements_path.is_file():
    raise AssertionError("system requirements.toml is missing")

payload = {
    "session_id": "container-smoke",
    "turn_id": "turn-smoke",
    "hook_event_name": "PreToolUse",
    "tool_name": "apply_patch",
    "tool_use_id": "tool-smoke",
    "tool_input": {"command": "private patch content"},
}
result = subprocess.run(
    [str(hook_path)],
    input=json.dumps(payload),
    text=True,
    capture_output=True,
    check=False,
)
if result.returncode != 0:
    raise AssertionError(f"managed hook failed: {result.stderr}")

state_path = pathlib.Path(os.environ["MIRA_COMPANION_STATE_DIR"]) / "state.json"
state = json.loads(state_path.read_text(encoding="utf-8"))
if state["status"] != "typing" or state["toolCategory"] != "edit":
    raise AssertionError(f"unexpected bridge state: {state}")
if "private patch content" in state_path.read_text(encoding="utf-8"):
    raise AssertionError("private tool input leaked into Mira state")

print(
    "Mira managed hook OK: 9 trusted system events and a sanitized typing state"
)
PY
