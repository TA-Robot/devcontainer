# Orchestration benchmark container runbook

This runbook keeps the benchmark loop intentionally small: build one frozen image, start one long-lived container, run the orchestrator in `tmux`, and evaluate the resulting project and trace. It is not a second orchestration system.

## Build and start

Build after changing the devcontainer, `agentctl`, provider adapters, or benchmark readiness checks:

```bash
scripts/test-devcontainer-lock.sh --build
```

Start a benchmark checkout in a named container:

```bash
scripts/benchmark-devcontainer.py start \
  --name robot-soccer-bench-03 \
  --workspace /absolute/path/to/benchmark-project
```

The launcher creates three container-name-scoped volumes:

- `<name>-docker` for the private nested Docker daemon;
- `<name>-agentctl` for durable jobs and attempt evidence;
- `<name>-mira` for content-free collaboration observations.

The dedicated `/var/lib/docker` volume is mandatory. Omitting it can put Docker overlay storage on an incompatible outer overlay filesystem and make simulator containers fail with `invalid argument`. The launcher waits for the nested daemon and runs `agentctl doctor --json`; a stale image that lacks the current provider-auth contract is rejected. A failed readiness check leaves the named container intact for inspection.

Target projects do not need to copy this infrastructure repository's `.devcontainer/devcontainer-lock.json`. Its exact absence is reported as `not_applicable_checks`; a present-but-invalid lock, provider capability mismatch, stale auth contract, or Docker failure remains a readiness failure.

The frozen image includes `tmux` because the normal benchmark path needs one
inspectable terminal owner that survives an operator disconnect. Its impact is
one small distro package in the base image. A detached `codex exec` plus an
explicit terminal marker is a diagnostic fallback, but it is a different
execution surface and must be recorded as such. If interactive benchmark
operation is retired, remove `tmux` from `.devcontainer/Dockerfile`, remove its
image smoke assertion, and update this runbook together.

Host Codex, Claude, and Grok credential directories are bind-mounted when present. API-key variables are forwarded by name only when set; their values are not embedded in the Docker command. This remains a trusted local benchmark profile with a privileged container and shared credentials, not a security boundary.

If the simulator is distributed as an image archive, stream it into the private daemon after startup:

```bash
scripts/benchmark-devcontainer.py load-image \
  --name robot-soccer-bench-03 \
  --archive /absolute/path/to/robot-soccer-simulator.tar
```

## Run the goal

Open a shell, then use ordinary `tmux` and the orchestrator's normal goal command:

```bash
scripts/benchmark-devcontainer.py shell --name robot-soccer-bench-03
command -v tmux && tmux -V  # fail before the run if a stale image lacks it
tmux new -s benchmark
codex
# submit the benchmark through /goal
```

Do not add a benchmark-specific scheduler around this. The evaluation needs the same project contracts, skills, agent relationships, and `agentctl` paths that a normal project receives. Record the immutable starting commit, wall-clock start/end, final commit, evaluator result, agentctl job IDs, and collaboration episode ID so later analysis can reconstruct parallelization and decision flow.

## Inspect and preserve evidence

```bash
scripts/benchmark-devcontainer.py status --name robot-soccer-bench-03
docker exec -it robot-soccer-bench-03 agentctl job list
docker exec -it robot-soccer-bench-03 agentctl supervisor status --json
```

`status` reports outer-container state, nested-Docker readiness, the current doctor result, and provider authentication readiness. Codex and Claude can be verified without a model request. Grok credential presence is only `configuration-only`; require a successful bounded canary before treating it as live-ready.

Stop and resume without deleting container or volume evidence:

```bash
scripts/benchmark-devcontainer.py stop --name robot-soccer-bench-03
scripts/benchmark-devcontainer.py resume --name robot-soccer-bench-03
```

After copying the required evidence, remove only the container:

```bash
scripts/benchmark-devcontainer.py remove --name robot-soccer-bench-03 --force
```

The launcher deliberately preserves all three named volumes. Inspect and delete those exact volumes separately only after the benchmark record is complete; never use a broad Docker prune as benchmark cleanup.
