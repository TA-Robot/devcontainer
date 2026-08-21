#!/usr/bin/env python3
"""Translate Codex lifecycle hooks into a small, sanitized Mira state file."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
SESSION_TTL_SECONDS = 60 * 60
MAX_RECENT_EVENTS = 24

STATE_PRIORITY = {
    "idle": 0,
    "ready": 10,
    "thinking": 20,
    "research": 30,
    "typing": 30,
    "terminal": 30,
    "testing": 35,
    "delegating": 40,
    "success": 50,
    "error": 80,
    "approval": 100,
}

STATE_MESSAGES = {
    "idle": "待機中だよ",
    "ready": "準備できたよ",
    "thinking": "方針を考えてるよ",
    "research": "調べもの中だよ",
    "typing": "実装してるよ",
    "terminal": "コマンドを実行中だよ",
    "testing": "テストで確認中だよ",
    "delegating": "みんなにお願いしてるよ",
    "approval": "確認を待ってるよ",
    "success": "完了したよ！",
    "error": "うまくいかなかったみたい",
}

TRANSIENT_SECONDS = {
    "ready": 4,
    "success": 8,
    "error": 15,
}

TEST_COMMAND_PATTERN = re.compile(
    r"(?:^|[;&|]\s*)(?:"
    r"pytest|python(?:3)?\s+-m\s+(?:pytest|unittest)|"
    r"npm\s+(?:run\s+)?test|pnpm\s+(?:run\s+)?test|yarn\s+(?:run\s+)?test|"
    r"cargo\s+test|go\s+test|dotnet\s+test|mvn\s+test|gradle\s+test|"
    r"bash\s+[^\s]*test[^\s]*\.sh|[^\s/]*test[^\s/]*\.sh"
    r")(?:\s|$)",
    re.IGNORECASE,
)

SECOND_AGENT_PATTERN = re.compile(
    r"(?:^|[;&|]\s*)(?:codex-second-agent|claude-second-agent|second-agent)(?:\s|$)",
    re.IGNORECASE,
)


def utc_iso(epoch: float | None = None) -> str:
    value = time.time() if epoch is None else epoch
    return datetime.fromtimestamp(value, timezone.utc).isoformat().replace("+00:00", "Z")


def state_directory() -> Path:
    configured = os.environ.get("MIRA_COMPANION_STATE_DIR")
    if configured:
        return Path(configured).expanduser()
    xdg_state = os.environ.get("XDG_STATE_HOME")
    base = Path(xdg_state).expanduser() if xdg_state else Path.home() / ".local" / "state"
    return base / "mira-companion"


def opaque_id(value: object, fallback: str) -> str:
    text = str(value or fallback)
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]


def read_json(path: Path, fallback: Any) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return fallback


def atomic_json_write(path: Path, value: object) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary_path = Path(temporary_name)
    try:
        os.fchmod(file_descriptor, 0o600)
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        try:
            temporary_path.unlink()
        except FileNotFoundError:
            pass


def string_field(value: object, limit: int = 80) -> str:
    return str(value or "")[:limit]


def tool_state(payload: dict[str, Any]) -> tuple[str, str]:
    tool_name = string_field(payload.get("tool_name"), 120)
    normalized = tool_name.lower()

    if normalized in {"agent", "spawn_agent", "subagent"}:
        return "delegating", "agent"
    if normalized in {"apply_patch", "edit", "write", "write_file", "replace"}:
        return "typing", "edit"
    if normalized == "bash":
        tool_input = payload.get("tool_input")
        command = tool_input.get("command", "") if isinstance(tool_input, dict) else ""
        command = str(command)
        if SECOND_AGENT_PATTERN.search(command):
            return "delegating", "agent"
        if TEST_COMMAND_PATTERN.search(command):
            return "testing", "test"
        return "terminal", "shell"
    if any(
        token in normalized
        for token in ("read", "search", "find", "list", "glob", "view_image", "open")
    ):
        return "research", "read"
    if normalized in {"update_plan", "request_user_input"}:
        return "thinking", "planning"
    return "thinking", "tool"


def tool_outcome(payload: dict[str, Any]) -> str:
    """Read only explicit structured success/failure fields from a tool response."""

    def inspect(value: object, depth: int = 0) -> str | None:
        if depth > 4:
            return None
        if isinstance(value, dict):
            if value.get("isError") is True or value.get("is_error") is True:
                return "failure"
            for key in ("exit_code", "exitCode"):
                exit_code = value.get(key)
                if isinstance(exit_code, int) and not isinstance(exit_code, bool):
                    return "success" if exit_code == 0 else "failure"
            status = value.get("status")
            if status in {"failed", "failure", "error"}:
                return "failure"
            if status in {"passed", "success", "succeeded"}:
                return "success"
            for child in list(value.values())[:24]:
                outcome = inspect(child, depth + 1)
                if outcome:
                    return outcome
        elif isinstance(value, list):
            for child in value[:24]:
                outcome = inspect(child, depth + 1)
                if outcome:
                    return outcome
        return None

    return inspect(payload.get("tool_response")) or "unknown"


def new_record(session_key: str, now: float) -> dict[str, Any]:
    return {
        "session": session_key,
        "status": "idle",
        "event": "Unknown",
        "toolCategory": None,
        "subagents": [],
        "updatedEpoch": now,
        "expiresEpoch": None,
    }


def set_record_state(
    record: dict[str, Any], status: str, event: str, now: float, tool_category: str | None = None
) -> None:
    record["status"] = status
    record["event"] = event
    record["toolCategory"] = tool_category
    record["updatedEpoch"] = now
    duration = TRANSIENT_SECONDS.get(status)
    record["expiresEpoch"] = now + duration if duration else None


def apply_event(
    sessions: dict[str, dict[str, Any]], payload: dict[str, Any], now: float
) -> dict[str, Any]:
    event = string_field(payload.get("hook_event_name"), 80) or "Unknown"
    session_key = opaque_id(payload.get("session_id"), "default-session")
    timeline_status = "thinking"
    timeline_category: str | None = None
    outcome = "unknown"

    if event == "SessionEnd":
        sessions.pop(session_key, None)
        return {
            "id": f"{time.time_ns():x}-{os.getpid():x}",
            "at": utc_iso(now),
            "session": session_key,
            "event": event,
            "status": "idle",
            "category": None,
            "outcome": outcome,
        }

    record = sessions.setdefault(session_key, new_record(session_key, now))
    subagents = set(str(item) for item in record.get("subagents", []))

    if event == "SessionStart":
        set_record_state(record, "ready", event, now)
        timeline_status = "ready"
    elif event == "UserPromptSubmit":
        set_record_state(record, "thinking", event, now)
        timeline_status = "thinking"
    elif event == "PreToolUse":
        status, category = tool_state(payload)
        set_record_state(record, status, event, now, category)
        timeline_status = status
        timeline_category = category
    elif event == "PermissionRequest":
        set_record_state(record, "approval", event, now, "approval")
        timeline_status = "approval"
        timeline_category = "approval"
    elif event == "PostToolUse":
        tool_status, category = tool_state(payload)
        timeline_status = tool_status
        timeline_category = category
        outcome = tool_outcome(payload)
        status = "delegating" if subagents else "thinking"
        set_record_state(record, status, event, now)
    elif event == "SubagentStart":
        subagents.add(opaque_id(payload.get("agent_id"), f"agent-{len(subagents) + 1}"))
        record["subagents"] = sorted(subagents)
        set_record_state(record, "delegating", event, now, "agent")
        timeline_status = "delegating"
        timeline_category = "agent"
    elif event == "SubagentStop":
        subagents.discard(opaque_id(payload.get("agent_id"), "unknown-agent"))
        record["subagents"] = sorted(subagents)
        status = "delegating" if subagents else "thinking"
        set_record_state(record, status, event, now, "agent")
        timeline_status = status
        timeline_category = "agent"
    elif event == "Stop":
        set_record_state(record, "success", event, now)
        timeline_status = "success"
        outcome = "success"
    else:
        set_record_state(record, "thinking", event, now)
        timeline_status = "thinking"

    record["subagents"] = sorted(subagents)
    return {
        "id": f"{time.time_ns():x}-{os.getpid():x}",
        "at": utc_iso(now),
        "session": session_key,
        "event": event,
        "status": timeline_status,
        "category": timeline_category,
        "outcome": outcome,
    }


def aggregate_state(sessions: dict[str, dict[str, Any]], now: float) -> dict[str, Any]:
    active = []
    for record in sessions.values():
        updated = float(record.get("updatedEpoch") or 0)
        if updated >= now - SESSION_TTL_SECONDS:
            expires = record.get("expiresEpoch")
            if expires and float(expires) <= now:
                record["status"] = "idle"
                record["event"] = "TransientExpired"
                record["toolCategory"] = None
                record["expiresEpoch"] = None
            active.append(record)

    if not active:
        return {
            "schemaVersion": SCHEMA_VERSION,
            "revision": time.time_ns(),
            "updatedAt": utc_iso(now),
            "status": "idle",
            "message": STATE_MESSAGES["idle"],
            "event": "NoActiveSession",
            "toolCategory": None,
            "activeSubagents": 0,
            "session": None,
            "expiresAt": None,
            "source": "codex-hook",
        }

    selected = max(
        active,
        key=lambda item: (
            STATE_PRIORITY.get(str(item.get("status")), 0),
            float(item.get("updatedEpoch") or 0),
        ),
    )
    status = str(selected.get("status") or "idle")
    expires_epoch = selected.get("expiresEpoch")
    return {
        "schemaVersion": SCHEMA_VERSION,
        "revision": time.time_ns(),
        "updatedAt": utc_iso(now),
        "status": status,
        "message": STATE_MESSAGES.get(status, STATE_MESSAGES["thinking"]),
        "event": string_field(selected.get("event"), 80),
        "toolCategory": selected.get("toolCategory"),
        "activeSubagents": sum(len(item.get("subagents", [])) for item in active),
        "session": selected.get("session"),
        "expiresAt": utc_iso(float(expires_epoch)) if expires_epoch else None,
        "source": "codex-hook",
    }


def process_payload(payload: dict[str, Any], now: float | None = None) -> None:
    current_time = time.time() if now is None else now
    directory = state_directory()
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(directory, 0o700)
    lock_path = directory / "state.lock"
    with lock_path.open("a+", encoding="utf-8") as lock_handle:
        os.chmod(lock_path, 0o600)
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        sessions_path = directory / "sessions.json"
        sessions = read_json(sessions_path, {})
        if not isinstance(sessions, dict):
            sessions = {}
        sessions = {
            str(key): value
            for key, value in sessions.items()
            if isinstance(value, dict)
            and float(value.get("updatedEpoch") or 0) >= current_time - SESSION_TTL_SECONDS
        }
        recent_events = read_json(directory / "timeline.json", [])
        if not isinstance(recent_events, list):
            recent_events = []
        event = apply_event(sessions, payload, current_time)
        state = aggregate_state(sessions, current_time)
        event["activeSubagents"] = state["activeSubagents"]
        recent_events = [item for item in recent_events if isinstance(item, dict)]
        recent_events.append(event)
        recent_events = recent_events[-MAX_RECENT_EVENTS:]
        state["recentEvents"] = recent_events
        atomic_json_write(sessions_path, sessions)
        atomic_json_write(directory / "timeline.json", recent_events)
        atomic_json_write(directory / "state.json", state)


def main() -> int:
    if os.environ.get("MIRA_COMPANION_ENABLED", "1").strip().lower() in {
        "0",
        "false",
        "no",
        "off",
    }:
        return 0
    try:
        raw = sys.stdin.read(1024 * 1024)
        payload = json.loads(raw) if raw.strip() else {}
        if not isinstance(payload, dict):
            payload = {}
        process_payload(payload)
    except Exception as error:  # Hooks must never interrupt Codex.
        if os.environ.get("MIRA_COMPANION_DEBUG") == "1":
            print(f"mira-codex-hook: {error}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
