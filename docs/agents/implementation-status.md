# Native-first multi-agent refresh status

Updated: 2026-08-26

The numbered source roadmap is `temp/multi-agent-refresh/03-recommendation-and-roadmap.md`. This file records implementation state; design changes belong in the ADR or architecture docs.

## Complete

### Phase 0: baseline and decision

- ADR-0001 fixes the native-first ownership boundary and read / write / isolated lanes.
- Representative read, write, and Docker scenarios have deterministic measurement rules.
- The legacy wrapper baseline and read-only inventory are recorded.
- `second-agent` is feature-frozen with explicit retirement gates.

### Phase 1: reproducible container and safe default

- Stable Feature/tool versions are pinned and checked with a frozen Dev Container build.
- Host CLI synchronization is edge-only; stable startup performs no package install.
- Normal Codex / Claude / Grok commands preserve provider safety; trusted bypass has explicit command names.
- `agentctl doctor --json` probes provider and Docker capabilities instead of trusting version labels.
- API key variables use remote process injection and are rejected from built image metadata.

### Phase 2: native-first project contract

- `.agent/schemas/` defines provider-neutral task and result envelopes at schema version 1.
- Dependency-free validation rejects invalid paths, lane/profile mismatches, false-clean completion, missing failure reasons, and inconsistent checks.
- Codex, Claude, and Grok project-native researcher, implementer, and reviewer mappings share neutral role definitions.
- `CLAUDE.md` imports `AGENTS.md`, avoiding policy duplication.
- `AGENTS_TEMPLATE.md` and `project/AGENTS.md` now contain only scope, lanes, permissions, completion, and single-writer integration rules.
- Wrapper choreography is isolated in the legacy compatibility runbook.
- Failure classification, orphan recovery, clean retry, resource collision, integration, and GC are centralized in the target-project runbook.

### Adaptive collaboration guidance C0 and initial C1

- Execution lane, role, relation, lifecycle, and authority are separate axes; multi-agent work is no longer described only as independent fan-out.
- The sixty-pattern catalog remains exploratory. Grok 4.6 and Claude Opus 5 independently reviewed the model, and the primary synthesis rejected unsupported global participant, exchange, candidate, and blindness defaults.
- The canonical model starts from a causal value mechanism and binding constraint, derives participants from distinct work or evidence, and continues only while evidence or artifact value changes.
- `solo / delegate / consult / compete / verify` are current relation aliases rather than a closed enum; one-shot, bounded-exchange, event-triggered, and scheduled are a separate lifecycle axis.
- A reusable collaboration-plan template records the solo alternative, mechanism, constraint, participant derivation, independence rationale, human review, parameter roles, continuation evidence, and project-local learning.
- Numeric and boolean parameters are classified as hard guard, cost cap, planning prior, or hypothesis, with scope, rationale, invalidation evidence, and update ownership.
- The native-agent template validator requires the adaptive playbook and plan template and rejects reintroduction of unsupported fixed defaults in the project copy source.
- Scheduled and event-triggered agents are guidance only. `agentctl` 0.7 has no cron or event-trigger runtime; recurring work must not be inferred from the capacity scheduler.

### Phase 3a: foreground job / workspace fabric

- `agentctl` persists stable project identities, immutable jobs, dependencies, attempts, leases, and state transitions in an owner-only SQLite store.
- Every write attempt starts from the recorded full base SHA in a distinct branch and linked worktree; explicit clean retry preserves prior evidence.
- Codex, Claude, and Grok foreground adapters consume the same task and result contracts, while trusted-fast dispatch requires two independent opt-ins.
- The provider edits in its constrained worktree and returns `ready_for_commit`; the broker independently checks the exact NUL-delimited Git path set, stages only allowed paths, and creates the job commit.
- Failed processes, malformed results, false SHAs, scope escapes, unvalidated dependencies, and broker failures cannot become success.
- Deterministic fake-provider tests cover all three adapters, Grok's final-document recovery plus incomplete-final rejection, required command-acceptance evidence, concurrent same-base jobs, primary-checkout isolation, dependency gating, failure, and retry.
- A 2026-08-13 live Grok 1.0.3 canary verified project-native agent discovery, read-only structured output, and a safe write job through broker commit and validation; the observed concatenated-progress output remains raw evidence and cannot bypass final schema/acceptance/Git checks.
- The stable image owns `/var/lib/agentctl` as a persistent named volume. Both the plain image build and frozen-lock Dev Container build start successfully and pass `agentctl doctor`.
- Durable provider start/terminal transitions best-effort feed Mira Companion through a content-free provider/role envelope. Codex / Claude / Grok agentctl jobs now share one visual activity contract without making the UI part of broker correctness.

### Phase 3b: durable local process ownership

- An owner-only Unix socket accepts versioned requests only from the same UID; concurrent clients start at most one local supervisor per state root.
- Detached submit prepares one attempt before spawning a dedicated, start-gated runner, so duplicate dispatch cannot create an unowned provider race.
- Runner and provider use separate process groups and record PID plus Linux process start time; the runner refreshes `heartbeat_at` while the provider is active.
- Cancellation records terminal state before signalling only identity-checked process groups. Conditional PID registration closes the launch/cancel race.
- Startup and periodic reconciliation classify expired ownership as `failed` before provider launch or `orphaned` after launch; it never infers success from a missing process.
- Fault-injection tests cover client-disconnected completion, process-group cancellation, and supervisor/runner/provider loss followed by restart reconciliation.

