#!/usr/bin/env python3
"""Measure Lane I runtime candidates without invoking a model.

The executable probes optional Docker Sandboxes (`sbx`) and Docker Agent
installations.  Its runnable comparator is a disposable privileged container
with a private Docker daemon.  The comparator receives only a committed Git
bundle, has no outer network, and returns a result bundle through a dedicated
artifact directory.  It is deliberately *not* described as a security boundary:
privileged Docker-in-Docker shares the host kernel.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_IMAGE = "devcontainer-frozen-smoke:latest"
CONTAINER_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")


PRIVATE_DIND_FIXTURE = r"""set -euo pipefail

daemon_ready_ns="$(date +%s%N)"
inner_daemon_id="$(docker info --format '{{.ID}}')"
if [[ -z "$inner_daemon_id" || "$inner_daemon_id" == "$BENCHMARK_HOST_DAEMON_ID" ]]; then
  echo "private Docker daemon identity is missing or matches the outer daemon" >&2
  exit 31
fi

secret_env_present=false
if env | cut -d= -f1 | grep -Eqi \
  '(api[_-]?key|token|secret|password|passwd|credential|private[_-]?key)'; then
  secret_env_present=true
fi

workspace=/tmp/agentctl-isolated-workspace
git clone -q /run/agentctl/input.bundle "$workspace"
clone_ready_ns="$(date +%s%N)"
git -C "$workspace" config user.email benchmark@example.invalid
git -C "$workspace" config user.name 'agentctl isolated fixture'
printf 'private daemon fixture\n' >"$workspace/isolated-result.txt"
git -C "$workspace" add isolated-result.txt
git -C "$workspace" commit -qm 'fixture: isolated result'
head_sha="$(git -C "$workspace" rev-parse HEAD)"
git -C "$workspace" branch agentctl-result "$head_sha"

network_name=agentctl-isolated-fixture
docker network create \
  --label dev.agentctl.benchmark=true \
  "$network_name" >/dev/null
docker network rm "$network_name" >/dev/null
residual_networks="$(docker network ls \
  --filter label=dev.agentctl.benchmark=true -q | wc -l | tr -d ' ')"
if [[ "$residual_networks" != 0 ]]; then
  echo "private daemon fixture left a labeled network" >&2
  exit 32
fi

git -C "$workspace" bundle create \
  /run/agentctl/artifacts/result.bundle refs/heads/agentctl-result
docker_state_bytes="$(sudo du -sb /var/lib/docker | awk '{print $1}')"
completed_ns="$(date +%s%N)"

jq -n \
  --argjson daemon_ready_ns "$daemon_ready_ns" \
  --argjson clone_ready_ns "$clone_ready_ns" \
  --argjson completed_ns "$completed_ns" \
  --arg inner_daemon_id "$inner_daemon_id" \
  --arg head_sha "$head_sha" \
  --argjson secret_env_present "$secret_env_present" \
  --argjson residual_networks "$residual_networks" \
  --argjson docker_state_bytes "$docker_state_bytes" \
  '{
    schema_version: 1,
    daemon_ready_ns: $daemon_ready_ns,
    clone_ready_ns: $clone_ready_ns,
    completed_ns: $completed_ns,
    inner_daemon_id: $inner_daemon_id,
    head_sha: $head_sha,
    secret_env_present: $secret_env_present,
    residual_networks: $residual_networks,
    docker_state_bytes: $docker_state_bytes,
    workspace_transport: "committed_git_bundle",
    host_workspace_mounted: false,
    outer_network_mode: "none"
  }' >/run/agentctl/artifacts/sample.json
