#!/usr/bin/env python3
"""Finite isolated live-provider runners for duration-study calibration."""

from __future__ import annotations

import base64
import hashlib
import json
import math
import os
from pathlib import Path
import re
import resource
import stat
import subprocess
import tempfile
import time
from typing import Any, Mapping
from datetime import datetime, timezone

from agent_contracts import load_json
from agent_duration_fixtures import (
    DEFAULT_CATALOG,
    build_fixture,
    evaluate_fixture_isolated,
    task_artifact_paths,
)
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
PROVIDERS = {"codex", "claude", "grok"}
ARTIFACT_RETENTIONS = {"content-free-only", "task-artifacts"}
ARTIFACT_FILE_BYTES_CAP = 256 * 1024
ARTIFACT_TOTAL_BYTES_CAP = 1024 * 1024
PROVIDER_EFFORTS = {
    "codex": {"low", "medium", "high", "xhigh", "max", "ultra"},
    "claude": {"low", "medium", "high", "xhigh", "max"},
    # Grok 1.0.5 advertises the flag but not its values.  Keep the experiment
    # ladder explicit and rely on ephemeral session metadata to distinguish an
    # applied value from a rejection or an unobservable request.
    "grok": {"medium", "high", "xhigh", "max"},
}
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


def _validate_private_json_file(path: Path, *, label: str) -> Path:
    if path.is_symlink():
        raise DurationStudyError(f"{label} must not be a symlink")
    try:
        metadata = path.stat()
    except OSError as exc:
        raise DurationStudyError(f"{label} is unavailable") from exc
    if not stat.S_ISREG(metadata.st_mode):
        raise DurationStudyError(f"{label} must be a regular file")
    if metadata.st_uid != os.getuid():
        raise DurationStudyError(f"{label} must be owned by the invoking user")
    if stat.S_IMODE(metadata.st_mode) & 0o077:
        raise DurationStudyError(f"{label} must not be group/world accessible")
    if metadata.st_size <= 0 or metadata.st_size > 1024 * 1024:
        raise DurationStudyError(f"{label} size is outside the allowed range")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DurationStudyError(f"{label} is not valid JSON") from exc
    if not isinstance(value, dict):
        raise DurationStudyError(f"{label} root must be an object")
    return path.resolve()


def _validate_auth_file(path: Path) -> Path:
    return _validate_private_json_file(path, label="Codex auth source")


def _jwt_expiry(value: Any) -> float | None:
    if not isinstance(value, str):
        return None
    parts = value.split(".")
    if len(parts) != 3:
        return None
    try:
        payload = parts[1] + "=" * (-len(parts[1]) % 4)
        decoded = json.loads(base64.urlsafe_b64decode(payload).decode("utf-8"))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    expiry = decoded.get("exp") if isinstance(decoded, dict) else None
    if isinstance(expiry, (int, float)) and not isinstance(expiry, bool):
        return float(expiry)
    return None


def _provider_credential_expiry(provider: str, value: dict[str, Any]) -> float | None:
    if provider == "codex":
        if isinstance(value.get("OPENAI_API_KEY"), str) and value["OPENAI_API_KEY"]:
            return math.inf
        tokens = value.get("tokens")
        if not isinstance(tokens, dict) or not isinstance(tokens.get("refresh_token"), str):
            return None
        return _jwt_expiry(tokens.get("access_token"))
    if provider == "claude":
        oauth = value.get("claudeAiOauth")
        if not isinstance(oauth, dict):
            return None
        if not isinstance(oauth.get("accessToken"), str) or not oauth["accessToken"]:
            return None
        if not isinstance(oauth.get("refreshToken"), str) or not oauth["refreshToken"]:
            return None
        expiry = oauth.get("expiresAt")
        if isinstance(expiry, (int, float)) and not isinstance(expiry, bool):
            return float(expiry) / 1000
        return None
    if provider == "grok":
        if len(value) != 1:
            return None
        credential = next(iter(value.values()))
        if not isinstance(credential, dict):
            return None
        if not isinstance(credential.get("key"), str) or not credential["key"]:
            return None
        if not isinstance(credential.get("refresh_token"), str) or not credential["refresh_token"]:
            return None
        raw_expiry = credential.get("expires_at")
        if not isinstance(raw_expiry, str):
            return None
        try:
            parsed = datetime.fromisoformat(raw_expiry.replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return None
        return parsed.timestamp()
    return None


def _validate_provider_credential_window(
    provider: str,
    path: Path,
    *,
    timeout_seconds: float,
    refresh_margin_seconds: float = 300,
) -> Path:
    resolved = _validate_private_json_file(
        path,
        label=f"{provider.title()} credential source",
    )
    value = json.loads(resolved.read_text(encoding="utf-8"))
    expiry = _provider_credential_expiry(provider, value)
    required_until = time.time() + timeout_seconds + refresh_margin_seconds
    if expiry is None:
        raise DurationStudyError(
            f"{provider} credential freshness is not observable; refusing a live run"
        )
    if expiry < required_until:
        raise DurationStudyError(
            f"{provider} credential expires inside the live-run safety window; refresh login first"
        )
    return resolved


def _validate_provider_binary(path: Path, *, provider: str) -> Path:
    resolved = path.resolve()
    try:
        metadata = resolved.stat()
    except OSError as exc:
        raise DurationStudyError(f"{provider} provider binary is unavailable") from exc
    if not stat.S_ISREG(metadata.st_mode) or not os.access(resolved, os.X_OK):
        raise DurationStudyError(f"{provider} provider binary must be an executable file")
    if metadata.st_size <= 0 or metadata.st_size > 1024 * 1024 * 1024:
        raise DurationStudyError(f"{provider} provider binary size is outside the allowed range")
    return resolved


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


def _provider_cli_version(
    provider: str,
    *,
    docker_bin: str,
    image: str,
    provider_binary: Path | None = None,
) -> str:
    if provider == "codex" and provider_binary is None:
        return _codex_cli_version(docker_bin, image)
    if provider not in {"claude", "grok"}:
        raise DurationStudyError(f"unsupported provider version probe: {provider}")
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
    ]
    executable = provider
    if provider_binary is not None:
        binary = _validate_provider_binary(provider_binary, provider=provider)
        if "," in str(binary) or "\n" in str(binary):
            raise DurationStudyError("provider binary path cannot be encoded as a bind mount")
        command.extend(
            [
                "--mount",
                f"type=bind,src={binary},dst=/provider-bin/{provider},readonly",
            ]
        )
        executable = f"/provider-bin/{provider}"
    command.extend([image, executable, "--version"])
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
        raise DurationStudyError(f"cannot observe {provider} version") from exc
    match = SEMVER.search(f"{completed.stdout}\n{completed.stderr}")
    if completed.returncode != 0 or match is None:
        raise DurationStudyError(f"{provider} version is not observable")
    return match.group(1)


