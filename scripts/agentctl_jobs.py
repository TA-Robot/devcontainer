#!/usr/bin/env python3
"""Transactional project/job/worktree primitives for agentctl.

The provider conversation remains outside this module. It owns immutable job
identity, attempts, workspace leases, process state, and final result
verification only.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import shutil
import signal
import socket
import sqlite3
import stat
import subprocess
import time
from typing import Any, Iterator
import uuid

from agent_contracts import ContractValidationError, load_json, validate


DB_SCHEMA_VERSION = 2
CONTRACT_SCHEMA_VERSION = 1
JOB_ID_PATTERN = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$")
GIT_SHA_PATTERN = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
CROCKFORD32 = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

RESOURCE_CLASSES = ("light", "write", "integration", "isolated")
PRIORITY_LEVELS = {"background": 0, "normal": 1, "interactive": 2}
DEFAULT_CAPACITY = {
    "light": 4,
    "write": 2,
    "integration": 1,
    "isolated": 0,
}
RUNTIME_LEASE_KINDS = ("capacity", "port", "process")
SECRET_ENV_NAME = re.compile(
    r"(?i)(?:API[_-]?KEY|TOKEN|SECRET|PASSWORD|PASSWD|CREDENTIAL|PRIVATE[_-]?KEY)"
)
SECRET_TEXT_PATTERNS = (
    re.compile(r"\b(?:sk-ant|sk-proj|sk)-[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"\bxai-[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"\bgh(?:p|o|u|s|r)_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
)
DOCKER_INVENTORY_TIMEOUT_SECONDS = 5.0
MAX_PROVIDER_LOG_BYTES = 8 * 1024 * 1024
MAX_RUNNER_LOG_BYTES = 1024 * 1024
LOG_RETENTION_MARKER = b"[agentctl: earlier provider output discarded by retention policy]\n"
RUNNER_LOG_RETENTION_MARKER = (
    b"[agentctl: earlier runner output discarded by retention policy]\n"
)
MIRA_AGENT_JOB_EVENTS = {
    "AgentJobStart",
    "AgentJobSucceeded",
    "AgentJobFailed",
    "AgentJobCancelled",
    "AgentJobOrphaned",
}
COLLABORATION_RELATIONS = {
    "solo", "delegate", "consult", "compete", "verify", "project-specific"
}
COLLABORATION_LIFECYCLES = {
    "one-shot", "bounded-exchange", "event-triggered", "scheduled", "project-specific"
}
COLLABORATION_MECHANISMS = {
    "latency-overlap",
    "context-partitioning",
    "coverage",
    "error-decorrelation",
    "empirical-selection",
    "evidence-producing-refinement",
    "temporal-sampling",
    "project-specific",
}
COLLABORATION_CONSTRAINTS = {
    "serialization",
    "human-review",
    "wall-clock",
    "quota",
    "agentctl-capacity",
    "integration",
    "context-coupling",
    "evaluator",
    "late-failure",
    "other",
    "unknown",
}

ACTIVE_STATES = {"waiting_capacity", "preparing", "ready", "running"}
RETRYABLE_STATES = {"failed", "cancelled", "orphaned", "rejected"}
TERMINAL_STATES = {"succeeded", "validated", *RETRYABLE_STATES}

JOB_TRANSITIONS = {
    "created": {"waiting_capacity", "preparing", "rejected"},
    "waiting_capacity": {"preparing", "cancelled"},
    "preparing": {"ready", "failed", "rejected"},
    "ready": {"running", "failed", "cancelled"},
    "running": {"succeeded", "failed", "cancelled", "orphaned"},
    "succeeded": {"validated", "failed"},
    "failed": {"waiting_capacity", "preparing"},
    "cancelled": {"waiting_capacity", "preparing"},
    "orphaned": {"waiting_capacity", "preparing"},
    "rejected": {"waiting_capacity", "preparing"},
    "validated": set(),
}

ATTEMPT_TRANSITIONS = {
    "preparing": {"ready", "failed", "rejected"},
    "ready": {"running", "failed", "cancelled"},
    "running": {"succeeded", "failed", "cancelled", "orphaned"},
    "succeeded": {"validated", "failed"},
    "failed": set(),
    "cancelled": set(),
    "orphaned": set(),
    "rejected": set(),
    "validated": set(),
}


class AgentctlJobError(RuntimeError):
    """An expected job, state, contract, or workspace error."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _bounded_integer_environment(
    name: str,
    default: int,
    *,
    minimum: int,
    maximum: int,
) -> int:
    raw = os.environ.get(name, str(default))
    try:
        value = int(raw)
    except ValueError as exc:
        raise AgentctlJobError(f"invalid {name}: {raw!r}; expected an integer") from exc
    if not minimum <= value <= maximum:
        raise AgentctlJobError(
            f"{name} must be between {minimum} and {maximum}, got {value}"
        )
    return value


def capacity_limits() -> dict[str, int]:
    """Return the process-wide local resource-class budget."""

    return {
        resource_class: _bounded_integer_environment(
            f"AGENTCTL_CAPACITY_{resource_class.upper()}",
            default,
            minimum=0,
            maximum=256,
        )
        for resource_class, default in DEFAULT_CAPACITY.items()
    }


def queue_limit() -> int:
    return _bounded_integer_environment(
        "AGENTCTL_QUEUE_LIMIT", 128, minimum=1, maximum=10000
    )


def queue_aging_seconds() -> int:
    return _bounded_integer_environment(
        "AGENTCTL_QUEUE_AGING_SECONDS", 300, minimum=1, maximum=86400
    )


def port_range() -> tuple[int, int]:
    raw = os.environ.get("AGENTCTL_PORT_RANGE", "24000-24999")
    match = re.fullmatch(r"([0-9]{1,5})-([0-9]{1,5})", raw)
    if match is None:
        raise AgentctlJobError(
            f"invalid AGENTCTL_PORT_RANGE: {raw!r}; expected START-END"
        )
    start, end = (int(match.group(1)), int(match.group(2)))
    if start < 1024 or end > 65535 or start > end or end - start > 10000:
        raise AgentctlJobError(
            "AGENTCTL_PORT_RANGE must be an ordered 1024..65535 range "
            "containing at most 10001 ports"
        )
    return start, end


def new_ulid(timestamp_ms: int | None = None) -> str:
    """Return a canonical, sortable ULID without adding a dependency."""

    if timestamp_ms is None:
        timestamp_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    if not 0 <= timestamp_ms < 2**48:
        raise AgentctlJobError("ULID timestamp is outside the 48-bit range")
    value = (timestamp_ms << 80) | int.from_bytes(secrets.token_bytes(10), "big")
    encoded = ["0"] * 26
    for index in range(25, -1, -1):
        encoded[index] = CROCKFORD32[value & 31]
        value >>= 5
    return "".join(encoded)


def require_job_id(value: str) -> str:
    candidate = value.upper()
    if not JOB_ID_PATTERN.fullmatch(candidate):
        raise AgentctlJobError(f"invalid job id: {value!r}; expected a canonical 26-character ULID")
    return candidate


def run_command(
    argv: list[str],
    *,
    cwd: Path | None = None,
    check: bool = True,
    input_text: str | None = None,
    timeout: float | None = None,
) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            argv,
            cwd=cwd,
            input=input_text,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise AgentctlJobError(
            f"command timed out after {timeout:g}s: {argv[0]!r}"
        ) from exc
    except OSError as exc:
        raise AgentctlJobError(f"cannot execute {argv[0]!r}: {exc}") from exc
    if check and result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()[-2000:]
        raise AgentctlJobError(f"command failed ({result.returncode}): {' '.join(argv)}\n{detail}")
    return result


def git(workspace: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run_command(["git", "-C", str(workspace), *arguments], check=check)


def resolve_git_workspace(value: str | Path) -> Path:
    requested = Path(value).expanduser().resolve()
    result = git(requested, "rev-parse", "--show-toplevel", check=False)
    if result.returncode != 0:
        raise AgentctlJobError(f"workspace is not a Git worktree: {requested}")
    return Path(result.stdout.strip()).resolve()


def git_common_dir(workspace: Path) -> Path:
    value = git(workspace, "rev-parse", "--git-common-dir").stdout.strip()
    path = Path(value)
    if not path.is_absolute():
        path = workspace / path
    return path.resolve()


def resolve_full_commit(workspace: Path, revision: str) -> str:
    if not revision or revision.startswith("-") or len(revision) > 1024:
        raise AgentctlJobError(
            f"unsafe Git revision: {revision!r}; revisions must be non-empty, bounded, and not options"
        )
    result = git(workspace, "rev-parse", "--verify", f"{revision}^{{commit}}", check=False)
    if result.returncode != 0:
        raise AgentctlJobError(f"base revision is not a commit in this project: {revision!r}")
    full = result.stdout.strip().lower()
    if not GIT_SHA_PATTERN.fullmatch(full):
        raise AgentctlJobError(f"Git returned a non-full object id for {revision!r}: {full!r}")
    return full


def _mkdir_private(path: Path) -> None:
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        path.chmod(0o700)
    except OSError:
        pass


def write_json_private(path: Path, payload: Any) -> None:
    _mkdir_private(path.parent)
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(8)}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


@dataclass(frozen=True)
class StatePaths:
    root: Path

    @classmethod
    def from_value(cls, value: str | Path | None) -> "StatePaths":
        configured = value or os.environ.get("AGENTCTL_STATE_DIR") or "~/.local/state/agentctl"
        root = Path(configured).expanduser().resolve()
        if root == Path(root.anchor):
            raise AgentctlJobError("agentctl state root may not be a filesystem root")
        _mkdir_private(root)
        _mkdir_private(root / "projects")
        _mkdir_private(root / "locks")
        return cls(root=root)

    @property
    def database(self) -> Path:
        return self.root / "state.db"

    def project_dir(self, project_id: str) -> Path:
        return self.root / "projects" / project_id

    def job_dir(self, project_id: str, job_id: str) -> Path:
        return self.project_dir(project_id) / "jobs" / job_id

    def attempt_dir(self, project_id: str, job_id: str, attempt_number: int) -> Path:
        return self.job_dir(project_id, job_id) / "attempts" / str(attempt_number)

    def worktree_dir(self, project_id: str, job_id: str, attempt_number: int) -> Path:
        return self.project_dir(project_id) / "worktrees" / job_id / f"attempt-{attempt_number}"


