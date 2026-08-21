# ADR-0001: Native-first multi-agent execution fabric

- Status: Accepted for phased implementation
- Date: 2026-08-12
- Owners: repository maintainers
- Decision source: `temp/multi-agent-refresh/03-recommendation-and-roadmap.md`

## Context

The legacy `second-agent` wrapper combines provider invocation, session identity,
workspace selection, worktree lifecycle, logs, and permission bypass in one Bash
process. It is useful, but adding more providers, retries, detached jobs, resource
leases, and recovery semantics to that process would make correctness harder to
verify. Provider-native subagents now also cover interactive planning and
read-only fan-out better than a common wrapper can.

The platform still needs a provider-neutral layer for durable write jobs. That
layer must improve startup speed and recovery without recreating provider
conversations or pretending that a shared privileged container is a security
boundary.

## Decision

Adopt a native-first architecture with three explicit execution lanes.

| Lane | Default use | Workspace/runtime | Isolation claim |
|---|---|---|---|
| R: read | research, review, planning, decomposition | provider-native subagents in the primary checkout | read policy and provider sandbox only |
| W: write | ordinary trusted implementation and unit tests | one job per Git worktree in the current devcontainer | Git/workspace separation, not OS isolation |
| I: isolated | untrusted code, credential-sensitive work, destructive or conflicting Docker integration | disposable runtime or hosted worker | runtime-specific isolation, verified before use |

The first routing question is whether the task writes. Read-only work stays in
Lane R. Trusted writes use Lane W. Tasks needing a real security boundary or an
independent Docker daemon use Lane I.

### Control-plane ownership

The new `agentctl` control plane owns only:

- project, job, and attempt identity;
- immutable base SHA;
- worktree, branch, process, and resource leases;
- state transitions, heartbeat, cancellation, and orphan detection;
- bounded logs, task/result validation, and commit collection;
- explicit garbage-collection candidates.

It does not own provider conversations, native subagent topology, planning,
token accounting, raw event normalization, implicit retries, merge/push/PR
actions, or security isolation inside the current privileged container.

### Integration and state rules

- A role is reusable policy; a job is one objective; an attempt is one execution.
- Retries create a new attempt and never overwrite prior evidence.
- A missing process is not success. Success requires a zero exit status, a valid
  result, and the expected Git state.
- Workers do not merge or push. A single coordinator validates and integrates
  returned commits.
- Runtime state lives outside the repository once the new fabric is introduced.
  Prompts, raw transcripts, and secrets are not stored in the metadata database.

### Permissions and toolchain

- Normal `codex` and `claude` commands are safe by default and do not inject
  dangerous bypass flags.
- The legacy-equivalent path is explicitly named `codex-trusted` or
  `claude-trusted`; it is not a security boundary.
- Stable images pin the base image, Dev Container Features, Node, global npm
  tools, and provider CLIs. Stable startup performs no package update.
- Host-version synchronization and newer CLI canaries are an opt-in edge channel.
- Capability probes, rather than version-number assumptions, gate provider
  adapters.

### Legacy migration

`second-agent`, `codex-second-agent`, and `claude-second-agent` enter feature
freeze. They receive security, data-loss, and compatibility fixes only. The new
command is introduced alongside them; old commands are never silently redirected
and old state is never automatically deleted. Retirement requires the gates below
and at least one observed release cycle.

## Consequences

Positive consequences:

- Interactive read fan-out stays close to the provider's supported UX.
- Normal writes retain low latency and shared caches while gaining job identity.
- Job state, process state, and retries can be made transactional and testable.
- Provider upgrades can be rejected before a real job when required capabilities
  disappear.

Costs and limitations:

- There are two intentional surfaces: provider-native interaction and `agentctl`
  write/isolated jobs.
- Lane W shares the privileged devcontainer, Docker daemon, credentials, CPU,
  memory, and caches.
- Stable and edge channels require an explicit update/canary workflow.
- Lane I remains unavailable until a disposable runtime passes measured tests.

## Default-switch gates

The new fabric does not become the documented default until all of these pass:

1. Frozen devcontainer build and startup reproduce the pinned toolchain without
   startup installs.
2. Codex and Claude capability and result-contract tests pass.
3. Two write jobs from the same base finish in separate worktrees without
   changing the primary checkout.
4. Process kill, terminal disconnect, and container restart never produce false
   success and leave a clean retry path.
5. Two Docker integration jobs use independent namespaces and scoped cleanup.
6. Legacy sessions, branches, worktrees, and logs can be inventoried without
   deletion.
7. A third party can diagnose a failed job from the runbook and bounded evidence.

## Revisit conditions

Revisit this decision if the control plane repeatedly diverges from real process
state, provider upgrades require raw event-parser churn, the primary checkout is
contaminated, credentials leak to an unintended lane, or the new path adds more
operator work without measurable recovery gains.
