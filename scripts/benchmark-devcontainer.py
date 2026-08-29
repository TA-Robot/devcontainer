#!/usr/bin/env python3
"""Run a reproducible long-lived benchmark container from the frozen image."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Any


DEFAULT_IMAGE = "devcontainer-frozen-smoke:latest"
NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,62}$")
FORWARDED_SECRET_ENV = (
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "XAI_API_KEY",
    "GEMINI_API_KEY",
    "SAKANA_API_KEY",
)


class BenchmarkContainerError(RuntimeError):
    """A scoped benchmark-container operation failed."""


def require_name(value: str) -> str:
    if not NAME_PATTERN.fullmatch(value):
        raise BenchmarkContainerError(
            "container name must start with an alphanumeric character and contain only "
            "letters, numbers, dot, underscore, or dash (maximum 63 characters)"
        )
    return value


def require_workspace(value: str | Path) -> Path:
    workspace = Path(value).expanduser().resolve()
    if not workspace.is_dir():
        raise BenchmarkContainerError(f"workspace is not a directory: {workspace}")
    if any(character in str(workspace) for character in (",", "\n", "\r")):
        raise BenchmarkContainerError("workspace path contains a Docker --mount delimiter")
    return workspace


def _bind_mount(source: Path, destination: str, *, readonly: bool = False) -> str:
    option = f"type=bind,src={source},dst={destination}"
    return option + (",readonly" if readonly else "")


def build_start_command(
    *,
    docker: str,
    name: str,
    workspace: Path,
    image: str,
    host_home: Path,
    environment: dict[str, str],
) -> list[str]:
    """Build a command without embedding credential values in argv."""

    name = require_name(name)
    workspace = require_workspace(workspace)
    command = [
        docker,
        "run",
        "--detach",
        "--name",
        name,
        "--hostname",
        name,
        "--privileged",
        "--security-opt",
        "seccomp=unconfined",
        "--workdir",
        "/workspace",
        "--label",
        "dev.agentctl.benchmark=true",
        "--label",
        f"dev.agentctl.benchmark.name={name}",
        "--mount",
        _bind_mount(workspace, "/workspace"),
        "--mount",
        f"type=volume,src={name}-docker,dst=/var/lib/docker",
        "--mount",
        f"type=volume,src={name}-agentctl,dst=/var/lib/agentctl",
        "--mount",
        f"type=volume,src={name}-mira,dst=/var/lib/mira-observations",
        "--env",
        "MIRA_COMPANION_ENABLED=1",
        "--env",
        "MIRA_COMPANION_EPISODES_ENABLED=1",
        "--env",
        "MIRA_COMPANION_STATE_DIR=/home/devuser/.local/state/mira-companion",
        "--env",
        "MIRA_COMPANION_EPISODE_DIR=/var/lib/mira-observations",
    ]
    credential_mounts = (
        (host_home / ".codex", "/home/devuser/.codex", False),
        (host_home / ".claude", "/home/devuser/.claude", False),
        (host_home / ".claude.json", "/home/devuser/.claude.json", False),
        (host_home / ".grok", "/home/devuser/.grok", False),
        (host_home / ".gitconfig", "/home/devuser/.gitconfig", True),
    )
    for source, destination, readonly in credential_mounts:
        if source.exists():
            command.extend(
                ["--mount", _bind_mount(source.resolve(), destination, readonly=readonly)]
            )
    for variable in FORWARDED_SECRET_ENV:
        if environment.get(variable):
            # Docker imports the value from this process; argv contains only its name.
            command.extend(["--env", variable])
    command.extend(
        [
            image,
            "/usr/local/share/docker-init.sh",
            "bash",
            "-lc",
            "while :; do sleep 3600; done",
        ]
    )
    return command


def run(
    argv: list[str],
    *,
    input_file: Any = None,
    timeout: float = 30,
    capture: bool = True,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            argv,
            stdin=input_file,
            text=True,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.PIPE if capture else None,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise BenchmarkContainerError(f"cannot run {argv[0]!r}: {exc}") from exc


def require_ok(result: subprocess.CompletedProcess[str], action: str) -> str:
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()[-2000:]
        raise BenchmarkContainerError(f"{action} failed ({result.returncode}): {detail}")
    return (result.stdout or "").strip()


def container_exists(docker: str, name: str) -> bool:
    result = run([docker, "container", "inspect", name])
    return result.returncode == 0


def wait_for_nested_docker(docker: str, name: str, timeout_seconds: float) -> str:
    deadline = time.monotonic() + timeout_seconds
    last_error = "nested Docker did not answer"
    while time.monotonic() < deadline:
        result = run(
            [docker, "exec", name, "docker", "info", "--format", "{{.ServerVersion}}"],
            timeout=5,
        )
        if result.returncode == 0 and result.stdout and result.stdout.strip():
            return result.stdout.strip()
        last_error = (result.stderr or result.stdout or last_error).strip()[-1000:]
        time.sleep(0.5)
    raise BenchmarkContainerError(
        f"nested Docker was not ready after {timeout_seconds:g}s: {last_error}; "
        f"inspect with `docker logs {name}`"
    )


def summarize_doctor_payload(payload: dict[str, Any], returncode: int) -> dict[str, Any]:
    capabilities = payload.get("capabilities", {})
    provider_auth = {
        provider: capabilities.get(provider, {}).get("auth")
        for provider in ("codex", "claude", "grok")
    }
    auth_contract_ready = all(isinstance(value, dict) for value in provider_auth.values())
    failed = [
        check
        for check in payload.get("checks", [])
        if isinstance(check, dict) and check.get("status") == "fail"
    ]
    not_applicable = [
        check.get("id")
        for check in failed
        if check.get("id") == "toolchain.feature_lock"
        and check.get("summary") == "Dev Container Feature lockfile is missing"
    ]
    failed_checks = [
        check.get("id") for check in failed if check.get("id") not in not_applicable
    ]
    if not auth_contract_ready:
        failed_checks.append("provider.auth-contract")
    return {
        "ok": not failed_checks and auth_contract_ready,
        "returncode": returncode,
        "auth_contract_ready": auth_contract_ready,
        "provider_auth": provider_auth,
        "failed_checks": failed_checks,
        "not_applicable_checks": not_applicable,
    }


def doctor_summary(docker: str, name: str) -> dict[str, Any]:
    result = run(
        [docker, "exec", name, "agentctl", "doctor", "--json", "--workspace", "/workspace"],
        timeout=30,
    )
    try:
        payload = json.loads(result.stdout or "")
    except json.JSONDecodeError as exc:
        raise BenchmarkContainerError(
            f"agentctl doctor returned unreadable output: {(result.stderr or result.stdout or '').strip()[-1000:]}"
        ) from exc
    if not isinstance(payload, dict):
        raise BenchmarkContainerError("agentctl doctor did not return a JSON object")
    return summarize_doctor_payload(payload, result.returncode)


def start(args: argparse.Namespace) -> int:
    name = require_name(args.name)
    workspace = require_workspace(args.workspace)
    if container_exists(args.docker, name):
        raise BenchmarkContainerError(
            f"container already exists: {name}; use `status`, `stop`, or `remove` explicitly"
        )
    command = build_start_command(
        docker=args.docker,
        name=name,
        workspace=workspace,
        image=args.image,
        host_home=Path.home(),
        environment=os.environ,
    )
    container_id = require_ok(run(command, timeout=60), "benchmark container start")
    docker_version = wait_for_nested_docker(args.docker, name, args.wait_seconds)
    summary = doctor_summary(args.docker, name)
    output = {
        "status": "started",
        "name": name,
        "container_id": container_id,
        "workspace": str(workspace),
        "image": args.image,
        "nested_docker_version": docker_version,
        "doctor": summary,
        "shell_command": f"{args.docker} exec -it {name} bash",
    }
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["ok"] else 1


def status(args: argparse.Namespace) -> int:
    name = require_name(args.name)
    inspect = run(
        [args.docker, "container", "inspect", name, "--format", "{{json .State}}"]
    )
    state_text = require_ok(inspect, "container inspect")
    try:
        state = json.loads(state_text)
    except json.JSONDecodeError as exc:
        raise BenchmarkContainerError("Docker returned an invalid container state") from exc
    nested = run(
        [args.docker, "exec", name, "docker", "info", "--format", "{{.ServerVersion}}"],
        timeout=5,
    )
    doctor = doctor_summary(args.docker, name) if nested.returncode == 0 else None
    print(
        json.dumps(
            {
                "name": name,
                "state": state,
                "nested_docker_ready": nested.returncode == 0,
                "nested_docker_version": (nested.stdout or "").strip() or None,
                "doctor": doctor,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def resume(args: argparse.Namespace) -> int:
    name = require_name(args.name)
    require_ok(run([args.docker, "container", "start", name], timeout=30), "container start")
    docker_version = wait_for_nested_docker(args.docker, name, args.wait_seconds)
    summary = doctor_summary(args.docker, name)
    print(
        json.dumps(
            {
                "status": "running",
                "name": name,
                "nested_docker_version": docker_version,
                "doctor": summary,
                "shell_command": f"{args.docker} exec -it {name} bash",
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if summary["ok"] else 1


def stop(args: argparse.Namespace) -> int:
    name = require_name(args.name)
    require_ok(run([args.docker, "container", "stop", name], timeout=30), "container stop")
    print(f"stopped {name}; benchmark volumes were preserved")
    return 0


def remove(args: argparse.Namespace) -> int:
    name = require_name(args.name)
    command = [args.docker, "container", "rm"]
    if args.force:
        command.append("--force")
    command.append(name)
    require_ok(run(command, timeout=30), "container remove")
    print(f"removed container {name}; benchmark volumes were preserved")
    return 0


def load_image(args: argparse.Namespace) -> int:
    name = require_name(args.name)
    archive = Path(args.archive).expanduser().resolve()
    if not archive.is_file():
        raise BenchmarkContainerError(f"image archive is not a file: {archive}")
    with archive.open("rb") as source:
        result = run(
            [args.docker, "exec", "--interactive", name, "docker", "load"],
            input_file=source,
            timeout=args.timeout,
        )
    print(require_ok(result, "nested Docker image load"))
    return 0


def shell(args: argparse.Namespace) -> int:
    name = require_name(args.name)
    os.execvp(args.docker, [args.docker, "exec", "--interactive", "--tty", name, "bash"])
    return 127


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument("--docker", default=os.environ.get("BENCHMARK_DOCKER_BIN", "docker"))
    commands = root.add_subparsers(dest="command", required=True)

    start_parser = commands.add_parser("start", help="create and verify a benchmark container")
    start_parser.add_argument("--name", required=True)
    start_parser.add_argument("--workspace", required=True)
    start_parser.add_argument("--image", default=os.environ.get("DEVCONTAINER_FROZEN_IMAGE", DEFAULT_IMAGE))
    start_parser.add_argument("--wait-seconds", type=float, default=60)
    start_parser.set_defaults(handler=start)

    for command_name, handler in (
        ("status", status),
        ("stop", stop),
        ("shell", shell),
    ):
        command = commands.add_parser(command_name)
        command.add_argument("--name", required=True)
        command.set_defaults(handler=handler)

    resume_parser = commands.add_parser("resume", help="restart and verify a stopped benchmark container")
    resume_parser.add_argument("--name", required=True)
    resume_parser.add_argument("--wait-seconds", type=float, default=60)
    resume_parser.set_defaults(handler=resume)

    remove_parser = commands.add_parser("remove", help="remove only the named container; preserve volumes")
    remove_parser.add_argument("--name", required=True)
    remove_parser.add_argument("--force", action="store_true")
    remove_parser.set_defaults(handler=remove)

    load_parser = commands.add_parser("load-image", help="stream an image archive into nested Docker")
    load_parser.add_argument("--name", required=True)
    load_parser.add_argument("--archive", required=True)
    load_parser.add_argument("--timeout", type=float, default=120)
    load_parser.set_defaults(handler=load_image)
    return root


def main() -> int:
    try:
        args = parser().parse_args()
        if hasattr(args, "wait_seconds") and not 1 <= args.wait_seconds <= 300:
            raise BenchmarkContainerError("--wait-seconds must be between 1 and 300")
        if hasattr(args, "timeout") and not 1 <= args.timeout <= 3600:
            raise BenchmarkContainerError("--timeout must be between 1 and 3600")
        return int(args.handler(args))
    except BenchmarkContainerError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
