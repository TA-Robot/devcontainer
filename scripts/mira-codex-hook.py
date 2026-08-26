#!/usr/bin/python3
"""Translate trusted provider activity into sanitized Mira state and episodes.

The executable name remains ``mira-codex-hook`` for Codex configuration
compatibility.  Provider-specific symlink names select the Claude or Grok wire
adapter, and the bridge also accepts the deliberately tiny ``agentctl`` event
envelope emitted by the broker.  Completed turns are summarized into a
bounded, content-free observation ledger without entering the correctness
path.
"""

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
OBSERVATION_SCHEMA_VERSION = 1
SESSION_TTL_SECONDS = 60 * 60
MAX_RECENT_EVENTS = 24
DEFAULT_MAX_OBSERVATION_EPISODES = 512
MAX_CONFIGURED_OBSERVATION_EPISODES = 4096

AGENT_PROVIDERS = {"codex", "claude", "grok"}
AGENT_ROLES = {"implementer", "researcher", "reviewer", "tester"}
AGENT_ROLE_ALIASES = {
    "coder": "implementer",
    "general-purpose": "implementer",
    "implementation": "implementer",
    "implementer": "implementer",
    "explore": "researcher",
    "research": "researcher",
    "researcher": "researcher",
    "plan": "reviewer",
    "planner": "reviewer",
    "reviewer": "reviewer",
    "test": "tester",
    "tester": "tester",
    "testing": "tester",
}
PROVIDER_ENTRYPOINTS = {
    "mira-codex-hook": "codex",
    "mira-codex-hook.py": "codex",
    "mira-claude-hook": "claude",
    "mira-grok-hook": "grok",
}
DIRECT_HOOK_EVENTS = {
    "SessionStart",
    "SessionEnd",
    "UserPromptSubmit",
    "PreToolUse",
    "PostToolUse",
    "PostToolUseFailure",
    "PermissionRequest",
    "PermissionDenied",
    "Notification",
    "SubagentStart",
    "SubagentStop",
    "Stop",
    "StopFailure",
    "StopCancelled",
    "TurnIdle",
}
GROK_EVENT_NAMES = {
    "session_start": "SessionStart",
    "session_end": "SessionEnd",
    "user_prompt_submit": "UserPromptSubmit",
    "pre_tool_use": "PreToolUse",
    "post_tool_use": "PostToolUse",
    "post_tool_use_failure": "PostToolUseFailure",
    "permission_denied": "PermissionDenied",
    "notification": "Notification",
    "subagent_start": "SubagentStart",
    "subagent_stop": "SubagentStop",
    "stop": "Stop",
    "stop_failure": "StopFailure",
    "stop_cancelled": "StopCancelled",
}
AGENT_JOB_TERMINAL_EVENTS = {
    "AgentJobSucceeded": ("success", "success"),
    "AgentJobFailed": ("error", "failure"),
    "AgentJobOrphaned": ("error", "failure"),
    "AgentJobCancelled": ("ready", "unknown"),
}
AGENT_JOB_EVENTS = {"AgentJobStart", *AGENT_JOB_TERMINAL_EVENTS}

OBSERVATION_TERMINAL_EVENTS = {
    "AgentJobSucceeded",
    "AgentJobFailed",
    "AgentJobOrphaned",
    "AgentJobCancelled",
    "SessionEnd",
    "Stop",
    "StopFailure",
    "StopCancelled",
}
OBSERVATION_EXCLUDED_START_EVENTS = {
    "SessionStart",
    "TurnIdle",
    "Unknown",
} | OBSERVATION_TERMINAL_EVENTS
OBSERVATION_EXPLICIT_START_EVENTS = {"UserPromptSubmit", "AgentJobStart"}

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


def observation_directory() -> Path:
    configured = os.environ.get("MIRA_COMPANION_EPISODE_DIR")
    if configured:
        return Path(configured).expanduser()
    return state_directory()


def opaque_id(value: object, fallback: str) -> str:
    text = str(value or fallback)
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]


def workspace_key(value: object) -> str:
    """Return a stable-enough opaque workspace key without persisting its path."""

    raw = string_field(value, 4096).strip()
    if not raw:
        return "unknown"
    try:
        normalized = str(Path(raw).expanduser().resolve(strict=False))
    except (OSError, RuntimeError):
        normalized = raw
    return opaque_id(f"workspace:{normalized}", "workspace:unknown")