"""


class PilotError(RuntimeError):
    """A deterministic preflight or benchmark invariant failed."""


def run(
    command: list[str],
    *,
    cwd: Path | None = None,
    timeout: float = 120.0,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise PilotError(f"cannot execute {command[0]!r}: {exc}") from exc


def require_ok(result: subprocess.CompletedProcess[str], label: str) -> str:
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()[-3000:]
        raise PilotError(f"{label} failed with {result.returncode}: {detail}")
    return result.stdout.strip()


def percentile(samples: list[float], fraction: float) -> float:
    if not samples:
        return 0.0
    ordered = sorted(samples)
    rank = max(0, math.ceil(fraction * len(ordered)) - 1)
    return ordered[rank]


def tree_bytes(path: Path) -> int:
    total = 0
    for directory, directory_names, file_names in os.walk(path, followlinks=False):
        directory_path = Path(directory)
        directory_names[:] = [
            name for name in directory_names if not (directory_path / name).is_symlink()
        ]
        for name in file_names:
            candidate = directory_path / name
            try:
                if not candidate.is_symlink():
                    total += candidate.stat().st_size
            except OSError:
                continue
    return total


def source_revision() -> str:
    result = run(["git", "-C", str(ROOT), "rev-parse", "HEAD"])
    return require_ok(result, "source revision")


def source_dirty() -> bool:
    result = run(["git", "-C", str(ROOT), "status", "--porcelain", "--untracked-files=all"])
    require_ok(result, "source dirty-state probe")
    return bool(result.stdout.strip())


def harness_sha256() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def docker_client() -> dict[str, Any]:
    docker = shutil.which("docker")
    if not docker:
        return {"available": False, "reason": "Docker CLI is unavailable"}
    version = run([docker, "version", "--format", "{{.Client.Version}}"], timeout=10)
    info = run([docker, "info", "--format", "{{json .ClientInfo.Plugins}}"], timeout=10)
    daemon = run([docker, "info", "--format", "{{.ID}}"], timeout=10)
    plugins: list[dict[str, Any]] = []
    if info.returncode == 0:
        try:
            parsed = json.loads(info.stdout)
            if isinstance(parsed, list):
                plugins = [entry for entry in parsed if isinstance(entry, dict)]
        except json.JSONDecodeError:
            pass
    return {
        "available": version.returncode == 0,
        "path": docker,
        "version": version.stdout.strip() or None,
        "daemon_available": daemon.returncode == 0 and bool(daemon.stdout.strip()),
        "daemon_id": daemon.stdout.strip() or None,
        "plugins": plugins,
        "error": None if version.returncode == 0 else (version.stderr or version.stdout).strip(),
    }


def probe_sbx() -> dict[str, Any]:
    executable = shutil.which("sbx")
    if not executable:
        return {
            "status": "unavailable",
            "reason": "standalone sbx CLI is not installed",
            "required_workspace_mode": "clone",
            "measured": False,
        }
    version = run([executable, "version"], timeout=10)
    return {
        "status": "available_unmeasured" if version.returncode == 0 else "unhealthy",
        "path": executable,
        "version": version.stdout.strip() or None,
        "error": None if version.returncode == 0 else (version.stderr or version.stdout).strip(),
        "kvm_device": Path("/dev/kvm").exists(),
        "required_workspace_mode": "clone",
        "measured": False,
    }


def probe_docker_agent(client: dict[str, Any]) -> dict[str, Any]:
    plugin = next(
        (
            item
            for item in client.get("plugins", [])
            if str(item.get("Name", "")).lower() in {"agent", "docker-agent", "cagent"}
        ),
        None,
    )
    if plugin is None:
        return {
            "status": "unavailable",
            "reason": "Docker Agent CLI plugin is not installed",
            "measured": False,
        }
    return {
        "status": "available_unmeasured",
        "plugin": plugin,
        "measured": False,
        "model_request_performed": False,
    }


def make_fixture_repo(parent: Path, index: int) -> tuple[Path, str]:
    repo = parent / f"fixture-repo-{index}"
    repo.mkdir()
    require_ok(run(["git", "init", "-q", str(repo)]), "fixture git init")
    require_ok(
        run(["git", "-C", str(repo), "config", "user.email", "benchmark@example.invalid"]),
        "fixture email config",
    )
    require_ok(
        run(["git", "-C", str(repo), "config", "user.name", "isolated benchmark"]),
        "fixture name config",
    )
    (repo / "tracked.txt").write_text("isolated fixture base\n", encoding="utf-8")
    require_ok(run(["git", "-C", str(repo), "add", "tracked.txt"]), "fixture add")
    require_ok(run(["git", "-C", str(repo), "commit", "-qm", "fixture base"]), "fixture commit")
    base_sha = require_ok(run(["git", "-C", str(repo), "rev-parse", "HEAD"]), "fixture SHA")
    return repo, base_sha


def validate_result_bundle(bundle: Path, parent: Path, expected_head: str) -> None:
    parent.mkdir(mode=0o700, parents=True)
    require_ok(run(["git", "bundle", "verify", str(bundle)]), "result bundle verification")
    recovered = parent / "recovered"
    require_ok(
        run(["git", "clone", "-q", "-b", "agentctl-result", str(bundle), str(recovered)]),
        "result bundle clone",
    )
    observed_head = require_ok(
        run(["git", "-C", str(recovered), "rev-parse", "HEAD"]), "recovered SHA"
    )
    if observed_head != expected_head:
        raise PilotError(f"recovered head differs: {observed_head} != {expected_head}")
    result_path = recovered / "isolated-result.txt"
    if result_path.read_text(encoding="utf-8") != "private daemon fixture\n":
        raise PilotError("recovered result content differs from the deterministic fixture")


def private_dind_sample(
    docker: str,
    image: str,
    host_daemon_id: str,
    parent: Path,
    index: int,
    *,
    cpus: float,
    memory: str,
) -> dict[str, Any]:
    parent.mkdir(mode=0o700, parents=True)
    repo, base_sha = make_fixture_repo(parent, index)
    input_bundle = parent / f"input-{index}.bundle"
    require_ok(
        run(["git", "-C", str(repo), "bundle", "create", str(input_bundle), "--all"]),
        "input bundle creation",
    )
    artifacts = parent / f"artifacts-{index}"
    artifacts.mkdir(mode=0o700)
    container_name = f"agentctl-isolated-bench-{os.getpid()}-{index}"
    if not CONTAINER_NAME_PATTERN.fullmatch(container_name):
        raise PilotError(f"generated unsafe container name: {container_name!r}")

    create_started = time.time_ns()
    container_id: str | None = None
    try:
        create = run(
            [
                docker,
                "create",
                "--name",
                container_name,
                "--privileged",
                "--network",
                "none",
                "--cpus",
                str(cpus),
                "--memory",
                memory,
                "--pids-limit",
                "2048",
                "--env",
                f"BENCHMARK_HOST_DAEMON_ID={host_daemon_id}",
                "--mount",
                f"type=bind,src={input_bundle},dst=/run/agentctl/input.bundle,readonly",
                "--mount",
                f"type=bind,src={artifacts},dst=/run/agentctl/artifacts",
                image,
                "/usr/local/share/docker-init.sh",
                "bash",
                "-lc",
                PRIVATE_DIND_FIXTURE,
            ],
            timeout=30,
        )
        container_id = require_ok(create, "private DinD container create")
        started = run([docker, "start", "--attach", container_id], timeout=180)
        require_ok(started, "private DinD fixture")
        process_finished = time.time_ns()

        sample_path = artifacts / "sample.json"
        try:
            sample = json.loads(sample_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise PilotError(f"private DinD sample evidence is unreadable: {exc}") from exc
        if not isinstance(sample, dict) or sample.get("schema_version") != 1:
            raise PilotError("private DinD sample evidence has an invalid root/schema")
        if sample.get("secret_env_present") is not False:
            raise PilotError("secret-like environment name reached the disposable worker")
        if sample.get("residual_networks") != 0:
            raise PilotError("job-labeled private-daemon network remains")
        if sample.get("host_workspace_mounted") is not False:
            raise PilotError("benchmark unexpectedly mounted the host workspace")

        result_bundle = artifacts / "result.bundle"
        validate_result_bundle(result_bundle, parent / f"recovery-{index}", str(sample["head_sha"]))
        size = run([docker, "inspect", "--size", "--format", "{{.SizeRw}}", container_id])
        writable_layer_bytes = int(require_ok(size, "container writable-layer size") or "0")
        evidence_bytes = tree_bytes(artifacts)
    finally:
        remove_started = time.time_ns()
        if container_id:
            remove = run([docker, "container", "rm", "--force", container_id], timeout=30)
            if remove.returncode != 0 and "No such container" not in remove.stderr:
                raise PilotError(
                    "scoped private DinD cleanup failed: "
                    + (remove.stderr or remove.stdout).strip()[-1000:]
                )
        removed_at = time.time_ns()

    return {
        "status": "passed",
        "base_sha": base_sha,
        "head_sha": sample["head_sha"],
        "daemon_ready_ms": round((int(sample["daemon_ready_ns"]) - create_started) / 1e6, 3),
        "clone_ready_ms": round((int(sample["clone_ready_ns"]) - create_started) / 1e6, 3),
        "completion_ms": round((process_finished - create_started) / 1e6, 3),
        "teardown_ms": round((removed_at - remove_started) / 1e6, 3),
        "docker_state_bytes": int(sample["docker_state_bytes"]),
        "container_writable_layer_bytes": writable_layer_bytes,
        "evidence_bytes": evidence_bytes,
        "inner_daemon_distinct": sample["inner_daemon_id"] != host_daemon_id,
        "secret_env_present": sample["secret_env_present"],
        "residual_networks": sample["residual_networks"],
        "workspace_transport": sample["workspace_transport"],
        "host_workspace_mounted": sample["host_workspace_mounted"],
        "outer_network_mode": sample["outer_network_mode"],
        "result_bundle_verified": True,
    }


def summarize_samples(samples: list[dict[str, Any]]) -> dict[str, Any]:
    passed = [sample for sample in samples if sample.get("status") == "passed"]
    metrics = (
        "daemon_ready_ms",
        "clone_ready_ms",
        "completion_ms",
        "teardown_ms",
        "docker_state_bytes",
        "container_writable_layer_bytes",
        "evidence_bytes",
    )
    summary: dict[str, Any] = {
        "status": "passed" if len(passed) == len(samples) else "failed",
        "samples": samples,
        "passed": len(passed),
        "failed": len(samples) - len(passed),
    }
    for metric in metrics:
        values = [float(sample[metric]) for sample in passed]
        if values:
            summary[f"{metric}_median"] = round(statistics.median(values), 3)
            summary[f"{metric}_p95"] = round(percentile(values, 0.95), 3)
    return summary


def private_dind_benchmark(
    client: dict[str, Any],
    image: str,
    repetitions: int,
    *,
    cpus: float,
    memory: str,
) -> dict[str, Any]:
    if not client.get("available") or not client.get("daemon_available"):
        return {"status": "skipped", "reason": "Docker CLI/daemon is unavailable"}
    docker = str(client["path"])
    image_probe = run(
        [docker, "image", "inspect", "--format", "{{.Id}}", image], timeout=10
    )
    if image_probe.returncode != 0:
        return {
            "status": "skipped",
            "reason": f"local pilot image is unavailable: {image}",
            "image_pull_performed": False,
        }

    samples: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="agentctl-isolated-pilot-") as raw_temp:
        root = Path(raw_temp)
        for index in range(repetitions):
            try:
                samples.append(
                    private_dind_sample(
                        docker,
                        image,
                        str(client["daemon_id"]),
                        root / f"sample-{index}",
                        index,
                        cpus=cpus,
                        memory=memory,
                    )
                )
            except PilotError as exc:
                samples.append({"status": "failed", "error": str(exc)})
    return summarize_samples(samples) | {
        "runtime": "disposable privileged container with private DinD daemon",
        "image": image,
        "image_id": image_probe.stdout.strip(),
        "image_pull_performed": False,
        "model_request_performed": False,
        "security_boundary_accepted": False,
        "reason": "private daemon and narrow mounts reduce collision/exposure, but --privileged shares the host kernel",
        "resource_limits": {"cpus": cpus, "memory": memory, "pids": 2048},
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Probe and deterministically benchmark optional Lane I runtimes"
    )
    parser.add_argument("--repetitions", type=int, default=5)
    parser.add_argument("--image", default=os.environ.get("AGENTCTL_ISOLATED_PILOT_IMAGE", DEFAULT_IMAGE))
    parser.add_argument("--cpus", type=float, default=2.0)
    parser.add_argument("--memory", default="3g")
    parser.add_argument(
        "--probe-only",
        action="store_true",
        help="report capabilities without creating a disposable private-DinD container",
    )
    args = parser.parse_args()
    if not 1 <= args.repetitions <= 20:
        parser.error("--repetitions must be between 1 and 20")
    if not 0.25 <= args.cpus <= 256:
        parser.error("--cpus must be between 0.25 and 256")
    if not re.fullmatch(r"[1-9][0-9]*(?:[kKmMgG])?", args.memory):
        parser.error("--memory must be a positive Docker memory value such as 3g")

    client = docker_client()
    private_dind = (
        {"status": "not_run", "reason": "--probe-only"}
        if args.probe_only
        else private_dind_benchmark(
            client,
            args.image,
            args.repetitions,
            cpus=args.cpus,
            memory=args.memory,
        )
    )
    payload = {
        "schema_version": 1,
        "measured_at": datetime.now(timezone.utc).isoformat(),
        "source_revision": source_revision(),
        "source_dirty": source_dirty(),
        "harness_sha256": harness_sha256(),
        "harness": "deterministic fixtures only; no model request and no image pull",
        "environment": {
            "platform": os.uname().sysname + " " + os.uname().release,
            "python": sys.version.split()[0],
            "docker": client,
            "kvm_device": Path("/dev/kvm").exists(),
        },
        "candidates": {
            "docker_sandboxes": probe_sbx(),
            "docker_agent": probe_docker_agent(client),
            "private_dind": private_dind,
        },
        "decision": {
            "stable_isolated_adapter_enabled": False,
            "shared_container_fallback_allowed": False,
            "next_gate": "measure sbx clone mode on a host with sbx/KVM and compare the same Git/result fixture",
        },
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if private_dind.get("status") == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
