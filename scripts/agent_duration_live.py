#!/usr/bin/env python3
"""Finite isolated live-provider runners for duration-study calibration."""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import re
import resource
import shutil
import stat
import subprocess
import tempfile
import time
from typing import Any
from datetime import datetime, timezone

from agent_contracts import load_json
from agent_duration_fixtures import DEFAULT_CATALOG, build_fixture, evaluate_fixture_isolated
from agent_duration_study import (
    DurationStudyError,
    EventClock,
    ROOT,
    RunRecorder,
    SystemClock,
    atomic_write_json,
    canonical_json_digest,
    content_digest,
    event,
    validate_case_catalog_record,
    validate_fixture_record,
)


CODEX_PROFILE = (
    ROOT
    / "experiments"
    / "multi-agent-duration"
    / "provider-profiles"
    / "codex-primary-only.toml"
)
SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
MODEL_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
EFFORTS = {"low", "medium", "high", "xhigh", "max", "ultra"}
RECORD_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
SEMVER = re.compile(r"(?<![0-9])([0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?)")
CODEX_SANDBOX_PROBE_SCRIPT = """from pathlib import Path
import socket

secret = Path("/agent-home/.codex/sandbox-secret.txt")
probe = Path("/case/.duration-sandbox-probe")
try:
    secret.read_bytes()
except OSError:
    pass
else:
    raise SystemExit(41)

probe.write_text("ok", encoding="utf-8")
probe.unlink()

sock = None
try:
    sock = socket.socket()
    sock.settimeout(0.2)
    sock.connect(("1.1.1.1", 53))
except OSError:
    pass
else:
    raise SystemExit(42)
finally:
    if sock is not None:
        sock.close()
"""


def _load_fixture_manifest(fixture_dir: Path) -> dict[str, Any]:
    value = load_json(fixture_dir / "fixture.json")
    if not isinstance(value, dict):
        raise DurationStudyError("fixture manifest root must be an object")
    validate_fixture_record(value)
    return value


def _load_catalog() -> dict[str, Any]:
    value = load_json(DEFAULT_CATALOG)
    if not isinstance(value, dict):
        raise DurationStudyError("case catalog root must be an object")
    validate_case_catalog_record(value)
    return value


def _catalog_entry_for_fixture(manifest: dict[str, Any]) -> dict[str, Any]:
    catalog = _load_catalog()
    if manifest["case"]["catalog_digest"] != canonical_json_digest(catalog):
        raise DurationStudyError("fixture catalog digest is stale")
    case_id = manifest["case"]["case_id"]
    entries = [entry for entry in catalog["entries"] if entry["case"]["case_id"] == case_id]
    if len(entries) != 1:
        raise DurationStudyError(f"catalog does not contain exactly one {case_id!r} entry")
    return entries[0]


def _capsule_for_fixture(manifest: dict[str, Any]) -> bytes:
    entry = _catalog_entry_for_fixture(manifest)
    capsule_path = (ROOT / entry["fixture"]["capsule_path"]).resolve()
    capsule = capsule_path.read_bytes()
    if len(capsule) > 64 * 1024:
        raise DurationStudyError("task capsule exceeds the live-run input cap")
    if content_digest(capsule) != manifest["case"]["capsule_digest"]:
        raise DurationStudyError("fixture capsule digest is stale")
    return capsule


def _validate_auth_file(path: Path) -> Path:
    if path.is_symlink():
        raise DurationStudyError("Codex auth source must not be a symlink")
    try:
        metadata = path.stat()
    except OSError as exc:
        raise DurationStudyError("Codex auth source is unavailable") from exc
    if not stat.S_ISREG(metadata.st_mode):
        raise DurationStudyError("Codex auth source must be a regular file")
    if metadata.st_uid != os.getuid():
        raise DurationStudyError("Codex auth source must be owned by the invoking user")
    if stat.S_IMODE(metadata.st_mode) & 0o077:
        raise DurationStudyError("Codex auth source must not be group/world accessible")
    if metadata.st_size <= 0 or metadata.st_size > 1024 * 1024:
        raise DurationStudyError("Codex auth source size is outside the allowed range")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DurationStudyError("Codex auth source is not valid JSON") from exc
    if not isinstance(value, dict):
        raise DurationStudyError("Codex auth source root must be an object")
    return path.resolve()


