# Isolated runtime pilot: 2026-08-12

This pilot establishes a deterministic Lane I comparison path. It does not run
Codex, Claude, or any model request, does not pull an image, and does not enable
an isolated `agentctl` adapter.

## Candidate discovery

The current Docker Sandboxes surface is the standalone `sbx` CLI, not a
`docker sandbox` subcommand. Docker documents a microVM, private Docker Engine,
host-side network/credential proxy, and opt-in private Git clone; its
[`sbx create --clone`](https://docs.docker.com/reference/cli/sbx/create/) flow is
the relevant Lane I candidate. Docker Agent remains a separate Docker CLI
plugin, as described by its [installation guide](https://docs.docker.com/ai/docker-agent/).

Local capability probe:

- platform: WSL2 Linux `6.6.87.2-microsoft-standard-WSL2`;
- `/dev/kvm`: present;
- Docker client/daemon: available, client `29.6.0`;
- Docker client plugins: Buildx and Compose only;
- `sbx`: not installed;
- Docker Agent plugin: not installed.

The pilot does not install either optional dependency. Doing so would add a
host-level runtime, sign-in/state, upgrade, and rollback surface before its
benefit has been measured.

## Runnable comparator

`scripts/benchmark-isolated-runtime-pilot.py` runs the locally built
`devcontainer-frozen-smoke:latest` image as a disposable privileged container.
The Dev Container DinD entrypoint starts a private daemon. Each sample has:

- 2 CPUs, 3 GiB memory, and a 2048 PID limit;
- outer network mode `none`;
- no forwarded credential variables and no host Docker socket;
- no host workspace mount;
- one read-only committed Git bundle as input;
- one dedicated temporary artifact directory as output;
- a distinct inner Docker daemon;
- one uniquely labeled private-daemon network, removed and inventoried before completion;
- one result Git bundle, verified and cloned on the host before cleanup.

The comparator deliberately uses only committed state. Untracked files,
repository-local credentials, host Git configuration, and the primary checkout
never cross the mount boundary.

## Five-sample result

Command:

```bash
scripts/benchmark-isolated-runtime-pilot.py --repetitions 5
```

The harness completed 5/5 samples. Values are milliseconds except byte counts.

| Measurement | Median | p95 |
|---|---:|---:|
| private daemon ready | 2575.626 | 3319.852 |
| private Git clone ready | 2716.281 | 3479.477 |
| fixture + Docker network + result bundle complete | 3487.356 | 4249.880 |
| scoped container teardown | 80.875 | 100.273 |
| inner Docker state bytes | 372833 | 372833 |
| outer container writable-layer bytes | 279103 | 279103 |
| returned evidence bytes | 1095 | 1095 |

The measured image ID was
`sha256:aac4be136abb9e9c7f84a5d735811ba7e24472ba8acad667a48a3b491904a89b`
and the harness SHA-256 was
`ea42fc0a6aef165a8dfd709bcb539e71429f367d5d9d2c61edb89198b4971344`.
The repository had unrelated/uncommitted development state, so the report marks
`source_dirty: true` instead of pretending the recorded Git HEAD fully identifies
the harness.

Every sample proved:

- the inner daemon ID differed from the outer daemon;
- no secret-like environment name reached the worker;
- the host workspace was not mounted;
- the outer container had no network;
- no benchmark-labeled inner network remained;
- the returned commit bundle was valid and contained the expected deterministic result.

The first development run failed only because the harness attempted to measure
`/var/lib/docker` without elevation. The fixture, Git recovery, and scoped Docker
cleanup had completed; the observation command was corrected to `sudo du`, and
the five recorded samples then passed. This pre-measurement run is not silently
included as a successful sample.

## What this does and does not prove

The roughly 4.3-second p95 makes a private daemon a viable performance
comparator for infrequent integration work. It also proves that a committed
bundle/result-bundle transport can avoid sharing the primary checkout and its
untracked files.

It is not an accepted Lane I security boundary. `--privileged` DinD still shares
the host kernel; Docker's own [Sandboxes architecture comparison](https://docs.docker.com/ai/sandboxes/architecture/)
classifies DinD as partial isolation, while Sandboxes use a microVM. The fixture
also does not measure image pulls, BuildKit cache hits, Compose service health,
real untrusted code, provider authentication, or live agent output quality.

Docker Sandboxes clone mode has stronger Git semantics: the host repository is
read-only and work happens in a private clone. However, Docker explicitly notes
that the read-only source covers the whole Git root, including untracked and
ignored files, and clone creation must start from the main checkout rather than
a linked worktree. Those details must be tested against this repository's
credential and job/worktree rules before adoption; see the official
[isolation model](https://docs.docker.com/ai/sandboxes/security/isolation/) and
[usage constraints](https://docs.docker.com/ai/sandboxes/usage/).

## Decision and next gate

- Keep `AGENTCTL_CAPACITY_ISOLATED=0` and continue rejecting same-container fallback.
- Keep the private-DinD comparator as a measured lower-overhead/runtime baseline,
  not a production security adapter.
- On a host where `sbx` is intentionally installed and authenticated, run the
  same committed-bundle, private-daemon, result-recovery, startup, disk, and
  cleanup measurements in clone mode.
- Measure Docker Agent only after its plugin is intentionally installed, and
  keep model-bearing canaries separate from deterministic control-plane data.
- Choose an adapter only after credential exposure, main-checkout constraints,
  cache behavior, Compose compatibility, teardown, and rollback all pass.

`--probe-only` can be used at any time without starting a candidate runtime:

```bash
scripts/benchmark-isolated-runtime-pilot.py --probe-only
```