def _validate_sandbox_preflight(
    value: dict[str, Any],
    *,
    manifest: dict[str, Any],
    provider: str = "codex",
    profile_digest: str | None = None,
) -> dict[str, Any]:
    if provider == "codex":
        expected_profile_digest = content_digest(CODEX_PROFILE.read_bytes())
        assurance = "probed"
        boundaries = {
            "workspace_write": "observed",
            "unrelated_read": "denied",
            "command_network": "denied",
        }
    elif provider in {"claude", "grok"} and profile_digest is not None:
        expected_profile_digest = profile_digest
        assurance = "configured"
        boundaries = {
            "workspace_write": "configured",
            "unrelated_read": "configured",
            "command_network": "configured",
        }
    else:
        raise DurationStudyError(f"unsupported sandbox preflight provider: {provider}")
    expected = {
        "assurance": assurance,
        "status": "pass",
        "provider": provider,
        "fixture_id": manifest["fixture_id"],
        "profile_digest": expected_profile_digest,
        **boundaries,
        "generation_request_performed": False,
    }
    for key, expected_value in expected.items():
        if value.get(key) != expected_value:
            raise DurationStudyError(f"{provider} sandbox preflight evidence mismatch: {key}")
    if SHA256.fullmatch(str(value.get("image_digest", ""))) is None:
        raise DurationStudyError(f"{provider} sandbox preflight image digest is invalid")
    return value


def _configured_sandbox_evidence(
    provider: str,
    *,
    manifest: dict[str, Any],
    image_digest: str,
    profile_digest: str,
) -> dict[str, Any]:
    if provider not in {"claude", "grok"}:
        raise DurationStudyError(f"configured sandbox evidence is unsupported for {provider}")
    return {
        "assurance": "configured",
        "status": "pass",
        "provider": provider,
        "fixture_id": manifest["fixture_id"],
        "image_digest": image_digest,
        "profile_digest": profile_digest,
        "workspace_write": "configured",
        "unrelated_read": "configured",
        "command_network": "configured",
        "generation_request_performed": False,
    }


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


def _prepare_claude_session_root(parent: Path) -> tuple[Path, str]:
    session_root = parent / "agent-home"
    claude_home = session_root / ".claude"
    claude_home.mkdir(mode=0o700, parents=True)
    settings = {
        "sandbox": {
            "enabled": True,
            "failIfUnavailable": True,
            "autoAllowBashIfSandboxed": True,
            "allowUnsandboxedCommands": False,
            "filesystem": {
                "denyRead": ["~/"],
                "allowRead": ["/case"],
                "denyWrite": ["~/"],
                "allowWrite": ["/case"],
            },
            "network": {"allowedDomains": []},
            "credentials": {
                "files": [
                    {"path": "~/.claude/.credentials.json", "mode": "deny"}
                ]
            },
        },
        "permissions": {
            "allow": ["Read(/case/**)", "Edit(/case/**)", "Write(/case/**)", "Bash"],
            "deny": [
                "Read(//agent-home/**)",
                "Edit(//agent-home/**)",
                "Write(//agent-home/**)",
                "WebFetch",
                "WebSearch",
                "Task",
            ],
        },
    }
    encoded = (json.dumps(settings, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )
    settings_path = claude_home / "settings.json"
    with settings_path.open("xb") as handle:
        handle.write(encoded)
    settings_path.chmod(0o600)
    return session_root, content_digest(encoded)


def _prepare_grok_session_root(parent: Path) -> tuple[Path, str]:
    session_root = parent / "agent-home"
    grok_home = session_root / ".grok"
    grok_home.mkdir(mode=0o700, parents=True)
    config = b'''[cli]
auto_update = false

[sandbox]
profile = "duration-fixture"

[shell_environment_policy]
inherit = "none"
include_only = ["PATH", "HOME", "LANG", "LC_ALL", "TZ"]
'''
    sandbox = b'''[profiles.duration-fixture]
extends = "strict"
restrict_network = true
'''
    for name, payload in (("config.toml", config), ("sandbox.toml", sandbox)):
        path = grok_home / name
        with path.open("xb") as handle:
            handle.write(payload)
        path.chmod(0o600)
    return session_root, content_digest(config + b"\0" + sandbox)


def _prepare_provider_session_root(provider: str, parent: Path) -> tuple[Path, str]:
    if provider == "codex":
        return _prepare_session_root(parent)
    if provider == "claude":
        return _prepare_claude_session_root(parent)
    if provider == "grok":
        return _prepare_grok_session_root(parent)
    raise DurationStudyError(f"unsupported provider session profile: {provider}")


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
        "--env",
        "PYTHONDONTWRITEBYTECODE=1",
        "--env",
        "PATH=/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin",
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


def _non_codex_container_base(
    *,
    provider: str,
    docker_bin: str,
    image: str,
    container_name: str,
    fixture_id: str,
    workspace: Path,
    session_root: Path,
    auth_file: Path,
    provider_binary: Path | None,
) -> tuple[list[str], str]:
    if provider not in {"claude", "grok"}:
        raise DurationStudyError(f"unsupported isolated provider: {provider}")
    paths = [workspace, session_root, auth_file]
    if provider_binary is not None:
        paths.append(provider_binary)
    if any("," in str(path) or "\n" in str(path) for path in paths):
        raise DurationStudyError("provider path cannot be encoded as a Docker bind mount")
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
        "LANG=C.UTF-8",
        "--env",
        "LC_ALL=C.UTF-8",
        "--env",
        "TZ=UTC",
        "--env",
        "PYTHONDONTWRITEBYTECODE=1",
        "--env",
        "PATH=/usr/local/lib/provider-sandbox:/usr/local/bin:/usr/bin:/bin",
        "--mount",
        f"type=bind,src={workspace},dst=/case",
        "--mount",
        f"type=bind,src={session_root},dst=/agent-home",
    ]
    if provider == "claude":
        command.extend(
            [
                "--env",
                "CLAUDE_CONFIG_DIR=/agent-home/.claude",
                "--env",
                "DISABLE_AUTOUPDATER=1",
                "--env",
                "CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1",
                "--mount",
                (
                    f"type=bind,src={auth_file},"
                    "dst=/agent-home/.claude/.credentials.json,readonly"
                ),
            ]
        )
        provider_command = "claude"
    else:
        command.extend(
            [
                "--mount",
                f"type=bind,src={auth_file},dst=/agent-home/.grok/auth.json,readonly",
            ]
        )
        provider_command = "grok"
        if provider_binary is not None:
            command.extend(
                [
                    "--mount",
                    f"type=bind,src={provider_binary},dst=/provider-bin/grok,readonly",
                ]
            )
            provider_command = "/provider-bin/grok"
    command.append(image)
    return command, provider_command


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


