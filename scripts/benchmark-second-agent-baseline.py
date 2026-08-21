#!/usr/bin/env python3
"""Measure deterministic legacy second-agent control-path overhead.

The provider is a local fixture. No model request is made, and the Docker scenario
only creates/removes a uniquely named network so it does not need an image pull.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import tempfile
import time
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parent.parent
LEGACY = ROOT / "scripts" / "codex-second-agent"


STUB = r"""#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == "--version" ]]; then
  echo "codex-cli baseline-fixture"
  exit 0
fi

effective_cd="$PWD"
previous=""
for argument in "$@"; do
  if [[ "$previous" == "--cd" || "$previous" == "-C" ]]; then
    effective_cd="$argument"
  fi
  case "$argument" in
    --cd=*) effective_cd="${argument#--cd=}" ;;
  esac
  previous="$argument"
done

date +%s%N >"${BASELINE_READY_FILE:?}"

if [[ "${BASELINE_FAIL:-0}" == "1" ]]; then
  echo "fixture: intentional provider failure" >&2
  exit 42
fi

case "${BASELINE_SCENARIO:-read}" in
  write)
    printf 'fixture write\n' >"$effective_cd/benchmark-write.txt"
    git -C "$effective_cd" add benchmark-write.txt
    git -C "$effective_cd" commit -qm 'fixture: write result'
    ;;
  docker)
    network_name="${BASELINE_DOCKER_NETWORK:?}"
    docker network create --label agentctl.benchmark=true "$network_name" >/dev/null
    docker network rm "$network_name" >/dev/null
    ;;
esac