def observation_episode_limit() -> int:
    """Storage cost cap, not a collaboration-quality or sampling default."""

    raw = os.environ.get("MIRA_COMPANION_EPISODE_LIMIT", "")
    if raw:
        try:
            configured = int(raw)
        except ValueError:
            configured = DEFAULT_MAX_OBSERVATION_EPISODES
        return min(max(configured, 1), MAX_CONFIGURED_OBSERVATION_EPISODES)
    return DEFAULT_MAX_OBSERVATION_EPISODES


def observation_episodes_enabled() -> bool:
    configured = os.environ.get("MIRA_COMPANION_EPISODES_ENABLED", "1")
    return configured.strip().lower() not in {"0", "false", "no", "off"}


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
            # Mira state is reconstructable presentation data. Atomic replace
            # prevents partial JSON reads; storage-level durability would add
            # multiple fsync stalls to every provider tool event.
        os.replace(temporary_path, path)
    finally:
        try:
            temporary_path.unlink()
        except FileNotFoundError:
            pass


def string_field(value: object, limit: int = 80) -> str:
    return str(value or "")[:limit]


def enum_field(value: object, allowed: set[str], fallback: str = "unknown") -> str:
    normalized = string_field(value, 40).strip().lower()
    return normalized if normalized in allowed else fallback


def role_field(value: object) -> str:
    role = AGENT_ROLE_ALIASES.get(string_field(value, 40).strip().lower(), "unknown")
    return role if role in AGENT_ROLES else "unknown"


def invocation_provider() -> str:
    configured = enum_field(os.environ.get("MIRA_COMPANION_PROVIDER"), AGENT_PROVIDERS)
    if configured != "unknown":
        return configured
    return PROVIDER_ENTRYPOINTS.get(Path(sys.argv[0]).name, "codex")


def canonical_hook_event(value: object) -> str:
    event = string_field(value, 80)
    if event in DIRECT_HOOK_EVENTS:
        return event
    return GROK_EVENT_NAMES.get(event.lower(), "Unknown")


def normalize_hook_payload(payload: dict[str, Any], provider: str) -> dict[str, Any]:
    """Keep only bridge inputs and adapt Grok's camelCase hook wire format."""

    if payload.get("mira_source") == "agentctl":
        event = string_field(payload.get("hook_event_name"), 80)
        if event not in AGENT_JOB_EVENTS:
            event = "Unknown"
        return {
            "mira_source": "agentctl",
            "hook_event_name": event,
            "session_id": payload.get("session_id"),
            "attempt_id": payload.get("attempt_id"),
            "provider": payload.get("provider"),
            "role": payload.get("role"),
            "_mira_workspace": payload.get("_mira_workspace"),
        }

    if provider == "grok":
        event = canonical_hook_event(
            payload.get("hookEventName") or os.environ.get("GROK_HOOK_EVENT")
        )
        notification_type = string_field(payload.get("notificationType"), 80)
        if event == "Notification" and notification_type == "permission_prompt":
            event = "PermissionRequest"
        elif event == "Notification" and notification_type == "idle_prompt":
            event = "TurnIdle"
        subagent_type = payload.get("subagentType") or payload.get("agentType")
        subagent_id = (
            payload.get("subagentId")
            or payload.get("agentId")
            or subagent_type
            or payload.get("toolUseId")
            or payload.get("promptId")
        )
        return {
            "_mira_provider": provider,
            "hook_event_name": event,
            "session_id": payload.get("sessionId")
            or os.environ.get("GROK_SESSION_ID"),
            "tool_name": payload.get("toolName"),
            "tool_input": payload.get("toolInput"),
            "tool_response": payload.get("toolResult"),
            "agent_id": subagent_id,
            "agent_type": subagent_type,
            "_mira_workspace_path": payload.get("cwd") or os.environ.get("PWD"),
        }

    return {
        "_mira_provider": provider,
        "hook_event_name": canonical_hook_event(payload.get("hook_event_name")),
        "session_id": payload.get("session_id"),
        "tool_name": payload.get("tool_name"),
        "tool_input": payload.get("tool_input"),
        "tool_response": payload.get("tool_response"),
        "agent_id": payload.get("agent_id"),
        "agent_type": payload.get("agent_type"),
        "_mira_workspace_path": payload.get("cwd") or os.environ.get("PWD"),
    }