def _image_digest(docker_bin: str, image: str) -> str:
    try:
        completed = subprocess.run(
            [docker_bin, "image", "inspect", "--format", "{{.Id}}", image],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise DurationStudyError("cannot inspect live-provider image") from exc
    digest = completed.stdout.strip()
    if completed.returncode != 0 or SHA256.fullmatch(digest) is None:
        raise DurationStudyError("live-provider image is unavailable or has no exact digest")
    return digest


def _codex_cli_version(docker_bin: str, image: str) -> str:
    command = [
        docker_bin,
        "run",
        "--rm",
        "--pull",
        "never",
        "--network",
        "none",
        "--read-only",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--pids-limit",
        "64",
        "--memory",
        "256m",
        "--cpus",
        "1.0",
        "--tmpfs",
        "/tmp:rw,nosuid,nodev,noexec,size=16m,mode=1777",
        "--user",
        f"{os.getuid()}:{os.getgid()}",
        "--env",
        "HOME=/tmp",
        image,
        "codex",
        "--version",
    ]
    try:
        completed = subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise DurationStudyError("cannot observe Codex version in the locked image") from exc
    match = SEMVER.search(f"{completed.stdout}\n{completed.stderr}")
    if completed.returncode != 0 or match is None:
        raise DurationStudyError("Codex version is not observable in the locked image")
    return match.group(1)


def _validate_sandbox_preflight(
    value: dict[str, Any],
    *,
    manifest: dict[str, Any],
) -> dict[str, Any]:
    expected = {
        "status": "pass",
        "provider": "codex",
        "fixture_id": manifest["fixture_id"],
        "profile_digest": content_digest(CODEX_PROFILE.read_bytes()),
        "workspace_write": "observed",
        "unrelated_read": "denied",
        "command_network": "denied",
        "generation_request_performed": False,
    }
    for key, expected_value in expected.items():
        if value.get(key) != expected_value:
            raise DurationStudyError(f"Codex sandbox preflight evidence mismatch: {key}")
    if SHA256.fullmatch(str(value.get("image_digest", ""))) is None:
        raise DurationStudyError("Codex sandbox preflight image digest is invalid")
    return value


def _prepare_session_root(parent: Path) -> tuple[Path, str]:
    profile = CODEX_PROFILE.read_bytes()
    session_root = parent / "agent-home"
    codex_home = session_root / ".codex"
    codex_home.mkdir(mode=0o700, parents=True)
    config = codex_home / "config.toml"
    with config.open("xb") as handle:
        handle.write(profile)
    config.chmod(0o600)
    return session_root, content_digest(profile)


def _owned_container_name(prefix: str) -> str:
    return f"mira-duration-{prefix}-{os.getpid()}-{time.time_ns()}"


def _cleanup_container(docker_bin: str, container_name: str) -> None:
    try:
        subprocess.run(
            [docker_bin, "rm", "--force", container_name],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise DurationStudyError(
            f"could not issue exact cleanup for owned container: {container_name}"
        ) from exc


def _container_base(
    *,
    docker_bin: str,
    image: str,
    container_name: str,
    fixture_id: str,
    workspace: Path,
    session_root: Path,
    auth_file: Path | None,
) -> list[str]:
    for path in (workspace, session_root, *(tuple() if auth_file is None else (auth_file,))):
        if "," in str(path) or "\n" in str(path):
            raise DurationStudyError("live-run path cannot be encoded as a Docker bind mount")
    command = [
        docker_bin,
        "run",
        "--rm",
        "--interactive",
        "--pull",
        "never",
        "--name",
        container_name,
        "--label",
        f"devcontainer.duration-study.fixture={fixture_id}",
        "--read-only",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--security-opt",
        "seccomp=unconfined",
        "--pids-limit",
        "256",
        "--memory",
        "2g",
        "--cpus",
        "2.0",
        "--ulimit",
        "nofile=512:512",
        "--tmpfs",
        "/tmp:rw,nosuid,nodev,size=256m,mode=1777",
        "--tmpfs",
        (
            "/var/lib/mira-observations:rw,nosuid,nodev,noexec,size=16m,mode=700,"
            f"uid={os.getuid()},gid={os.getgid()}"
        ),
        "--user",
        f"{os.getuid()}:{os.getgid()}",
        "--workdir",
        "/case",
        "--env",
        "HOME=/agent-home",
        "--env",
        "CODEX_HOME=/agent-home/.codex",
        "--env",
        "LANG=C.UTF-8",
        "--env",
        "LC_ALL=C.UTF-8",
        "--env",
        "TZ=UTC",
        "--mount",
        f"type=bind,src={workspace},dst=/case",
        "--mount",
        f"type=bind,src={session_root},dst=/agent-home",
    ]
    if auth_file is not None:
        command.extend(
            [
                "--mount",
                f"type=bind,src={auth_file},dst=/agent-home/.codex/auth.json,readonly",
            ]
        )
    command.append(image)
    return command


def _validate_clean_fixture(fixture_dir: Path, manifest: dict[str, Any]) -> Path:
    workspace = (fixture_dir.resolve() / manifest["paths"]["workspace"]).resolve()
    if not workspace.is_dir():
        raise DurationStudyError("fixture workspace is missing")
    completed = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=workspace,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
        check=False,
    )
    if completed.returncode != 0 or completed.stdout:
        raise DurationStudyError("live canary requires a clean generated fixture workspace")
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=workspace,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
        check=False,
    )
    if head.returncode != 0 or head.stdout.strip() != manifest["snapshot"]["base_sha"]:
        raise DurationStudyError("fixture base SHA does not match its manifest")
    return workspace


