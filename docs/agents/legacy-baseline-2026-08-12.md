# Legacy `second-agent` baseline — 2026-08-12

This is the first Phase 0 control-path baseline for ADR-0001. It is deliberately
not a model benchmark: a deterministic local Codex fixture emits a result as soon
as the legacy wrapper reaches it.

## Environment

- Host/kernel: WSL2, Linux `6.6.87.2-microsoft-standard-WSL2`
- Python: `3.12.10`
- Git: `2.43.0`
- Docker daemon: available, client/server `29.6.0`
- Source HEAD: `e78d4965d20c7602fed8cf8dfd61e52f941f50f2`
- Repetitions: 7 fresh repositories per read/write scenario
- Fixture: local fake Codex process; no authentication, network, token, or model
  latency

The source worktree contained unrelated uncommitted work. The benchmark creates
all repositories, state, worktrees, branches, and Docker networks under temporary
or uniquely named locations and removes them at exit.

## Results

| Scenario | Ready median / p95 | Complete median / p95 | Notes |
|---|---:|---:|---|
| R-REVIEW-001 | 222.595 / 737.795 ms | 463.626 / 1104.640 ms | fresh default-agent state |
| W-WRITE-001 | 325.152 / 427.819 ms | 589.899 / 897.109 ms | auto-worktree + fixture commit; prior `workspace init` excluded |
| I-DOCKER-001 proxy | 238.951 / 328.105 ms | 1033.806 / 1356.778 ms | unique labeled network create/remove; no image pull |

One W-WRITE-001 run produced a median 636 bytes of legacy state, excluding Git
object/worktree storage. The figure is a lower bound because the fixture emits
only two tiny events and one transcript record.

## Failure and recovery observation

The fixture exited 42 before emitting a provider event.

- failure detection: 545.031 ms;
- the legacy worktree was preserved;
- an explicit retry in the same legacy agent/worktree completed in 1492.131 ms.

This demonstrates recoverability of partial files, but not clean-attempt
semantics. The current wrapper reuses agent identity, session location, branch,
and worktree. The new fabric must preserve the failed attempt and create a new
attempt from the immutable base when `retry --clean` is requested.

## Interpretation and next comparison

The ready values are wrapper, state, Git, process, and filesystem overhead that
exists before any useful model work. They therefore establish an actionable
floor for the new control plane. They do not set a user-facing SLO yet: WSL
filesystem scheduling produced visible variance, and live provider latency is
orders of magnitude more variable.

Repeat the same script after the first Lane W prototype, then add separately
labeled live canaries for Codex and Claude. A result is an improvement only if it
also preserves correct failure state, leaves the primary checkout unchanged, and
does not leave Docker resources behind.

Reproduce with:

```bash
scripts/benchmark-second-agent-baseline.py --repetitions 7
```