def agent_activity(role: str) -> tuple[str, str]:
    if role == "researcher":
        return "research", "read"
    if role == "implementer":
        return "typing", "edit"
    if role == "tester":
        return "testing", "test"
    return "thinking", "planning"


def tool_state(payload: dict[str, Any]) -> tuple[str, str]:
    tool_name = string_field(payload.get("tool_name"), 120)
    normalized = tool_name.lower()

    if normalized in {
        "agent",
        "spawn_agent",
        "spawn_subagent",
        "subagent",
        "task",
    }:
        return "delegating", "agent"
    if normalized in {
        "apply_patch",
        "edit",
        "search_replace",
        "write",
        "write_file",
        "replace",
    }:
        return "typing", "edit"
    if normalized in {
        "bash",
        "execute_command",
        "run_shell_command",
        "run_terminal_command",
        "shell",
    }:
        tool_input = payload.get("tool_input")
        command = ""
        if isinstance(tool_input, dict):
            command = tool_input.get("command") or tool_input.get("cmd") or ""
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


def new_record(
    session_key: str,
    now: float,
    source: str = "codex",
    opaque_workspace: str = "unknown",
) -> dict[str, Any]:
    return {
        "session": session_key,
        "source": source,
        "provider": source if source in AGENT_PROVIDERS else "unknown",
        "workspace": opaque_workspace,
        "status": "idle",
        "event": "Unknown",
        "toolCategory": None,
        "subagents": [],
        "agentMeta": {},
        "observationSequence": 0,
        "observation": None,
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


def payload_source(payload: dict[str, Any]) -> str:
    direct_provider = enum_field(payload.get("_mira_provider"), AGENT_PROVIDERS, "codex")
    return "agentctl" if payload.get("mira_source") == "agentctl" else direct_provider


def payload_session_key(payload: dict[str, Any]) -> str:
    source = payload_source(payload)
    raw_session = payload.get("session_id") or "default-session"
    return opaque_id(f"{source}:{raw_session}", f"{source}:default-session")


def increment_counter(container: dict[str, Any], field: str, key: str) -> None:
    counters = container.setdefault(field, {})
    if not isinstance(counters, dict):
        counters = {}
        container[field] = counters
    counters[key] = int(counters.get(key) or 0) + 1


def begin_observation(
    record: dict[str, Any], event_name: str, now: float, *, start_observed: bool
) -> dict[str, Any]:
    try:
        sequence = int(record.get("observationSequence") or 0) + 1
    except (TypeError, ValueError):
        sequence = 1
    record["observationSequence"] = sequence
    observation = {
        "id": opaque_id(
            f"{record.get('session', 'unknown')}:{sequence}:{now}:{time.time_ns()}",
            f"observation:{time.time_ns()}",
        ),
        "startedEpoch": now,
        "startEvent": event_name,
        "startObserved": start_observed,
        "eventCounts": {},
        "categoryCounts": {},
        "outcomeCounts": {},
        "testOutcomes": {"success": 0, "failure": 0, "unknown": 0},
        "lastTestOutcome": "unknown",
        "testRecoveries": 0,
        "editEventsAfterTestFailure": 0,
        "workerStarts": 0,
        "workerStops": 0,
        "peakConcurrentWorkers": 0,
        "workerActiveStartedEpoch": {},
        "workerActiveMs": 0,
        "workerStartCoverage": True,
        "workerProviderCounts": {},
        "workerRoleCounts": {},
        "firstWorkerStartedEpoch": None,
        "lastWorkerStoppedEpoch": None,
        "postWorkerEventCounts": {},
        "postWorkerCategoryCounts": {},
    }
    record["observation"] = observation
    return observation


def normalized_counter(value: object) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, int] = {}
    for raw_key, raw_count in value.items():
        key = string_field(raw_key, 80)
        if not key:
            continue
        try:
            count = int(raw_count)
        except (TypeError, ValueError):
            continue
        if count >= 0:
            result[key] = count
    return dict(sorted(result.items()))