def probe_codex_agent_sandbox(
    fixture_dir: Path,
    *,
    image: str,
    docker_bin: str = "docker",
    timeout_seconds: float = 30,
) -> dict[str, Any]:
    """Prove workspace write, unrelated-read denial, and command-network denial."""

    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0 or timeout_seconds > 120:
        raise DurationStudyError("sandbox probe timeout must be > 0 and <= 120 seconds")
    manifest = _load_fixture_manifest(fixture_dir)
    workspace = _validate_clean_fixture(fixture_dir, manifest)
    image_identity = _image_digest(docker_bin, image)
    with tempfile.TemporaryDirectory(prefix="duration-codex-sandbox-") as raw_temp:
        session_root, profile_digest = _prepare_session_root(Path(raw_temp))
        fake_secret = session_root / ".codex" / "sandbox-secret.txt"
        fake_secret.write_text("fixture-marker\n", encoding="utf-8")
        fake_secret.chmod(0o600)
        container_name = _owned_container_name("codex-sandbox")
        command = _container_base(
            docker_bin=docker_bin,
            image=image,
            container_name=container_name,
            fixture_id=manifest["fixture_id"],
            workspace=workspace,
            session_root=session_root,
            auth_file=None,
        )
        command.extend(
            [
                "codex",
                "sandbox",
                "-P",
                "duration-fixture",
                "-C",
                "/case",
                "--",
                "python3",
                "-c",
                CODEX_SANDBOX_PROBE_SCRIPT,
            ]
        )
        started = time.monotonic_ns()
        try:
            completed = subprocess.run(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired:
            _cleanup_container(docker_bin, container_name)
            raise DurationStudyError("Codex sandbox probe timed out")
        except OSError as exc:
            raise DurationStudyError("cannot start Codex sandbox probe") from exc
        duration_ms = round((time.monotonic_ns() - started) / 1_000_000, 3)
        if completed.returncode != 0:
            raise DurationStudyError(
                f"Codex sandbox probe failed closed with exit {completed.returncode}"
            )
    if subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=workspace,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    ).stdout:
        raise DurationStudyError("Codex sandbox probe left workspace changes")
    return {
        "status": "pass",
        "provider": "codex",
        "fixture_id": manifest["fixture_id"],
        "image_digest": image_identity,
        "profile_digest": profile_digest,
        "workspace_write": "observed",
        "unrelated_read": "denied",
        "command_network": "denied",
        "generation_request_performed": False,
    }


