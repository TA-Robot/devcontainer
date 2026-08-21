#!/usr/bin/env python3
"""Small local supervisor for detached agentctl attempts.

The supervisor owns process dispatch and recovery only. Planning, provider
conversation state, and task decomposition deliberately remain outside it.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import signal
import socket
import stat
import struct
import subprocess
import sys
import time
from typing import Any

from agentctl_jobs import (
    AgentctlJobError,
    StatePaths,
    Store,
    capacity_limits,
    capacity_snapshot,
    cancel_job,
    get_job,
    mark_detached_launch_failure,
    prepare_attempt,
    process_identity_matches,
    reconcile_attempts,
    record_detached_runner,
    show_job,
    waiting_jobs,
    write_json_private,
    _process_start_marker,
)


PROTOCOL_VERSION = 2
MAX_REQUEST_BYTES = 1024 * 1024


def supervisor_socket(paths: StatePaths) -> Path:
    path = paths.root / "agentd.sock"
    if len(os.fsencode(path)) >= 104:
        raise AgentctlJobError(
            f"agentctl state path is too long for a Unix socket: {path}"
        )
    return path


def supervisor_pid_file(paths: StatePaths) -> Path:
    return paths.root / "agentd.json"


def supervisor_log_file(paths: StatePaths) -> Path:
    return paths.root / "agentd.log"


def _read_response(connection: socket.socket) -> dict[str, Any]:
    chunks: list[bytes] = []
    size = 0
    while True:
        chunk = connection.recv(65536)
        if not chunk:
            break
        size += len(chunk)
        if size > MAX_REQUEST_BYTES:
            raise AgentctlJobError("supervisor response exceeds protocol limit")
        chunks.append(chunk)
        if b"\n" in chunk:
            break
    raw = b"".join(chunks).split(b"\n", 1)[0]
    try:
        response = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AgentctlJobError("supervisor returned an invalid response") from exc
    if not isinstance(response, dict):
        raise AgentctlJobError("supervisor response root is not an object")
    return response


def supervisor_request(
    paths: StatePaths,
    payload: dict[str, Any],
    *,
    timeout: float = 15.0,
) -> dict[str, Any]:
    request = {"protocol_version": PROTOCOL_VERSION, **payload}
    encoded = json.dumps(request, separators=(",", ":"), sort_keys=True).encode("utf-8") + b"\n"
    if len(encoded) > MAX_REQUEST_BYTES:
        raise AgentctlJobError("supervisor request exceeds protocol limit")
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
            connection.settimeout(timeout)
            connection.connect(str(supervisor_socket(paths)))
            connection.sendall(encoded)
            connection.shutdown(socket.SHUT_WR)
            response = _read_response(connection)
    except (OSError, socket.timeout) as exc:
        raise AgentctlJobError(f"cannot reach local agentctl supervisor: {exc}") from exc
    if response.get("protocol_version") != PROTOCOL_VERSION:
        raise AgentctlJobError("supervisor protocol version mismatch")
    if response.get("ok") is not True:
        raise AgentctlJobError(str(response.get("error") or "supervisor request failed"))
    return response


def _read_pid_identity(paths: StatePaths) -> tuple[int, str] | None:
    try:
        payload = json.loads(supervisor_pid_file(paths).read_text(encoding="utf-8"))
        return int(payload["pid"]), str(payload["process_started_at"])
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        return None


def _remove_stale_socket(paths: StatePaths) -> None:
    path = supervisor_socket(paths)
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return
    if not stat.S_ISSOCK(metadata.st_mode):
        raise AgentctlJobError(f"refusing to replace non-socket supervisor path: {path}")
    if metadata.st_uid != os.getuid():
        raise AgentctlJobError(f"supervisor socket is not owned by the current user: {path}")
    path.unlink()


def _try_ping(paths: StatePaths) -> dict[str, Any] | None:
    try:
        return supervisor_request(paths, {"command": "ping"}, timeout=0.5)
    except AgentctlJobError:
        return None


def ensure_supervisor(paths: StatePaths, entrypoint: Path) -> dict[str, Any]:
    current = _try_ping(paths)
    if current is not None:
        return current

    lock_path = paths.root / "locks" / "supervisor-start.lock"
    descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        import fcntl

        fcntl.flock(descriptor, fcntl.LOCK_EX)
        current = _try_ping(paths)
        if current is not None:
            return current
        identity = _read_pid_identity(paths)
        if identity is not None and process_identity_matches(*identity):
            raise AgentctlJobError(
                "agentctl supervisor process is alive but its socket is unresponsive or uses an "
                "incompatible protocol; stop it with the matching CLI or rebuild the container"
            )
        _remove_stale_socket(paths)
        supervisor_pid_file(paths).unlink(missing_ok=True)

        log_descriptor = os.open(
            supervisor_log_file(paths),
            os.O_WRONLY | os.O_CREAT | os.O_APPEND,
            0o600,
        )
        with os.fdopen(log_descriptor, "a", encoding="utf-8") as output:
            subprocess.Popen(
                [
                    sys.executable,
                    str(entrypoint),
                    "--state-dir",
                    str(paths.root),
                    "_supervisor",
                    "serve",
                ],
                stdin=subprocess.DEVNULL,
                stdout=output,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                close_fds=True,
                env=os.environ.copy(),
            )

        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline:
            current = _try_ping(paths)
            if current is not None:
                return current
            time.sleep(0.05)
        raise AgentctlJobError(
            f"local supervisor did not become ready; inspect {supervisor_log_file(paths)}"
        )
    finally:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        except (NameError, OSError):
            pass
        os.close(descriptor)


class Supervisor:
    def __init__(self, paths: StatePaths, entrypoint: Path):
        self.paths = paths
        self.entrypoint = entrypoint.resolve()
        self.stopping = False
        self.children: dict[int, subprocess.Popen[str]] = {}
        # Dispatch environments can contain provider credentials. Keep them in
        # memory only; the durable DB queue intentionally stores no secrets.
        self.pending_submissions: dict[str, dict[str, Any]] = {}
        capacity_limits()
        raw_threshold = os.environ.get("AGENTCTL_ORPHAN_AFTER_SECONDS", "30")
        try:
            self.orphan_after_seconds = float(raw_threshold)
        except ValueError as exc:
            raise AgentctlJobError(
                f"invalid AGENTCTL_ORPHAN_AFTER_SECONDS: {raw_threshold!r}"
            ) from exc
        if self.orphan_after_seconds < 0.1:
            raise AgentctlJobError("AGENTCTL_ORPHAN_AFTER_SECONDS must be at least 0.1")
        self.reconcile_interval = min(5.0, max(0.1, self.orphan_after_seconds / 2))
        self.last_reconcile = 0.0

    def _peer_is_owner(self, connection: socket.socket) -> bool:
        if not hasattr(socket, "SO_PEERCRED"):
            return False
        credentials = connection.getsockopt(
            socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize("3i")
        )
        _pid, uid, _gid = struct.unpack("3i", credentials)
        return uid == os.getuid()

    def _read_request(self, connection: socket.socket) -> dict[str, Any]:
        chunks: list[bytes] = []
        size = 0
        while True:
            chunk = connection.recv(65536)
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_REQUEST_BYTES:
                raise AgentctlJobError("supervisor request exceeds protocol limit")
            chunks.append(chunk)
            if b"\n" in chunk:
                break
        raw = b"".join(chunks).split(b"\n", 1)[0]
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise AgentctlJobError("invalid supervisor JSON request") from exc
        if not isinstance(payload, dict):
            raise AgentctlJobError("supervisor request root is not an object")
        if payload.get("protocol_version") != PROTOCOL_VERSION:
            raise AgentctlJobError("unsupported supervisor protocol version")
        return payload

    def _reply(self, connection: socket.socket, payload: dict[str, Any]) -> None:
        response = {"protocol_version": PROTOCOL_VERSION, **payload}
        connection.sendall(
            json.dumps(response, separators=(",", ":"), sort_keys=True).encode("utf-8") + b"\n"
        )

    def _spawn_runner(
        self,
        store: Store,
        attempt: dict[str, Any],
        *,
        allow_trusted_fast: bool,
        environment: dict[str, str],
    ) -> dict[str, Any]:
        runner_log = Path(attempt["log_path"]).with_name("runner.log")
        log_descriptor = os.open(runner_log, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        argv = [
            sys.executable,
            str(self.entrypoint),
            "--state-dir",
            str(self.paths.root),
            "_runner",
            attempt["attempt_id"],
        ]
        if allow_trusted_fast:
            argv.append("--allow-trusted-fast")
        runner_environment = dict(environment)
        runner_environment["AGENTCTL_STATE_DIR"] = str(self.paths.root)
        process: subprocess.Popen[str] | None = None
        try:
            with os.fdopen(log_descriptor, "w", encoding="utf-8") as output:
                process = subprocess.Popen(
                    argv,
                    stdin=subprocess.PIPE,
                    stdout=output,
                    stderr=subprocess.STDOUT,
                    text=True,
                    start_new_session=True,
                    close_fds=True,
                    env=runner_environment,
                )
            marker = _process_start_marker(process.pid)
            runtime_id = record_detached_runner(store, attempt["attempt_id"], process.pid, marker)
            if process.stdin is None:
                raise AgentctlJobError("detached runner control pipe is unavailable")
            process.stdin.write("go\n")
            process.stdin.close()
            process.stdin = None
            self.children[process.pid] = process
            return {
                "job_id": attempt["job_id"],
                "attempt_id": attempt["attempt_id"],
                "attempt_number": attempt["number"],
                "runtime_id": runtime_id,
                "state": "accepted",
            }
        except BaseException as exc:
            if process is not None and process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            mark_detached_launch_failure(store, attempt["attempt_id"], str(exc))
            raise

    def _queued_result(self, store: Store, job_id: str) -> dict[str, Any]:
        job = show_job(store, job_id)
        return {
            "job_id": job["job_id"],
            "state": "waiting_capacity",
            "resource_class": job["resource_class"],
            "priority": job["priority"],
            "queue": job["queue"],
            "dispatch_envelope": "resident",
        }

    def _drain_queue(self) -> list[dict[str, Any]]:
        promotions: list[dict[str, Any]] = []
        with Store(self.paths) as store:
            for job in waiting_jobs(store):
                job_id = str(job["job_id"])
                submission = self.pending_submissions.get(job_id)
                if submission is None:
                    continue
                try:
                    attempt = prepare_attempt(
                        store,
                        job_id,
                        str(submission["provider"]),
                        queue_if_full=True,
                        from_queue=True,
                    )
                    if attempt is None:
                        continue
                    self.pending_submissions.pop(job_id, None)
                    result = self._spawn_runner(
                        store,
                        attempt,
                        allow_trusted_fast=bool(submission["allow_trusted_fast"]),
                        environment=dict(submission["environment"]),
                    )
                    promotions.append(result)
                except BaseException as exc:
                    self.pending_submissions.pop(job_id, None)
                    promotions.append(
                        {"job_id": job_id, "state": "dispatch_failed", "error": str(exc)}
                    )
                    print(
                        f"agentctl supervisor: queued dispatch failed for {job_id}: {exc}",
                        file=sys.stderr,
                        flush=True,
                    )
        return promotions

    def _dispatch(self, request: dict[str, Any]) -> dict[str, Any]:
        command = request.get("command")
        if command == "ping":
            with Store(self.paths) as store:
                capacity = capacity_snapshot(store)
                queued = waiting_jobs(store)
            return {
                "ok": True,
                "result": {
                    "protocol_version": PROTOCOL_VERSION,
                    "pid": os.getpid(),
                    "process_started_at": _process_start_marker(os.getpid()),
                    "socket": str(supervisor_socket(self.paths)),
                    "capacity": capacity,
                    "queued_jobs": len(queued),
                    "dispatch_envelopes": len(self.pending_submissions),
                    "awaiting_resubmit": [
                        job["job_id"]
                        for job in queued
                        if job["job_id"] not in self.pending_submissions
                    ],
                },
            }
        if command == "submit":
            job_id = request.get("job_id")
            provider = request.get("provider")
            if not isinstance(job_id, str) or provider not in {"codex", "claude"}:
                raise AgentctlJobError("submit requires a job_id and supported provider")
            clean_retry = request.get("clean_retry") is True
            allow_trusted_fast = request.get("allow_trusted_fast") is True
            environment = request.get("environment")
            if not isinstance(environment, dict) or not all(
                isinstance(key, str) and isinstance(value, str)
                for key, value in environment.items()
            ):
                raise AgentctlJobError("submit requires a string-to-string process environment")
            with Store(self.paths) as store:
                job = get_job(store, job_id)
                if job["permission_profile"] == "trusted-fast" and not allow_trusted_fast:
                    raise AgentctlJobError(
                        "task requests trusted-fast; dispatch requires explicit --allow-trusted-fast"
                    )
                from_queue = job["state"] == "waiting_capacity"
                attempt = prepare_attempt(
                    store,
                    job_id,
                    provider,
                    clean_retry=clean_retry,
                    queue_if_full=True,
                    from_queue=from_queue,
                )
                if attempt is None:
                    self.pending_submissions[job["job_id"]] = {
                        "provider": provider,
                        "allow_trusted_fast": allow_trusted_fast,
                        "environment": dict(environment),
                    }
                    result = self._queued_result(store, job["job_id"])
                else:
                    self.pending_submissions.pop(job["job_id"], None)
                    result = self._spawn_runner(
                        store,
                        attempt,
                        allow_trusted_fast=allow_trusted_fast,
                        environment=environment,
                    )
            return {"ok": True, "result": result}
        if command == "cancel":
            job_id = request.get("job_id")
            if not isinstance(job_id, str):
                raise AgentctlJobError("cancel requires a job_id")
            with Store(self.paths) as store:
                result = cancel_job(store, job_id)
            self.pending_submissions.pop(result["job_id"], None)
            self._drain_queue()
            return {"ok": True, "result": result}
        if command == "reconcile":
            with Store(self.paths) as store:
                actions = reconcile_attempts(
                    store, orphan_after_seconds=self.orphan_after_seconds
                )
            promotions = self._drain_queue()
            return {
                "ok": True,
                "result": {"actions": actions, "promotions": promotions},
            }
        if command == "stop":
            self.stopping = True
            return {"ok": True, "result": {"stopping": True}}
        raise AgentctlJobError(f"unknown supervisor command: {command!r}")

    def _reap_children(self) -> None:
        for pid, process in list(self.children.items()):
            if process.poll() is not None:
                self.children.pop(pid, None)

    def _periodic_reconcile(self) -> None:
        now = time.monotonic()
        if now - self.last_reconcile < self.reconcile_interval:
            return
        self.last_reconcile = now
        with Store(self.paths) as store:
            reconcile_attempts(store, orphan_after_seconds=self.orphan_after_seconds)
        self._drain_queue()

    def serve(self) -> int:
        socket_path = supervisor_socket(self.paths)
        recorded = _read_pid_identity(self.paths)
        if (
            recorded is not None
            and recorded[0] != os.getpid()
            and process_identity_matches(*recorded)
        ):
            raise AgentctlJobError("another agentctl supervisor already owns this state directory")
        _remove_stale_socket(self.paths)
        previous_umask = os.umask(0o077)
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            server.bind(str(socket_path))
        finally:
            os.umask(previous_umask)
        socket_path.chmod(0o600)
        server.listen(16)
        server.settimeout(0.5)
        marker = _process_start_marker(os.getpid())
        if marker == "unknown":
            server.close()
            socket_path.unlink(missing_ok=True)
            raise AgentctlJobError("supervisor process identity cannot be recorded")
        write_json_private(
            supervisor_pid_file(self.paths),
            {"pid": os.getpid(), "process_started_at": marker},
        )

        def request_stop(_signum: int, _frame: Any) -> None:
            self.stopping = True

        signal.signal(signal.SIGTERM, request_stop)
        signal.signal(signal.SIGINT, request_stop)
        try:
            self._periodic_reconcile()
            while not self.stopping:
                self._reap_children()
                self._periodic_reconcile()
                try:
                    connection, _ = server.accept()
                except socket.timeout:
                    continue
                with connection:
                    try:
                        if not self._peer_is_owner(connection):
                            raise AgentctlJobError("supervisor client UID does not match owner")
                        response = self._dispatch(self._read_request(connection))
                    except BaseException as exc:
                        response = {"ok": False, "error": str(exc)}
                    try:
                        self._reply(connection, response)
                    except OSError:
                        pass
        finally:
            server.close()
            try:
                metadata = socket_path.lstat()
                if stat.S_ISSOCK(metadata.st_mode) and metadata.st_uid == os.getuid():
                    socket_path.unlink()
            except FileNotFoundError:
                pass
            supervisor_pid_file(self.paths).unlink(missing_ok=True)
        return 0


def serve_supervisor(paths: StatePaths, entrypoint: Path) -> int:
    return Supervisor(paths, entrypoint).serve()