def finalize_observation(
    record: dict[str, Any],
    finished_epoch: float,
    terminal_event: str,
    terminal_outcome: str,
    *,
    completion: str,
    terminal_observed: bool,
) -> dict[str, Any] | None:
    observation = record.get("observation")
    if not isinstance(observation, dict):
        return None

    try:
        started_epoch = float(observation.get("startedEpoch") or finished_epoch)
    except (TypeError, ValueError):
        started_epoch = finished_epoch
    finished_epoch = max(finished_epoch, started_epoch)

    active_starts = observation.get("workerActiveStartedEpoch")
    active_starts = active_starts if isinstance(active_starts, dict) else {}
    worker_active_ms = int(observation.get("workerActiveMs") or 0)
    for raw_started in active_starts.values():
        try:
            worker_active_ms += max(0, round((finished_epoch - float(raw_started)) * 1000))
        except (TypeError, ValueError):
            observation["workerStartCoverage"] = False

    active_workers = len(record.get("subagents", []))
    worker_starts = int(observation.get("workerStarts") or 0)
    peak_workers = int(observation.get("peakConcurrentWorkers") or 0)
    source = string_field(record.get("source"), 24) or "unknown"
    if source == "agentctl":
        topology = "managed-job"
    elif worker_starts > 0 or peak_workers > 0:
        topology = "delegated"
    else:
        topology = "solo-observed"

    last_worker_stopped = observation.get("lastWorkerStoppedEpoch")
    review_available = (
        source in AGENT_PROVIDERS
        and worker_starts > 0
        and active_workers == 0
        and isinstance(last_worker_stopped, (int, float))
    )
    review_elapsed_ms = (
        max(0, round((finished_epoch - float(last_worker_stopped)) * 1000))
        if review_available
        else None
    )

    test_outcomes = normalized_counter(observation.get("testOutcomes"))
    for outcome in ("success", "failure", "unknown"):
        test_outcomes.setdefault(outcome, 0)

    episode = {
        "schemaVersion": OBSERVATION_SCHEMA_VERSION,
        "id": string_field(observation.get("id"), 32),
        "session": string_field(record.get("session"), 32),
        "workspace": string_field(record.get("workspace"), 32) or "unknown",
        "source": source,
        "provider": enum_field(
            observation.get("provider") or record.get("provider"), AGENT_PROVIDERS
        ),
        "startedAt": utc_iso(started_epoch),
        "finishedAt": utc_iso(finished_epoch),
        "durationMs": max(0, round((finished_epoch - started_epoch) * 1000)),
        "startEvent": string_field(observation.get("startEvent"), 80),
        "terminalEvent": string_field(terminal_event, 80),
        "terminalOutcome": enum_field(
            terminal_outcome, {"success", "failure", "unknown"}
        ),
        "completion": enum_field(
            completion, {"observed-terminal", "superseded", "expired"}
        ),
        "topology": topology,
        "eventCounts": normalized_counter(observation.get("eventCounts")),
        "categoryCounts": normalized_counter(observation.get("categoryCounts")),
        "outcomeCounts": normalized_counter(observation.get("outcomeCounts")),
        "testOutcomes": test_outcomes,
        "delegation": {
            "starts": worker_starts,
            "stops": int(observation.get("workerStops") or 0),
            "peakConcurrent": peak_workers,
            "workerActiveMs": max(0, worker_active_ms),
            "unfinishedAtTerminal": active_workers,
            "providerCounts": normalized_counter(
                observation.get("workerProviderCounts")
            ),
            "roleCounts": normalized_counter(observation.get("workerRoleCounts")),
        },
        "reviewProxy": {
            "kind": "post-worker-tail",
            "available": review_available,
            "elapsedMs": review_elapsed_ms,
            "eventCounts": normalized_counter(
                observation.get("postWorkerEventCounts")
            ),
            "categoryCounts": normalized_counter(
                observation.get("postWorkerCategoryCounts")
            ),
        },
        "reworkProxy": {
            "testRecoveries": int(observation.get("testRecoveries") or 0),
            "editEventsAfterTestFailure": int(
                observation.get("editEventsAfterTestFailure") or 0
            ),
        },
        "semantics": {
            "expectedMechanisms": [],
            "bindingConstraint": "unknown",
            "relation": "unknown",
            "lifecycle": "unknown",
            "annotationSource": "none",
        },
        "coverage": {
            "startObserved": bool(observation.get("startObserved")),
            "terminalObserved": terminal_observed,
            "workerStartsObserved": bool(
                observation.get("workerStartCoverage", True)
            ),
        },
    }
    record["observation"] = None
    return episode


