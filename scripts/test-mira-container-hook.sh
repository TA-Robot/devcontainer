#!/usr/bin/env bash
set -euo pipefail

image="${1:-devcontainer-smoke:latest}"

docker image inspect "$image" >/dev/null

docker run --rm -i \
  --entrypoint python3 \
  -e MIRA_COMPANION_STATE_DIR=/tmp/mira-companion-state \
  -e MIRA_COMPANION_EPISODE_DIR=/var/lib/mira-observations \
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
EXPECTED_CLAUDE_EVENTS = {
    "SessionStart",
    "SessionEnd",
    "UserPromptSubmit",
    "PreToolUse",
    "PostToolUse",
    "PostToolUseFailure",
    "PermissionRequest",
    "PermissionDenied",
    "SubagentStart",
    "SubagentStop",
    "Stop",
    "StopFailure",
}
REQUIRED_GROK_EVENTS = {
    "session_start",
    "session_end",
    "user_prompt_submit",
    "pre_tool_use",
    "post_tool_use",
    "post_tool_use_failure",
    "permission_denied",
    "notification",
    "subagent_start",
    "subagent_stop",
    "stop",
    "stop_failure",
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
bridge_entrypoint = pathlib.Path("/usr/local/bin/mira-codex-hook")
claude_entrypoint = pathlib.Path("/usr/local/bin/mira-claude-hook")
grok_entrypoint = pathlib.Path("/usr/local/bin/mira-grok-hook")
requirements_path = pathlib.Path("/etc/codex/requirements.toml")
claude_settings_path = pathlib.Path(
    "/etc/claude-code/managed-settings.d/50-mira-companion.json"
)
grok_config_path = pathlib.Path("/etc/grok/managed_config.toml")
observation_dir = pathlib.Path(os.environ["MIRA_COMPANION_EPISODE_DIR"])
if not hook_path.is_file() or not os.access(hook_path, os.X_OK):
    raise AssertionError("managed Mira hook is missing or not executable")
if not bridge_entrypoint.is_file() or not os.access(bridge_entrypoint, os.X_OK):
    raise AssertionError("agentctl cannot discover the Mira bridge on PATH")
for entrypoint in (claude_entrypoint, grok_entrypoint):
    if not entrypoint.is_file() or not os.access(entrypoint, os.X_OK):
        raise AssertionError(f"provider Mira entrypoint is unavailable: {entrypoint}")
if not requirements_path.is_file():
    raise AssertionError("system requirements.toml is missing")
for config_path in (claude_settings_path, grok_config_path):
    if not config_path.is_file() or config_path.stat().st_mode & 0o222:
        raise AssertionError(f"managed provider config is missing or writable: {config_path}")
if (
    not observation_dir.is_dir()
    or observation_dir.stat().st_uid != os.getuid()
    or observation_dir.stat().st_mode & 0o777 != 0o700
):
    raise AssertionError(
        f"persistent observation directory is not private/writable: {observation_dir}"
    )

claude_settings = json.loads(claude_settings_path.read_text(encoding="utf-8"))
claude_hooks = claude_settings.get("hooks", {})
if set(claude_hooks) != EXPECTED_CLAUDE_EVENTS:
    raise AssertionError(f"unexpected Claude hook events: {sorted(claude_hooks)}")
for event, groups in claude_hooks.items():
    handlers = [handler for group in groups for handler in group.get("hooks", [])]
    if len(handlers) != 1 or handlers[0].get("command") != str(claude_entrypoint):
        raise AssertionError(f"unexpected Claude hook handler for {event}: {handlers}")

claude_state_dir = pathlib.Path("/tmp/mira-claude-native")
claude_environment = os.environ.copy()
claude_environment["MIRA_COMPANION_STATE_DIR"] = str(claude_state_dir)
claude_init = subprocess.run(
    ["claude", "--init-only"],
    cwd="/workspace",
    env=claude_environment,
    text=True,
    capture_output=True,
    timeout=20,
    check=False,
)
if claude_init.returncode != 0:
    raise AssertionError(
        f"Claude managed hook probe failed: {claude_init.stdout}\n{claude_init.stderr}"
    )
claude_timeline_path = claude_state_dir / "timeline.json"
if not claude_timeline_path.is_file():
    raise AssertionError("Claude --init-only did not fire the managed SessionStart hook")
claude_timeline = json.loads(claude_timeline_path.read_text(encoding="utf-8"))
if not any(
    event.get("event") == "SessionStart" and event.get("provider") == "claude"
    for event in claude_timeline
):
    raise AssertionError(f"Claude native hook was not provider-aware: {claude_timeline}")

grok_inspect = subprocess.run(
    ["grok", "inspect", "--json"],
    cwd="/workspace",
    text=True,
    capture_output=True,
    timeout=20,
    check=False,
)
if grok_inspect.returncode != 0:
    raise AssertionError(
        f"Grok managed hook discovery failed: {grok_inspect.stdout}\n{grok_inspect.stderr}"
    )
grok_discovery = json.loads(grok_inspect.stdout)
managed_grok_hooks = [
    hook
    for hook in grok_discovery.get("hooks", [])
    if hook.get("target") == str(grok_entrypoint)
]
actual_grok_events = {hook.get("event") for hook in managed_grok_hooks}
if not REQUIRED_GROK_EVENTS.issubset(actual_grok_events):
    raise AssertionError(
        f"missing Grok managed hook events: {sorted(REQUIRED_GROK_EVENTS - actual_grok_events)}"
    )
if not all("managed" in str(hook.get("source", {})).lower() for hook in managed_grok_hooks):
    raise AssertionError(f"Grok hooks were not managed: {managed_grok_hooks}")
notification_matchers = {
    hook.get("matcher")
    for hook in managed_grok_hooks
    if hook.get("event") == "notification"
}
if notification_matchers != {"permission_prompt", "idle_prompt"}:
    raise AssertionError(f"unexpected Grok notification hooks: {notification_matchers}")

grok_state_dir = pathlib.Path("/tmp/mira-grok-native")
grok_environment = os.environ.copy()
grok_environment["MIRA_COMPANION_STATE_DIR"] = str(grok_state_dir)
grok_payload = {
    "hookEventName": "pre_tool_use",
    "sessionId": "private-container-grok-session",
    "toolName": "run_terminal_command",
    "toolInput": {"command": "pytest private-container-grok-suite"},
}
grok_bridge = subprocess.run(
    [str(grok_entrypoint)],
    input=json.dumps(grok_payload),
    env=grok_environment,
    text=True,
    capture_output=True,
    check=False,
)
if grok_bridge.returncode != 0:
    raise AssertionError(f"Grok provider adapter failed: {grok_bridge.stderr}")
grok_state_path = grok_state_dir / "state.json"
grok_state = json.loads(grok_state_path.read_text(encoding="utf-8"))
if (
    grok_state["source"] != "grok-hook"
    or grok_state["status"] != "testing"
    or grok_state["providerCounts"] != {"codex": 0, "claude": 0, "grok": 1}
):
    raise AssertionError(f"unexpected Grok provider state: {grok_state}")
if "private-container-grok" in "".join(
    path.read_text(encoding="utf-8") for path in grok_state_dir.glob("*.json")
):
    raise AssertionError("private Grok hook input leaked into Mira state")

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

agentctl_payload = {
    "mira_source": "agentctl",
    "session_id": "private-agentctl-job",
    "attempt_id": "private-agentctl-attempt",
    "hook_event_name": "AgentJobStart",
    "provider": "grok",
    "role": "implementer",
    "objective": "private objective",
}
result = subprocess.run(
    [str(hook_path)],
    input=json.dumps(agentctl_payload),
    text=True,
    capture_output=True,
    check=False,
)
if result.returncode != 0:
    raise AssertionError(f"managed agentctl bridge failed: {result.stderr}")
state = json.loads(state_path.read_text(encoding="utf-8"))
if state["source"] != "mira-activity-bridge":
    raise AssertionError(f"unexpected mixed activity source: {state['source']}")
if state["providerCounts"] != {"codex": 1, "claude": 0, "grok": 1}:
    raise AssertionError(f"unexpected provider counts: {state['providerCounts']}")
if state["activeAgents"][0]["role"] != "implementer":
    raise AssertionError(f"unexpected active agent metadata: {state['activeAgents']}")
agentctl_payload["hook_event_name"] = "AgentJobSucceeded"
result = subprocess.run(
    [str(hook_path)],
    input=json.dumps(agentctl_payload),
    text=True,
    capture_output=True,
    check=False,
)
if result.returncode != 0:
    raise AssertionError(f"managed observation terminal failed: {result.stderr}")
ledger_path = (
    pathlib.Path(os.environ["MIRA_COMPANION_EPISODE_DIR"])
    / "collaboration-episodes.json"
)
ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
managed_episodes = [
    episode
    for episode in ledger.get("episodes", [])
    if episode.get("topology") == "managed-job"
]
if len(managed_episodes) != 1:
    raise AssertionError(f"managed job episode was not observed: {ledger}")
if (
    managed_episodes[0].get("provider") != "grok"
    or managed_episodes[0].get("terminalOutcome") != "success"
):
    raise AssertionError(f"unexpected managed episode: {managed_episodes[0]}")
persisted = "".join(
    path.read_text(encoding="utf-8")
    for path in state_path.parent.glob("*.json")
)
persisted += ledger_path.read_text(encoding="utf-8")
if "private-agentctl-job" in persisted or "private objective" in persisted:
    raise AssertionError("private agentctl content leaked into Mira state")

print(
    "Mira bridge OK: native hooks, sanitized agentctl state, zero-input episodes"
)
PY

observation_volume="mira-observation-smoke-${BASHPID}-${RANDOM}"
cleanup_observation_volume() {
  if [[ "$observation_volume" == mira-observation-smoke-* ]]; then
    docker volume rm -f "$observation_volume" >/dev/null 2>&1 || true
  fi
}
trap cleanup_observation_volume EXIT
docker volume create "$observation_volume" >/dev/null

docker run --rm -i \
  --entrypoint python3 \
  -v "$observation_volume:/var/lib/mira-observations" \
  -e MIRA_COMPANION_STATE_DIR=/tmp/mira-persistence-state \
  -e MIRA_COMPANION_EPISODE_DIR=/var/lib/mira-observations \
  "$image" - <<'PY'
import json
import os
import pathlib
import subprocess

hook = "/usr/local/bin/mira-codex-hook"
environment = os.environ.copy()
for event in ("UserPromptSubmit", "Stop"):
    result = subprocess.run(
        [hook],
        input=json.dumps(
            {
                "session_id": "private-persistence-session",
                "hook_event_name": event,
                "prompt": "private-persistence-content",
            }
        ),
        text=True,
        capture_output=True,
        env=environment,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
ledger = pathlib.Path(os.environ["MIRA_COMPANION_EPISODE_DIR"]) / "collaboration-episodes.json"
if not ledger.is_file():
    raise AssertionError("observation ledger was not written to the mounted volume")
PY

docker run --rm -i \
  --entrypoint python3 \
  -v "$observation_volume:/var/lib/mira-observations" \
  -e MIRA_COMPANION_EPISODE_DIR=/var/lib/mira-observations \
  "$image" - <<'PY'
import json
import os
import pathlib

ledger_path = pathlib.Path(os.environ["MIRA_COMPANION_EPISODE_DIR"]) / "collaboration-episodes.json"
ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
if len(ledger.get("episodes", [])) != 1:
    raise AssertionError(f"observation did not survive container recreation: {ledger}")
serialized = ledger_path.read_text(encoding="utf-8")
if "private-persistence" in serialized:
    raise AssertionError("private persistence probe content leaked into the ledger")
PY

cleanup_observation_volume
trap - EXIT
echo "Mira observation persistence OK: named-volume ledger survives recreation"