def _parse_codex_events(path: Path) -> dict[str, Any]:
    event_counts: dict[str, int] = {}
    item_counts: dict[str, int] = {}
    invalid_lines = 0
    thread_digest: str | None = None
    usage: dict[str, int] = {}
    final_message_observed = False
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                invalid_lines += 1
                continue
            if not isinstance(event, dict):
                invalid_lines += 1
                continue
            event_type = event.get("type")
            if not isinstance(event_type, str):
                invalid_lines += 1
                continue
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
            if event_type == "thread.started" and isinstance(event.get("thread_id"), str):
                thread_digest = hashlib.sha256(event["thread_id"].encode("utf-8")).hexdigest()
            item = event.get("item")
            if isinstance(item, dict) and isinstance(item.get("type"), str):
                item_type = item["type"]
                item_counts[item_type] = item_counts.get(item_type, 0) + 1
                if item_type == "agent_message" and event_type == "item.completed":
                    final_message_observed = True
            if event_type == "turn.completed" and isinstance(event.get("usage"), dict):
                usage = {
                    key: value
                    for key, value in event["usage"].items()
                    if key
                    in {
                        "input_tokens",
                        "cached_input_tokens",
                        "output_tokens",
                        "reasoning_output_tokens",
                    }
                    and isinstance(value, int)
                    and not isinstance(value, bool)
                    and value >= 0
                }
    summary: dict[str, Any] = {
        "event_counts": dict(sorted(event_counts.items())),
        "item_type_counts": dict(sorted(item_counts.items())),
        "invalid_lines": invalid_lines,
        "final_message_observed": final_message_observed,
        "usage": usage,
    }
    if thread_digest is not None:
        summary["thread_id_digest"] = f"sha256:{thread_digest}"
    return summary


def _limit_output_file(bytes_cap: int) -> None:
    resource.setrlimit(resource.RLIMIT_FSIZE, (bytes_cap, bytes_cap))


def _classify_codex_failure(stderr: str) -> str:
    normalized = stderr.lower()
    classifications = (
        ("prompt-input-missing", ("no prompt provided",)),
        ("configuration", ("strict config", "config error", "unknown config", "invalid config")),
        ("authentication", ("not logged in", "authentication", "auth.json", "login required")),
        ("credential-read-only", ("read-only file system", "device or resource busy")),
        ("managed-hook", ("hook", "mira-codex-hook")),
        ("sandbox", ("bwrap", "sandbox", "permission profile", "landlock", "seccomp")),
        ("model-unavailable", ("model is not", "unknown model", "model unavailable")),
        ("provider-network", ("connection", "dns", "network", "timed out", "websocket")),
    )
    for failure_class, markers in classifications:
        if any(marker in normalized for marker in markers):
            return failure_class
    return "provider-startup-unknown"