def observe_event(
    record: dict[str, Any] | None,
    event: dict[str, Any],
    now: float,
    active_before: set[str],
    active_after: set[str],
) -> list[dict[str, Any]]:
    if record is None:
        return []
    event_name = string_field(event.get("event"), 80) or "Unknown"
    completed: list[dict[str, Any]] = []

    existing = record.get("observation")
    if event_name in OBSERVATION_EXPLICIT_START_EVENTS and isinstance(existing, dict):
        previous = finalize_observation(
            record,
            now,
            "Superseded",
            "unknown",
            completion="superseded",
            terminal_observed=False,
        )
        if previous:
            completed.append(previous)

    observation = record.get("observation")
    if not isinstance(observation, dict) and event_name not in OBSERVATION_EXCLUDED_START_EVENTS:
        observation = begin_observation(
            record,
            event_name,
            now,
            start_observed=event_name in OBSERVATION_EXPLICIT_START_EVENTS,
        )

    if not isinstance(observation, dict):
        return completed

    observed_provider = enum_field(event.get("provider"), AGENT_PROVIDERS)
    if observed_provider != "unknown" and observation.get("provider") in {
        None,
        "",
        "unknown",
    }:
        observation["provider"] = observed_provider

    increment_counter(observation, "eventCounts", event_name)
    category = string_field(event.get("category"), 40)
    if category:
        increment_counter(observation, "categoryCounts", category)
    outcome = enum_field(event.get("outcome"), {"success", "failure", "unknown"})
    increment_counter(observation, "outcomeCounts", outcome)

    added_workers = active_after - active_before
    removed_workers = active_before - active_after
    active_started = observation.setdefault("workerActiveStartedEpoch", {})
    if not isinstance(active_started, dict):
        active_started = {}
        observation["workerActiveStartedEpoch"] = active_started
        observation["workerStartCoverage"] = False

    for worker_id in added_workers:
        active_started[worker_id] = now
    if added_workers:
        observation["workerStarts"] = int(observation.get("workerStarts") or 0) + len(
            added_workers
        )
        if observation.get("firstWorkerStartedEpoch") is None:
            observation["firstWorkerStartedEpoch"] = now
        observation["lastWorkerStoppedEpoch"] = None
        provider = enum_field(event.get("provider"), AGENT_PROVIDERS)
        role = role_field(event.get("role"))
        for _ in added_workers:
            increment_counter(observation, "workerProviderCounts", provider)
            increment_counter(observation, "workerRoleCounts", role)

    for worker_id in removed_workers:
        raw_started = active_started.pop(worker_id, None)
        if raw_started is None:
            observation["workerStartCoverage"] = False
            continue
        try:
            elapsed_ms = max(0, round((now - float(raw_started)) * 1000))
        except (TypeError, ValueError):
            observation["workerStartCoverage"] = False
            continue
        observation["workerActiveMs"] = (
            int(observation.get("workerActiveMs") or 0) + elapsed_ms
        )
    if removed_workers:
        observation["workerStops"] = int(observation.get("workerStops") or 0) + len(
            removed_workers
        )
        if not active_after:
            observation["lastWorkerStoppedEpoch"] = now

    for worker_id in active_after:
        if worker_id not in active_started:
            active_started[worker_id] = now
            observation["workerStartCoverage"] = False
    observation["peakConcurrentWorkers"] = max(
        int(observation.get("peakConcurrentWorkers") or 0), len(active_after)
    )

    if category == "test" and event_name in {"PostToolUse", "PostToolUseFailure"}:
        increment_counter(observation, "testOutcomes", outcome)
        previous_test = enum_field(
            observation.get("lastTestOutcome"), {"success", "failure", "unknown"}
        )
        if previous_test == "failure" and outcome == "success":
            observation["testRecoveries"] = (
                int(observation.get("testRecoveries") or 0) + 1
            )
        observation["lastTestOutcome"] = outcome
    elif (
        category == "edit"
        and event_name == "PreToolUse"
        and observation.get("lastTestOutcome") == "failure"
    ):
        observation["editEventsAfterTestFailure"] = int(
            observation.get("editEventsAfterTestFailure") or 0
        ) + 1

    last_worker_stopped = observation.get("lastWorkerStoppedEpoch")
    if (
        isinstance(last_worker_stopped, (int, float))
        and not active_after
        and event_name not in OBSERVATION_TERMINAL_EVENTS
        and event_name not in {"SubagentStop", "TurnIdle"}
    ):
        increment_counter(observation, "postWorkerEventCounts", event_name)
        if category:
            increment_counter(observation, "postWorkerCategoryCounts", category)

    if event_name in OBSERVATION_TERMINAL_EVENTS:
        terminal = finalize_observation(
            record,
            now,
            event_name,
            outcome,
            completion="observed-terminal",
            terminal_observed=True,
        )
        if terminal:
            completed.append(terminal)
    return completed