class Store:
    def __init__(self, paths: StatePaths):
        self.paths = paths
        self.connection = sqlite3.connect(paths.database, timeout=30.0, isolation_level=None)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute("PRAGMA busy_timeout = 30000")
        self.connection.execute("PRAGMA journal_mode = WAL")
        self._migrate()
        try:
            paths.database.chmod(0o600)
        except OSError:
            pass

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "Store":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    @contextlib.contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            yield self.connection
        except BaseException:
            self.connection.rollback()
            raise
        else:
            self.connection.commit()

    def _migrate(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS schema_meta (
                singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                version INTEGER NOT NULL
            );
            """
        )
        with self.transaction() as connection:
            row = connection.execute(
                "SELECT version FROM schema_meta WHERE singleton = 1"
            ).fetchone()
            existing_version = int(row["version"]) if row is not None else None
            if existing_version is not None and not 1 <= existing_version <= DB_SCHEMA_VERSION:
                raise AgentctlJobError(
                    f"unsupported agentctl database schema {existing_version}; "
                    f"supported range is 1..{DB_SCHEMA_VERSION}"
                )
            if existing_version == 1:
                columns = {
                    column["name"]
                    for column in connection.execute("PRAGMA table_info(jobs)").fetchall()
                }
                if "priority" not in columns:
                    connection.execute(
                        "ALTER TABLE jobs ADD COLUMN priority TEXT NOT NULL DEFAULT 'normal'"
                    )
                if "queue_reason" not in columns:
                    connection.execute("ALTER TABLE jobs ADD COLUMN queue_reason TEXT")
                if "queued_at" not in columns:
                    connection.execute("ALTER TABLE jobs ADD COLUMN queued_at TEXT")
                connection.execute(
                    "UPDATE schema_meta SET version = ? WHERE singleton = 1",
                    (DB_SCHEMA_VERSION,),
                )
            elif existing_version is None:
                connection.execute(
                    "INSERT INTO schema_meta(singleton, version) VALUES (1, ?)",
                    (DB_SCHEMA_VERSION,),
                )

        self.connection.executescript(
            """
                CREATE TABLE IF NOT EXISTS projects (
                    project_id TEXT PRIMARY KEY,
                    git_common_dir TEXT NOT NULL UNIQUE,
                    registered_path TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL REFERENCES projects(project_id),
                    base_sha TEXT NOT NULL,
                    role TEXT NOT NULL,
                    lane TEXT NOT NULL,
                    permission_profile TEXT NOT NULL,
                    resource_class TEXT NOT NULL,
                    priority TEXT NOT NULL DEFAULT 'normal',
                    task_path TEXT NOT NULL,
                    state TEXT NOT NULL,
                    queue_reason TEXT,
                    queued_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS job_dependencies (
                    job_id TEXT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
                    depends_on_job_id TEXT NOT NULL REFERENCES jobs(job_id),
                    PRIMARY KEY(job_id, depends_on_job_id),
                    CHECK(job_id != depends_on_job_id)
                );

                CREATE TABLE IF NOT EXISTS attempts (
                    attempt_id TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
                    number INTEGER NOT NULL,
                    provider TEXT NOT NULL,
                    state TEXT NOT NULL,
                    pid INTEGER,
                    process_started_at TEXT,
                    runtime_id TEXT,
                    workspace_path TEXT,
                    branch_name TEXT,
                    started_at TEXT,
                    heartbeat_at TEXT,
                    finished_at TEXT,
                    exit_code INTEGER,
                    exit_reason TEXT,
                    result_path TEXT NOT NULL,
                    log_path TEXT NOT NULL,
                    head_sha TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(job_id, number)
                );

                CREATE TABLE IF NOT EXISTS leases (
                    lease_id TEXT PRIMARY KEY,
                    attempt_id TEXT NOT NULL REFERENCES attempts(attempt_id) ON DELETE CASCADE,
                    kind TEXT NOT NULL,
                    value TEXT NOT NULL,
                    acquired_at TEXT NOT NULL,
                    released_at TEXT
                );

                CREATE UNIQUE INDEX IF NOT EXISTS leases_active_kind_value
                    ON leases(kind, value) WHERE released_at IS NULL;

                CREATE INDEX IF NOT EXISTS jobs_waiting_capacity_order
                    ON jobs(state, queued_at, job_id);

                CREATE TABLE IF NOT EXISTS validations (
                    validation_id TEXT PRIMARY KEY,
                    attempt_id TEXT NOT NULL REFERENCES attempts(attempt_id) ON DELETE CASCADE,
                    profile TEXT NOT NULL,
                    status TEXT NOT NULL,
                    target_sha TEXT,
                    report_path TEXT NOT NULL,
                    finished_at TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS validations_attempt_profile
                    ON validations(attempt_id, profile, created_at);

                CREATE TABLE IF NOT EXISTS state_events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
                    attempt_id TEXT REFERENCES attempts(attempt_id) ON DELETE CASCADE,
                    entity TEXT NOT NULL,
                    from_state TEXT,
                    to_state TEXT NOT NULL,
                    reason TEXT,
                    created_at TEXT NOT NULL
                );
            """
        )


@contextlib.contextmanager
def workspace_lock(paths: StatePaths) -> Iterator[None]:
    lock_path = paths.root / "locks" / "workspace.lock"
    descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def _row(row: sqlite3.Row | None, *, message: str) -> dict[str, Any]:
    if row is None:
        raise AgentctlJobError(message)
    return dict(row)


def get_job(store: Store, job_id: str) -> dict[str, Any]:
    canonical = require_job_id(job_id)
    return _row(
        store.connection.execute("SELECT * FROM jobs WHERE job_id = ?", (canonical,)).fetchone(),
        message=f"unknown job: {canonical}",
    )


def get_project(store: Store, project_id: str) -> dict[str, Any]:
    return _row(
        store.connection.execute("SELECT * FROM projects WHERE project_id = ?", (project_id,)).fetchone(),
        message=f"unknown project: {project_id}",
    )


def get_attempt(store: Store, attempt_id: str) -> dict[str, Any]:
    return _row(
        store.connection.execute("SELECT * FROM attempts WHERE attempt_id = ?", (attempt_id,)).fetchone(),
        message=f"unknown attempt: {attempt_id}",
    )


def latest_attempt(store: Store, job_id: str) -> dict[str, Any] | None:
    row = store.connection.execute(
        "SELECT * FROM attempts WHERE job_id = ? ORDER BY number DESC LIMIT 1",
        (require_job_id(job_id),),
    ).fetchone()
    return dict(row) if row is not None else None


def _mira_collaboration_annotation(task_path: object) -> dict[str, Any] | None:
    """Return the bounded, content-free projection accepted by Mira telemetry."""

    try:
        task = load_json(Path(str(task_path)))
    except (ContractValidationError, OSError, TypeError, ValueError):
        return None
    raw = task.get("collaboration") if isinstance(task, dict) else None
    if not isinstance(raw, dict):
        return None
    plan_id = raw.get("plan_id")
    candidate_id = raw.get("candidate_id")
    digest = raw.get("decision_digest")
    relation = raw.get("relation")
    lifecycle = raw.get("lifecycle")
    mechanisms = raw.get("expected_mechanisms")
    constraint = raw.get("binding_constraint")
    if not (
        isinstance(plan_id, str)
        and isinstance(candidate_id, str)
        and isinstance(digest, str)
        and re.fullmatch(r"sha256:[0-9a-f]{64}", digest)
        and relation in COLLABORATION_RELATIONS
        and lifecycle in COLLABORATION_LIFECYCLES
        and isinstance(mechanisms, list)
        and 1 <= len(mechanisms) <= 8
        and len(set(mechanisms)) == len(mechanisms)
        and all(item in COLLABORATION_MECHANISMS for item in mechanisms)
        and constraint in COLLABORATION_CONSTRAINTS
        and raw.get("annotation_source") == "primary-plan"
    ):
        return None
    return {
        "plan": hashlib.sha256(
            f"collaboration-plan:{plan_id}".encode("utf-8", errors="replace")
        ).hexdigest()[:16],
        "candidate": hashlib.sha256(
            f"collaboration-candidate:{plan_id}:{candidate_id}".encode(
                "utf-8", errors="replace"
            )
        ).hexdigest()[:16],
        "decisionDigest": digest,
        "relation": relation,
        "lifecycle": lifecycle,
        "expectedMechanisms": list(mechanisms),
        "bindingConstraint": constraint,
        "annotationSource": "primary-plan",
    }


def _emit_mira_agent_job_event(
    store: Store,
    job_id: str,
    attempt_id: str,
    event: str,
) -> None:
    """Best-effort, sanitized activity/observation bridge from broker state.

    The bridge is outside the correctness path: missing binaries, lock
    contention, hook errors, and timeouts must never change the job result.
    Task text, paths, provider output, and reasons deliberately never enter
    this envelope.
    """

    if event not in MIRA_AGENT_JOB_EVENTS:
        return
    if os.environ.get("MIRA_COMPANION_ENABLED", "1").strip().lower() in {
        "0",
        "false",
        "no",
        "off",
    }:
        return
    configured = os.environ.get("AGENTCTL_MIRA_BRIDGE_BIN")
    bridge = configured or shutil.which("mira-codex-hook")
    if not bridge:
        return
    job = store.connection.execute(
        """
        SELECT jobs.role, jobs.task_path, projects.registered_path
        FROM jobs
        JOIN projects ON projects.project_id = jobs.project_id
        WHERE jobs.job_id = ?
        """,
        (job_id,),
    ).fetchone()
    attempt = store.connection.execute(
        "SELECT provider FROM attempts WHERE attempt_id = ? AND job_id = ?",
        (attempt_id, job_id),
    ).fetchone()
    if job is None or attempt is None:
        return
    try:
        registered_path = str(Path(job["registered_path"]).resolve(strict=False))
    except (OSError, RuntimeError):
        registered_path = str(job["registered_path"])
    opaque_workspace = hashlib.sha256(
        f"workspace:{registered_path}".encode("utf-8", errors="replace")
    ).hexdigest()[:16]
    payload = {
        "mira_source": "agentctl",
        "hook_event_name": event,
        "session_id": f"agentctl:{job_id}",
        "attempt_id": attempt_id,
        "provider": attempt["provider"],
        "role": job["role"],
        "_mira_workspace": opaque_workspace,
    }
    collaboration = _mira_collaboration_annotation(job["task_path"])
    if collaboration is not None:
        payload["collaboration"] = collaboration
    environment = {
        key: os.environ[key]
        for key in (
            "HOME",
            "LANG",
            "LC_ALL",
            "MIRA_COMPANION_DEBUG",
            "MIRA_COMPANION_ENABLED",
            "MIRA_COMPANION_EPISODE_DIR",
            "MIRA_COMPANION_EPISODE_LIMIT",
            "MIRA_COMPANION_EPISODES_ENABLED",
            "MIRA_COMPANION_STATE_DIR",
            "PATH",
            "XDG_STATE_HOME",
        )
        if key in os.environ
    }
    try:
        subprocess.run(
            [bridge],
            input=json.dumps(payload, separators=(",", ":")),
            text=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=environment,
            timeout=1.0,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return


def _transition(
    connection: sqlite3.Connection,
    *,
    table: str,
    id_column: str,
    identity: str,
    target: str,
    transitions: dict[str, set[str]],
    job_id: str,
    attempt_id: str | None,
    entity: str,
    reason: str | None = None,
    fields: dict[str, Any] | None = None,
) -> None:
    row = connection.execute(f"SELECT state FROM {table} WHERE {id_column} = ?", (identity,)).fetchone()
    if row is None:
        raise AgentctlJobError(f"cannot transition missing {entity}: {identity}")
    current = row["state"]
    if target not in transitions.get(current, set()):
        raise AgentctlJobError(f"invalid {entity} state transition: {current} -> {target}")
    values = dict(fields or {})
    values["state"] = target
    values["updated_at"] = utc_now()
    assignments = ", ".join(f"{key} = ?" for key in values)
    connection.execute(
        f"UPDATE {table} SET {assignments} WHERE {id_column} = ?",
        (*values.values(), identity),
    )
    connection.execute(
        """
        INSERT INTO state_events(job_id, attempt_id, entity, from_state, to_state, reason, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (job_id, attempt_id, entity, current, target, reason, utc_now()),
    )


def transition_job(
    connection: sqlite3.Connection,
    job_id: str,
    target: str,
    *,
    reason: str | None = None,
    fields: dict[str, Any] | None = None,
) -> None:
    _transition(
        connection,
        table="jobs",
        id_column="job_id",
        identity=job_id,
        target=target,
        transitions=JOB_TRANSITIONS,
        job_id=job_id,
        attempt_id=None,
        entity="job",
        reason=reason,
        fields=fields,
    )


def transition_attempt(
    connection: sqlite3.Connection,
    job_id: str,
    attempt_id: str,
    target: str,
    *,
    reason: str | None = None,
    fields: dict[str, Any] | None = None,
) -> None:
    _transition(
        connection,
        table="attempts",
        id_column="attempt_id",
        identity=attempt_id,
        target=target,
        transitions=ATTEMPT_TRANSITIONS,
        job_id=job_id,
        attempt_id=attempt_id,
        entity="attempt",
        reason=reason,
        fields=fields,
    )


def register_project(store: Store, workspace_value: str | Path) -> dict[str, Any]:
    workspace = resolve_git_workspace(workspace_value)
    common_dir = git_common_dir(workspace)
    configured = git(workspace, "config", "--local", "--get", "agentctl.projectId", check=False)
    if configured.returncode == 0 and configured.stdout.strip():
        project_id = configured.stdout.strip()
        try:
            uuid.UUID(project_id)
        except ValueError as exc:
            raise AgentctlJobError(
                f"invalid agentctl.projectId in local Git config: {project_id!r}"
            ) from exc
    else:
        project_id = str(uuid.uuid4())
        git(workspace, "config", "--local", "agentctl.projectId", project_id)

    now = utc_now()
    with store.transaction() as connection:
        by_id = connection.execute(
            "SELECT * FROM projects WHERE project_id = ?", (project_id,)
        ).fetchone()
        by_common = connection.execute(
            "SELECT * FROM projects WHERE git_common_dir = ?", (str(common_dir),)
        ).fetchone()
        if by_common is not None and by_common["project_id"] != project_id:
            raise AgentctlJobError(
                "Git common directory is already registered with a different project id; "
                "inspect local Git config before changing identity"
            )
        if by_id is None:
            connection.execute(
                """
                INSERT INTO projects(project_id, git_common_dir, registered_path, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (project_id, str(common_dir), str(workspace), now, now),
            )
        else:
            connection.execute(
                """
                UPDATE projects SET git_common_dir = ?, registered_path = ?, updated_at = ?
                WHERE project_id = ?
                """,
                (str(common_dir), str(workspace), now, project_id),
            )
    return get_project(store, project_id)


def show_project(store: Store, workspace_value: str | Path) -> dict[str, Any]:
    workspace = resolve_git_workspace(workspace_value)
    configured = git(workspace, "config", "--local", "--get", "agentctl.projectId", check=False)
    if configured.returncode != 0 or not configured.stdout.strip():
        raise AgentctlJobError("project is not registered; run `agentctl project register`")
    project = get_project(store, configured.stdout.strip())
    return {**project, "current_path": str(workspace), "git_common_dir_current": str(git_common_dir(workspace))}


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _project_contract_path(workspace: Path, relative: str) -> Path:
    path = (workspace / relative).resolve()
    if not _inside(path, workspace):
        raise AgentctlJobError(f"contract path escapes project: {relative}")
    if not path.is_file():
        raise AgentctlJobError(f"required project contract file is missing: {relative}")
    return path


def _load_project_config(workspace: Path) -> dict[str, Any]:
    path = _project_contract_path(workspace, ".agent/config.json")
    config = load_json(path)
    if not isinstance(config, dict) or config.get("schema_version") != CONTRACT_SCHEMA_VERSION:
        raise AgentctlJobError(f"unsupported project contract config: {path}")
    return config


def _copy_and_validate_task(
    workspace: Path,
    task_source: Path,
    *,
    requested_job_id: str | None,
    base_revision: str | None,
) -> dict[str, Any]:
    source = task_source.expanduser().resolve()
    if not _inside(source, workspace):
        raise AgentctlJobError("task JSON must be inside the registered project")
    task = load_json(source)
    if not isinstance(task, dict):
        raise AgentctlJobError("task envelope root must be a JSON object")

    source_job_id = task.get("job_id")
    if requested_job_id and source_job_id and requested_job_id.upper() != str(source_job_id).upper():
        raise AgentctlJobError("--job-id conflicts with task envelope job_id")
    job_id = require_job_id(requested_job_id or source_job_id or new_ulid())
    task["job_id"] = job_id

    source_base = task.get("base_sha")
    if base_revision and source_base and GIT_SHA_PATTERN.fullmatch(str(source_base)):
        requested_full = resolve_full_commit(workspace, base_revision)
        if requested_full != str(source_base).lower():
            raise AgentctlJobError("--base conflicts with immutable task envelope base_sha")
    revision = base_revision or source_base
    if not revision:
        raise AgentctlJobError("task envelope base_sha or explicit --base is required")
    full_base = resolve_full_commit(workspace, str(revision))
    task["base_sha"] = full_base
    task.setdefault("priority", "normal")

    config = _load_project_config(workspace)
    schema_relative = config.get("contracts", {}).get("task")
    if not isinstance(schema_relative, str):
        raise AgentctlJobError("project config does not declare the task schema")
    schema_path = _project_contract_path(workspace, schema_relative)
    schema = load_json(schema_path)
    try:
        validate(task, schema)
    except ContractValidationError as exc:
        raise AgentctlJobError(f"task envelope does not satisfy {schema_relative}: {exc}") from exc

    role = task["role"]
    role_config = config.get("roles", {}).get(role)
    if not isinstance(role_config, dict):
        raise AgentctlJobError(f"task role is not declared in .agent/config.json: {role}")
    if role_config.get("default_lane") != task["lane"]:
        raise AgentctlJobError(
            f"task lane {task['lane']!r} conflicts with role {role!r} default lane "
            f"{role_config.get('default_lane')!r}"
        )
    return task


def create_job(
    store: Store,
    workspace_value: str | Path,
    task_source: str | Path,
    *,
    requested_job_id: str | None = None,
    base_revision: str | None = None,
) -> dict[str, Any]:
    workspace = resolve_git_workspace(workspace_value)
    project = register_project(store, workspace)
    task = _copy_and_validate_task(
        workspace,
        Path(task_source),
        requested_job_id=requested_job_id,
        base_revision=base_revision,
    )
    job_id = task["job_id"]
    stored_task_path = store.paths.job_dir(project["project_id"], job_id) / "task.json"
    if stored_task_path.exists():
        raise AgentctlJobError(f"job task already exists: {job_id}")

    dependency_ids = task.get("dependency_job_ids", [])
    now = utc_now()
    with workspace_lock(store.paths):
        existing = store.connection.execute("SELECT 1 FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
        if existing is not None:
            raise AgentctlJobError(f"job already exists: {job_id}")
        for dependency_id in dependency_ids:
            dependency = store.connection.execute(
                "SELECT project_id FROM jobs WHERE job_id = ?", (dependency_id,)
            ).fetchone()
            if dependency is None:
                raise AgentctlJobError(f"unknown dependency job: {dependency_id}")
            if dependency["project_id"] != project["project_id"]:
                raise AgentctlJobError(f"dependency belongs to another project: {dependency_id}")

        write_json_private(stored_task_path, task)
        try:
            with store.transaction() as connection:
                connection.execute(
                    """
                    INSERT INTO jobs(
                        job_id, project_id, base_sha, role, lane, permission_profile,
                        resource_class, priority, task_path, state, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'created', ?, ?)
                    """,
                    (
                        job_id,
                        project["project_id"],
                        task["base_sha"],
                        task["role"],
                        task["lane"],
                        task["permission_profile"],
                        task["resource_class"],
                        task["priority"],
                        str(stored_task_path),
                        now,
                        now,
                    ),
                )
                connection.execute(
                    """
                    INSERT INTO state_events(job_id, attempt_id, entity, from_state, to_state, reason, created_at)
                    VALUES (?, NULL, 'job', NULL, 'created', 'job created', ?)
                    """,
                    (job_id, now),
                )
                for dependency_id in dependency_ids:
                    connection.execute(
                        "INSERT INTO job_dependencies(job_id, depends_on_job_id) VALUES (?, ?)",
                        (job_id, dependency_id),
                    )
        except BaseException:
            stored_task_path.unlink(missing_ok=True)
            raise
    return show_job(store, job_id)


def list_jobs(
    store: Store,
    workspace_value: str | Path | None = None,
    *,
    state: str | None = None,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    values: list[Any] = []
    if workspace_value is not None:
        project = show_project(store, workspace_value)
        clauses.append("project_id = ?")
        values.append(project["project_id"])
    if state:
        clauses.append("state = ?")
        values.append(state)
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    rows = store.connection.execute(
        f"SELECT * FROM jobs{where} ORDER BY created_at, job_id", values
    ).fetchall()
    return [dict(row) for row in rows]


def _timestamp_age(value: str | None) -> float:
    if not value:
        return float("inf")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return float("inf")
    return max(0.0, (datetime.now(timezone.utc) - parsed).total_seconds())


def waiting_jobs(store: Store) -> list[dict[str, Any]]:
    """Return the durable queue in priority-with-aging, then FIFO order."""

    aging_seconds = queue_aging_seconds()
    rows = [
        dict(row)
        for row in store.connection.execute(
            "SELECT * FROM jobs WHERE state = 'waiting_capacity'"
        ).fetchall()
    ]
    for job in rows:
        wait_seconds = _timestamp_age(job["queued_at"] or job["created_at"])
        if wait_seconds == float("inf"):
            # Corrupt/missing queue timestamps must not crash scheduling or
            # starve the job indefinitely. Treat them as fully aged and keep
            # deterministic FIFO ordering on the stored timestamp/job id.
            wait_seconds = float(aging_seconds * 2)
        base_level = PRIORITY_LEVELS.get(job["priority"], PRIORITY_LEVELS["normal"])
        effective_level = min(
            PRIORITY_LEVELS["interactive"],
            base_level + int(wait_seconds // aging_seconds),
        )
        job["wait_seconds"] = wait_seconds
        job["effective_priority"] = next(
            name for name, level in PRIORITY_LEVELS.items() if level == effective_level
        )
        job["_effective_priority_level"] = effective_level
    rows.sort(
        key=lambda job: (
            -int(job["_effective_priority_level"]),
            str(job["queued_at"] or job["created_at"]),
            str(job["job_id"]),
        )
    )
    for position, job in enumerate(rows, start=1):
        job.pop("_effective_priority_level", None)
        job["queue_position"] = position
    return rows


def capacity_snapshot(store: Store) -> dict[str, Any]:
    limits = capacity_limits()
    active_values = [
        row["value"]
        for row in store.connection.execute(
            "SELECT value FROM leases WHERE kind = 'capacity' AND released_at IS NULL"
        ).fetchall()
    ]
    used = {resource_class: 0 for resource_class in RESOURCE_CLASSES}
    for value in active_values:
        resource_class, separator, _slot = str(value).partition(":")
        if separator and resource_class in used:
            used[resource_class] += 1
    waiting = {resource_class: 0 for resource_class in RESOURCE_CLASSES}
    for row in store.connection.execute(
        "SELECT resource_class, COUNT(*) AS count FROM jobs "
        "WHERE state = 'waiting_capacity' GROUP BY resource_class"
    ).fetchall():
        if row["resource_class"] in waiting:
            waiting[row["resource_class"]] = int(row["count"])
    return {
        "limits": limits,
        "used": used,
        "available": {
            resource_class: max(0, limits[resource_class] - used[resource_class])
            for resource_class in RESOURCE_CLASSES
        },
        "waiting": waiting,
    }


def _available_capacity_slot(
    connection: sqlite3.Connection,
    resource_class: str,
) -> str | None:
    limits = capacity_limits()
    if resource_class not in limits:
        raise AgentctlJobError(f"unsupported resource class: {resource_class!r}")
    active = {
        str(row["value"])
        for row in connection.execute(
            "SELECT value FROM leases WHERE kind = 'capacity' AND released_at IS NULL"
        ).fetchall()
    }
    for slot in range(1, limits[resource_class] + 1):
        value = f"{resource_class}:{slot}"
        if value not in active:
            return value
    return None


def _available_port(connection: sqlite3.Connection, job_id: str) -> str:
    start, end = port_range()
    active = {
        int(row["value"])
        for row in connection.execute(
            "SELECT value FROM leases WHERE kind = 'port' AND released_at IS NULL"
        ).fetchall()
        if str(row["value"]).isdigit()
    }
    width = end - start + 1
    offset = sum(job_id.encode("ascii")) % width
    for step in range(width):
        candidate = start + ((offset + step) % width)
        if candidate in active:
            continue
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
                probe.bind(("127.0.0.1", candidate))
        except OSError:
            continue
        return str(candidate)
    raise AgentctlJobError(
        f"no free integration port is available in AGENTCTL_PORT_RANGE={start}-{end}"
    )


def _release_runtime_leases(
    connection: sqlite3.Connection,
    attempt_id: str,
    released_at: str,
) -> None:
    placeholders = ", ".join("?" for _ in RUNTIME_LEASE_KINDS)
    connection.execute(
        f"UPDATE leases SET released_at = ? WHERE attempt_id = ? "
        f"AND kind IN ({placeholders}) AND released_at IS NULL",
        (released_at, attempt_id, *RUNTIME_LEASE_KINDS),
    )


def _redact_log_text(text: str) -> tuple[str, int]:
    redactions = 0
    for pattern in SECRET_TEXT_PATTERNS:
        text, count = pattern.subn("[REDACTED]", text)
        redactions += count

    authorization = re.compile(
        r"(?i)\b(Authorization\s*[:=]\s*)(?:Bearer|Basic)\s+[^\s,;]+"
    )
    text, count = authorization.subn(r"\1[REDACTED]", text)
    redactions += count

    assignments = re.compile(
        r"(?i)\b((?:[A-Z0-9_]*(?:API[_-]?KEY|TOKEN|SECRET|PASSWORD|PASSWD|CREDENTIAL)"
        r"[A-Z0-9_]*|AUTHORIZATION)\s*[:=]\s*)(?:Bearer\s+)?([^\s,;]+)"
    )
    text, count = assignments.subn(r"\1[REDACTED]", text)
    redactions += count

    for name, value in sorted(os.environ.items(), key=lambda item: len(item[1]), reverse=True):
        if len(value) < 8 or SECRET_ENV_NAME.search(name) is None:
            continue
        count = text.count(value)
        if count:
            text = text.replace(value, "[REDACTED]")
            redactions += count
    return text, redactions


def enforce_log_tail_retention(
    path: Path,
    *,
    max_bytes: int,
    marker: bytes,
    policy: str,
    report_path: Path,
    in_place: bool = False,
    report_unchanged: bool = True,
) -> dict[str, Any] | None:
    """Retain a bounded line-aligned tail of an owner-only regular log."""

    if max_bytes <= len(marker):
        raise AgentctlJobError("log retention limit must exceed its marker size")

    try:
        metadata = path.lstat()
    except OSError as exc:
        raise AgentctlJobError(f"log is unavailable for retention: {exc}") from exc
    if not stat.S_ISREG(metadata.st_mode):
        raise AgentctlJobError("log retention requires a regular non-symlink file")
    if metadata.st_uid != os.getuid():
        raise AgentctlJobError("log retention requires a file owned by the current user")
    original_bytes = metadata.st_size

    truncated = original_bytes > max_bytes
    dropped_partial_line = False
    if truncated:
        tail_budget = max_bytes - len(marker)
        offset = max(0, original_bytes - tail_budget)
        descriptor = -1
        try:
            descriptor = os.open(
                path,
                (os.O_RDWR if in_place else os.O_RDONLY)
                | getattr(os, "O_NOFOLLOW", 0),
            )
            opened = os.fstat(descriptor)
            if (
                not stat.S_ISREG(opened.st_mode)
                or opened.st_uid != os.getuid()
                or opened.st_dev != metadata.st_dev
                or opened.st_ino != metadata.st_ino
            ):
                raise AgentctlJobError("log changed identity during retention")
            source_handle = os.fdopen(descriptor, "r+b" if in_place else "rb")
            descriptor = -1
            with source_handle as source:
                source.seek(offset)
                tail = source.read(tail_budget)
                if offset:
                    newline = tail.find(b"\n")
                    dropped_partial_line = True
                    tail = tail[newline + 1 :] if newline >= 0 else b""
                retained = marker + tail
                if in_place:
                    source.seek(0)
                    source.truncate(0)
                    source.write(retained)
                    source.flush()
                    os.fsync(source.fileno())
        except OSError as exc:
            raise AgentctlJobError(f"log cannot be read for retention: {exc}") from exc
        finally:
            if descriptor >= 0:
                os.close(descriptor)
        if not in_place:
            temporary = path.with_name(f".{path.name}.{secrets.token_hex(8)}.retention")
            descriptor = -1
            try:
                descriptor = os.open(
                    temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600
                )
                output_handle = os.fdopen(descriptor, "wb")
                descriptor = -1
                with output_handle as output:
                    output.write(retained)
                    output.flush()
                    os.fsync(output.fileno())
                os.replace(temporary, path)
            except BaseException:
                temporary.unlink(missing_ok=True)
                raise
            finally:
                if descriptor >= 0:
                    os.close(descriptor)
                temporary.unlink(missing_ok=True)

    if not truncated and not report_unchanged:
        return None

    report = {
        "schema_version": 1,
        "policy": policy,
        "max_bytes": max_bytes,
        "original_bytes": original_bytes,
        "retained_bytes": path.lstat().st_size,
        "truncated": truncated,
        "dropped_partial_line": dropped_partial_line,
        "raw_log_redacted": False,
        "applied_at": utc_now(),
    }
    write_json_private(report_path, report)
    return report


def enforce_terminal_log_retention(path: Path) -> dict[str, Any]:
    """Atomically retain at most the final MAX_PROVIDER_LOG_BYTES of a closed log."""

    report = enforce_log_tail_retention(
        path,
        max_bytes=MAX_PROVIDER_LOG_BYTES,
        marker=LOG_RETENTION_MARKER,
        policy="terminal_tail",
        report_path=path.with_name("log-retention.json"),
    )
    assert report is not None
    return report


def enforce_attempt_runner_log_retention(
    store: Store,
    attempt: dict[str, Any],
    *,
    max_bytes: int = MAX_RUNNER_LOG_BYTES,
) -> dict[str, Any] | None:
    """Bound a closed detached-runner log at its canonical attempt path."""

    job = get_job(store, str(attempt["job_id"]))
    attempt_dir = store.paths.attempt_dir(
        job["project_id"], job["job_id"], int(attempt["number"])
    ).resolve()
    recorded_log = Path(attempt["log_path"])
    if recorded_log.name != "process.log" or recorded_log.parent.resolve() != attempt_dir:
        raise AgentctlJobError(
            "recorded log path does not match its canonical attempt evidence path"
        )
    runner_log = attempt_dir / "runner.log"
    if runner_log.is_symlink():
        raise AgentctlJobError("runner log retention refuses a symbolic link")
    if not runner_log.is_file():
        return None
    retention_path = attempt_dir / "runner-log-retention.json"
    if retention_path.is_file():
        if retention_path.is_symlink():
            raise AgentctlJobError("runner log retention evidence is a symbolic link")
        try:
            existing = load_json(retention_path)
        except (OSError, json.JSONDecodeError, ContractValidationError) as exc:
            raise AgentctlJobError(
                f"runner log retention evidence is unreadable: {exc}"
            ) from exc
        if not isinstance(existing, dict):
            raise AgentctlJobError("runner log retention evidence root is not an object")
        return existing
    return enforce_log_tail_retention(
        runner_log,
        max_bytes=max_bytes,
        marker=RUNNER_LOG_RETENTION_MARKER,
        policy="runner_terminal_tail",
        report_path=retention_path,
    )


def enforce_attempt_log_retention(
    store: Store, attempt: dict[str, Any]
) -> dict[str, Any] | None:
    """Retain a closed attempt log without trusting its recorded path."""

    job = get_job(store, str(attempt["job_id"]))
    attempt_dir = store.paths.attempt_dir(
        job["project_id"], job["job_id"], int(attempt["number"])
    ).resolve()
    expected_log = attempt_dir / "process.log"
    recorded_log = Path(attempt["log_path"])
    if recorded_log.name != "process.log" or recorded_log.parent.resolve() != attempt_dir:
        raise AgentctlJobError(
            "recorded log path does not match its canonical attempt evidence path"
        )
    if expected_log.is_symlink():
        raise AgentctlJobError("provider log retention refuses a symbolic link")
    if not expected_log.is_file():
        return None
    retention_path = attempt_dir / "log-retention.json"
    if retention_path.is_file():
        try:
            existing = load_json(retention_path)
        except (OSError, json.JSONDecodeError, ContractValidationError) as exc:
            raise AgentctlJobError(f"log retention evidence is unreadable: {exc}") from exc
        if not isinstance(existing, dict):
            raise AgentctlJobError("log retention evidence root is not an object")
        return existing
    return enforce_terminal_log_retention(expected_log)


def read_job_log(
    store: Store,
    job_id: str,
    *,
    attempt_number: int | None = None,
    source: str = "process",
    max_lines: int = 80,
    max_bytes: int = 65536,
) -> dict[str, Any]:
    canonical = require_job_id(job_id)
    if source not in {"process", "runner"}:
        raise AgentctlJobError(f"unsupported log source: {source!r}")
    if not 1 <= max_lines <= 1000:
        raise AgentctlJobError("log line limit must be between 1 and 1000")
    if not 1024 <= max_bytes <= 1024 * 1024:
        raise AgentctlJobError("log byte limit must be between 1024 and 1048576")

    job = get_job(store, canonical)
    if attempt_number is None:
        attempt = latest_attempt(store, canonical)
    else:
        if attempt_number < 1:
            raise AgentctlJobError("attempt number must be positive")
        row = store.connection.execute(
            "SELECT * FROM attempts WHERE job_id = ? AND number = ?",
            (canonical, attempt_number),
        ).fetchone()
        attempt = dict(row) if row is not None else None
    if attempt is None:
        raise AgentctlJobError(f"job has no matching attempt log: {canonical}")

    attempt_dir = store.paths.attempt_dir(
        job["project_id"], canonical, int(attempt["number"])
    ).resolve()
    state_root = store.paths.root.resolve()
    if not _inside(attempt_dir, state_root):
        raise AgentctlJobError("canonical attempt directory escapes the private state root")
    recorded_result = Path(attempt["result_path"])
    recorded_log = Path(attempt["log_path"])
    if (
        recorded_result.name != "result.json"
        or recorded_result.parent.resolve() != attempt_dir
    ):
        raise AgentctlJobError(
            "recorded result path does not match its canonical attempt evidence path"
        )
    if recorded_log.name != "process.log" or recorded_log.parent.resolve() != attempt_dir:
        raise AgentctlJobError(
            "recorded log path does not match its canonical attempt evidence path"
        )
    path = recorded_log if source == "process" else attempt_dir / "runner.log"
    if path.is_symlink():
        raise AgentctlJobError("recorded log path is a symbolic link")
    path = path.resolve()
    if not _inside(path, attempt_dir):
        raise AgentctlJobError("recorded log path escapes its attempt evidence directory")
    if not path.is_file():
        raise AgentctlJobError(f"{source} log is not available for attempt {attempt['number']}")

    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    except OSError as exc:
        raise AgentctlJobError(f"{source} log cannot be opened safely: {exc}") from exc
    metadata = os.fstat(descriptor)
    if not stat.S_ISREG(metadata.st_mode):
        os.close(descriptor)
        raise AgentctlJobError(f"{source} log is not a regular file")
    size = metadata.st_size
    offset = max(0, size - max_bytes)
    with os.fdopen(descriptor, "rb") as handle:
        handle.seek(offset)
        raw = handle.read(max_bytes)
    dropped_partial_line = False
    if offset:
        newline = raw.find(b"\n")
        dropped_partial_line = True
        raw = raw[newline + 1 :] if newline >= 0 else b""
    decoded = raw.decode("utf-8", errors="replace")
    lines = decoded.splitlines()
    line_truncated = len(lines) > max_lines
    selected = lines[-max_lines:]
    content = "\n".join(selected)
    if selected and decoded.endswith("\n"):
        content += "\n"
    redacted, redaction_count = _redact_log_text(content)
    retention_path = attempt_dir / (
        "log-retention.json" if source == "process" else "runner-log-retention.json"
    )
    retention = None
    if retention_path.is_file():
        if retention_path.is_symlink():
            raise AgentctlJobError("log retention evidence is a symbolic link")
        try:
            loaded_retention = load_json(retention_path)
        except (OSError, json.JSONDecodeError, ContractValidationError) as exc:
            raise AgentctlJobError(f"log retention evidence is unreadable: {exc}") from exc
        if not isinstance(loaded_retention, dict):
            raise AgentctlJobError("log retention evidence root is not an object")
        retention = loaded_retention
    return {
        "job_id": canonical,
        "attempt_id": attempt["attempt_id"],
        "attempt_number": attempt["number"],
        "source": source,
        "path": str(path),
        "file_bytes": size,
        "max_bytes": max_bytes,
        "max_lines": max_lines,
        "byte_truncated": offset > 0,
        "line_truncated": line_truncated,
        "dropped_partial_line": dropped_partial_line,
        "redaction_count": redaction_count,
        "retention": retention,
        "content": redacted,
    }


def show_job(store: Store, job_id: str) -> dict[str, Any]:
    job = get_job(store, job_id)
    attempts = [
        dict(row)
        for row in store.connection.execute(
            "SELECT * FROM attempts WHERE job_id = ? ORDER BY number", (job["job_id"],)
        ).fetchall()
    ]
    leases = [
        dict(row)
        for row in store.connection.execute(
            """
            SELECT leases.* FROM leases
            JOIN attempts ON attempts.attempt_id = leases.attempt_id
            WHERE attempts.job_id = ? ORDER BY leases.acquired_at
            """,
            (job["job_id"],),
        ).fetchall()
    ]
    dependencies = [
        row["depends_on_job_id"]
        for row in store.connection.execute(
            "SELECT depends_on_job_id FROM job_dependencies WHERE job_id = ? ORDER BY depends_on_job_id",
            (job["job_id"],),
        ).fetchall()
    ]
    validations = [
        dict(row)
        for row in store.connection.execute(
            """
            SELECT validations.* FROM validations
            JOIN attempts ON attempts.attempt_id = validations.attempt_id
            WHERE attempts.job_id = ? ORDER BY validations.created_at, validations.validation_id
            """,
            (job["job_id"],),
        ).fetchall()
    ]
    queue = None
    if job["state"] == "waiting_capacity":
        queue = next(
            (entry for entry in waiting_jobs(store) if entry["job_id"] == job["job_id"]),
            None,
        )
        if queue is not None:
            queue = {
                "position": queue["queue_position"],
                "priority": queue["priority"],
                "effective_priority": queue["effective_priority"],
                "wait_seconds": queue["wait_seconds"],
                "reason": queue["queue_reason"],
            }
    return {
        **job,
        "attempts": attempts,
        "leases": leases,
        "dependency_job_ids": dependencies,
        "validations": validations,
        "queue": queue,
    }


def _dependencies_ready(store: Store, job_id: str) -> None:
    rows = store.connection.execute(
        """
        SELECT jobs.job_id, jobs.state
        FROM job_dependencies
        JOIN jobs ON jobs.job_id = job_dependencies.depends_on_job_id
        WHERE job_dependencies.job_id = ?
        """,
        (job_id,),
    ).fetchall()
    incomplete = [f"{row['job_id']}:{row['state']}" for row in rows if row["state"] != "validated"]
    if incomplete:
        raise AgentctlJobError("job dependencies are not validated: " + ", ".join(sorted(incomplete)))


def _assert_state_path(path: Path, expected_root: Path) -> Path:
    resolved = path.resolve()
    root = expected_root.resolve()
    if not _inside(resolved, root) or resolved == root:
        raise AgentctlJobError(f"computed state path escapes its dedicated root: {resolved}")
    return resolved


def _attempt_branch(job_id: str, number: int) -> str:
    suffix = "" if number == 1 else f"-a{number}"
    branch = f"agentctl/{job_id.lower()}{suffix}"
    result = run_command(["git", "check-ref-format", "--branch", branch], check=False)
    if result.returncode != 0:
        raise AgentctlJobError(f"generated invalid job branch: {branch}")
    return branch


def _record_prepare_failure(
    store: Store,
    job_id: str,
    attempt_id: str,
    reason: str,
) -> None:
    job_failed = False
    with store.transaction() as connection:
        attempt = connection.execute(
            "SELECT state FROM attempts WHERE attempt_id = ?", (attempt_id,)
        ).fetchone()
        job = connection.execute("SELECT state FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
        if attempt is not None and attempt["state"] == "preparing":
            transition_attempt(
                connection,
                job_id,
                attempt_id,
                "failed",
                reason=reason,
                fields={"finished_at": utc_now(), "exit_reason": "workspace_prepare"},
            )
        if job is not None and job["state"] == "preparing":
            transition_job(connection, job_id, "failed", reason=reason)
            job_failed = True
        _release_runtime_leases(connection, attempt_id, utc_now())
    if job_failed:
        _emit_mira_agent_job_event(store, job_id, attempt_id, "AgentJobFailed")


def prepare_attempt(
    store: Store,
    job_id: str,
    provider: str,
    *,
    clean_retry: bool = False,
    queue_if_full: bool = False,
    from_queue: bool = False,
) -> dict[str, Any] | None:
    canonical = require_job_id(job_id)
    if provider not in {"codex", "claude", "grok"}:
        raise AgentctlJobError(f"unsupported provider: {provider}")

    with workspace_lock(store.paths):
        job = get_job(store, canonical)
        if job["lane"] == "isolated":
            raise AgentctlJobError("isolated lane runtime is not implemented; refusing same-container fallback")
        if job["state"] == "created":
            if clean_retry:
                raise AgentctlJobError("--clean-retry is only valid after a terminal failure")
        elif job["state"] in RETRYABLE_STATES:
            if not clean_retry:
                raise AgentctlJobError("terminal job requires explicit --clean-retry")
        elif job["state"] == "waiting_capacity":
            if not from_queue:
                raise AgentctlJobError(
                    "job is already waiting for capacity; resume it with `job run --detach`"
                )
        else:
            raise AgentctlJobError(f"job cannot start from state {job['state']!r}")

        _dependencies_ready(store, canonical)
        project = get_project(store, job["project_id"])
        workspace = resolve_git_workspace(project["registered_path"])
        current_common = git_common_dir(workspace)
        if str(current_common) != project["git_common_dir"]:
            raise AgentctlJobError(
                "registered project path no longer resolves to the recorded Git common directory; "
                "run `agentctl project register` from the moved project"
            )
        resolved_base = resolve_full_commit(workspace, job["base_sha"])
        if resolved_base != job["base_sha"]:
            raise AgentctlJobError("stored immutable base SHA no longer resolves exactly")

        capacity_slot = _available_capacity_slot(store.connection, job["resource_class"])
        if capacity_slot is None:
            if not queue_if_full:
                raise AgentctlJobError(
                    f"no {job['resource_class']} capacity is available; use --detach to queue"
                )
            if job["state"] != "waiting_capacity":
                waiting_count = store.connection.execute(
                    "SELECT COUNT(*) AS count FROM jobs WHERE state = 'waiting_capacity'"
                ).fetchone()["count"]
                if int(waiting_count) >= queue_limit():
                    raise AgentctlJobError(
                        f"capacity queue limit ({queue_limit()}) has been reached"
                    )
                queued_at = utc_now()
                reason = f"waiting for {job['resource_class']} capacity"
                with store.transaction() as connection:
                    transition_job(
                        connection,
                        canonical,
                        "waiting_capacity",
                        reason=reason,
                        fields={"queue_reason": reason, "queued_at": queued_at},
                    )
            return None

        port_value = None
        if job["resource_class"] == "integration":
            port_value = _available_port(store.connection, canonical)

        previous_number = store.connection.execute(
            "SELECT COALESCE(MAX(number), 0) AS number FROM attempts WHERE job_id = ?", (canonical,)
        ).fetchone()["number"]
        number = int(previous_number) + 1
        attempt_id = new_ulid()
        attempt_dir = _assert_state_path(
            store.paths.attempt_dir(project["project_id"], canonical, number),
            store.paths.project_dir(project["project_id"]),
        )
        _mkdir_private(attempt_dir)
        result_path = attempt_dir / "result.json"
        log_path = attempt_dir / "process.log"
        branch_name: str | None = None
        workspace_path = workspace
        if job["lane"] == "write":
            branch_name = _attempt_branch(canonical, number)
            workspace_path = _assert_state_path(
                store.paths.worktree_dir(project["project_id"], canonical, number),
                store.paths.project_dir(project["project_id"]),
            )

        now = utc_now()
        with store.transaction() as connection:
            transition_job(
                connection,
                canonical,
                "preparing",
                reason=(
                    "capacity lease acquired"
                    if job["state"] == "waiting_capacity"
                    else "clean retry"
                    if clean_retry
                    else "attempt preparation"
                ),
                fields={"queue_reason": None, "queued_at": None},
            )
            connection.execute(
                """
                INSERT INTO attempts(
                    attempt_id, job_id, number, provider, state, workspace_path, branch_name,
                    result_path, log_path, created_at, updated_at
                ) VALUES (?, ?, ?, ?, 'preparing', ?, ?, ?, ?, ?, ?)
                """,
                (
                    attempt_id,
                    canonical,
                    number,
                    provider,
                    str(workspace_path),
                    branch_name,
                    str(result_path),
                    str(log_path),
                    now,
                    now,
                ),
            )
            connection.execute(
                """
                INSERT INTO state_events(job_id, attempt_id, entity, from_state, to_state, reason, created_at)
                VALUES (?, ?, 'attempt', NULL, 'preparing', 'attempt created', ?)
                """,
                (canonical, attempt_id, now),
            )
            connection.execute(
                """
                INSERT INTO leases(lease_id, attempt_id, kind, value, acquired_at)
                VALUES (?, ?, 'capacity', ?, ?)
                """,
                (new_ulid(), attempt_id, capacity_slot, now),
            )
            if port_value is not None:
                connection.execute(
                    """
                    INSERT INTO leases(lease_id, attempt_id, kind, value, acquired_at)
                    VALUES (?, ?, 'port', ?, ?)
                    """,
                    (new_ulid(), attempt_id, port_value, now),
                )

        try:
            if job["lane"] == "write":
                if workspace_path.exists():
                    raise AgentctlJobError(f"attempt worktree path already exists: {workspace_path}")
                branch_exists = git(
                    workspace,
                    "show-ref",
                    "--verify",
                    "--quiet",
                    f"refs/heads/{branch_name}",
                    check=False,
                )
                if branch_exists.returncode == 0:
                    raise AgentctlJobError(f"attempt branch already exists: {branch_name}")
                _mkdir_private(workspace_path.parent)
                git(workspace, "worktree", "add", "-b", str(branch_name), str(workspace_path), job["base_sha"])

            with store.transaction() as connection:
                if job["lane"] == "write":
                    for kind, value in (
                        ("worktree", str(workspace_path)),
                        ("branch", str(branch_name)),
                    ):
                        connection.execute(
                            """
                            INSERT INTO leases(lease_id, attempt_id, kind, value, acquired_at)
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (new_ulid(), attempt_id, kind, value, utc_now()),
                        )
                transition_attempt(connection, canonical, attempt_id, "ready", reason="workspace prepared")
                transition_job(connection, canonical, "ready", reason="workspace prepared")
        except BaseException as exc:
            _record_prepare_failure(store, canonical, attempt_id, str(exc))
            raise
    return get_attempt(store, attempt_id)


def _provider_binary(provider: str, permission_profile: str) -> str:
    trusted = permission_profile == "trusted-fast"
    if provider == "codex":
        env_name = "AGENTCTL_CODEX_TRUSTED_BIN" if trusted else "AGENTCTL_CODEX_BIN"
        fallback = "codex-trusted" if trusted else "codex"
    elif provider == "claude":
        env_name = "AGENTCTL_CLAUDE_TRUSTED_BIN" if trusted else "AGENTCTL_CLAUDE_BIN"
        fallback = "claude-trusted" if trusted else "claude"
    elif provider == "grok":
        env_name = "AGENTCTL_GROK_TRUSTED_BIN" if trusted else "AGENTCTL_GROK_BIN"
        fallback = "grok-trusted" if trusted else "grok"
    else:
        raise AgentctlJobError(f"unsupported provider: {provider}")
    return os.environ.get(env_name) or shutil.which(fallback) or fallback


def _result_schema(workspace: Path) -> tuple[Path, dict[str, Any]]:
    config = _load_project_config(workspace)
    relative = config.get("contracts", {}).get("result")
    if not isinstance(relative, str):
        raise AgentctlJobError("project config does not declare the result schema")
    path = _project_contract_path(workspace, relative)
    schema = load_json(path)
    if not isinstance(schema, dict):
        raise AgentctlJobError(f"result schema root is not an object: {path}")
    return path, schema


TRANSPORT_SCHEMA_OMITTED_KEYWORDS = frozenset(
    {
        "$schema",
        "$id",
        "title",
        "description",
        "uniqueItems",
        "minLength",
        "maxLength",
        "pattern",
        "minimum",
        "maximum",
        "minItems",
        "maxItems",
        "allOf",
        "if",
        "then",
        "else",
    }
)


def provider_transport_schema(value: Any) -> Any:
    """Return the common structured-output subset accepted by pinned providers.

    The project schema remains the authoritative validator after the provider
    exits.  This projection only constrains transport shape; keywords used for
    uniqueness, conditional invariants, bounds, and canonical identifiers are
    deliberately enforced by the broker instead of provider-specific schema
    implementations.
    """

    if isinstance(value, list):
        return [provider_transport_schema(item) for item in value]
    if not isinstance(value, dict):
        return value
    projected: dict[str, Any] = {}
    for key, item in value.items():
        if key in TRANSPORT_SCHEMA_OMITTED_KEYWORDS:
            continue
        projected["anyOf" if key == "oneOf" else key] = provider_transport_schema(
            item
        )
    if "type" not in projected:
        candidates: list[Any] = []
        if "const" in projected:
            candidates = [projected["const"]]
        elif isinstance(projected.get("enum"), list) and projected["enum"]:
            candidates = projected["enum"]
        inferred = {_json_schema_primitive_type(item) for item in candidates}
        inferred.discard(None)
        if len(inferred) == 1:
            projected["type"] = inferred.pop()
    properties = projected.get("properties")
    if isinstance(properties, dict):
        canonical_required = {
            item for item in value.get("required", []) if isinstance(item, str)
        }
        for name in properties.keys() - canonical_required:
            property_schema = properties[name]
            properties[name] = {
                "anyOf": [property_schema, {"type": "null"}]
            }
        projected["required"] = list(properties)
    return projected


def _json_schema_primitive_type(value: Any) -> str | None:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    return None


def normalize_transport_result(value: Any, canonical_schema: Any) -> Any:
    """Drop only transport-added nulls for canonically optional properties."""

    if isinstance(value, list):
        item_schema = (
            canonical_schema.get("items")
            if isinstance(canonical_schema, dict)
            else None
        )
        return [normalize_transport_result(item, item_schema) for item in value]
    if not isinstance(value, dict) or not isinstance(canonical_schema, dict):
        return value
    properties = canonical_schema.get("properties")
    if not isinstance(properties, dict):
        return value
    required = {
        item for item in canonical_schema.get("required", []) if isinstance(item, str)
    }
    normalized: dict[str, Any] = {}
    for key, item in value.items():
        property_schema = properties.get(key)
        if key not in required and item is None:
            continue
        normalized[key] = normalize_transport_result(item, property_schema)
    return normalized


def _build_prompt(workspace: Path, job: dict[str, Any]) -> str:
    task = load_json(Path(job["task_path"]))
    config = _load_project_config(workspace)
    role_config = config.get("roles", {}).get(job["role"], {})
    role_relative = role_config.get("definition")
    if not isinstance(role_relative, str):
        raise AgentctlJobError(f"role definition is missing for {job['role']!r}")
    role_path = _project_contract_path(workspace, role_relative)
    role_text = role_path.read_text(encoding="utf-8")
    task_text = json.dumps(task, ensure_ascii=False, indent=2, sort_keys=True)
    write_handoff = ""
    if job["lane"] == "write":
        write_handoff = (
            "This is an agentctl broker-managed write job. Do not run git commit, merge, rebase, or push.\n"
            "Leave only the intended scoped working-tree changes, report the current pre-commit HEAD, "
            "and use status ready_for_commit with dirty_state.is_dirty=true.\n"
            "The broker will independently verify scope and create the job commit.\n"
        )
    return (
        "Follow the provider-neutral role and task contract below.\n"
        "Do not change the job id, base SHA, lane, permission profile, or scope.\n"
        f"{write_handoff}"
        "Do not emit a result object as progress. Complete all required tool work and checks first; "
        "before that, communicate only through tool calls.\n"
        "For every command acceptance item, copy its value exactly into checks.command and report its actual status.\n"
        "Return only one JSON object matching .agent/schemas/result.schema.json; do not use Markdown fences.\n\n"
        f"ROLE CONTRACT:\n{role_text}\n\nTASK ENVELOPE:\n{task_text}\n"
    )


@dataclass(frozen=True)
class ProviderInvocation:
    argv: list[str]
    prompt: str
    environment: dict[str, str]
    raw_output_path: Path
    result_path: Path
    result_schema: dict[str, Any]


def prepare_provider_invocation(
    store: Store,
    job: dict[str, Any],
    attempt: dict[str, Any],
    *,
    allow_trusted_fast: bool,
) -> ProviderInvocation:
    permission_profile = job["permission_profile"]
    if permission_profile == "trusted-fast" and not allow_trusted_fast:
        raise AgentctlJobError(
            "task requests trusted-fast; rerun with explicit --allow-trusted-fast after checking the boundary"
        )
    if permission_profile not in {"safe", "trusted-fast"}:
        raise AgentctlJobError(f"unsupported same-container permission profile: {permission_profile}")

    workspace = Path(attempt["workspace_path"]).resolve()
    _schema_path, schema = _result_schema(workspace)
    transport_schema = provider_transport_schema(schema)
    prompt = _build_prompt(workspace, job)
    binary = _provider_binary(attempt["provider"], permission_profile)
    result_path = Path(attempt["result_path"])
    raw_output_path = Path(attempt["log_path"])
    transport_schema_path = result_path.parent / "provider-output-schema.json"
    write_json_private(transport_schema_path, transport_schema)

    if attempt["provider"] == "codex":
        sandbox = "read-only" if job["lane"] == "read" else "workspace-write"
        argv = [binary]
        if permission_profile == "safe":
            argv.extend(["--ask-for-approval", "never"])
        argv.extend(
            [
                "exec",
                "--ephemeral",
                "--sandbox",
                sandbox,
                "--color",
                "never",
                "--output-schema",
                str(transport_schema_path),
                "--output-last-message",
                str(result_path),
                "--cd",
                str(workspace),
                "-",
            ]
        )
    elif attempt["provider"] == "claude":
        argv = [
            binary,
            "--agent",
            job["role"],
            "--print",
            "--output-format",
            "json",
            "--json-schema",
            json.dumps(transport_schema, separators=(",", ":"), sort_keys=True),
            "--no-session-persistence",
        ]
        if permission_profile == "safe":
            argv.extend(
                [
                    "--permission-mode",
                    "plan" if job["lane"] == "read" else "acceptEdits",
                ]
            )
    elif attempt["provider"] == "grok":
        argv = [
            binary,
            "--agent",
            job["role"],
            "--cwd",
            str(workspace),
            "--output-format",
            "json",
            "--json-schema",
            json.dumps(transport_schema, separators=(",", ":"), sort_keys=True),
            "--prompt-file",
            "/dev/stdin",
            "--no-auto-update",
            "--no-subagents",
            "--max-turns",
            "64",
        ]
        if permission_profile == "safe":
            argv.extend(
                [
                    "--permission-mode",
                    "dontAsk",
                    "--sandbox",
                    "read-only" if job["lane"] == "read" else "workspace",
                ]
            )
            for rule in ("Read", "Grep", "Glob", "WebFetch", "WebSearch", "Edit", "Write", "Bash"):
                argv.extend(["--allow", rule])
            for rule in (
                "Bash(git push*)",
                "Bash(git commit*)",
                "Bash(git merge*)",
                "Bash(git rebase*)",
                "Bash(git checkout*)",
                "Bash(git switch*)",
                "Bash(rm -rf *)",
                "Bash(sudo *)",
            ):
                argv.extend(["--deny", rule])
    else:
        raise AgentctlJobError(f"unsupported provider: {attempt['provider']}")

    attempt_temp = result_path.parent / "tmp"
    _mkdir_private(attempt_temp)
    compose_project = "agent_" + job["job_id"].lower()
    environment = os.environ.copy()
    environment.update(
        {
            "AGENTCTL_JOB_ID": job["job_id"],
            "AGENTCTL_ATTEMPT_ID": attempt["attempt_id"],
            "AGENTCTL_PERMISSION_PROFILE": permission_profile,
            "AGENTCTL_RESOURCE_CLASS": job["resource_class"],
            "AGENTCTL_COMPOSE_PROJECT_NAME": compose_project,
            "AGENTCTL_DOCKER_LABEL": f"dev.agentctl.job={job['job_id']}",
            "COMPOSE_PROJECT_NAME": compose_project,
            "TMPDIR": str(attempt_temp),
        }
    )
    if attempt["provider"] == "grok":
        # GROK_MEMORY=0 is supported across the pinned 1.0.3 binary and newer
        # builds whose advertised --no-memory flag may be absent from clap.
        environment["GROK_MEMORY"] = "0"
    port_lease = store.connection.execute(
        """
        SELECT value FROM leases
        WHERE attempt_id = ? AND kind = 'port' AND released_at IS NULL
        ORDER BY acquired_at LIMIT 1
        """,
        (attempt["attempt_id"],),
    ).fetchone()
    if port_lease is not None:
        environment["AGENTCTL_PORT"] = str(port_lease["value"])
    return ProviderInvocation(
        argv=argv,
        prompt=prompt,
        environment=environment,
        raw_output_path=raw_output_path,
        result_path=result_path,
        result_schema=schema,
    )


def _process_stat_identity(pid: int) -> tuple[str, str] | None:
    stat_path = Path(f"/proc/{pid}/stat")
    try:
        raw = stat_path.read_text(encoding="utf-8")
        # comm is parenthesized and may itself contain spaces. Field 22
        # (starttime) is field index 19 after the closing parenthesis.
        closing = raw.rfind(")")
        if closing < 0:
            return None
        fields = raw[closing + 1 :].split()
        return fields[19], fields[0]
    except (OSError, IndexError):
        return None


def _process_start_marker(pid: int) -> str:
    identity = _process_stat_identity(pid)
    if identity is None:
        return "unknown"
    return identity[0]


def process_identity_matches(pid: int | None, marker: str | None) -> bool:
    """Return true only while pid still names the originally recorded process."""

    if not isinstance(pid, int) or pid <= 1 or not marker or marker == "unknown":
        return False
    try:
        os.kill(pid, 0)
    except (ProcessLookupError, PermissionError):
        return False
    identity = _process_stat_identity(pid)
    return identity is not None and identity[0] == marker and identity[1] != "Z"


def _heartbeat_interval() -> float:
    raw = os.environ.get("AGENTCTL_HEARTBEAT_SECONDS", "2")
    try:
        value = float(raw)
    except ValueError as exc:
        raise AgentctlJobError(f"invalid AGENTCTL_HEARTBEAT_SECONDS: {raw!r}") from exc
    if not 0.05 <= value <= 60:
        raise AgentctlJobError("AGENTCTL_HEARTBEAT_SECONDS must be between 0.05 and 60")
    return value


def _touch_running_attempt(store: Store, attempt_id: str) -> bool:
    now = utc_now()
    with store.transaction() as connection:
        updated = connection.execute(
            """
            UPDATE attempts SET heartbeat_at = ?, updated_at = ?
            WHERE attempt_id = ? AND state = 'running'
            """,
            (now, now, attempt_id),
        )
    return updated.rowcount == 1


def _extract_claude_result(raw_path: Path, result_path: Path) -> None:
    try:
        text = raw_path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise AgentctlJobError(f"cannot read Claude provider output: {exc}") from exc
    if not text:
        raise AgentctlJobError("Claude provider returned empty output")
    candidates = [text, *reversed([line for line in text.splitlines() if line.strip()])]
    payload: Any = None
    for candidate in candidates:
        try:
            payload = json.loads(candidate)
            break
        except json.JSONDecodeError:
            continue
    if payload is None:
        raise AgentctlJobError("Claude provider output is not JSON")

    result: Any = payload
    if isinstance(payload, dict) and "structured_output" in payload:
        result = payload["structured_output"]
    elif isinstance(payload, dict) and isinstance(payload.get("result"), str):
        try:
            result = json.loads(payload["result"])
        except json.JSONDecodeError as exc:
            raise AgentctlJobError("Claude result field is not structured JSON") from exc
    if not isinstance(result, dict):
        raise AgentctlJobError("Claude structured result is not a JSON object")
    write_json_private(result_path, result)


def _extract_grok_result(raw_path: Path, result_path: Path) -> None:
    try:
        text = raw_path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise AgentctlJobError(f"cannot read Grok provider output: {exc}") from exc
    if not text:
        raise AgentctlJobError("Grok provider returned empty output")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise AgentctlJobError("Grok provider output is not one JSON object") from exc
    if not isinstance(payload, dict):
        raise AgentctlJobError("Grok provider output root is not a JSON object")
    result = payload.get("structuredOutput")
    if not isinstance(result, dict):
        # Grok 1.0.3 can concatenate JSON-shaped assistant progress turns in
        # `text` and report no structuredOutput. The last top-level document is
        # the final response candidate; every preceding byte must still decode
        # as a JSON object. The result schema, required acceptance checks, and
        # Git verification run immediately after extraction, so an incomplete
        # final progress object cannot become success.
        text_result = payload.get("text")
        if not isinstance(text_result, str) or not text_result.strip():
            structured_error = payload.get("structuredOutputError")
            if isinstance(structured_error, str) and structured_error:
                raise AgentctlJobError(f"Grok structured output failed: {structured_error}")
            raise AgentctlJobError("Grok provider did not return a structuredOutput object")
        decoder = json.JSONDecoder()
        documents: list[dict[str, Any]] = []
        offset = 0
        try:
            while offset < len(text_result):
                while offset < len(text_result) and text_result[offset].isspace():
                    offset += 1
                if offset == len(text_result):
                    break
                document, offset = decoder.raw_decode(text_result, offset)
                if not isinstance(document, dict):
                    raise AgentctlJobError("Grok text fallback contains a non-object JSON document")
                documents.append(document)
        except json.JSONDecodeError as exc:
            raise AgentctlJobError("Grok text fallback is not a sequence of JSON objects") from exc
        if not documents:
            raise AgentctlJobError("Grok text fallback contains no JSON object")
        result = documents[-1]
    write_json_private(result_path, result)


def _git_path_list(workspace: Path, *arguments: str) -> list[str]:
    output = git(workspace, *arguments).stdout
    return sorted({value for value in output.split("\0") if value})


def inspect_git_result(workspace: Path, base_sha: str) -> dict[str, Any]:
    head_sha = resolve_full_commit(workspace, "HEAD")
    ancestor = git(workspace, "merge-base", "--is-ancestor", base_sha, head_sha, check=False).returncode == 0
    changed_paths = _git_path_list(workspace, "diff", "--name-only", "-z", f"{base_sha}..{head_sha}")
    dirty_paths = sorted(
        set(_git_path_list(workspace, "diff", "--name-only", "-z"))
        | set(_git_path_list(workspace, "diff", "--cached", "--name-only", "-z"))
        | set(_git_path_list(workspace, "ls-files", "--others", "--exclude-standard", "-z"))
    )
    return {
        "head_sha": head_sha,
        "base_is_ancestor": ancestor,
        "changed_paths": changed_paths,
        "dirty_state": {"is_dirty": bool(dirty_paths), "paths": dirty_paths},
    }


def _normalize_contract_path(value: str) -> str:
    if value == ".":
        return "."
    path = PurePosixPath(value)
    return str(path).rstrip("/")


def _under(path: str, prefix: str) -> bool:
    path_value = _normalize_contract_path(path)
    prefix_value = _normalize_contract_path(prefix)
    return prefix_value == "." or path_value == prefix_value or path_value.startswith(prefix_value + "/")


def verify_result(
    job: dict[str, Any],
    attempt: dict[str, Any],
    result_schema: dict[str, Any],
    *,
    broker_final: bool = False,
) -> dict[str, Any]:
    result_path = Path(attempt["result_path"])
    result = load_json(result_path)
    try:
        validate(result, result_schema)
    except ContractValidationError as exc:
        raise AgentctlJobError(f"result schema validation failed: {exc}") from exc
    if not isinstance(result, dict):
        raise AgentctlJobError("result root must be a JSON object")
    if result.get("job_id") != job["job_id"]:
        raise AgentctlJobError("result job_id does not match the immutable job")

    workspace = Path(attempt["workspace_path"]).resolve()
    observed = inspect_git_result(workspace, job["base_sha"])
    if not observed["base_is_ancestor"]:
        raise AgentctlJobError("attempt HEAD does not descend from the immutable base SHA")
    if result.get("head_sha") is not None and result.get("head_sha") != observed["head_sha"]:
        raise AgentctlJobError(
            f"reported head_sha differs from Git: {result.get('head_sha')!r} != {observed['head_sha']!r}"
        )
    status = result["status"]
    if status == "ready_for_commit":
        if job["lane"] != "write":
            raise AgentctlJobError("ready_for_commit is only valid for a write lane")
        if broker_final:
            raise AgentctlJobError("broker-final result may not remain ready_for_commit")
        if observed["head_sha"] != job["base_sha"] or observed["changed_paths"]:
            raise AgentctlJobError("write provider changed Git history; the broker must own the job commit")
        expected_changed_paths = observed["dirty_state"]["paths"]
    else:
        expected_changed_paths = observed["changed_paths"]
        if status in {"failed", "blocked"}:
            expected_changed_paths = sorted(
                set(expected_changed_paths) | set(observed["dirty_state"]["paths"])
            )
        if (
            job["lane"] == "write"
            and not broker_final
            and observed["head_sha"] != job["base_sha"]
        ):
            raise AgentctlJobError("write provider changed Git history; the broker must own the job commit")
    if sorted(result.get("changed_paths", [])) != expected_changed_paths:
        raise AgentctlJobError("reported changed_paths differ from broker-observed paths")
    reported_dirty = result.get("dirty_state", {})
    if (
        reported_dirty.get("is_dirty") != observed["dirty_state"]["is_dirty"]
        or sorted(reported_dirty.get("paths", [])) != observed["dirty_state"]["paths"]
    ):
        raise AgentctlJobError("reported dirty_state differs from the worktree")

    task = load_json(Path(job["task_path"]))
    if result["status"] in {"ready_for_commit", "completed"}:
        reported_checks = result.get("checks", [])
        for acceptance in task.get("acceptance", []):
            if acceptance.get("kind") != "command":
                continue
            command = acceptance["value"]
            if not any(
                check.get("command") == command
                and check.get("status") == "passed"
                and check.get("exit_code") == 0
                for check in reported_checks
            ):
                raise AgentctlJobError(
                    f"required acceptance command was not reported as passed: {command}"
                )
    allowed = task["scope"]["allowed_paths"]
    forbidden = task["scope"]["forbidden_paths"]
    scope_paths = sorted(
        set(observed["changed_paths"]) | set(observed["dirty_state"]["paths"])
    )
    violations = [
        path
        for path in scope_paths
        if not any(_under(path, prefix) for prefix in allowed)
        or any(_under(path, prefix) for prefix in forbidden)
    ]
    if violations:
        raise AgentctlJobError("Git changes escape the task scope: " + ", ".join(violations))
    if result["status"] == "completed" and observed["dirty_state"]["is_dirty"]:
        raise AgentctlJobError("completed result has a dirty worktree")
    return {"result": result, "observed_git": observed}


def broker_commit_ready_result(
    job: dict[str, Any],
    attempt: dict[str, Any],
    result_schema: dict[str, Any],
    verified: dict[str, Any],
) -> dict[str, Any]:
    if verified["result"]["status"] != "ready_for_commit":
        return verified
    workspace = Path(attempt["workspace_path"]).resolve()
    dirty_paths = verified["observed_git"]["dirty_state"]["paths"]
    if not dirty_paths:
        raise AgentctlJobError("ready_for_commit result has no broker-observed dirty path")

    for key in ("user.name", "user.email"):
        configured = git(workspace, "config", "--get", key, check=False)
        if configured.returncode != 0 or not configured.stdout.strip():
            raise AgentctlJobError(f"broker commit requires Git {key} configuration")

    git(workspace, "add", "-A", "--", *dirty_paths)
    staged_paths = _git_path_list(workspace, "diff", "--cached", "--name-only", "-z")
    if staged_paths != dirty_paths:
        raise AgentctlJobError("broker-staged paths differ from the verified dirty path set")

    task = load_json(Path(job["task_path"]))
    objective_line = str(task["objective"]).strip().splitlines()[0][:72]
    message = f"agentctl({job['job_id'].lower()}): {objective_line}"
    git(
        workspace,
        "-c",
        "core.hooksPath=/dev/null",
        "-c",
        "commit.gpgSign=false",
        "commit",
        "--no-verify",
        "-m",
        message,
    )
    observed = inspect_git_result(workspace, job["base_sha"])
    if observed["dirty_state"]["is_dirty"]:
        raise AgentctlJobError("broker commit did not leave a clean worktree")

    final_result = dict(verified["result"])
    final_result.update(
        {
            "status": "completed",
            "head_sha": observed["head_sha"],
            "changed_paths": observed["changed_paths"],
            "dirty_state": observed["dirty_state"],
        }
    )
    final_result["checks"] = [
        *final_result.get("checks", []),
        {
            "command": "agentctl broker commit",
            "status": "passed",
            "exit_code": 0,
            "summary": "Broker verified scope and created the job commit with hooks and signing disabled.",
        },
    ]
    write_json_private(Path(attempt["result_path"]), final_result)
    return verify_result(job, attempt, result_schema, broker_final=True)


def _mark_run_failure(
    store: Store,
    job_id: str,
    attempt_id: str,
    *,
    exit_code: int | None,
    exit_reason: str,
    reason: str,
) -> None:
    now = utc_now()
    job_failed = False
    with store.transaction() as connection:
        attempt = connection.execute(
            "SELECT state FROM attempts WHERE attempt_id = ?", (attempt_id,)
        ).fetchone()
        job = connection.execute("SELECT state FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
        fields = {
            "exit_code": exit_code,
            "exit_reason": exit_reason,
            "finished_at": now,
            "heartbeat_at": now,
        }
        if attempt is not None and attempt["state"] in {"ready", "running", "succeeded"}:
            transition_attempt(connection, job_id, attempt_id, "failed", reason=reason, fields=fields)
        if job is not None and job["state"] in {"ready", "running", "succeeded"}:
            transition_job(connection, job_id, "failed", reason=reason)
            job_failed = True
        _release_runtime_leases(connection, attempt_id, now)
    if job_failed:
        _emit_mira_agent_job_event(store, job_id, attempt_id, "AgentJobFailed")


def _mark_run_cancelled(
    store: Store,
    job_id: str,
    attempt_id: str,
    *,
    exit_code: int | None,
    reason: str,
) -> None:
    now = utc_now()
    job_cancelled = False
    with store.transaction() as connection:
        attempt = connection.execute(
            "SELECT state FROM attempts WHERE attempt_id = ?", (attempt_id,)
        ).fetchone()
        job = connection.execute("SELECT state FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
        fields = {
            "exit_code": exit_code,
            "exit_reason": "foreground_interrupted",
            "finished_at": now,
            "heartbeat_at": now,
        }
        if attempt is not None and attempt["state"] == "running":
            transition_attempt(
                connection, job_id, attempt_id, "cancelled", reason=reason, fields=fields
            )
        if job is not None and job["state"] == "running":
            transition_job(connection, job_id, "cancelled", reason=reason)
            job_cancelled = True
        _release_runtime_leases(connection, attempt_id, now)
    if job_cancelled:
        _emit_mira_agent_job_event(store, job_id, attempt_id, "AgentJobCancelled")


def _terminate_process_group(process: subprocess.Popen[str]) -> int | None:
    if process.poll() is not None:
        return process.returncode
    try:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=5)
    except (ProcessLookupError, subprocess.TimeoutExpired):
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
    return process.returncode


def run_prepared_attempt(
    store: Store,
    attempt_id: str,
    *,
    allow_trusted_fast: bool = False,
) -> dict[str, Any]:
    attempt = get_attempt(store, attempt_id)
    job = get_job(store, attempt["job_id"])
    provider = attempt["provider"]
    if attempt["state"] != "ready" or job["state"] != "ready":
        raise AgentctlJobError(
            f"prepared runner requires ready state, got job={job['state']!r} "
            f"attempt={attempt['state']!r}"
        )
    if job["permission_profile"] == "trusted-fast" and not allow_trusted_fast:
        raise AgentctlJobError(
            "task requests trusted-fast; rerun with explicit --allow-trusted-fast after checking the boundary"
        )
    try:
        invocation = prepare_provider_invocation(
            store,
            job,
            attempt,
            allow_trusted_fast=allow_trusted_fast,
        )
    except BaseException as exc:
        _mark_run_failure(
            store,
            job["job_id"],
            attempt["attempt_id"],
            exit_code=None,
            exit_reason="adapter_prepare",
            reason=str(exc),
        )
        raise

    _mkdir_private(invocation.raw_output_path.parent)
    launch_time = utc_now()
    with store.transaction() as connection:
        transition_attempt(
            connection,
            job["job_id"],
            attempt["attempt_id"],
            "running",
            reason="foreground provider launch reserved",
            fields={"started_at": launch_time, "heartbeat_at": launch_time},
        )
        transition_job(
            connection,
            job["job_id"],
            "running",
            reason="foreground provider launch reserved",
        )
    _emit_mira_agent_job_event(
        store,
        job["job_id"],
        attempt["attempt_id"],
        "AgentJobStart",
    )
    process: subprocess.Popen[str] | None = None
    try:
        log_descriptor = os.open(
            invocation.raw_output_path,
            os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
            0o600,
        )
        with os.fdopen(log_descriptor, "w", encoding="utf-8") as output:
            process = subprocess.Popen(
                invocation.argv,
                cwd=Path(attempt["workspace_path"]),
                env=invocation.environment,
                stdin=subprocess.PIPE,
                stdout=output,
                stderr=subprocess.STDOUT,
                text=True,
                start_new_session=True,
            )
            marker = _process_start_marker(process.pid)
            if marker == "unknown":
                raise AgentctlJobError("provider process start marker is unavailable; refusing untrackable run")
            now = utc_now()
            try:
                with store.transaction() as connection:
                    connection.execute(
                        """
                        UPDATE attempts
                        SET pid = ?, process_started_at = ?, heartbeat_at = ?, updated_at = ?
                        WHERE attempt_id = ? AND state = 'running'
                        """,
                        (process.pid, marker, now, now, attempt["attempt_id"]),
                    )
                    if connection.execute("SELECT changes()").fetchone()[0] != 1:
                        raise AgentctlJobError(
                            "attempt left running state before provider identity registration"
                        )
                    connection.execute(
                        """
                        INSERT INTO leases(lease_id, attempt_id, kind, value, acquired_at)
                        VALUES (?, ?, 'process', ?, ?)
                        """,
                        (new_ulid(), attempt["attempt_id"], f"{process.pid}:{marker}", now),
                    )
            except BaseException:
                _terminate_process_group(process)
                raise
            try:
                if process.stdin is None:
                    raise AgentctlJobError("provider stdin pipe is unavailable")
                process.stdin.write(invocation.prompt)
                process.stdin.close()
                process.stdin = None
                interval = _heartbeat_interval()
                while True:
                    try:
                        exit_code = int(process.wait(timeout=interval))
                        break
                    except subprocess.TimeoutExpired:
                        if not _touch_running_attempt(store, attempt["attempt_id"]):
                            exit_code = _terminate_process_group(process)
                            raise AgentctlJobError(
                                "attempt left running state while provider was active"
                            )
            except KeyboardInterrupt as exc:
                exit_code = _terminate_process_group(process)
                _mark_run_cancelled(
                    store,
                    job["job_id"],
                    attempt["attempt_id"],
                    exit_code=exit_code,
                    reason="foreground client interrupted",
                )
                raise AgentctlJobError("foreground job interrupted; attempt marked cancelled") from exc
            _touch_running_attempt(store, attempt["attempt_id"])
        enforce_terminal_log_retention(invocation.raw_output_path)
    except OSError as exc:
        _mark_run_failure(
            store,
            job["job_id"],
            attempt["attempt_id"],
            exit_code=127,
            exit_reason="spawn",
            reason=str(exc),
        )
        raise AgentctlJobError(f"provider process could not start: {exc}") from exc
    except AgentctlJobError as exc:
        if process is not None:
            exit_code = _terminate_process_group(process)
        else:
            exit_code = None
        _mark_run_failure(
            store,
            job["job_id"],
            attempt["attempt_id"],
            exit_code=exit_code,
            exit_reason="runner_control",
            reason=str(exc),
        )
        raise
    except BaseException as exc:
        if process is not None:
            exit_code = _terminate_process_group(process)
        else:
            exit_code = None
        _mark_run_failure(
            store,
            job["job_id"],
            attempt["attempt_id"],
            exit_code=exit_code,
            exit_reason="runner_internal",
            reason=str(exc),
        )
        raise AgentctlJobError(f"foreground runner failed: {exc}") from exc
    finally:
        retention_path = invocation.raw_output_path.with_name("log-retention.json")
        if (
            not retention_path.is_file()
            and invocation.raw_output_path.is_file()
            and (process is None or process.poll() is not None)
        ):
            try:
                enforce_terminal_log_retention(invocation.raw_output_path)
            except (AgentctlJobError, OSError):
                # Preserve the primary execution/cancellation error. Validated jobs
                # still require retention evidence before becoming GC candidates.
                pass

    if exit_code != 0:
        _mark_run_failure(
            store,
            job["job_id"],
            attempt["attempt_id"],
            exit_code=exit_code,
            exit_reason="provider_exit",
            reason=f"provider exited with status {exit_code}",
        )
        raise AgentctlJobError(f"provider exited with status {exit_code}")

    try:
        if provider == "claude":
            _extract_claude_result(invocation.raw_output_path, invocation.result_path)
        elif provider == "grok":
            _extract_grok_result(invocation.raw_output_path, invocation.result_path)
        elif provider == "codex":
            if not invocation.result_path.is_file():
                raise AgentctlJobError("Codex did not write the required final result file")
        else:
            raise AgentctlJobError(f"unsupported provider: {provider}")
        transported_result = load_json(invocation.result_path)
        normalized_result = normalize_transport_result(
            transported_result, invocation.result_schema
        )
        if normalized_result != transported_result:
            write_json_private(invocation.result_path, normalized_result)
        refreshed_attempt = get_attempt(store, attempt["attempt_id"])
        verified = verify_result(job, refreshed_attempt, invocation.result_schema)
        write_json_private(
            invocation.result_path.with_name("provider-result.json"),
            verified["result"],
        )
        if verified["result"]["status"] == "ready_for_commit":
            verified = broker_commit_ready_result(
                job,
                refreshed_attempt,
                invocation.result_schema,
                verified,
            )
    except BaseException as exc:
        _mark_run_failure(
            store,
            job["job_id"],
            attempt["attempt_id"],
            exit_code=exit_code,
            exit_reason="result_validation",
            reason=str(exc),
        )
        raise

    result_status = verified["result"]["status"]
    if result_status != "completed":
        reason = (
            verified["result"].get("blocked_reason")
            or verified["result"].get("error", {}).get("message")
            or f"agent reported {result_status}"
        )
        _mark_run_failure(
            store,
            job["job_id"],
            attempt["attempt_id"],
            exit_code=exit_code,
            exit_reason=f"agent_reported_{result_status}",
            reason=reason,
        )
        raise AgentctlJobError(reason)

    now = utc_now()
    with store.transaction() as connection:
        transition_attempt(
            connection,
            job["job_id"],
            attempt["attempt_id"],
            "succeeded",
            reason="provider exit and result/Git validation passed",
            fields={
                "exit_code": 0,
                "exit_reason": "completed",
                "finished_at": now,
                "heartbeat_at": now,
                "head_sha": verified["observed_git"]["head_sha"],
            },
        )
        transition_job(
            connection,
            job["job_id"],
            "succeeded",
            reason="provider exit and result/Git validation passed",
        )
        _release_runtime_leases(connection, attempt["attempt_id"], now)
    _emit_mira_agent_job_event(
        store,
        job["job_id"],
        attempt["attempt_id"],
        "AgentJobSucceeded",
    )
    return show_job(store, job["job_id"])


def run_job_foreground(
    store: Store,
    job_id: str,
    provider: str,
    *,
    clean_retry: bool = False,
    allow_trusted_fast: bool = False,
) -> dict[str, Any]:
    preflight_job = get_job(store, job_id)
    if preflight_job["permission_profile"] == "trusted-fast" and not allow_trusted_fast:
        raise AgentctlJobError(
            "task requests trusted-fast; rerun with explicit --allow-trusted-fast after checking the boundary"
        )
    attempt = prepare_attempt(store, job_id, provider, clean_retry=clean_retry)
    return run_prepared_attempt(
        store,
        attempt["attempt_id"],
        allow_trusted_fast=allow_trusted_fast,
    )


def record_detached_runner(store: Store, attempt_id: str, pid: int, marker: str) -> str:
    if not process_identity_matches(pid, marker):
        raise AgentctlJobError("detached runner identity cannot be verified")
    runtime_id = f"runner:{pid}:{marker}"
    now = utc_now()
    with store.transaction() as connection:
        updated = connection.execute(
            """
            UPDATE attempts SET runtime_id = ?, updated_at = ?
            WHERE attempt_id = ? AND state = 'ready' AND runtime_id IS NULL
            """,
            (runtime_id, now, attempt_id),
        )
        if updated.rowcount != 1:
            raise AgentctlJobError("attempt is no longer available for detached runner ownership")
    return runtime_id


def mark_detached_launch_failure(
    store: Store,
    attempt_id: str,
    reason: str,
) -> None:
    attempt = get_attempt(store, attempt_id)
    _mark_run_failure(
        store,
        attempt["job_id"],
        attempt_id,
        exit_code=127,
        exit_reason="runner_spawn",
        reason=reason,
    )


def _runtime_process(value: str | None) -> tuple[int, str] | None:
    if not value or not value.startswith("runner:"):
        return None
    parts = value.split(":", 2)
    if len(parts) != 3:
        return None
    try:
        pid = int(parts[1])
    except ValueError:
        return None
    return pid, parts[2]


def _signal_recorded_group(pid: int | None, marker: str | None, sig: int) -> bool:
    if not process_identity_matches(pid, marker):
        return False
    assert pid is not None
    try:
        if os.getpgid(pid) != pid:
            return False
        os.killpg(pid, sig)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def _wait_for_identity_exit(pid: int, marker: str, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while process_identity_matches(pid, marker) and time.monotonic() < deadline:
        time.sleep(0.05)
    return not process_identity_matches(pid, marker)


def _terminate_recorded_group(pid: int | None, marker: str | None, grace_seconds: float) -> None:
    if not _signal_recorded_group(pid, marker, signal.SIGTERM):
        return
    assert pid is not None and marker is not None
    if _wait_for_identity_exit(pid, marker, grace_seconds):
        return
    _signal_recorded_group(pid, marker, signal.SIGKILL)
    _wait_for_identity_exit(pid, marker, 1.0)


def cancel_job(store: Store, job_id: str, *, grace_seconds: float = 5.0) -> dict[str, Any]:
    canonical = require_job_id(job_id)
    job = get_job(store, canonical)
    if job["state"] == "waiting_capacity":
        with workspace_lock(store.paths):
            current = get_job(store, canonical)
            if current["state"] != "waiting_capacity":
                raise AgentctlJobError(
                    f"job left the capacity queue before cancellation: {current['state']!r}"
                )
            with store.transaction() as connection:
                transition_job(
                    connection,
                    canonical,
                    "cancelled",
                    reason="operator cancelled queued job",
                    fields={"queue_reason": None, "queued_at": None},
                )
        return show_job(store, canonical)

    attempt = latest_attempt(store, canonical)
    if attempt is None or job["state"] not in {"ready", "running"}:
        raise AgentctlJobError(
            "job cancellation requires waiting_capacity/ready/running state, "
            f"got {job['state']!r}"
        )
    if attempt["state"] not in {"ready", "running"}:
        raise AgentctlJobError(f"latest attempt is not cancellable: {attempt['state']!r}")

    now = utc_now()
    with store.transaction() as connection:
        current_job = connection.execute(
            "SELECT state FROM jobs WHERE job_id = ?", (canonical,)
        ).fetchone()
        current_attempt = connection.execute(
            "SELECT * FROM attempts WHERE attempt_id = ?", (attempt["attempt_id"],)
        ).fetchone()
        if (
            current_job is None
            or current_attempt is None
            or current_job["state"] not in {"ready", "running"}
            or current_attempt["state"] not in {"ready", "running"}
        ):
            raise AgentctlJobError("attempt became non-cancellable before cancellation was recorded")
        provider_identity = (
            current_attempt["pid"],
            current_attempt["process_started_at"],
        )
        runner_identity = _runtime_process(current_attempt["runtime_id"])
        transition_attempt(
            connection,
            canonical,
            attempt["attempt_id"],
            "cancelled",
            reason="operator requested cancellation",
            fields={
                "exit_reason": "cancel_requested",
                "finished_at": now,
                "heartbeat_at": now,
            },
        )
        transition_job(connection, canonical, "cancelled", reason="operator requested cancellation")
        _release_runtime_leases(connection, attempt["attempt_id"], now)

    _emit_mira_agent_job_event(
        store,
        canonical,
        attempt["attempt_id"],
        "AgentJobCancelled",
    )

    provider_pid, provider_marker = provider_identity
    if _signal_recorded_group(provider_pid, provider_marker, signal.SIGTERM):
        assert provider_pid is not None and provider_marker is not None
        if not _wait_for_identity_exit(provider_pid, provider_marker, grace_seconds):
            _signal_recorded_group(provider_pid, provider_marker, signal.SIGKILL)
            _wait_for_identity_exit(provider_pid, provider_marker, 1.0)

    if runner_identity is not None:
        runner_pid, runner_marker = runner_identity
        if process_identity_matches(runner_pid, runner_marker):
            if not _wait_for_identity_exit(runner_pid, runner_marker, 1.0):
                _signal_recorded_group(runner_pid, runner_marker, signal.SIGTERM)
                if not _wait_for_identity_exit(runner_pid, runner_marker, 1.0):
                    _signal_recorded_group(runner_pid, runner_marker, signal.SIGKILL)
    try:
        enforce_attempt_log_retention(store, attempt)
    except AgentctlJobError:
        # Cancellation is already durable and scoped. Missing/corrupt retention
        # evidence blocks later GC rather than changing the cancellation result.
        pass
    return show_job(store, canonical)


def _mark_run_orphaned(store: Store, job_id: str, attempt_id: str, reason: str) -> None:
    now = utc_now()
    job_orphaned = False
    with store.transaction() as connection:
        attempt = connection.execute(
            "SELECT state FROM attempts WHERE attempt_id = ?", (attempt_id,)
        ).fetchone()
        job = connection.execute("SELECT state FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
        if attempt is not None and attempt["state"] == "running":
            transition_attempt(
                connection,
                job_id,
                attempt_id,
                "orphaned",
                reason=reason,
                fields={
                    "exit_reason": "orphaned",
                    "finished_at": now,
                    "heartbeat_at": now,
                },
            )
        if job is not None and job["state"] == "running":
            transition_job(connection, job_id, "orphaned", reason=reason)
            job_orphaned = True
        _release_runtime_leases(connection, attempt_id, now)
    if job_orphaned:
        _emit_mira_agent_job_event(store, job_id, attempt_id, "AgentJobOrphaned")


def reconcile_attempts(store: Store, *, orphan_after_seconds: float = 30.0) -> list[dict[str, Any]]:
    if orphan_after_seconds < 0.1:
        raise AgentctlJobError("orphan reconciliation threshold must be at least 0.1 seconds")
    rows = [
        dict(row)
        for row in store.connection.execute(
            "SELECT * FROM attempts WHERE state IN ('ready', 'running') ORDER BY created_at"
        ).fetchall()
    ]
    actions: list[dict[str, Any]] = []
    for attempt in rows:
        runner_identity = _runtime_process(attempt["runtime_id"])
        runner_alive = bool(
            runner_identity
            and process_identity_matches(runner_identity[0], runner_identity[1])
        )
        age = _timestamp_age(attempt["heartbeat_at"] or attempt["updated_at"])

        if attempt["state"] == "ready":
            # Foreground preparation has no runtime_id and is owned by its caller.
            runner_start_deadline = max(5.0, orphan_after_seconds)
            if runner_identity is not None and age >= runner_start_deadline:
                if runner_alive:
                    _terminate_recorded_group(
                        runner_identity[0], runner_identity[1], 1.0
                    )
                reason = "detached runner did not reach provider launch before its ownership deadline"
                _mark_run_failure(
                    store,
                    attempt["job_id"],
                    attempt["attempt_id"],
                    exit_code=None,
                    exit_reason="runner_lost",
                    reason=reason,
                )
                actions.append({"attempt_id": attempt["attempt_id"], "action": "failed", "reason": reason})
            continue

        provider_alive = process_identity_matches(
            attempt["pid"], attempt["process_started_at"]
        )
        if age < orphan_after_seconds:
            continue
        reason = "running attempt heartbeat expired without a live owner"
        if provider_alive:
            _terminate_recorded_group(
                attempt["pid"], attempt["process_started_at"], 1.0
            )
        if runner_identity is not None and runner_alive:
            _terminate_recorded_group(runner_identity[0], runner_identity[1], 1.0)
        retention_error = None
        try:
            enforce_attempt_log_retention(store, attempt)
        except AgentctlJobError as exc:
            retention_error = str(exc)
        _mark_run_orphaned(store, attempt["job_id"], attempt["attempt_id"], reason)
        action = {
            "attempt_id": attempt["attempt_id"],
            "action": "orphaned",
            "reason": reason,
        }
        if retention_error is not None:
            action["retention_error"] = retention_error
        actions.append(action)
    return actions


def validate_succeeded_job(store: Store, job_id: str) -> dict[str, Any]:
    canonical = require_job_id(job_id)
    with workspace_lock(store.paths):
        job = get_job(store, canonical)
        if job["state"] != "succeeded":
            raise AgentctlJobError(f"job validation requires succeeded state, got {job['state']!r}")
        attempt = latest_attempt(store, canonical)
        if attempt is None or attempt["state"] != "succeeded":
            raise AgentctlJobError("latest attempt is not succeeded")
        _, schema = _result_schema(Path(attempt["workspace_path"]))
        try:
            verified = verify_result(job, attempt, schema, broker_final=True)
        except BaseException as exc:
            _mark_run_failure(
                store,
                canonical,
                attempt["attempt_id"],
                exit_code=attempt["exit_code"],
                exit_reason="post_validation",
                reason=str(exc),
            )
            raise
        validation_id = new_ulid()
        verified_at = utc_now()
        report_path = Path(attempt["result_path"]).with_name("validation.json")
        validation_report = {
            "schema_version": 1,
            "validation_id": validation_id,
            "profile": "job",
            "status": "passed",
            "job_id": canonical,
            "attempt_id": attempt["attempt_id"],
            "base_sha": job["base_sha"],
            "head_sha": verified["observed_git"]["head_sha"],
            "changed_paths": verified["observed_git"]["changed_paths"],
            "dirty_state": verified["observed_git"]["dirty_state"],
            "result_path": attempt["result_path"],
            "verified_at": verified_at,
        }
        write_json_private(report_path, validation_report)
        try:
            with store.transaction() as connection:
                transition_attempt(
                    connection,
                    canonical,
                    attempt["attempt_id"],
                    "validated",
                    reason="explicit post-run validation passed",
                )
                transition_job(
                    connection,
                    canonical,
                    "validated",
                    reason="explicit post-run validation passed",
                )
                connection.execute(
                    """
                    INSERT INTO validations(
                        validation_id, attempt_id, profile, status, target_sha,
                        report_path, finished_at, created_at
                    ) VALUES (?, ?, 'job', 'passed', NULL, ?, ?, ?)
                    """,
                    (
                        validation_id,
                        attempt["attempt_id"],
                        str(report_path),
                        verified_at,
                        verified_at,
                    ),
                )
        except BaseException:
            report_path.unlink(missing_ok=True)
            raise
    return {**show_job(store, canonical), "validation": validation_report}


def _dependency_order(store: Store, root_job_id: str) -> list[str]:
    order: list[str] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(job_id: str) -> None:
        if job_id in visited:
            return
        if job_id in visiting:
            raise AgentctlJobError(f"job dependency cycle detected at {job_id}")
        visiting.add(job_id)
        rows = store.connection.execute(
            "SELECT depends_on_job_id FROM job_dependencies "
            "WHERE job_id = ? ORDER BY depends_on_job_id",
            (job_id,),
        ).fetchall()
        for row in rows:
            visit(str(row["depends_on_job_id"]))
        visiting.remove(job_id)
        visited.add(job_id)
        order.append(job_id)

    visit(root_job_id)
    return order


def _target_dirty_paths(workspace: Path) -> list[str]:
    return sorted(
        set(_git_path_list(workspace, "diff", "--name-only", "-z"))
        | set(_git_path_list(workspace, "diff", "--cached", "--name-only", "-z"))
        | set(_git_path_list(workspace, "ls-files", "--others", "--exclude-standard", "-z"))
    )


def _patch_id_for_commit(workspace: Path, commit_sha: str) -> str | None:
    patch = git(
        workspace,
        "show",
        "--pretty=format:%H",
        "--no-ext-diff",
        "--full-index",
        "--patch",
        commit_sha,
    ).stdout
    result = run_command(["git", "patch-id", "--stable"], input_text=patch)
    first = result.stdout.splitlines()[0].split() if result.stdout.splitlines() else []
    return first[0] if first else None


def _patch_ids_for_range(workspace: Path, base_sha: str, target_sha: str) -> set[str]:
    patches = git(
        workspace,
        "log",
        "--pretty=format:%H",
        "--no-ext-diff",
        "--full-index",
        "--patch",
        f"{base_sha}..{target_sha}",
    ).stdout
    result = run_command(["git", "patch-id", "--stable"], input_text=patches)
    return {
        fields[0]
        for line in result.stdout.splitlines()
        if len(fields := line.split()) >= 1
    }


def collect_job(
    store: Store,
    job_id: str,
    *,
    target_revision: str | None = None,
) -> dict[str, Any]:
    """Create a read-only, immutable single-writer integration handoff report."""

    canonical = require_job_id(job_id)
    with workspace_lock(store.paths):
        root_job = get_job(store, canonical)
        if root_job["state"] != "validated":
            raise AgentctlJobError(
                f"job collection requires validated state, got {root_job['state']!r}"
            )
        project = get_project(store, root_job["project_id"])
        workspace = resolve_git_workspace(project["registered_path"])
        if str(git_common_dir(workspace)) != project["git_common_dir"]:
            raise AgentctlJobError(
                "registered project path no longer resolves to the recorded Git common directory"
            )
        target_expression = target_revision or "HEAD"
        target_sha = resolve_full_commit(workspace, target_expression)
        ordered_job_ids = _dependency_order(store, canonical)

        members: list[dict[str, Any]] = []
        candidates: list[dict[str, str]] = []
        blockers: list[dict[str, Any]] = []
        target_overlaps: list[dict[str, Any]] = []
        inter_job_overlaps: list[dict[str, Any]] = []
        observed_paths: list[tuple[str, set[str]]] = []
        seen_heads: set[str] = set()
        target_patch_ids: dict[str, set[str]] = {}

        for member_job_id in ordered_job_ids:
            member_job = get_job(store, member_job_id)
            if member_job["project_id"] != root_job["project_id"]:
                raise AgentctlJobError(
                    f"dependency belongs to another project: {member_job_id}"
                )
            if member_job["state"] != "validated":
                raise AgentctlJobError(
                    f"collection dependency is not validated: {member_job_id}:{member_job['state']}"
                )
            attempt = latest_attempt(store, member_job_id)
            if attempt is None or attempt["state"] != "validated":
                raise AgentctlJobError(
                    f"collection dependency has no validated latest attempt: {member_job_id}"
                )
            _, result_schema = _result_schema(Path(attempt["workspace_path"]))
            verified = verify_result(
                member_job,
                attempt,
                result_schema,
                broker_final=True,
            )
            result = verified["result"]
            observed = verified["observed_git"]
            head_sha = str(observed["head_sha"])
            changed_paths = list(observed["changed_paths"])
            base_sha = str(member_job["base_sha"])
            commit_count = int(
                git(
                    Path(attempt["workspace_path"]),
                    "rev-list",
                    "--count",
                    f"{base_sha}..{head_sha}",
                ).stdout.strip()
                or "0"
            )
            target_descends_base = (
                git(
                    workspace,
                    "merge-base",
                    "--is-ancestor",
                    base_sha,
                    target_sha,
                    check=False,
                ).returncode
                == 0
            )
            ancestor_integrated = (
                git(
                    workspace,
                    "merge-base",
                    "--is-ancestor",
                    head_sha,
                    target_sha,
                    check=False,
                ).returncode
                == 0
            )
            patch_id = _patch_id_for_commit(workspace, head_sha) if commit_count == 1 else None
            if target_descends_base and base_sha not in target_patch_ids:
                target_patch_ids[base_sha] = _patch_ids_for_range(
                    workspace, base_sha, target_sha
                )
            patch_integrated = bool(
                patch_id
                and target_descends_base
                and patch_id in target_patch_ids.get(base_sha, set())
            )
            already_integrated = ancestor_integrated or patch_integrated
            integration_match = (
                "ancestor"
                if ancestor_integrated
                else "patch_id"
                if patch_integrated
                else None
            )
            target_changed_paths = (
                set(_git_path_list(workspace, "diff", "--name-only", "-z", f"{base_sha}..{target_sha}"))
                if target_descends_base
                else set()
            )
            overlap = sorted(set(changed_paths) & target_changed_paths)
            if overlap and not already_integrated:
                target_overlaps.append(
                    {"job_id": member_job_id, "paths": overlap}
                )

            for prior_job_id, prior_paths in observed_paths:
                shared = sorted(set(changed_paths) & prior_paths)
                if shared:
                    inter_job_overlaps.append(
                        {
                            "earlier_job_id": prior_job_id,
                            "later_job_id": member_job_id,
                            "paths": shared,
                        }
                    )
            observed_paths.append((member_job_id, set(changed_paths)))

            has_collectible_commit = (
                member_job["lane"] == "write"
                and head_sha != base_sha
                and bool(changed_paths)
            )
            if has_collectible_commit and commit_count != 1:
                blockers.append(
                    {
                        "kind": "unexpected_commit_count",
                        "job_id": member_job_id,
                        "expected": 1,
                        "observed": commit_count,
                    }
                )
            if has_collectible_commit and not already_integrated and not target_descends_base:
                blockers.append(
                    {
                        "kind": "target_not_descendant_of_job_base",
                        "job_id": member_job_id,
                        "base_sha": base_sha,
                        "target_sha": target_sha,
                    }
                )
            if has_collectible_commit and not already_integrated and head_sha not in seen_heads:
                candidates.append({"job_id": member_job_id, "head_sha": head_sha})
                seen_heads.add(head_sha)

            members.append(
                {
                    "job_id": member_job_id,
                    "attempt_id": attempt["attempt_id"],
                    "role": member_job["role"],
                    "lane": member_job["lane"],
                    "provider": attempt["provider"],
                    "base_sha": base_sha,
                    "head_sha": head_sha,
                    "commit_count": commit_count,
                    "patch_id": patch_id,
                    "already_integrated": already_integrated,
                    "integration_match": integration_match,
                    "changed_paths": changed_paths,
                    "summary": result["summary"],
                    "checks": result["checks"],
                    "risks": result["risks"],
                    "followups": result["followups"],
                    "result_path": attempt["result_path"],
                }
            )

        if blockers:
            status = "blocked"
            assessment = "structural_blocker"
        elif not candidates:
            status = "ready"
            assessment = "already_integrated_or_no_change"
        elif target_overlaps or inter_job_overlaps:
            status = "ready"
            assessment = "review_required"
        else:
            status = "ready"
            assessment = "clean_candidate"

        root_attempt = latest_attempt(store, canonical)
        assert root_attempt is not None
        collection_id = new_ulid()
        collected_at = utc_now()
        report_path = (
            Path(root_attempt["result_path"]).parent
            / "collections"
            / f"{collection_id}.json"
        )
        report = {
            "schema_version": 1,
            "collection_id": collection_id,
            "status": status,
            "integration_assessment": assessment,
            "decision_owner": "primary",
            "automatic_integration_performed": False,
            "root_job_id": canonical,
            "project_id": root_job["project_id"],
            "target_revision": target_expression,
            "target_sha": target_sha,
            "target_dirty_paths": _target_dirty_paths(workspace),
            "dependency_order": ordered_job_ids,
            "candidate_commits": candidates,
            "members": members,
            "target_path_overlaps": target_overlaps,
            "inter_job_path_overlaps": inter_job_overlaps,
            "blockers": blockers,
            "report_path": str(report_path),
            "collected_at": collected_at,
        }
        write_json_private(report_path, report)
        try:
            with store.transaction() as connection:
                connection.execute(
                    """
                    INSERT INTO validations(
                        validation_id, attempt_id, profile, status, target_sha,
                        report_path, finished_at, created_at
                    ) VALUES (?, ?, 'integration', ?, ?, ?, ?, ?)
                    """,
                    (
                        collection_id,
                        root_attempt["attempt_id"],
                        status,
                        target_sha,
                        str(report_path),
                        collected_at,
                        collected_at,
                    ),
                )
        except BaseException:
            report_path.unlink(missing_ok=True)
            raise
    return report


def _directory_bytes_no_follow(root: Path) -> int:
    if not root.exists():
        return 0
    total = 0
    for directory, directory_names, file_names in os.walk(root, followlinks=False):
        directory_path = Path(directory)
        directory_names[:] = [
            name for name in directory_names if not (directory_path / name).is_symlink()
        ]
        for name in file_names:
            path = directory_path / name
            try:
                if not path.is_symlink():
                    total += path.stat().st_size
            except OSError:
                continue
    return total


def _docker_project_inventory(project_name: str) -> dict[str, Any]:
    docker = os.environ.get("AGENTCTL_DOCKER_BIN") or shutil.which("docker")
    if not docker:
        return {"status": "unavailable", "error": "Docker CLI is unavailable"}
    commands = {
        "containers": ["ps", "-aq"],
        "networks": ["network", "ls", "-q"],
        "volumes": ["volume", "ls", "-q"],
    }
    resources: dict[str, list[str]] = {}
    label = f"com.docker.compose.project={project_name}"
    for kind, arguments in commands.items():
        try:
            result = run_command(
                [docker, *arguments, "--filter", f"label={label}"],
                check=False,
                timeout=DOCKER_INVENTORY_TIMEOUT_SECONDS,
            )
        except AgentctlJobError as exc:
            error, _ = _redact_log_text(str(exc)[-1000:])
            return {
                "status": "unavailable",
                "error": f"Docker {kind} inventory failed: {error}",
            }
        if result.returncode != 0:
            error, _ = _redact_log_text((result.stderr or result.stdout).strip()[-1000:])
            return {
                "status": "unavailable",
                "error": f"Docker {kind} inventory failed: {error}",
            }
        resources[kind] = sorted(line for line in result.stdout.splitlines() if line)
    return {
        "status": "available",
        "project_name": project_name,
        **resources,
        "residual_count": sum(len(values) for values in resources.values()),
    }


def _integration_proof(
    store: Store,
    job: dict[str, Any],
    attempt: dict[str, Any],
    registered_workspace: Path,
) -> dict[str, Any] | None:
    head_sha = attempt.get("head_sha")
    if not head_sha or head_sha == job["base_sha"]:
        return {"kind": "no_change", "head_sha": head_sha or job["base_sha"]}
    registered_head = resolve_full_commit(registered_workspace, "HEAD")
    rows = store.connection.execute(
        """
        SELECT validations.* FROM validations
        JOIN attempts ON attempts.attempt_id = validations.attempt_id
        JOIN jobs ON jobs.job_id = attempts.job_id
        WHERE jobs.project_id = ? AND validations.profile = 'integration'
        ORDER BY validations.created_at DESC, validations.validation_id DESC
        """,
        (job["project_id"],),
    ).fetchall()
    for row in rows:
        report_path = Path(row["report_path"]).resolve()
        if not _inside(report_path, store.paths.root) or not report_path.is_file():
            continue
        try:
            report = load_json(report_path)
        except (OSError, json.JSONDecodeError, ContractValidationError):
            continue
        if not isinstance(report, dict):
            continue
        member = next(
            (
                entry
                for entry in report.get("members", [])
                if isinstance(entry, dict)
                and entry.get("job_id") == job["job_id"]
                and entry.get("head_sha") == head_sha
                and entry.get("already_integrated") is True
            ),
            None,
        )
        target_sha = report.get("target_sha")
        if member is None or not isinstance(target_sha, str):
            continue
        target_still_reachable = (
            git(
                registered_workspace,
                "merge-base",
                "--is-ancestor",
                target_sha,
                registered_head,
                check=False,
            ).returncode
            == 0
        )
        if not target_still_reachable:
            continue
        integration_match = member.get("integration_match")
        if integration_match == "ancestor":
            proof_valid = (
                git(
                    registered_workspace,
                    "merge-base",
                    "--is-ancestor",
                    str(head_sha),
                    target_sha,
                    check=False,
                ).returncode
                == 0
            )
        elif integration_match == "patch_id":
            target_descends_base = (
                git(
                    registered_workspace,
                    "merge-base",
                    "--is-ancestor",
                    str(job["base_sha"]),
                    target_sha,
                    check=False,
                ).returncode
                == 0
            )
            patch_id = _patch_id_for_commit(registered_workspace, str(head_sha))
            proof_valid = bool(
                target_descends_base
                and patch_id
                and patch_id
                in _patch_ids_for_range(
                    registered_workspace, str(job["base_sha"]), target_sha
                )
            )
        else:
            proof_valid = False
        if proof_valid:
            return {
                "kind": "collection",
                "collection_id": report.get("collection_id"),
                "target_sha": target_sha,
                "registered_head": registered_head,
                "integration_match": integration_match,
            }
    return None


def gc_inventory(store: Store, *, job_id: str | None = None) -> dict[str, Any]:
    """Return conservative GC candidates. This function never deletes state."""

    canonical = require_job_id(job_id) if job_id is not None else None
    if canonical is not None:
        get_job(store, canonical)
    rows = store.connection.execute(
        "SELECT * FROM jobs "
        + ("WHERE job_id = ? " if canonical is not None else "")
        + "ORDER BY created_at, job_id",
        (canonical,) if canonical is not None else (),
    ).fetchall()
    jobs: list[dict[str, Any]] = []
    for raw_job in rows:
        job = dict(raw_job)
        project = get_project(store, job["project_id"])
        reasons: list[dict[str, Any]] = []
        registered_workspace: Path | None = None
        try:
            registered_workspace = resolve_git_workspace(project["registered_path"])
            if str(git_common_dir(registered_workspace)) != project["git_common_dir"]:
                raise AgentctlJobError(
                    "registered workspace no longer matches the recorded Git common directory"
                )
        except AgentctlJobError as exc:
            reasons.append(
                {"kind": "registered_workspace_unavailable", "error": str(exc)}
            )
        attempts = [
            dict(row)
            for row in store.connection.execute(
                "SELECT * FROM attempts WHERE job_id = ? ORDER BY number",
                (job["job_id"],),
            ).fetchall()
        ]
        attempt_inventory: list[dict[str, Any]] = []
        candidate_actions: list[dict[str, Any]] = []

        if job["state"] != "validated":
            reasons.append({"kind": "job_not_validated", "state": job["state"]})
        if not attempts:
            reasons.append({"kind": "no_attempt_evidence"})

        for attempt in attempts:
            attempt_reasons: list[dict[str, Any]] = []
            if attempt["state"] not in ATTEMPT_TRANSITIONS or ATTEMPT_TRANSITIONS[attempt["state"]]:
                attempt_reasons.append(
                    {"kind": "attempt_not_terminal", "state": attempt["state"]}
                )
            provider_alive = process_identity_matches(
                attempt["pid"], attempt["process_started_at"]
            )
            runner_identity = _runtime_process(attempt["runtime_id"])
            runner_alive = bool(
                runner_identity
                and process_identity_matches(runner_identity[0], runner_identity[1])
            )
            if provider_alive or runner_alive:
                attempt_reasons.append(
                    {
                        "kind": "live_process",
                        "provider_alive": provider_alive,
                        "runner_alive": runner_alive,
                    }
                )

            leases = [
                dict(row)
                for row in store.connection.execute(
                    "SELECT * FROM leases WHERE attempt_id = ? ORDER BY acquired_at",
                    (attempt["attempt_id"],),
                ).fetchall()
            ]
            active_runtime = [
                lease
                for lease in leases
                if lease["released_at"] is None and lease["kind"] in RUNTIME_LEASE_KINDS
            ]
            if active_runtime:
                attempt_reasons.append(
                    {
                        "kind": "active_runtime_lease",
                        "leases": [lease["lease_id"] for lease in active_runtime],
                    }
                )

            worktree_path = Path(attempt["workspace_path"]).resolve()
            worktree_candidate = None
            dirty_paths: list[str] | None = None
            if job["lane"] == "write":
                expected_worktree = store.paths.worktree_dir(
                    job["project_id"], job["job_id"], int(attempt["number"])
                ).resolve()
                expected_branch = _attempt_branch(job["job_id"], int(attempt["number"]))
                if worktree_path != expected_worktree:
                    attempt_reasons.append(
                        {
                            "kind": "worktree_path_mismatch",
                            "expected": str(expected_worktree),
                            "observed": str(worktree_path),
                        }
                    )
                elif attempt["branch_name"] != expected_branch:
                    attempt_reasons.append(
                        {
                            "kind": "branch_name_mismatch",
                            "expected": expected_branch,
                            "observed": attempt["branch_name"],
                        }
                    )
                elif not worktree_path.is_dir():
                    attempt_reasons.append({"kind": "worktree_missing"})
                else:
                    try:
                        resolved_worktree = resolve_git_workspace(worktree_path)
                        if resolved_worktree != worktree_path:
                            raise AgentctlJobError(
                                "worktree path does not resolve to its own Git top level"
                            )
                        if str(git_common_dir(worktree_path)) != project["git_common_dir"]:
                            raise AgentctlJobError(
                                "worktree Git common directory differs from the registered project"
                            )
                        current_branch = git(
                            worktree_path, "symbolic-ref", "--quiet", "--short", "HEAD"
                        ).stdout.strip()
                        if current_branch != expected_branch:
                            raise AgentctlJobError(
                                f"worktree branch differs from recorded ownership: {current_branch!r}"
                            )
                        if attempt["head_sha"]:
                            current_head = resolve_full_commit(worktree_path, "HEAD")
                            if current_head != attempt["head_sha"]:
                                raise AgentctlJobError(
                                    "worktree HEAD differs from the validated attempt head"
                                )
                        dirty_paths = _target_dirty_paths(worktree_path)
                    except AgentctlJobError as exc:
                        attempt_reasons.append(
                            {"kind": "worktree_identity_unverified", "error": str(exc)}
                        )
                    if dirty_paths:
                        attempt_reasons.append(
                            {"kind": "worktree_dirty", "paths": dirty_paths}
                        )
                    if not attempt_reasons:
                        worktree_candidate = str(worktree_path)

            attempt_evidence_root = store.paths.attempt_dir(
                job["project_id"], job["job_id"], int(attempt["number"])
            ).resolve()
            expected_evidence_paths = {
                "process_log": (attempt_evidence_root / "process.log").resolve(),
                "result": (attempt_evidence_root / "result.json").resolve(),
                "log_retention": (attempt_evidence_root / "log-retention.json").resolve(),
            }
            evidence_paths = {
                "process_log": Path(attempt["log_path"]).resolve(),
                "result": Path(attempt["result_path"]).resolve(),
                "log_retention": (attempt_evidence_root / "log-retention.json").resolve(),
            }
            mismatched_evidence = [
                {
                    "name": name,
                    "expected": str(expected_evidence_paths[name]),
                    "observed": str(path),
                }
                for name, path in evidence_paths.items()
                if path != expected_evidence_paths[name]
            ]
            if mismatched_evidence:
                attempt_reasons.append(
                    {"kind": "evidence_path_mismatch", "paths": mismatched_evidence}
                )
            escaped_evidence = [
                str(path)
                for path in evidence_paths.values()
                if not _inside(path, attempt_evidence_root)
            ]
            if escaped_evidence:
                attempt_reasons.append(
                    {"kind": "evidence_path_outside_attempt", "paths": escaped_evidence}
                )
            missing_evidence = [
                str(path)
                for path in expected_evidence_paths.values()
                if _inside(path, attempt_evidence_root) and not path.is_file()
            ]
            if missing_evidence:
                attempt_reasons.append(
                    {"kind": "missing_evidence", "paths": missing_evidence}
                )

            attempt_inventory.append(
                {
                    "attempt_id": attempt["attempt_id"],
                    "number": attempt["number"],
                    "state": attempt["state"],
                    "workspace_path": str(worktree_path),
                    "branch_name": attempt["branch_name"],
                    "head_sha": attempt["head_sha"],
                    "dirty_paths": dirty_paths,
                    "provider_alive": provider_alive,
                    "runner_alive": runner_alive,
                    "leases": leases,
                    "reasons": attempt_reasons,
                }
            )
            reasons.extend(
                {**reason, "attempt_id": attempt["attempt_id"]}
                for reason in attempt_reasons
            )
            if worktree_candidate:
                candidate_actions.append(
                    {
                        "kind": "remove_worktree",
                        "attempt_id": attempt["attempt_id"],
                        "path": worktree_candidate,
                    }
                )
            if attempt["branch_name"]:
                candidate_actions.append(
                    {
                        "kind": "delete_branch",
                        "attempt_id": attempt["attempt_id"],
                        "branch": attempt["branch_name"],
                    }
                )
            for lease in leases:
                if lease["released_at"] is None and lease["kind"] in {"worktree", "branch"}:
                    candidate_actions.append(
                        {
                            "kind": "release_lease",
                            "attempt_id": attempt["attempt_id"],
                            "lease_id": lease["lease_id"],
                            "lease_kind": lease["kind"],
                            "value": lease["value"],
                        }
                    )

        latest = attempts[-1] if attempts else None
        integration_proof = None
        if (
            latest is not None
            and job["state"] == "validated"
            and registered_workspace is not None
        ):
            try:
                integration_proof = _integration_proof(
                    store, job, latest, registered_workspace
                )
            except AgentctlJobError as exc:
                reasons.append(
                    {"kind": "integration_proof_unreadable", "error": str(exc)}
                )
            if integration_proof is None:
                reasons.append(
                    {
                        "kind": "job_commit_not_integrated_in_registered_head",
                        "head_sha": latest["head_sha"],
                    }
                )

        docker_inventory = None
        if job["resource_class"] == "integration":
            docker_inventory = _docker_project_inventory(
                "agent_" + job["job_id"].lower()
            )
            if docker_inventory["status"] != "available":
                reasons.append(
                    {
                        "kind": "docker_ownership_unverified",
                        "error": docker_inventory.get("error"),
                    }
                )
            elif docker_inventory["residual_count"]:
                reasons.append(
                    {
                        "kind": "docker_resources_remain",
                        "count": docker_inventory["residual_count"],
                    }
                )

        eligible = not reasons
        if not eligible:
            candidate_actions = []
        job_dir = store.paths.job_dir(job["project_id"], job["job_id"])
        jobs.append(
            {
                "job_id": job["job_id"],
                "state": job["state"],
                "resource_class": job["resource_class"],
                "eligible": eligible,
                "reasons": reasons,
                "integration_proof": integration_proof,
                "docker": docker_inventory,
                "attempts": attempt_inventory,
                "candidate_actions": candidate_actions,
                "evidence_bytes": _directory_bytes_no_follow(job_dir),
                "evidence_policy": "retain",
            }
        )

    return {
        "schema_version": 1,
        "generated_at": utc_now(),
        "destructive": False,
        "dry_run": True,
        "state_root": str(store.paths.root),
        "summary": {
            "jobs": len(jobs),
            "eligible": sum(1 for job in jobs if job["eligible"]),
            "blocked": sum(1 for job in jobs if not job["eligible"]),
            "evidence_bytes": sum(int(job["evidence_bytes"]) for job in jobs),
        },
        "jobs": jobs,
    }