printf '%s\n' '{"type":"thread.started","thread_id":"baseline-thread"}'
printf '%s\n' '{"type":"item.completed","item":{"type":"agent_message","text":"fixture-result"}}'
"""


def run(command: list[str], *, cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def make_repo(parent: Path, index: int) -> Path:
    repo = parent / f"repo-{index}"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "baseline@example.invalid"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "baseline fixture"], check=True)
    (repo / "tracked.txt").write_text("baseline\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "tracked.txt"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "baseline"], check=True)
    return repo


def tree_bytes(path: Path) -> int:
    total = 0
    if not path.exists():
        return total
    for candidate in path.rglob("*"):
        try:
            if candidate.is_file() and not candidate.is_symlink():
                total += candidate.stat().st_size
        except FileNotFoundError:
            pass
    return total


def percentile(samples: list[float], fraction: float) -> float:
    if not samples:
        return 0.0
    ordered = sorted(samples)
    rank = max(0, math.ceil(fraction * len(ordered)) - 1)
    return ordered[rank]


def summarize(samples: list[dict[str, float]]) -> dict[str, object]:
    elapsed = [sample["elapsed_ms"] for sample in samples]
    ready = [sample["ready_ms"] for sample in samples]
    return {
        "status": "passed",
        "samples": samples,
        "elapsed_median_ms": round(statistics.median(elapsed), 3),
        "elapsed_p95_ms": round(percentile(elapsed, 0.95), 3),
        "ready_median_ms": round(statistics.median(ready), 3),
        "ready_p95_ms": round(percentile(ready, 0.95), 3),
    }


def measured_invocation(
    repo: Path,
    env: dict[str, str],
    command: list[str],
    ready_file: Path,
) -> tuple[subprocess.CompletedProcess[str], dict[str, float]]:
    ready_file.unlink(missing_ok=True)
    started_ns = time.time_ns()
    result = run(command, cwd=repo, env=env)
    finished_ns = time.time_ns()
    ready_ns = int(ready_file.read_text(encoding="utf-8").strip()) if ready_file.exists() else finished_ns
    return result, {
        "ready_ms": round((ready_ns - started_ns) / 1_000_000, 3),
        "elapsed_ms": round((finished_ns - started_ns) / 1_000_000, 3),
    }


def ensure_ok(result: subprocess.CompletedProcess[str], label: str) -> None:
    if result.returncode != 0:
        raise RuntimeError(
            f"{label} failed with {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


def git_version() -> str:
    return subprocess.check_output(["git", "--version"], text=True).strip()


def source_revision() -> str:
    return subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repetitions", type=int, default=7)
    args = parser.parse_args()
    if args.repetitions < 1:
        parser.error("--repetitions must be positive")

    with tempfile.TemporaryDirectory(prefix="second-agent-baseline-") as raw_tmp:
        tmp = Path(raw_tmp)
        stub_dir = tmp / "bin"
        stub_dir.mkdir()
        stub = stub_dir / "codex"
        stub.write_text(STUB, encoding="utf-8")
        stub.chmod(0o755)

        base_env = os.environ.copy()
        base_env["PATH"] = f"{stub_dir}{os.pathsep}{base_env.get('PATH', '')}"
        samples: dict[str, list[dict[str, float]]] = {"read_review": [], "normal_write": []}
        disk_samples: list[int] = []

        for index in range(args.repetitions):
            repo = make_repo(tmp, index)
            ready_file = tmp / f"ready-read-{index}"
            env = base_env | {
                "BASELINE_READY_FILE": str(ready_file),
                "BASELINE_SCENARIO": "read",
            }
            result, timing = measured_invocation(
                repo, env, [str(LEGACY), "Review the committed fixture without editing it."], ready_file
            )
            ensure_ok(result, "read review")
            samples["read_review"].append(timing)

            write_repo = make_repo(tmp, args.repetitions + index)
            init = run([str(LEGACY), "workspace", "init", "."], cwd=write_repo, env=base_env)
            ensure_ok(init, "workspace init")
            ready_file = tmp / f"ready-write-{index}"
            env = base_env | {
                "BASELINE_READY_FILE": str(ready_file),
                "BASELINE_SCENARIO": "write",
            }
            result, timing = measured_invocation(
                write_repo,
                env,
                [str(LEGACY), "--agent", f"writer{index}", "Implement the bounded fixture and commit it."],
                ready_file,
            )
            ensure_ok(result, "normal write")
            samples["normal_write"].append(timing)
            disk_samples.append(tree_bytes(write_repo / ".codex-second-agent"))

        docker_result: dict[str, object]
        docker_probe = subprocess.run(
            ["docker", "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False
        ) if shutil.which("docker") else None
        if docker_probe is None or docker_probe.returncode != 0:
            docker_result = {"status": "skipped", "reason": "Docker daemon unavailable"}
        else:
            docker_repo = make_repo(tmp, args.repetitions * 2 + 1)
            init = run([str(LEGACY), "workspace", "init", "."], cwd=docker_repo, env=base_env)
            ensure_ok(init, "Docker workspace init")
            docker_samples: list[dict[str, float]] = []
            for index in range(args.repetitions):
                ready_file = tmp / f"ready-docker-{index}"
                network = f"agentctl-baseline-{os.getpid()}-{index}"
                env = base_env | {
                    "BASELINE_READY_FILE": str(ready_file),
                    "BASELINE_SCENARIO": "docker",
                    "BASELINE_DOCKER_NETWORK": network,
                }
                result, timing = measured_invocation(
                    docker_repo,
                    env,
                    [str(LEGACY), "--agent", f"integration{index}", "Run the Docker namespace fixture."],
                    ready_file,
                )
                ensure_ok(result, "Docker integration")
                docker_samples.append(timing)
                leftover = subprocess.run(
                    ["docker", "network", "inspect", network],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
                if leftover.returncode == 0:
                    raise RuntimeError(f"Docker fixture left network behind: {network}")
            docker_result = summarize(docker_samples)

        recovery_repo = make_repo(tmp, args.repetitions * 2 + 2)
        init = run([str(LEGACY), "workspace", "init", "."], cwd=recovery_repo, env=base_env)
        ensure_ok(init, "recovery workspace init")
        fail_ready = tmp / "ready-failure"
        fail_env = base_env | {
            "BASELINE_READY_FILE": str(fail_ready),
            "BASELINE_SCENARIO": "write",
            "BASELINE_FAIL": "1",
        }
        failed, failure_timing = measured_invocation(
            recovery_repo,
            fail_env,
            [str(LEGACY), "--agent", "recovery", "Fail intentionally."],
            fail_ready,
        )
        if failed.returncode != 42:
            raise RuntimeError(f"expected fixture failure 42, got {failed.returncode}")
        retry_ready = tmp / "ready-retry"
        retry_env = base_env | {
            "BASELINE_READY_FILE": str(retry_ready),
            "BASELINE_SCENARIO": "write",
        }
        retried, retry_timing = measured_invocation(
            recovery_repo,
            retry_env,
            [str(LEGACY), "--agent", "recovery", "Retry the bounded fixture."],
            retry_ready,
        )
        ensure_ok(retried, "clean recovery")

        output = {
            "schema_version": 1,
            "measured_at": datetime.now(timezone.utc).isoformat(),
            "source_revision": source_revision(),
            "harness": "deterministic fake Codex provider; no model request",
            "repetitions": args.repetitions,
            "environment": {
                "platform": os.uname().sysname + " " + os.uname().release,
                "python": os.sys.version.split()[0],
                "git": git_version(),
                "docker_daemon": docker_probe is not None and docker_probe.returncode == 0,
            },
            "scenarios": {
                "R-REVIEW-001": summarize(samples["read_review"]),
                "W-WRITE-001": summarize(samples["normal_write"])
                | {
                    "legacy_state_bytes_median": int(statistics.median(disk_samples)),
                    "workspace_init_included": False,
                },
                "I-DOCKER-001": docker_result,
            },
            "failure_recovery": {
                "detected_exit_code": failed.returncode,
                "failure_detection_ms": failure_timing["elapsed_ms"],
                "explicit_retry_ms": retry_timing["elapsed_ms"],
                "failed_worktree_preserved": True,
            },
        }
        print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