### Phase 3c: bounded capacity and collision-resistant resources

- Schema v2 adds durable `waiting_capacity`, queue reason/time, and `interactive` / `normal` / `background` priority while migrating schema-v1 databases in place.
- Every attempt transactionally acquires one named capacity slot for `light`, `write`, `integration`, or `isolated`; foreground rejects oversubscription and detached submit queues without creating an attempt/worktree.
- The supervisor promotes queued jobs by effective priority and FIFO, with configurable aging to prevent starvation. Queue state survives restart while credential-bearing dispatch environments remain memory-only and require an explicit safe resubmit.
- Cancellation, failure, success, and orphan handling release runtime leases through one path. Supervisor status reports class limits, use, waiters, and queued jobs needing resubmit.
- Every attempt receives a job-scoped Compose project, Docker label hint, and temp directory. Integration attempts additionally acquire a collision-checked dynamic loopback port lease exposed as `AGENTCTL_PORT`.
- Concurrency/fault tests cover slot handoff, priority ordering, aging, queued cancellation, restart/resubmit, foreground refusal, schema migration, and integration namespace/port evidence.

### Phase 3d: validation ledger and single-writer collection

- Explicit validation writes an owner-only broker-observed report and records it in an additive SQLite validation ledger.
- `agentctl job collect [--onto REV]` requires a validated root, recursively revalidates its validated dependency closure, and emits a new immutable collection report for every assessment.
- Reports include dependency-ordered candidate commits, full base/head/target SHAs, checks, risks, follow-ups, target dirty paths, target/job overlaps, inter-job overlaps, already-integrated detection, and structural blockers.
- Collection never mutates the target checkout and never cherry-picks, merges, rebases, pushes, or opens a PR; the report explicitly retains decision ownership with the primary/integrator.
- Deterministic tests cover pre-validation refusal, report file permissions/immutability, already-integrated targets, dependency ordering, and overlapping worker paths.

### Phase 3e: bounded evidence and conservative cleanup inventory

- `agentctl 0.7 job logs` reads only a bounded canonical attempt tail and applies best-effort redaction for OpenAI/Anthropic/xAI/GitHub/AWS/JWT token, header, and secret-assignment forms without claiming the raw evidence is sanitized.
- Provider exit atomically retains at most the final 8 MiB of `process.log`; detached runner exit retains 1 MiB and a restarted supervisor recovers missed terminal retention. The long-lived supervisor keeps a 2 MiB in-place live tail without detaching its stdout/stderr inode. Each policy writes separate owner-only evidence, and effective operational limits appear in supervisor status. Only live provider-log growth remains an explicit log boundary.
- `agentctl gc --dry-run` is non-destructive by construction. It checks validated/terminal state, identity-checked process and lease absence, exact worktree/branch/Git identity, clean state, canonical evidence, and still-valid integration proof before proposing any action.
- Integration-class inventory uses only the exact Compose project label and blocks when Docker ownership cannot be verified or scoped containers/networks/volumes remain. No broad prune or automatic teardown exists.
- GC tolerates a moved/unavailable registered workspace per job, rejects database path redirection, retains all evidence, and rechecks ancestry or stable patch ID rather than trusting a stale collection flag.
- Deterministic tests cover bounded/redacted views, Basic/Bearer and token redaction, canonical path tampering, terminal log retention, pre-integration refusal, cherry-pick patch-ID proof, worktree path tampering, moved workspaces, exact Docker scope, and the guarantee that dry-run leaves worktrees intact.

### Phase 4a: isolated-runtime capability and private-daemon pilot

- A dependency-free harness probes the standalone Docker Sandboxes `sbx` CLI and Docker Agent plugin without invoking a model or interpreting unknown-command help as availability.
- The runnable comparator transports only a committed Git bundle into a disposable private-DinD container with no outer network, no credential variables, no host workspace/socket, explicit CPU/memory/PID bounds, and a dedicated output mount.
- Five deterministic samples passed private-daemon identity, scoped network teardown, result-bundle recovery, and residual-resource checks. Median completion was 3487.356 ms and p95 was 4249.880 ms; full method/boundaries are recorded in `isolated-runtime-pilot-2026-08-12.md`.
- Privileged DinD remains explicitly rejected as a security boundary. The local host has `/dev/kvm` but neither `sbx` nor Docker Agent installed, so no dependency was added and no stable isolated adapter was enabled.

## Next: Phase 4b

Run the same fixture on intentional `sbx --clone` and Docker Agent installations, then compare credential exposure, main-checkout/worktree constraints, cache, Compose, disk, teardown, and rollback before choosing an adapter. Destructive worktree/branch GC, verified job-scoped Docker teardown, evidence expiry, and live provider-log rotation remain unclaimed follow-ups; none should be inferred from Phase 3e eligibility.

## Next: collaboration C1-C2

Exercise delegate, consult, compete, and verify relations only where a representative task has a credible mechanism over solo. Record content-free relation / lifecycle, participant derivation, elapsed time, accepted artifact, decisive finding, rework, human review, integration effort, stop reason, and whether collaboration changed the outcome. Use those observations to remove unused fields and form project-local planning priors; do not infer global optima from provider count or invocation count. A comparison harness requires evidence that the evaluator can distinguish candidates. A read-only trigger pilot requires evidence that manual, CI, deterministic script, and ordinary cron alternatives are insufficient, plus specified trigger, dedupe, overlap, usage, backoff, circuit, restart, owner, expiry, and kill-path semantics.
