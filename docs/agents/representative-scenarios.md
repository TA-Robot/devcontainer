# Multi-agent representative scenarios

These three scenarios are the stable comparison set for the legacy wrappers,
the new execution fabric, and optional isolated runtimes. They measure the whole
operator-visible path, not model quality in isolation.

## Measurement rules

- Record the toolchain channel, provider/version, machine/container identity,
  base SHA, cache state, and whether the provider is real or a deterministic
  fixture.
- Measure at least five repetitions and report every sample plus median and p95.
- Separate `process ready` from `first useful result` and total completion time.
- A failed run remains a failed sample; do not silently retry it away.
- Record residual worktrees, branches, logs, Docker resources, and disk bytes.
- Deterministic fixture runs establish wrapper/control-plane overhead. Live model
  runs are a separate canary and must not be compared as if they were equivalent.

## R-REVIEW-001: read-only review

Objective: review a small committed diff and return three ranked findings without
editing the checkout.

- Lane: R
- Role: reviewer
- Input: base/head SHA and a bounded review prompt
- Required access: repository read and `git diff`
- Forbidden effects: file writes, branch creation, package install, Docker use
- Result: structured findings with severity, path, line, and rationale
- Success: first useful finding is produced and the primary checkout remains
  byte-for-byte unchanged
- Failure/recovery: restart a fresh native read task; no worktree or state cleanup
  should be necessary

Measurements: dispatch overhead, provider ready time, first useful result, total
time, checkout status, and manual actions.

## W-WRITE-001: ordinary implementation

Objective: make one bounded source change, add/update a unit test, run the named
check, and return a committed result.

- Lane: W
- Role: implementer
- Input: immutable base SHA, allowed paths, acceptance command, and constraints
- Required access: one job worktree and repository-local toolchain/cache
- Forbidden effects: writing the primary checkout, merge, push, global cleanup
- Result: head SHA, computed changed paths, check status, risks, and follow-ups
- Success: worktree becomes ready, the change is committed from the expected
  base, validation passes, and the primary checkout remains unchanged
- Failure/recovery: preserve failed-attempt evidence; create a clean attempt from
  the same immutable base only after an explicit retry

Measurements: worktree-ready time, provider ready time, total time, validation
time, worktree/log disk bytes, conflicts, and manual recovery actions.

## I-DOCKER-001: Docker integration

Objective: start a minimal service, verify it from a test process, and tear down
only resources owned by the job.

- Lane: W while using the trusted shared daemon; Lane I when independent daemon
  or stronger isolation is required
- Role: integration implementer
- Required namespace: `COMPOSE_PROJECT_NAME=agent_<job-id>` plus job labels
- Required resources: job-specific network, temporary directory, and dynamic or
  internal-only port
- Forbidden effects: fixed shared project names, `docker system prune`, broad
  volume deletion, or cleanup by an unresolved shell variable
- Success: two concurrent copies can complete without collision and scoped
  teardown leaves no labeled resource
- Failure/recovery: inventory by job label/lease, retain logs, and remove only
  resources whose ownership can be proven

Measurements: queue time for the integration slot, runtime startup/teardown,
cache hits, port/network collisions, residual resources, disk growth, and manual
recovery actions.

## Current deterministic baseline

Run the legacy control-path fixture with:

```bash
scripts/benchmark-second-agent-baseline.py --repetitions 7
```

The Docker fixture creates and removes a uniquely labeled Docker network; it does
not pull an image. This intentionally measures daemon/namespace overhead without
network-dependent image pulls. Live provider and real Compose canaries are added
to the same scenario IDs, but reported separately.

## Current isolated-runtime pilot

Probe optional Lane I runtimes and run the deterministic private-daemon
comparator with:

```bash
scripts/benchmark-isolated-runtime-pilot.py --probe-only
scripts/benchmark-isolated-runtime-pilot.py --repetitions 5
```

The runnable comparator performs no model request and no image pull. It passes a
committed Git bundle into a disposable private-DinD container, exercises scoped
Docker network creation/removal, and verifies a returned result bundle. Its
measurements and non-security-boundary decision are recorded in
`docs/agents/isolated-runtime-pilot-2026-08-12.md`. Docker Sandboxes and Docker
Agent remain `available_unmeasured` or `unavailable` until their real CLI/plugin
exists on the host; the harness never converts an absent candidate into a pass.