def run_codex_fixture(
    fixture_dir: Path,
    *,
    image: str,
    model: str,
    effort: str,
    auth_file: Path,
    live_generation_authorized: bool,
    docker_bin: str = "docker",
    timeout_seconds: float = 900,
    output_bytes_cap: int = 8 * 1024 * 1024,
    sandbox_preflight: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run exactly one primary-only Codex turn and retain content-free evidence."""

    if not live_generation_authorized:
        raise DurationStudyError("live provider generation requires explicit authorization")
    if MODEL_ID.fullmatch(model) is None:
        raise DurationStudyError("Codex model ID is invalid")
    if effort not in EFFORTS:
        raise DurationStudyError("Codex effort is invalid")
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0 or timeout_seconds > 3600:
        raise DurationStudyError("live run timeout must be > 0 and <= 3600 seconds")
    if output_bytes_cap < 1024 or output_bytes_cap > 64 * 1024 * 1024:
        raise DurationStudyError("live output cap must be between 1 KiB and 64 MiB")

    manifest = _load_fixture_manifest(fixture_dir)
    workspace = _validate_clean_fixture(fixture_dir, manifest)
    if sandbox_preflight is None:
        sandbox_preflight = probe_codex_agent_sandbox(
            fixture_dir,
            image=image,
            docker_bin=docker_bin,
            timeout_seconds=min(timeout_seconds, 120),
        )
    sandbox_preflight = _validate_sandbox_preflight(
        sandbox_preflight,
        manifest=manifest,
    )
    capsule = _capsule_for_fixture(manifest)
    auth_source = _validate_auth_file(auth_file)
    image_identity = sandbox_preflight["image_digest"]

    with tempfile.TemporaryDirectory(prefix="duration-codex-live-") as raw_temp:
        private_root = Path(raw_temp)
        session_root, profile_digest = _prepare_session_root(private_root)
        raw_output = private_root / "provider-events.jsonl"
        raw_error = private_root / "provider-stderr.log"
        container_name = _owned_container_name("codex-live")
        command = _container_base(
            docker_bin=docker_bin,
            image=image,
            container_name=container_name,
            fixture_id=manifest["fixture_id"],
            workspace=workspace,
            session_root=session_root,
            auth_file=auth_source,
        )
        command.extend(
            [
                "codex",
                "exec",
                "--strict-config",
                "--ephemeral",
                "--json",
                "--color",
                "never",
                "--cd",
                "/case",
                "--ignore-rules",
                "--model",
                model,
                "--config",
                f'model_reasoning_effort="{effort}"',
                "-",
            ]
        )
        started = time.monotonic_ns()
        infrastructure = "failure"
        stop_reason = "provider-exit"
        exit_code = 125
        with raw_output.open("xb") as output_handle, raw_error.open("xb") as error_handle:
            os.fchmod(output_handle.fileno(), 0o600)
            os.fchmod(error_handle.fileno(), 0o600)
            try:
                completed = subprocess.run(
                    command,
                    input=capsule,
                    stdout=output_handle,
                    stderr=error_handle,
                    timeout=timeout_seconds,
                    check=False,
                    preexec_fn=lambda: _limit_output_file(output_bytes_cap),
                )
                exit_code = completed.returncode
                infrastructure = "success" if exit_code == 0 else "failure"
                stop_reason = "provider-complete" if exit_code == 0 else "provider-exit"
            except subprocess.TimeoutExpired:
                _cleanup_container(docker_bin, container_name)
                exit_code = 124
                infrastructure = "timeout"
                stop_reason = "safety-cap"
            except OSError as exc:
                raise DurationStudyError("cannot start isolated Codex live run") from exc
        elapsed_ms = round((time.monotonic_ns() - started) / 1_000_000, 3)
        output_size = raw_output.stat().st_size
        error_size = raw_error.stat().st_size
        if output_size >= output_bytes_cap or error_size >= output_bytes_cap:
            _cleanup_container(docker_bin, container_name)
            infrastructure = "failure"
            stop_reason = "output-cap"
        event_summary = _parse_codex_events(raw_output)
        error_text = raw_error.read_text(encoding="utf-8", errors="replace")
        if infrastructure == "success":
            failure_class = None
        elif stop_reason == "safety-cap":
            failure_class = "timeout-cap"
        elif stop_reason == "output-cap":
            failure_class = "output-cap"
        else:
            failure_class = _classify_codex_failure(error_text)

    changed = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=workspace,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
        check=False,
    )
    changed_count = len(changed.stdout.splitlines()) if changed.returncode == 0 else 0
    return {
        "provider": "codex",
        "fixture_id": manifest["fixture_id"],
        "case_id": manifest["case"]["case_id"],
        "infrastructure": infrastructure,
        "exit_code": exit_code,
        "stop_reason": stop_reason,
        "failure_class": failure_class,
        "terminal_wall_ms": elapsed_ms,
        "workspace_changed_path_count": changed_count,
        "model_identity": {
            "requested_alias": model,
            "requested_source": "flag",
            "identity_confidence": "alias-only",
        },
        "generation_settings": [
            {
                "namespace": "codex.reasoning",
                "key": "effort",
                "requested_value": effort,
                "status": "unknown",
            }
        ],
        "runtime": {
            "image_digest": image_identity,
            "profile_digest": profile_digest,
            "execution_surface": "isolated-provider-container",
            "credential_source": "read-only-bind",
            "credential_path_persisted": False,
            "prompt_persisted": False,
            "raw_output_persisted": False,
            "raw_stderr_persisted": False,
            "nested_delegation": "disabled-by-feature",
            "task_network": "denied-by-permission-profile",
            "sandbox_preflight": "pass",
        },
        "output_cap_bytes": output_bytes_cap,
        "output_bytes": output_size,
        "stderr_bytes": error_size,
        "generation_request_performed": True,
        "events": event_summary,
    }


def _diagnostic_counters(values: dict[str, int], *, namespace: str) -> list[dict[str, Any]]:
    counters: list[dict[str, Any]] = []
    for raw_name, count in sorted(values.items()):
        name = raw_name
        if RECORD_ID.fullmatch(name) is None:
            digest = hashlib.sha256(name.encode("utf-8")).hexdigest()[:24]
            name = f"{namespace}-sha256-{digest}"
        counters.append({"name": name, "count": count})
    return counters


def _provider_diagnostics(
    result: dict[str, Any],
    sandbox_preflight: dict[str, Any],
) -> dict[str, Any]:
    events = result["events"]
    diagnostics: dict[str, Any] = {
        "status": result["infrastructure"],
        "exit_code": result["exit_code"],
        "terminal_wall_ms": result["terminal_wall_ms"],
        "output_cap_bytes": result["output_cap_bytes"],
        "output_bytes": result["output_bytes"],
        "stderr_bytes": result["stderr_bytes"],
        "workspace_changed_path_count": result["workspace_changed_path_count"],
        "event_counts": _diagnostic_counters(
            events["event_counts"],
            namespace="event",
        ),
        "item_type_counts": _diagnostic_counters(
            events["item_type_counts"],
            namespace="item",
        ),
        "invalid_event_lines": events["invalid_lines"],
        "final_message_observed": events["final_message_observed"],
        "usage": dict(events["usage"]),
        "generation_request_performed": result["generation_request_performed"],
        "prompt_persisted": False,
        "raw_output_persisted": False,
        "raw_stderr_persisted": False,
        "credential_path_persisted": False,
        "nested_delegation": "disabled-by-feature",
        "task_network": "denied-by-permission-profile",
        "sandbox_preflight": {
            "status": sandbox_preflight["status"],
            "image_digest": sandbox_preflight["image_digest"],
            "profile_digest": sandbox_preflight["profile_digest"],
            "workspace_write": sandbox_preflight["workspace_write"],
            "unrelated_read": sandbox_preflight["unrelated_read"],
            "command_network": sandbox_preflight["command_network"],
            "generation_request_performed": sandbox_preflight[
                "generation_request_performed"
            ],
        },
    }
    thread_digest = events.get("thread_id_digest")
    if isinstance(thread_digest, str):
        diagnostics["thread_id_digest"] = thread_digest
    return diagnostics


def _not_run_evaluator_diagnostics() -> dict[str, Any]:
    return {
        "status": "not-run",
        "evaluator_id": None,
        "isolation_profile": "not-run",
        "image_digest": None,
        "credential_mounts": False,
        "control_bundle_mounted": False,
        "checks": [],
    }


def _evaluator_diagnostics(result: dict[str, Any]) -> dict[str, Any]:
    checks = [*result["workspace_checks"], result["hidden_check"]]
    isolation = result["isolation"]
    return {
        "status": result["status"],
        "evaluator_id": result["evaluator_id"],
        "isolation_profile": isolation["profile"],
        "image_digest": isolation["image_digest"],
        "credential_mounts": isolation["credential_mounts"],
        "control_bundle_mounted": isolation["control_bundle_mounted"],
        "checks": [
            {
                "check_id": item["check_id"],
                "status": item["status"],
                "exit_code": item["exit_code"],
                "duration_ms": item["duration_ms"],
            }
            for item in checks
        ],
    }


def _live_base_record(
    manifest: dict[str, Any],
    *,
    study_id: str,
    run_id: str,
    block_id: str,
    model: str,
    effort: str,
    cli_version: str,
    image_digest: str,
    observed_at: str,
    timeout_seconds: float,
) -> dict[str, Any]:
    case = _catalog_entry_for_fixture(manifest)["case"]
    return {
        "schema_version": 2,
        "study_id": study_id,
        "run_id": run_id,
        "block_id": block_id,
        "case": {
            "case_id": case["case_id"],
            "revision": case["revision"],
            "catalog_digest": manifest["case"]["catalog_digest"],
            "capsule_digest": manifest["case"]["capsule_digest"],
            "source_type": case["source_type"],
            "family": case["family"],
            "size": case["size"],
            "profile_id": case["profile_id"],
            "strong_online_oracle": case["strong_online_oracle"],
        },
        "snapshot": {
            "base_sha": manifest["snapshot"]["base_sha"],
            "bundle_digest": manifest["snapshot"]["bundle_digest"],
            "fixture_revision": (
                f"{manifest['case']['recipe_id']}-r{manifest['case']['recipe_revision']}"
            ),
            "instruction_set_digest": manifest["snapshot"]["instruction_set_digest"],
        },
        "configuration": {
            "configuration_id": "C0",
            "relation": "primary-only",
            "participant_plan": "primary-only",
            "participants_actual": 1,
            "workers_actual": 0,
            "peak_concurrent": 0,
            "nested_delegation": "disabled",
            "independence_policy": "fresh-ephemeral-session",
            "lane": manifest["execution_contract"]["lane"],
        },
        "participants": [
            {
                "participant_id": "primary",
                "role": "implementer",
                "model_identity": {
                    "requested_alias": model,
                    "requested_source": "flag",
                    "identity_confidence": "alias-only",
                },
                "generation_settings": [
                    {
                        "namespace": "codex.reasoning",
                        "key": "effort",
                        "requested_value": effort,
                        "status": "unknown",
                    }
                ],
                "runtime_identity": {
                    "provider": "codex",
                    "cli_name": "codex",
                    "cli_version": cli_version,
                    "cli_source": "container-image",
                    "image_digest": image_digest,
                    "execution_surface": "isolated-provider-container",
                    "permission_mode": "automatic",
                    "observed_at": observed_at,
                },
            }
        ],
        "environment": {
            "image_digest": image_digest,
            "machine_class": "docker-limited-2cpu-2g",
            "session_context": "fresh",
            "repository_cache": "not-applicable",
            "dependency_cache": "not-applicable",
            "docker_cache": "warm",
            "provider_prompt_cache": "unknown",
            "compaction": "unknown",
            "competing_load": "unknown",
            "timezone": "UTC",
        },
        "limits": {
            "wall_clock_ms": math.ceil(timeout_seconds * 1000),
            "role": "safety-censoring-cap",
            "retry_policy": "none",
        },
        "correlation": {
            "episode_ids": [],
            "agentctl_job_ids": [],
            "attempt_ids": [],
        },
    }


def _default_run_id(case_id: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    normalized_case = case_id.lower()
    return f"codex-{normalized_case}-{timestamp}-{os.getpid()}"


def run_codex_study_once(
    case_id: str,
    output_dir: Path,
    *,
    image: str,
    model: str,
    effort: str,
    auth_file: Path,
    live_generation_authorized: bool,
    study_id: str = "duration-atlas-wave1",
    block_id: str = "codex-primary-calibration",
    run_id: str | None = None,
    docker_bin: str = "docker",
    timeout_seconds: float = 900,
    evaluator_timeout_seconds: float = 30,
    output_bytes_cap: int = 8 * 1024 * 1024,
    clock: EventClock | None = None,
) -> tuple[dict[str, Any], Path]:
    """Run one finite Codex sample and atomically join timing with evaluation."""

    if not live_generation_authorized:
        raise DurationStudyError("live provider generation requires explicit authorization")
    chosen_run_id = run_id or _default_run_id(case_id)
    for label, value in (
        ("study ID", study_id),
        ("block ID", block_id),
        ("run ID", chosen_run_id),
    ):
        if RECORD_ID.fullmatch(value) is None:
            raise DurationStudyError(f"{label} does not match the duration-study ID contract")
    if MODEL_ID.fullmatch(model) is None or effort not in EFFORTS:
        raise DurationStudyError("Codex model or effort is invalid")
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0 or timeout_seconds > 3600:
        raise DurationStudyError("live run timeout must be > 0 and <= 3600 seconds")
    if (
        not math.isfinite(evaluator_timeout_seconds)
        or evaluator_timeout_seconds <= 0
        or evaluator_timeout_seconds > 300
    ):
        raise DurationStudyError("evaluator timeout must be > 0 and <= 300 seconds")
    _validate_auth_file(auth_file)

    resolved_output = output_dir.resolve()
    record_path = resolved_output / f"{chosen_run_id}.json"
    if record_path.exists():
        raise DurationStudyError(f"refusing to repeat an existing run ID: {chosen_run_id}")
    active_clock = clock or SystemClock()
    provision_start = event(active_clock)

    fixture_suffix = hashlib.sha256(chosen_run_id.encode("utf-8")).hexdigest()[:12]
    fixture_id = f"codex-{case_id.lower()}-{fixture_suffix}"
    with tempfile.TemporaryDirectory(prefix="duration-codex-study-") as raw_temp:
        fixture_dir = Path(raw_temp) / "fixture"
        manifest = build_fixture(case_id, fixture_dir, fixture_id=fixture_id)
        sandbox_preflight = probe_codex_agent_sandbox(
            fixture_dir,
            image=image,
            docker_bin=docker_bin,
            timeout_seconds=min(timeout_seconds, 120),
        )
        cli_version = _codex_cli_version(docker_bin, image)
        provision_ready = event(active_clock)
        recorder = RunRecorder(
            _live_base_record(
                manifest,
                study_id=study_id,
                run_id=chosen_run_id,
                block_id=block_id,
                model=model,
                effort=effort,
                cli_version=cli_version,
                image_digest=sandbox_preflight["image_digest"],
                observed_at=provision_ready["wall_time"],
                timeout_seconds=timeout_seconds,
            ),
            active_clock,
        )
        recorder.record["landmarks"]["P0"] = provision_start
        recorder.record["landmarks"]["P1"] = provision_ready
        recorder.mark_landmark("T0")
        recorder.mark_landmark("T1")
        provider_result = run_codex_fixture(
            fixture_dir,
            image=image,
            model=model,
            effort=effort,
            auth_file=auth_file,
            live_generation_authorized=True,
            docker_bin=docker_bin,
            timeout_seconds=timeout_seconds,
            output_bytes_cap=output_bytes_cap,
            sandbox_preflight=sandbox_preflight,
        )
        recorder.mark_landmark("T2", status="not-observed")
        recorder.mark_landmark("T3", status="not-applicable")
        recorder.mark_landmark("T4", status="not-applicable")

        provider_diagnostics = _provider_diagnostics(
            provider_result,
            sandbox_preflight,
        )
        evaluator_diagnostics = _not_run_evaluator_diagnostics()
        provider_status = provider_result["infrastructure"]
        if provider_status == "success":
            recorder.mark_landmark("V0")
            try:
                evaluator_result = evaluate_fixture_isolated(
                    fixture_dir,
                    image=image,
                    docker_bin=docker_bin,
                    timeout_seconds=evaluator_timeout_seconds,
                )
            except DurationStudyError:
                recorder.mark_landmark("V1")
                evaluator_diagnostics = {
                    "status": "infrastructure-failure",
                    "evaluator_id": manifest["execution_contract"]["online_evaluator_id"],
                    "isolation_profile": "network-disabled-read-only-container",
                    "image_digest": sandbox_preflight["image_digest"],
                    "credential_mounts": False,
                    "control_bundle_mounted": False,
                    "checks": [],
                }
                outcome = {
                    "infrastructure": "invalid",
                    "artifact": (
                        "valid"
                        if provider_result["workspace_changed_path_count"] > 0
                        else "missing"
                    ),
                    "online_acceptance": "unavailable",
                    "offline_score": "not-run",
                    "failure_class": "evaluator-infrastructure",
                    "stop_reason": "evaluator-infrastructure",
                }
                recorder.mark_landmark("T6", status="not-observed")
            else:
                recorder.mark_landmark("V1")
                evaluator_diagnostics = _evaluator_diagnostics(evaluator_result)
                artifact = (
                    "valid"
                    if provider_result["workspace_changed_path_count"] > 0
                    else "missing"
                )
                if evaluator_result["status"] == "pass" and artifact != "valid":
                    raise DurationStudyError(
                        "passing evaluator observed no workspace artifact; refusing the sample"
                    )
                outcome = {
                    "infrastructure": "success",
                    "artifact": artifact,
                    "online_acceptance": evaluator_result["status"],
                    "offline_score": "not-run",
                    "failure_class": (
                        None
                        if evaluator_result["status"] == "pass"
                        else "online-validation-failed"
                    ),
                    "stop_reason": "result-ready",
                }
                recorder.mark_landmark("T6")
        else:
            recorder.mark_landmark("V0", status="not-observed")
            recorder.mark_landmark("V1", status="not-observed")
            recorder.mark_landmark("T6", status="not-observed")
            outcome = {
                "infrastructure": provider_status,
                "artifact": (
                    "invalid"
                    if provider_result["workspace_changed_path_count"] > 0
                    else "missing"
                ),
                "online_acceptance": "unavailable",
                "offline_score": "not-run",
                "failure_class": provider_result["failure_class"],
                "stop_reason": provider_result["stop_reason"],
            }

        recorder.mark_landmark("TX")
        recorder.mark_landmark("S0", status="not-applicable")
        recorder.mark_landmark("S1", status="not-applicable")
        record = recorder.finalize(
            outcome=outcome,
            quality={"evaluator_id": None, "metrics": []},
            diagnostics={
                "provider": provider_diagnostics,
                "evaluator": evaluator_diagnostics,
            },
        )
        atomic_write_json(record_path, record)
    return record, record_path