def _credential_literals(auth_file: Path) -> tuple[bytes, ...]:
    """Extract credential values used only to prevent accidental persistence."""

    try:
        raw = auth_file.read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DurationStudyError("cannot scan provider credential for artifact redaction") from exc
    literals: set[bytes] = set()

    def visit(item: Any) -> None:
        if isinstance(item, dict):
            for child in item.values():
                visit(child)
        elif isinstance(item, list):
            for child in item:
                visit(child)
        elif isinstance(item, str) and len(item.encode("utf-8")) >= 8:
            literals.add(item.encode("utf-8"))

    visit(value)
    return tuple(sorted(literals))


def _git_status_for_path(workspace: Path, raw_path: str) -> tuple[str, str] | None:
    completed = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all", "--", raw_path],
        cwd=workspace,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
        check=False,
    )
    if completed.returncode != 0:
        raise DurationStudyError("cannot inspect task artifact Git status")
    lines = completed.stdout.splitlines()
    if not lines:
        return None
    if len(lines) != 1 or len(lines[0]) < 3:
        raise DurationStudyError("task artifact Git status is ambiguous")
    return lines[0][:2], lines[0]


def _capture_task_artifacts(
    fixture_dir: Path,
    manifest: Mapping[str, Any],
    auth_file: Path,
) -> dict[str, Any]:
    """Capture only allowlisted synthetic task outputs under hard content caps."""

    workspace = (fixture_dir.resolve() / manifest["paths"]["workspace"]).resolve()
    allowed = task_artifact_paths(
        manifest["case"]["case_id"],
        manifest["case"]["recipe_id"],
    )
    if len(allowed) > 16:
        raise DurationStudyError("task artifact allowlist exceeds the hard file cap")
    all_status = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=workspace,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
        check=False,
    )
    if all_status.returncode != 0:
        raise DurationStudyError("cannot inspect workspace for artifact retention")
    all_changed_lines = set(all_status.stdout.splitlines())
    credential_literals = _credential_literals(auth_file)
    files: list[dict[str, Any]] = []
    retained_bytes = 0
    allowed_changed_lines: set[str] = set()
    for raw_path in allowed:
        git_entry = _git_status_for_path(workspace, raw_path)
        if git_entry is None:
            continue
        git_status, status_line = git_entry
        allowed_changed_lines.add(status_line)
        path = workspace / raw_path
        if not path.exists() and not path.is_symlink():
            files.append(
                {
                    "path": raw_path,
                    "git_status": git_status,
                    "content_status": "deleted",
                    "byte_count": 0,
                }
            )
            continue
        try:
            mode = path.lstat().st_mode
        except OSError as exc:
            raise DurationStudyError("cannot stat retained task artifact") from exc
        if not stat.S_ISREG(mode):
            files.append(
                {
                    "path": raw_path,
                    "git_status": git_status,
                    "content_status": "non-regular",
                    "byte_count": 0,
                }
            )
            continue
        byte_count = path.stat().st_size
        item: dict[str, Any] = {
            "path": raw_path,
            "git_status": git_status,
            "byte_count": byte_count,
        }
        if (
            byte_count > ARTIFACT_FILE_BYTES_CAP
            or retained_bytes + byte_count > ARTIFACT_TOTAL_BYTES_CAP
        ):
            item["content_status"] = "size-cap"
        else:
            try:
                content = path.read_bytes()
            except OSError as exc:
                raise DurationStudyError("cannot read retained task artifact") from exc
            if len(content) != byte_count:
                raise DurationStudyError("task artifact changed while being retained")
            item["content_digest"] = content_digest(content)
            if any(literal in content for literal in credential_literals):
                item["content_status"] = "redacted-credential"
                files.append(item)
                continue
            try:
                decoded = content.decode("utf-8")
            except UnicodeDecodeError:
                item["content_status"] = "non-utf8"
            else:
                item["content_status"] = "retained"
                item["content_utf8"] = decoded
                retained_bytes += len(content)
        files.append(item)
    unexpected_lines = all_changed_lines - allowed_changed_lines
    unexpected_summary = {
        "total": len(unexpected_lines),
        "tracked": sum(line[:2] != "??" for line in unexpected_lines),
        "untracked": sum(line[:2] == "??" for line in unexpected_lines),
        "deleted": sum(line[:2] != "??" and "D" in line[:2] for line in unexpected_lines),
    }
    unexpected = unexpected_summary["total"]
    manifest_files = [
        {key: value for key, value in item.items() if key != "content_utf8"}
        for item in files
    ]
    partial = unexpected > 0 or any(
        item["content_status"] not in {"retained", "deleted"} for item in files
    )
    return {
        "policy": "synthetic-task-artifacts-v1",
        "completeness": "partial" if partial else "complete",
        "unexpected_changed_path_count": unexpected,
        "unexpected_change_summary": unexpected_summary,
        "total_bytes": retained_bytes,
        "manifest_digest": canonical_json_digest(manifest_files),
        "files": files,
    }


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
                "/bin/bash",
                "/usr/local/bin/codex",
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
        try:
            completed = subprocess.run(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired:
            _cleanup_container(docker_bin, container_name)
            raise DurationStudyError("Codex sandbox probe timed out")
        except OSError as exc:
            raise DurationStudyError("cannot start Codex sandbox probe") from exc
        if completed.returncode != 0:
            diagnostic = "\n".join(
                value.decode("utf-8", errors="replace")
                for value in (completed.stdout[:65536], completed.stderr[:65536])
            )
            signals = _provider_failure_signals(diagnostic)
            terms = _provider_failure_terms(diagnostic)
            shape = re.sub(r"/(?:[^\s:]+/?)+", "<path>", diagnostic)
            shape = re.sub(r"[A-Za-z0-9_-]{32,}", "<opaque>", shape).strip()[-512:]
            raise DurationStudyError(
                "Codex sandbox probe failed closed "
                f"with exit {completed.returncode}; signals={signals}; terms={terms}; "
                f"shape={shape!r}"
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
        "assurance": "probed",
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
    terminal_event: str | None = None
    result_is_error = False
    event_failure_terms: set[str] = set()
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
                terminal_event = event_type
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
            elif event_type == "turn.failed":
                terminal_event = event_type
                result_is_error = True
                raw_error = event.get("error")
                if isinstance(raw_error, (str, dict, list)):
                    event_failure_terms.update(
                        _provider_failure_terms(
                            json.dumps(raw_error, ensure_ascii=False)
                        )
                    )
    summary: dict[str, Any] = {
        "event_counts": dict(sorted(event_counts.items())),
        "item_type_counts": dict(sorted(item_counts.items())),
        "invalid_lines": invalid_lines,
        "final_message_observed": final_message_observed,
        "usage": usage,
        "result_is_error": result_is_error,
        "event_failure_terms": sorted(event_failure_terms),
    }
    if terminal_event is not None:
        summary["terminal_event"] = terminal_event
    if thread_digest is not None:
        summary["thread_id_digest"] = f"sha256:{thread_digest}"
    return summary


def _safe_model_identity(value: Any) -> str | None:
    if not isinstance(value, str) or MODEL_ID.fullmatch(value) is None:
        return None
    return value


def _usage_summary(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    aliases = {
        "input_tokens": "input_tokens",
        "inputTokens": "input_tokens",
        "cache_read_input_tokens": "cached_input_tokens",
        "cacheReadInputTokens": "cached_input_tokens",
        "cached_input_tokens": "cached_input_tokens",
        "cachedInputTokens": "cached_input_tokens",
        "output_tokens": "output_tokens",
        "outputTokens": "output_tokens",
        "reasoning_output_tokens": "reasoning_output_tokens",
        "reasoningOutputTokens": "reasoning_output_tokens",
    }
    result: dict[str, int] = {}
    for source, target in aliases.items():
        raw = value.get(source)
        if isinstance(raw, int) and not isinstance(raw, bool) and raw >= 0:
            result[target] = raw
    return result


def _parse_claude_events(path: Path) -> dict[str, Any]:
    event_counts: dict[str, int] = {}
    item_counts: dict[str, int] = {}
    invalid_lines = 0
    session_ids: set[str] = set()
    models: set[str] = set()
    usage: dict[str, int] = {}
    final_message_observed = False
    tool_error_count = 0
    terminal_event: str | None = None
    result_is_error = False
    event_failure_terms: set[str] = set()
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
            subtype = event.get("subtype")
            if isinstance(subtype, str):
                subtype_name = f"{event_type}.{subtype}"
                event_counts[subtype_name] = event_counts.get(subtype_name, 0) + 1
            raw_error = event.get("error")
            if isinstance(raw_error, (str, dict, list)):
                event_failure_terms.update(
                    _provider_failure_terms(json.dumps(raw_error, ensure_ascii=False))
                )
            session_id = event.get("session_id")
            if isinstance(session_id, str) and session_id:
                session_ids.add(session_id)
            direct_model = _safe_model_identity(event.get("model"))
            if direct_model is not None:
                models.add(direct_model)
            message = event.get("message")
            if isinstance(message, dict):
                role = message.get("role")
                if isinstance(role, str):
                    item_counts[f"message-{role}"] = item_counts.get(
                        f"message-{role}", 0
                    ) + 1
                message_model = _safe_model_identity(message.get("model"))
                if message_model is not None:
                    models.add(message_model)
                content = message.get("content")
                if isinstance(content, list):
                    for block in content:
                        block_type = block.get("type") if isinstance(block, dict) else None
                        if isinstance(block_type, str):
                            item_counts[block_type] = item_counts.get(block_type, 0) + 1
                        if isinstance(block, dict) and block_type == "tool_use":
                            tool_name = block.get("name")
                            if isinstance(tool_name, str):
                                counter = f"tool-{tool_name}"
                                item_counts[counter] = item_counts.get(counter, 0) + 1
                        if (
                            isinstance(block, dict)
                            and block_type == "tool_result"
                            and block.get("is_error") is True
                        ):
                            tool_error_count += 1
            model_usage = event.get("modelUsage")
            if isinstance(model_usage, dict):
                for raw_model in model_usage:
                    model_id = _safe_model_identity(raw_model)
                    if model_id is not None:
                        models.add(model_id)
            observed_usage = _usage_summary(event.get("usage"))
            if observed_usage:
                usage = observed_usage
            if event_type == "result":
                final_message_observed = True
                result_is_error = event.get("is_error") is True
                if result_is_error and isinstance(event.get("result"), str):
                    event_failure_terms.update(
                        _provider_failure_terms(event["result"])
                    )
                if isinstance(subtype, str) and RECORD_ID.fullmatch(subtype):
                    terminal_event = subtype

    summary: dict[str, Any] = {
        "event_counts": dict(sorted(event_counts.items())),
        "item_type_counts": dict(sorted(item_counts.items())),
        "invalid_lines": invalid_lines,
        "final_message_observed": final_message_observed,
        "usage": usage,
        "tool_error_count": tool_error_count,
        "result_is_error": result_is_error,
        "event_failure_terms": sorted(event_failure_terms),
    }
    if terminal_event is not None:
        summary["terminal_event"] = terminal_event
    if len(session_ids) == 1:
        session_id = next(iter(session_ids))
        summary["thread_id_digest"] = f"sha256:{hashlib.sha256(session_id.encode('utf-8')).hexdigest()}"
    if len(models) == 1:
        summary["resolved_model"] = next(iter(models))
    return summary


def _nested_dicts(value: Any, *, depth: int = 0) -> list[dict[str, Any]]:
    if depth > 5:
        return []
    if isinstance(value, dict):
        values = [value]
        for child in value.values():
            values.extend(_nested_dicts(child, depth=depth + 1))
        return values
    if isinstance(value, list):
        values: list[dict[str, Any]] = []
        for child in value:
            values.extend(_nested_dicts(child, depth=depth + 1))
        return values
    return []


def _parse_grok_events(path: Path) -> dict[str, Any]:
    event_counts: dict[str, int] = {}
    item_counts: dict[str, int] = {}
    invalid_lines = 0
    session_ids: set[str] = set()
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
            dictionaries = _nested_dicts(event)
            update_types: set[str] = set()
            for item in dictionaries:
                for key in ("session_id", "sessionId"):
                    raw_session_id = item.get(key)
                    if isinstance(raw_session_id, str) and raw_session_id:
                        session_ids.add(raw_session_id)
                for key in ("sessionUpdate", "session_update"):
                    update_type = item.get(key)
                    if isinstance(update_type, str):
                        update_types.add(update_type)
                observed_usage = _usage_summary(item.get("usage"))
                if observed_usage:
                    usage = observed_usage
            raw_event_type = event.get("type")
            if not isinstance(raw_event_type, str):
                raw_event_type = event.get("method")
            if not isinstance(raw_event_type, str) and update_types:
                raw_event_type = sorted(update_types)[0]
            event_type = raw_event_type if isinstance(raw_event_type, str) else "json-object"
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
            for update_type in update_types:
                item_counts[update_type] = item_counts.get(update_type, 0) + 1
                if "agent_message" in update_type or update_type in {
                    "result",
                    "completed",
                }:
                    final_message_observed = True
            if event_type in {"result", "completed", "end"}:
                final_message_observed = True

    summary: dict[str, Any] = {
        "event_counts": dict(sorted(event_counts.items())),
        "item_type_counts": dict(sorted(item_counts.items())),
        "invalid_lines": invalid_lines,
        "final_message_observed": final_message_observed,
        "usage": usage,
    }
    if len(session_ids) == 1:
        session_id = next(iter(session_ids))
        summary["thread_id_digest"] = f"sha256:{hashlib.sha256(session_id.encode('utf-8')).hexdigest()}"
    return summary


def _grok_session_metadata(session_root: Path) -> dict[str, str]:
    sessions = session_root / ".grok" / "sessions"
    try:
        summaries = list(sessions.rglob("summary.json"))
    except OSError:
        return {}
    if len(summaries) != 1:
        return {}
    summary_path = summaries[0]
    try:
        if summary_path.stat().st_size > 1024 * 1024:
            return {}
        value = json.loads(summary_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    if not isinstance(value, dict):
        return {}
    result: dict[str, str] = {}
    model = _safe_model_identity(value.get("current_model_id"))
    if model is not None:
        result["resolved_model"] = model
    effort = value.get("reasoning_effort")
    if isinstance(effort, str) and effort in EFFORTS:
        result["applied_effort"] = effort
    sandbox_profile = value.get("sandbox_profile")
    if isinstance(sandbox_profile, str) and RECORD_ID.fullmatch(sandbox_profile):
        result["sandbox_profile"] = sandbox_profile
    return result


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


def _refine_codex_event_failure(
    fallback: str,
    event_summary: Mapping[str, Any],
) -> str:
    """Classify a content-free terminal event when stderr has no signal."""

    if fallback != "provider-startup-unknown":
        return fallback
    terms = set(event_summary.get("event_failure_terms", []))
    if terms & {"oauth", "auth", "authentication", "login"}:
        return "authentication"
    if "network" in terms:
        return "provider-network"
    if (
        event_summary.get("result_is_error") is True
        or event_summary.get("terminal_event") == "turn.failed"
    ):
        return "provider-result-error"
    return fallback


def _classify_provider_failure(provider: str, stderr: str) -> str:
    if provider == "codex":
        return _classify_codex_failure(stderr)
    normalized = stderr.lower()
    classifications = (
        (
            "generation-setting-rejected",
            (
                "reasoning effort",
                "reasoning_effort",
                "invalid value",
                "invalid effort",
                "unknown effort",
                "unsupported effort",
            ),
        ),
        ("sandbox", ("bwrap", "sandbox", "landlock", "seccomp")),
        (
            "configuration",
            ("invalid settings", "config error", "invalid config", "failed schema validation"),
        ),
        ("authentication", ("not logged in", "authentication", "login required", "oauth")),
        ("credential-read-only", ("read-only file system", "device or resource busy")),
        ("model-unavailable", ("unknown model", "model unavailable", "model is not")),
        ("provider-network", ("connection", "dns", "network", "timed out", "websocket")),
    )
    for failure_class, markers in classifications:
        if any(marker in normalized for marker in markers):
            return failure_class
    return "provider-startup-unknown"


def _provider_failure_signals(stderr: str) -> list[str]:
    normalized = stderr.lower()
    vocabulary = (
        ("unknown-option", ("unknown option", "unknown argument", "unexpected argument")),
        ("option-conflict", ("cannot be used with", "mutually exclusive", "conflicts with")),
        (
            "settings-schema-invalid",
            ("failed schema validation", "invalid settings", "settings validation"),
        ),
        (
            "sandbox-unavailable",
            ("sandbox unavailable", "failed to start sandbox", "sandbox could not"),
        ),
        ("sandbox-profile-invalid", ("unknown profile", "invalid profile")),
        ("credential-write-denied", ("read-only file system", "device or resource busy")),
        ("authentication-required", ("not logged in", "login required", "authentication failed")),
        (
            "effort-rejected",
            (
                "invalid reasoning effort",
                "invalid reasoning_effort",
                "invalid effort",
                "unknown effort",
                "unsupported effort",
            ),
        ),
        ("model-unavailable", ("unknown model", "model unavailable", "model is not")),
        ("network-failure", ("connection refused", "dns error", "network error")),
        ("mcp-configuration", ("mcp config", "mcp server")),
        ("permission-mode", ("permission mode", "permission-mode")),
        ("runtime-panic", ("panicked at", "fatal error", "segmentation fault")),
    )
    signals = [
        code for code, markers in vocabulary if any(marker in normalized for marker in markers)
    ]
    if "bwrap" in normalized and any(
        marker in normalized for marker in ("failed", "unavailable", "not found")
    ):
        signals.append("sandbox-unavailable")
    if "socat" in normalized and any(
        marker in normalized for marker in ("required", "unavailable", "not found")
    ):
        signals.append("sandbox-helper-missing")
    return sorted(set(signals))


def _provider_failure_terms(stderr: str) -> list[str]:
    allowlist = {
        "argument",
        "auth",
        "authentication",
        "bash",
        "bwrap",
        "config",
        "configuration",
        "credential",
        "credentials",
        "denied",
        "effort",
        "enoent",
        "eacces",
        "eperm",
        "erofs",
        "error",
        "failed",
        "home",
        "invalid",
        "landlock",
        "login",
        "mcp",
        "model",
        "network",
        "namespace",
        "oauth",
        "option",
        "operation",
        "permitted",
        "permission",
        "plugin",
        "prompt",
        "read-only",
        "required",
        "sandbox",
        "schema",
        "settings",
        "socat",
        "system",
        "stdin",
        "strict",
        "trust",
        "unavailable",
        "unknown",
        "userns",
        "version",
        "workspace",
    }
    observed = {
        match.group(0).lower()
        for match in re.finditer(r"[A-Za-z][A-Za-z0-9_-]*", stderr)
    }
    return sorted(observed & allowlist)


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
    auth_source = _validate_provider_credential_window(
        "codex",
        auth_file,
        timeout_seconds=timeout_seconds,
    )
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
                "/bin/bash",
                "/usr/local/bin/codex",
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
        failure_signals = _provider_failure_signals(error_text)
        failure_terms = _provider_failure_terms(error_text)
        if infrastructure == "success":
            failure_class = None
        elif stop_reason == "safety-cap":
            failure_class = "timeout-cap"
        elif stop_reason == "output-cap":
            failure_class = "output-cap"
        else:
            failure_class = _refine_codex_event_failure(
                _classify_codex_failure(error_text), event_summary
            )

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
        "failure_signals": failure_signals,
        "failure_terms": failure_terms,
        "events": event_summary,
    }


def run_isolated_provider_fixture(
    provider: str,
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
    provider_binary: Path | None = None,
) -> dict[str, Any]:
    """Run one Claude or Grok turn and retain only content-free evidence."""

    if provider not in {"claude", "grok"}:
        raise DurationStudyError("isolated provider runner supports Claude or Grok")
    if not live_generation_authorized:
        raise DurationStudyError("live provider generation requires explicit authorization")
    if MODEL_ID.fullmatch(model) is None:
        raise DurationStudyError(f"{provider} model ID is invalid")
    if effort not in PROVIDER_EFFORTS[provider]:
        raise DurationStudyError(f"{provider} effort is outside the declared study ladder")
    if provider != "grok" and provider_binary is not None:
        raise DurationStudyError("a host-synced provider binary is only supported for Grok")
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0 or timeout_seconds > 3600:
        raise DurationStudyError("live run timeout must be > 0 and <= 3600 seconds")
    if output_bytes_cap < 1024 or output_bytes_cap > 64 * 1024 * 1024:
        raise DurationStudyError("live output cap must be between 1 KiB and 64 MiB")

    manifest = _load_fixture_manifest(fixture_dir)
    workspace = _validate_clean_fixture(fixture_dir, manifest)
    capsule = _capsule_for_fixture(manifest)
    auth_source = _validate_provider_credential_window(
        provider,
        auth_file,
        timeout_seconds=timeout_seconds,
    )
    binary_source = (
        _validate_provider_binary(provider_binary, provider=provider)
        if provider_binary is not None
        else None
    )

    with tempfile.TemporaryDirectory(prefix=f"duration-{provider}-live-") as raw_temp:
        private_root = Path(raw_temp)
        session_root, profile_digest = _prepare_provider_session_root(provider, private_root)
        image_identity = _image_digest(docker_bin, image)
        if sandbox_preflight is None:
            sandbox_preflight = _configured_sandbox_evidence(
                provider,
                manifest=manifest,
                image_digest=image_identity,
                profile_digest=profile_digest,
            )
        sandbox_preflight = _validate_sandbox_preflight(
            sandbox_preflight,
            manifest=manifest,
            provider=provider,
            profile_digest=profile_digest,
        )
        if sandbox_preflight["image_digest"] != image_identity:
            raise DurationStudyError(f"{provider} runtime image changed after preflight")

        raw_output = private_root / "provider-events.jsonl"
        raw_error = private_root / "provider-stderr.log"
        container_name = _owned_container_name(f"{provider}-live")
        command, provider_command = _non_codex_container_base(
            provider=provider,
            docker_bin=docker_bin,
            image=image,
            container_name=container_name,
            fixture_id=manifest["fixture_id"],
            workspace=workspace,
            session_root=session_root,
            auth_file=auth_source,
            provider_binary=binary_source,
        )
        if provider == "claude":
            command.extend(
                [
                    provider_command,
                    "--print",
                    "--input-format",
                    "text",
                    "--output-format",
                    "stream-json",
                    "--verbose",
                    "--model",
                    model,
                    "--effort",
                    effort,
                    "--permission-mode",
                    "dontAsk",
                    "--no-session-persistence",
                    "--safe-mode",
                    "--disable-slash-commands",
                    "--setting-sources",
                    "user",
                    "--settings",
                    "/agent-home/.claude/settings.json",
                    "--tools",
                    "Read,Edit,Write,Bash,Grep,Glob",
                    "--allowedTools",
                    "Read,Edit,Write,Bash,Grep,Glob",
                    "--disallowedTools",
                    "WebFetch,WebSearch,Task",
                    "--strict-mcp-config",
                ]
            )
        else:
            # The model transport remains in-process; strict/custom sandboxing
            # blocks tool filesystem scope and child-process network.
            command[-1:-1] = [
                "--env",
                "GROK_MEMORY=0",
            ]
            command.extend(
                [
                    provider_command,
                    "--no-auto-update",
                    "--no-memory",
                    "--cwd",
                    "/case",
                    "--output-format",
                    "streaming-json",
                    "--prompt-file",
                    "/dev/stdin",
                    "--model",
                    model,
                    "--reasoning-effort",
                    effort,
                    "--permission-mode",
                    "dontAsk",
                    "--sandbox",
                    "duration-fixture",
                    "--tools",
                    "Read,Grep,Glob,Edit,Write,Bash",
                    "--allow",
                    "Read",
                    "--allow",
                    "Grep",
                    "--allow",
                    "Glob",
                    "--allow",
                    "Edit",
                    "--allow",
                    "Write",
                    "--allow",
                    "Bash",
                    "--deny",
                    "WebFetch",
                    "--deny",
                    "WebSearch",
                    "--deny",
                    "Read(/agent-home/.grok/**)",
                    "--deny",
                    "Grep(/agent-home/.grok/**)",
                    "--deny",
                    "Glob(/agent-home/.grok/**)",
                    "--disable-web-search",
                    "--no-subagents",
                    "--max-turns",
                    "64",
                    "--verbatim",
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
                raise DurationStudyError(
                    f"cannot start isolated {provider} live run"
                ) from exc
        elapsed_ms = round((time.monotonic_ns() - started) / 1_000_000, 3)
        output_size = raw_output.stat().st_size
        error_size = raw_error.stat().st_size
        if output_size >= output_bytes_cap or error_size >= output_bytes_cap:
            _cleanup_container(docker_bin, container_name)
            infrastructure = "failure"
            stop_reason = "output-cap"
        event_summary = (
            _parse_claude_events(raw_output)
            if provider == "claude"
            else _parse_grok_events(raw_output)
        )
        session_metadata = (
            _grok_session_metadata(session_root) if provider == "grok" else {}
        )
        error_text = raw_error.read_text(encoding="utf-8", errors="replace")
        failure_signals = _provider_failure_signals(error_text)
        failure_terms = _provider_failure_terms(error_text)
        if infrastructure == "success":
            failure_class = None
        elif stop_reason == "safety-cap":
            failure_class = "timeout-cap"
        elif stop_reason == "output-cap":
            failure_class = "output-cap"
        else:
            failure_class = _classify_provider_failure(provider, error_text)
        event_failure_terms = set(event_summary.get("event_failure_terms", []))
        if provider == "claude" and event_summary.get("result_is_error") is True:
            infrastructure = "failure"
            stop_reason = "provider-exit"
            if event_failure_terms & {"oauth", "auth", "authentication", "login"}:
                failure_class = "authentication"
            elif "network" in event_failure_terms:
                failure_class = "provider-network"
            elif failure_class is None:
                failure_class = "provider-result-error"

        resolved_model = session_metadata.get("resolved_model") or event_summary.get(
            "resolved_model"
        )
        if isinstance(resolved_model, str):
            model_identity = {
                "requested_alias": model,
                "requested_source": "flag",
                "resolved_id": resolved_model,
                "identity_confidence": "exact",
            }
        else:
            model_identity = {
                "requested_alias": model,
                "requested_source": "flag",
                "identity_confidence": "alias-only",
            }
        applied_effort = session_metadata.get("applied_effort")
        if failure_class == "generation-setting-rejected":
            setting_status = "rejected"
        elif infrastructure == "success" and isinstance(applied_effort, str):
            setting_status = "applied"
        else:
            setting_status = "unknown"
        setting: dict[str, Any] = {
            "namespace": f"{provider}.reasoning",
            "key": "effort",
            "requested_value": effort,
            "status": setting_status,
        }
        if setting_status == "applied":
            setting["applied_value"] = applied_effort

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
        "provider": provider,
        "fixture_id": manifest["fixture_id"],
        "case_id": manifest["case"]["case_id"],
        "infrastructure": infrastructure,
        "exit_code": exit_code,
        "stop_reason": stop_reason,
        "failure_class": failure_class,
        "terminal_wall_ms": elapsed_ms,
        "workspace_changed_path_count": changed_count,
        "model_identity": model_identity,
        "generation_settings": [setting],
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
            "task_network": "denied-by-provider-sandbox",
            "sandbox_preflight": "pass",
        },
        "output_cap_bytes": output_bytes_cap,
        "output_bytes": output_size,
        "stderr_bytes": error_size,
        "generation_request_performed": True,
        "failure_signals": failure_signals,
        "failure_terms": failure_terms,
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
        "tool_error_count": events.get("tool_error_count", 0),
        "result_is_error": events.get("result_is_error", False),
        "event_failure_terms": list(events.get("event_failure_terms", [])),
        "generation_request_performed": result["generation_request_performed"],
        "failure_signals": list(result.get("failure_signals", [])),
        "failure_terms": list(result.get("failure_terms", [])),
        "prompt_persisted": False,
        "raw_output_persisted": False,
        "raw_stderr_persisted": False,
        "credential_path_persisted": False,
        "nested_delegation": "disabled-by-feature",
        "task_network": result["runtime"]["task_network"],
        "sandbox_preflight": {
            "assurance": sandbox_preflight.get("assurance", "probed"),
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
    terminal_event = events.get("terminal_event")
    if isinstance(terminal_event, str):
        diagnostics["terminal_event"] = terminal_event
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
    checks = [*result["workspace_checks"], *result["hidden_checks"]]
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
                "scope": item["scope"],
                "status": item["status"],
                "exit_code": item["exit_code"],
                "duration_ms": item["duration_ms"],
            }
            for item in checks
        ],
        "score": dict(result["score"]),
    }


def _live_base_record(
    manifest: dict[str, Any],
    *,
    provider: str,
    study_id: str,
    run_id: str,
    block_id: str,
    model: str,
    effort: str,
    cli_version: str,
    cli_source: str,
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
                        "namespace": f"{provider}.reasoning",
                        "key": "effort",
                        "requested_value": effort,
                        "status": "unknown",
                    }
                ],
                "runtime_identity": {
                    "provider": provider,
                    "cli_name": provider,
                    "cli_version": cli_version,
                    "cli_source": cli_source,
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


def _default_run_id(provider: str, case_id: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    normalized_case = case_id.lower()
    return f"{provider}-{normalized_case}-{timestamp}-{os.getpid()}"


def run_provider_study_once(
    provider: str,
    case_id: str,
    output_dir: Path,
    *,
    image: str,
    model: str,
    effort: str,
    auth_file: Path,
    live_generation_authorized: bool,
    study_id: str = "duration-atlas-wave1",
    block_id: str | None = None,
    run_id: str | None = None,
    docker_bin: str = "docker",
    timeout_seconds: float = 900,
    evaluator_timeout_seconds: float = 30,
    output_bytes_cap: int = 8 * 1024 * 1024,
    provider_binary: Path | None = None,
    clock: EventClock | None = None,
    artifact_retention: str = "content-free-only",
) -> tuple[dict[str, Any], Path]:
    """Run one finite provider sample and atomically join timing with evaluation."""

    if not live_generation_authorized:
        raise DurationStudyError("live provider generation requires explicit authorization")
    if provider not in PROVIDERS:
        raise DurationStudyError(f"unsupported live study provider: {provider}")
    if provider != "grok" and provider_binary is not None:
        raise DurationStudyError("a host-synced provider binary is only supported for Grok")
    if artifact_retention not in ARTIFACT_RETENTIONS:
        raise DurationStudyError("unknown live task artifact retention policy")
    chosen_block_id = block_id or f"{provider}-primary-calibration"
    chosen_run_id = run_id or _default_run_id(provider, case_id)
    for label, value in (
        ("study ID", study_id),
        ("block ID", chosen_block_id),
        ("run ID", chosen_run_id),
    ):
        if RECORD_ID.fullmatch(value) is None:
            raise DurationStudyError(f"{label} does not match the duration-study ID contract")
    if MODEL_ID.fullmatch(model) is None or effort not in PROVIDER_EFFORTS[provider]:
        raise DurationStudyError(f"{provider} model or effort is invalid")
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0 or timeout_seconds > 3600:
        raise DurationStudyError("live run timeout must be > 0 and <= 3600 seconds")
    if (
        not math.isfinite(evaluator_timeout_seconds)
        or evaluator_timeout_seconds <= 0
        or evaluator_timeout_seconds > 300
    ):
        raise DurationStudyError("evaluator timeout must be > 0 and <= 300 seconds")
    _validate_provider_credential_window(
        provider,
        auth_file,
        timeout_seconds=timeout_seconds,
    )
    if provider_binary is not None:
        _validate_provider_binary(provider_binary, provider=provider)

    resolved_output = output_dir.resolve()
    record_path = resolved_output / f"{chosen_run_id}.json"
    if record_path.exists():
        raise DurationStudyError(f"refusing to repeat an existing run ID: {chosen_run_id}")
    active_clock = clock or SystemClock()
    provision_start = event(active_clock)

    fixture_suffix = hashlib.sha256(chosen_run_id.encode("utf-8")).hexdigest()[:12]
    fixture_id = f"{provider}-{case_id.lower()}-{fixture_suffix}"
    with tempfile.TemporaryDirectory(prefix=f"duration-{provider}-study-") as raw_temp:
        fixture_dir = Path(raw_temp) / "fixture"
        manifest = build_fixture(case_id, fixture_dir, fixture_id=fixture_id)
        if provider == "codex":
            sandbox_preflight = probe_codex_agent_sandbox(
                fixture_dir,
                image=image,
                docker_bin=docker_bin,
                timeout_seconds=min(timeout_seconds, 120),
            )
            cli_source = "container-image"
        else:
            preflight_root = Path(raw_temp) / "sandbox-profile"
            _session_root, profile_digest = _prepare_provider_session_root(
                provider,
                preflight_root,
            )
            sandbox_preflight = _configured_sandbox_evidence(
                provider,
                manifest=manifest,
                image_digest=_image_digest(docker_bin, image),
                profile_digest=profile_digest,
            )
            cli_source = "host-sync" if provider_binary is not None else "container-image"
        cli_version = _provider_cli_version(
            provider,
            docker_bin=docker_bin,
            image=image,
            provider_binary=provider_binary,
        )
        provision_ready = event(active_clock)
        recorder = RunRecorder(
            _live_base_record(
                manifest,
                provider=provider,
                study_id=study_id,
                run_id=chosen_run_id,
                block_id=chosen_block_id,
                model=model,
                effort=effort,
                cli_version=cli_version,
                cli_source=cli_source,
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
        if provider == "codex":
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
        else:
            provider_result = run_isolated_provider_fixture(
                provider,
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
                provider_binary=provider_binary,
            )
        participant = recorder.record["participants"][0]
        participant["model_identity"] = dict(provider_result["model_identity"])
        participant["generation_settings"] = [
            dict(item) for item in provider_result["generation_settings"]
        ]
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
        artifact_snapshot = (
            _capture_task_artifacts(fixture_dir, manifest, auth_file)
            if artifact_retention == "task-artifacts"
            else None
        )
        record = recorder.finalize(
            outcome=outcome,
            quality={"evaluator_id": None, "metrics": []},
            diagnostics={
                "provider": provider_diagnostics,
                "evaluator": evaluator_diagnostics,
            },
            artifact_snapshot=artifact_snapshot,
        )
        atomic_write_json(record_path, record)
    return record, record_path


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
    artifact_retention: str = "content-free-only",
) -> tuple[dict[str, Any], Path]:
    """Compatibility entrypoint for the original Codex-only live command."""

    return run_provider_study_once(
        "codex",
        case_id,
        output_dir,
        image=image,
        model=model,
        effort=effort,
        auth_file=auth_file,
        live_generation_authorized=live_generation_authorized,
        study_id=study_id,
        block_id=block_id,
        run_id=run_id,
        docker_bin=docker_bin,
        timeout_seconds=timeout_seconds,
        evaluator_timeout_seconds=evaluator_timeout_seconds,
        output_bytes_cap=output_bytes_cap,
        clock=clock,
        artifact_retention=artifact_retention,
    )