def append_observation_episodes(
    directory: Path, episodes: list[dict[str, Any]], now: float
) -> None:
    if not episodes:
        return
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(directory, 0o700)
    lock_path = directory / "collaboration-episodes.lock"
    with lock_path.open("a+", encoding="utf-8") as lock_handle:
        os.chmod(lock_path, 0o600)
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        path = directory / "collaboration-episodes.json"
        existing = read_json(path, {})
        retained = existing.get("episodes", []) if isinstance(existing, dict) else []
        retained = [item for item in retained if isinstance(item, dict)]
        known_ids = {string_field(item.get("id"), 32) for item in retained}
        for episode in episodes:
            episode_id = string_field(episode.get("id"), 32)
            if episode_id and episode_id not in known_ids:
                retained.append(episode)
                known_ids.add(episode_id)
        limit = observation_episode_limit()
        retained = retained[-limit:]
        atomic_json_write(
            path,
            {
                "schemaVersion": OBSERVATION_SCHEMA_VERSION,
                "updatedAt": utc_iso(now),
                "retention": {
                    "role": "storage-cost-cap",
                    "maxEpisodes": limit,
                },
                "episodes": retained,
            },
        )


def apply_event(
    sessions: dict[str, dict[str, Any]], payload: dict[str, Any], now: float
) -> dict[str, Any]:
    event = string_field(payload.get("hook_event_name"), 80) or "Unknown"
    direct_provider = enum_field(payload.get("_mira_provider"), AGENT_PROVIDERS, "codex")
    source = payload_source(payload)
    session_key = payload_session_key(payload)
    opaque_workspace = string_field(payload.get("_mira_workspace"), 32) or "unknown"
    timeline_status = "thinking"
    timeline_category: str | None = None
    outcome = "unknown"
    timeline_provider = direct_provider if source != "agentctl" else "unknown"
    timeline_role = "unknown"

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
            "provider": timeline_provider,
            "role": timeline_role,
        }

    record = sessions.setdefault(
        session_key, new_record(session_key, now, source, opaque_workspace)
    )
    record["source"] = source
    record["provider"] = direct_provider if source != "agentctl" else "unknown"
    if record.get("workspace") in {None, "", "unknown"}:
        record["workspace"] = opaque_workspace
    subagents = set(str(item) for item in record.get("subagents", []))
    raw_meta = record.get("agentMeta")
    agent_meta = raw_meta if isinstance(raw_meta, dict) else {}
    agent_meta = {
        str(agent_id): {
            "provider": enum_field(metadata.get("provider"), AGENT_PROVIDERS),
            "role": role_field(metadata.get("role")),
        }
        for agent_id, metadata in agent_meta.items()
        if str(agent_id) in subagents and isinstance(metadata, dict)
    }

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
    elif event in {"PostToolUse", "PostToolUseFailure"}:
        tool_status, category = tool_state(payload)
        outcome = (
            "failure" if event == "PostToolUseFailure" else tool_outcome(payload)
        )
        timeline_status = "error" if event == "PostToolUseFailure" else tool_status
        timeline_category = category
        status = (
            "error"
            if event == "PostToolUseFailure"
            else "delegating"
            if subagents
            else "thinking"
        )
        set_record_state(
            record, status, event, now, category if status == "error" else None
        )
    elif event == "PermissionDenied":
        set_record_state(record, "error", event, now, "approval")
        timeline_status = "error"
        timeline_category = "approval"
        outcome = "failure"
    elif event == "SubagentStart":
        agent_id = opaque_id(payload.get("agent_id"), f"agent-{len(subagents) + 1}")
        subagents.add(agent_id)
        timeline_provider = direct_provider
        timeline_role = role_field(payload.get("agent_type"))
        agent_meta[agent_id] = {
            "provider": timeline_provider,
            "role": timeline_role,
        }
        record["subagents"] = sorted(subagents)
        set_record_state(record, "delegating", event, now, "agent")
        timeline_status = "delegating"
        timeline_category = "agent"
    elif event == "SubagentStop":
        agent_id = opaque_id(payload.get("agent_id"), "unknown-agent")
        metadata = agent_meta.pop(agent_id, {})
        timeline_provider = enum_field(
            metadata.get("provider"), AGENT_PROVIDERS, direct_provider
        )
        timeline_role = role_field(metadata.get("role") or payload.get("agent_type"))
        subagents.discard(agent_id)
        record["subagents"] = sorted(subagents)
        status = "delegating" if subagents else "thinking"
        set_record_state(record, status, event, now, "agent")
        timeline_status = status
        timeline_category = "agent"
    elif event == "AgentJobStart" and source == "agentctl":
        agent_id = opaque_id(
            payload.get("attempt_id") or payload.get("agent_id"),
            f"agent-{len(subagents) + 1}",
        )
        timeline_provider = enum_field(payload.get("provider"), AGENT_PROVIDERS)
        timeline_role = role_field(payload.get("role"))
        subagents = {agent_id}
        agent_meta = {
            agent_id: {
                "provider": timeline_provider,
                "role": timeline_role,
            }
        }
        status, category = agent_activity(timeline_role)
        set_record_state(record, status, event, now, category)
        timeline_status = status
        timeline_category = "agent"
    elif event in AGENT_JOB_TERMINAL_EVENTS and source == "agentctl":
        timeline_provider = enum_field(payload.get("provider"), AGENT_PROVIDERS)
        timeline_role = role_field(payload.get("role"))
        status, outcome = AGENT_JOB_TERMINAL_EVENTS[event]
        subagents.clear()
        agent_meta.clear()
        set_record_state(record, status, event, now, "agent")
        timeline_status = status
        timeline_category = "agent"
    elif event == "Stop":
        set_record_state(record, "success", event, now)
        timeline_status = "success"
        outcome = "success"
    elif event == "StopFailure":
        set_record_state(record, "error", event, now)
        timeline_status = "error"
        outcome = "failure"
    elif event == "StopCancelled":
        set_record_state(record, "ready", event, now)
        timeline_status = "ready"
    elif event == "TurnIdle":
        current_status = string_field(record.get("status"), 20)
        current_expiry = float(record.get("expiresEpoch") or 0)
        if current_status in {"success", "error"} and current_expiry > now:
            timeline_status = current_status
            timeline_category = record.get("toolCategory")
            outcome = "success" if current_status == "success" else "failure"
        else:
            set_record_state(record, "ready", event, now)
            timeline_status = "ready"
    else:
        set_record_state(record, "thinking", event, now)
        timeline_status = "thinking"

    record["subagents"] = sorted(subagents)
    record["agentMeta"] = agent_meta
    return {
        "id": f"{time.time_ns():x}-{os.getpid():x}",
        "at": utc_iso(now),
        "session": session_key,
        "event": event,
        "status": timeline_status,
        "category": timeline_category,
        "outcome": outcome,
        "provider": timeline_provider,
        "role": timeline_role,
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
            "activeAgents": [],
            "providerCounts": {"codex": 0, "claude": 0, "grok": 0},
            "session": None,
            "expiresAt": None,
            "source": "codex-hook",
        }

    selection_pool = active
    if any(record.get("subagents") for record in active):
        selection_pool = [
            record
            for record in active
            if not (
                record.get("source") == "agentctl"
                and not record.get("subagents")
                and record.get("status") in {"ready", "success", "error"}
            )
        ]
    selected = max(
        selection_pool,
        key=lambda item: (
            STATE_PRIORITY.get(str(item.get("status")), 0),
            float(item.get("updatedEpoch") or 0),
        ),
    )
    status = str(selected.get("status") or "idle")
    expires_epoch = selected.get("expiresEpoch")
    active_agents = []
    ordered_records = [selected, *(item for item in active if item is not selected)]
    for record in ordered_records:
        metadata = record.get("agentMeta")
        metadata = metadata if isinstance(metadata, dict) else {}
        for agent_id in sorted(str(item) for item in record.get("subagents", [])):
            agent = metadata.get(agent_id, {})
            active_agents.append(
                {
                    "id": string_field(agent_id, 32),
                    "provider": enum_field(agent.get("provider"), AGENT_PROVIDERS),
                    "role": role_field(agent.get("role")),
                    "status": string_field(record.get("status"), 20),
                }
            )
    provider_counts = {"codex": 0, "claude": 0, "grok": 0}
    for record in active:
        provider = enum_field(record.get("provider"), AGENT_PROVIDERS)
        if provider in provider_counts and record.get("status") != "idle":
            provider_counts[provider] += 1
    for agent in active_agents:
        provider = agent["provider"]
        if provider in provider_counts:
            provider_counts[provider] += 1
    active_agents = active_agents[:8]
    sources = {str(item.get("source") or "codex") for item in active}
    if len(sources) > 1:
        state_source = "mira-activity-bridge"
    elif sources == {"agentctl"}:
        state_source = "agentctl"
    else:
        state_source = f"{next(iter(sources))}-hook"
    return {
        "schemaVersion": SCHEMA_VERSION,
        "revision": time.time_ns(),
        "updatedAt": utc_iso(now),
        "status": status,
        "message": STATE_MESSAGES.get(status, STATE_MESSAGES["thinking"]),
        "event": string_field(selected.get("event"), 80),
        "toolCategory": selected.get("toolCategory"),
        "activeSubagents": sum(len(item.get("subagents", [])) for item in active),
        "activeAgents": active_agents,
        "providerCounts": provider_counts,
        "session": selected.get("session"),
        "expiresAt": utc_iso(float(expires_epoch)) if expires_epoch else None,
        "source": state_source,
    }


def process_payload(payload: dict[str, Any], now: float | None = None) -> None:
    current_time = time.time() if now is None else now
    episodes_enabled = observation_episodes_enabled()
    raw_workspace = payload.pop("_mira_workspace_path", None)
    supplied_workspace = string_field(payload.get("_mira_workspace"), 32)
    if re.fullmatch(r"[0-9a-f]{16}", supplied_workspace):
        opaque_workspace = supplied_workspace
    else:
        opaque_workspace = workspace_key(raw_workspace)
    payload["_mira_workspace"] = opaque_workspace
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
        completed_observations: list[dict[str, Any]] = []
        active_sessions: dict[str, dict[str, Any]] = {}
        for key, value in sessions.items():
            if not isinstance(value, dict):
                continue
            try:
                updated_epoch = float(value.get("updatedEpoch") or 0)
            except (TypeError, ValueError):
                updated_epoch = 0
            if updated_epoch >= current_time - SESSION_TTL_SECONDS:
                active_sessions[str(key)] = value
                continue
            if episodes_enabled:
                expired = finalize_observation(
                    value,
                    updated_epoch or current_time,
                    "Expired",
                    "unknown",
                    completion="expired",
                    terminal_observed=False,
                )
                if expired:
                    completed_observations.append(expired)
        sessions = active_sessions
        recent_events = read_json(directory / "timeline.json", [])
        if not isinstance(recent_events, list):
            recent_events = []
        session_key = payload_session_key(payload)
        record_before = sessions.get(session_key)
        active_before = (
            {str(item) for item in record_before.get("subagents", [])}
            if isinstance(record_before, dict)
            else set()
        )
        event = apply_event(sessions, payload, current_time)
        if event.get("event") == "SessionEnd":
            observation_record = record_before
        else:
            observation_record = sessions.get(session_key)
        active_after = (
            {str(item) for item in observation_record.get("subagents", [])}
            if isinstance(observation_record, dict)
            else set()
        )
        if episodes_enabled:
            completed_observations.extend(
                observe_event(
                    observation_record,
                    event,
                    current_time,
                    active_before,
                    active_after,
                )
            )
        elif isinstance(observation_record, dict):
            observation_record["observation"] = None
        state = aggregate_state(sessions, current_time)
        event_provider = enum_field(event.get("provider"), AGENT_PROVIDERS)
        if state["event"] == "NoActiveSession" and event_provider != "unknown":
            state["source"] = f"{event_provider}-hook"
        event["activeSubagents"] = state["activeSubagents"]
        recent_events = [item for item in recent_events if isinstance(item, dict)]
        recent_events.append(event)
        recent_events = recent_events[-MAX_RECENT_EVENTS:]
        state["recentEvents"] = recent_events
        if episodes_enabled:
            try:
                append_observation_episodes(
                    observation_directory(),
                    completed_observations,
                    current_time,
                )
            except (OSError, TypeError, ValueError) as error:
                if os.environ.get("MIRA_COMPANION_DEBUG") == "1":
                    print(f"mira-codex-hook observation ledger: {error}", file=sys.stderr)
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
        process_payload(normalize_hook_payload(payload, invocation_provider()))
    except Exception as error:  # Presentation hooks must never interrupt a provider.
        if os.environ.get("MIRA_COMPANION_DEBUG") == "1":
            print(f"mira-codex-hook: {error}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
