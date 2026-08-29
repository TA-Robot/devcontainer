# `agentctl` job fabric

`agentctl` is the provider-neutral execution boundary for finite structured jobs. It does not plan tasks or normalize provider conversations. Safe Lane R jobs run in the registered checkout without a worktree and provide a cross-provider Codex / Claude / Grok consultation or verification path; Lane W jobs use broker-owned worktrees and commits. Version 0.7 implements the Phase 3a–3e job fabric and all three provider adapters: stable project identity, immutable jobs, attempts, worktree leases, foreground or detached provider execution, broker-owned commits, result validation, explicit retry, cancellation, heartbeat, orphan reconciliation, bounded resource-class capacity, a durable priority queue, per-job Compose/port namespaces, read-only integration collection, bounded/redacted operational log views, provider / runner terminal-log retention, live supervisor-log rotation, and conservative dry-run GC inventory.

## Persistent state

The devcontainer mounts a named volume at `/var/lib/agentctl` and sets `AGENTCTL_STATE_DIR` to that path. The directory and SQLite database are owner-only. Rebuilding the container preserves metadata, attempt evidence, and job worktrees.

Each Git project gets a UUID in local Git config:

```bash
agentctl project register
agentctl project show --json
```

The UUID is shared by linked worktrees through the Git common config, survives a repository move, and is not copied by a normal clone. `agentctl` records both the UUID and resolved Git common directory and refuses an ambiguous remap.

## Create one job

Create a task JSON for the target project. It must satisfy `.agent/schemas/task.schema.json`; use `agentctl job id` and a full commit SHA rather than a branch name. If the task file is inside the registered checkout, commit it before fixing the job base. This is required for Lane R because the provider runs in that checkout and validation rejects unrelated dirty state. An operator-generated task may instead live outside the checkout; `job create` copies the validated envelope into private state.

```bash
agentctl job id
git rev-parse HEAD
agentctl job create --task docs/agents/tasks/task-0001.json
agentctl job list
```

`job create` copies a validated, immutable envelope into private state. It verifies the full base commit exists, the role/lane pair is declared in `.agent/config.json`, dependencies belong to the same project, and project-relative paths do not escape the contract.

The input file may omit `job_id`; `job create` then generates a canonical ULID. `--job-id` can supply it explicitly, and `--base` can supply the revision when the task omits `base_sha`. The stored envelope always contains a canonical ULID and full SHA. For reproducible review, committing those values in the source task JSON is preferred.

## Run in foreground

```bash
agentctl job run <job-id> --provider codex
# or
agentctl job run <job-id> --provider claude
# or
agentctl job run <job-id> --provider grok

agentctl job show <job-id> --json
agentctl job validate <job-id>
```

Lane R uses the registered workspace with the `safe` profile: Codex receives `read-only`, Claude receives `plan`, and Grok receives its read-only sandbox. This is the structured path when a primary needs cross-provider research / review, including from a trusted interactive parent; it does not inherit the parent's live native-child override. The result must report `completed` with no Git changes. Lane W creates:

```text
1 job
└─ attempt N
   ├─ branch: agentctl/<job-id>[-aN]
   ├─ worktree: $AGENTCTL_STATE_DIR/projects/<project-id>/worktrees/<job-id>/attempt-N
   ├─ process.log
   ├─ provider-result.json
   └─ result.json
```

The provider runs in the attempt worktree. Codex safe jobs use `workspace-write` with approvals set to `never`; Claude safe write jobs use `acceptEdits`; Grok safe jobs use `dontAsk` plus explicit allow/deny rules and `read-only` or `workspace` sandboxing. All three receive the same role, task envelope, and result schema. Grok is invoked through its documented headless surface with `--agent`, `--cwd`, `--prompt-file`, `--output-format json`, and `--json-schema`; `structuredOutput` is the normal result path. Grok 1.0.3 can concatenate JSON-shaped progress turns in `text` while leaving `structuredOutput` empty. In that case every top-level text segment must decode as an object, only the final document is a result candidate, and it still must pass the local schema, every command acceptance, and broker-observed Git checks. See xAI's [headless/scripting](https://docs.x.ai/build/cli/headless-scripting), [permissions](https://docs.x.ai/build/features/permissions), and [sandbox](https://docs.x.ai/build/features/sandbox) references.

Safe dispatch also disables Grok's nested subagents and sets `GROK_MEMORY=0` for deterministic broker ownership. The environment form works with the pinned 1.0.3 binary and newer builds even when `--no-memory` is absent from their generated help. The adapter fixes an explicit bounded `--max-turns 64` so a provider-default change cannot silently alter the job budget; hitting that boundary remains failure, never partial success. `trusted-fast` uses the explicit `grok-trusted` wrapper and `bypassPermissions` / sandbox-off flags; it is never selected merely because Grok is the provider.

After durable `running`, `succeeded`, `failed`, `cancelled`, or `orphaned` transitions, the broker best-effort emits a sanitized lifecycle event to Mira Companion when `mira-codex-hook` is available. The envelope contains only the transition, provider, and role plus IDs that the bridge immediately hashes; it excludes task text, paths, commands, results, failure reasons, logs, and credential environment variables. Missing bridge, nonzero exit, and a one-second timeout are presentation failures and never change broker state or command success. Tests may override the executable with `AGENTCTL_MIRA_BRIDGE_BIN`; production discovers the container-managed bridge on `PATH`. `MIRA_COMPANION_ENABLED=0` disables both Codex and agentctl display events.

## Detach without losing process ownership

```bash
agentctl job run <job-id> --provider codex --detach
agentctl job show <job-id> --json
agentctl supervisor status
```

`--detach` submits a prepared attempt to a small local supervisor and returns only after a dedicated runner has an identity and start gate. It is not a shell background or `nohup` success signal. The owner-only Unix socket checks the peer UID; the supervisor, PID evidence, runner log, provider log, and database remain under the private state root. The dispatching CLI's current environment is passed transiently to that runner so refreshed provider credentials and job variables do not go stale with the long-lived daemon; the request environment is not written to the database, result, or logs.

The runner starts the provider in a separate process group, records both PID and Linux `/proc` start time, and updates `heartbeat_at` while it waits. Stopping the dispatching terminal does not stop that runner. Stopping or rebuilding the container does stop its processes, but the named state volume remains; the next supervisor start compares the recorded identities and heartbeat and marks lost execution `orphaned` rather than guessing success.

```bash
agentctl job cancel <job-id>
agentctl supervisor reconcile --json
agentctl supervisor stop
```

Cancellation first records `cancelled`, then terminates only the identity-checked provider and runner process groups. `supervisor stop` stops the control plane only and never implies cancellation of active runners. The defaults are a 2-second runner heartbeat and a 30-second orphan deadline; tests may shorten them with `AGENTCTL_HEARTBEAT_SECONDS` and `AGENTCTL_ORPHAN_AFTER_SECONDS`.

## Capacity and the durable queue

Every attempt acquires one slot for its task `resource_class`. Defaults are deliberately conservative and independent: `light=4`, `write=2`, `integration=1`, and `isolated=0`. Configure the supervisor before it starts with `AGENTCTL_CAPACITY_LIGHT`, `AGENTCTL_CAPACITY_WRITE`, `AGENTCTL_CAPACITY_INTEGRATION`, or `AGENTCTL_CAPACITY_ISOLATED`; each value must be `0..256`.

A foreground run never blocks invisibly. If its class is full, it exits without creating an attempt and suggests `--detach`. A detached run enters `waiting_capacity`, also without creating a worktree or attempt, and is promoted automatically when a slot is released:

```bash
agentctl job run <job-id> --provider codex --detach
agentctl job show <job-id> --json       # queue position and effective priority
agentctl supervisor status --json       # limits, use, waiters, restart state
agentctl job cancel <job-id>             # also cancels a queued job
```

Task priority is `interactive`, `normal` (the default), or `background`. Equal effective priority is FIFO. Every `AGENTCTL_QUEUE_AGING_SECONDS` (default 300) raises a waiting job by one level, capped at interactive, so background work cannot starve. `AGENTCTL_QUEUE_LIMIT` defaults to 128.

Queue identity, order, and reason are durable SQLite state. The dispatch environment is intentionally only memory-resident because it may contain provider credentials. If the supervisor restarts while a job waits, `supervisor status --json` lists it under `awaiting_resubmit`; rerun the same `job run ... --detach` command to replenish the envelope without creating a duplicate attempt.

Capacity, process, and port leases are released on success, failure, cancellation, and orphan reconciliation. Branch/worktree leases remain as evidence until a future destructive GC is explicitly implemented; version 0.7 only inventories candidates.

## Compose namespace and integration port

Each attempt receives `COMPOSE_PROJECT_NAME=agent_<job-id>`, the same value in `AGENTCTL_COMPOSE_PROJECT_NAME`, a `dev.agentctl.job=<job-id>` hint in `AGENTCTL_DOCKER_LABEL`, and its own `TMPDIR`. Compose's project label is the authoritative scope for its containers and networks.

An `integration` attempt additionally leases one host port from `AGENTCTL_PORT_RANGE` (default `24000-24999`) and receives it as `AGENTCTL_PORT`. The broker checks both active SQLite leases and current loopback bind availability before assignment. This prevents cooperating agentctl jobs from choosing the same port; an unrelated process can still race after the probe, so services should prefer internal networks and must report bind failure rather than selecting an unrecorded fixed port.

Cleanup commands must remain scoped to the recorded Compose project/job label. The broker does not issue broad Docker prune operations.

## Why the broker creates the commit

A linked worktree stores its writable Git index and refs under the common repository metadata, outside the worktree root. A direct probe with Codex's `:workspace` sandbox correctly rejected `git commit` because that common directory was read-only. Making all common Git metadata writable would let one worker affect unrelated branches.

Therefore a broker-managed write job uses this handoff:

1. The provider edits only allowed paths and returns `ready_for_commit` with the pre-commit HEAD and dirty path set.
2. The broker recomputes committed and dirty paths using NUL-delimited Git output.
3. It rejects a changed HEAD, path/report mismatch, forbidden path, dirty-state mismatch, or invalid schema.
4. It stages only the verified paths.
5. It creates one deterministic job commit with repository hooks and commit signing disabled.
6. It rewrites the final envelope as `completed`, with the actual full head SHA and clean state, while preserving the original provider result.

This is an accidental-write boundary, not a malicious-process security boundary. The provider and broker still share a UID, credentials, and container.

## Success and validation

Process exit zero is necessary but insufficient. `succeeded` requires:

- a schema-valid final result;
- matching job ID;
- every command acceptance copied exactly into `checks` with `passed` and exit code zero;
- HEAD descending from the immutable base;
- exact broker/reported SHA, changed paths, and dirty state;
- all changed or dirty paths inside allowed scope and outside forbidden scope;
- a clean worktree after the broker commit.

`agentctl job validate` repeats result and Git verification and moves `succeeded` to `validated`. Dependency jobs must reach `validated`, not merely exit, before a dependent job can start.

Validation writes an owner-only `validation.json` beside the attempt result and records it in the SQLite `validations` ledger. It contains only broker-observed identity/Git evidence, not prompts, transcripts, or credentials.

## Collect for single-writer integration

Collection is an explicit, read-only handoff after validation:

```bash
agentctl job collect <job-id> --json
agentctl job collect <job-id> --onto <integration-branch-or-sha> --json
```

`collect` recursively walks validated dependencies in topological order, revalidates every final result against its worktree, resolves the target to a full SHA, and writes a new immutable report under the root attempt's `collections/` directory. It reports candidate commits in dependency order, target/job path overlap, inter-job path overlap, checks, risks, follow-ups, target dirty paths, already-integrated commits, and structural blockers such as an unexpected commit count or a target that does not descend from the job base.

`clean_candidate` means the mechanical checks found no path overlap; it is not approval to integrate. `review_required` means overlap needs semantic review. `structural_blocker` means the proposed target/order is invalid. `already_integrated_or_no_change` means there is no remaining commit candidate. In all cases `automatic_integration_performed` is false: only the primary/integrator chooses cherry-pick, merge, rebase, aggregate tests, push, or PR actions.

For a single broker commit, collection also compares stable Git patch IDs. This recognizes an explicit cherry-pick whose commit SHA changed; it does not guess that a squash, hand edit, or semantically similar change is integrated.

## Read bounded operational logs

Use the view command instead of opening an arbitrarily large raw log in a terminal:

```bash
agentctl job logs <job-id>
agentctl job logs <job-id> --attempt 2 --lines 200 --bytes 262144
agentctl job logs <job-id> --runner --json
```

The default view reads only the final 64 KiB and 80 lines. The caller may request at most 1 MiB and 1000 lines. It resolves the canonical project/job/attempt evidence path rather than trusting a mutable path from the database and rejects a redirected file or symlink escaping private state.

Before printing, the view applies best-effort redaction for known OpenAI/Anthropic/xAI/GitHub/AWS/JWT token forms, Basic/Bearer authorization headers, secret-named assignments, and secret values present in the viewing process environment. This is an operational guardrail, not a data-loss-prevention guarantee: an unknown secret format or a value absent from the later viewer environment can remain.

`process.log` remains owner-only raw evidence and is not rewritten into a redacted transcript. Once a provider process closes, agentctl atomically retains at most its final 8 MiB and writes owner-only `log-retention.json` containing the original size, retained size, and whether an initial partial line was discarded. A detached `runner.log` is similarly retained at 1 MiB after exit, including recovery by a restarted supervisor, with evidence in `runner-log-retention.json`. `job logs --runner --json` returns that runner-specific evidence rather than the provider report.

The long-lived `agentd.log` uses a 2 MiB live tail. Rotation truncates the existing regular owner-only inode in place, so the supervisor's inherited stdout/stderr descriptors continue writing to the visible path; `agentd-log-retention.json` records the last rotation. `AGENTCTL_RUNNER_LOG_MAX_BYTES` and `AGENTCTL_SUPERVISOR_LOG_MAX_BYTES` may set 1 KiB–64 MiB limits before the supervisor starts, and `supervisor status --json` reports the effective values. Startup refuses a symlink or non-owner operational log. A running provider may still temporarily exceed the 8 MiB terminal limit before it closes.

## Inspect cleanup candidates

Cleanup begins with a non-mutating inventory:

```bash
agentctl gc --dry-run --json
agentctl gc --dry-run --job <job-id> --json
```

Without `--dry-run`, version 0.7 refuses the command. Even an eligible report is a proposal only: `destructive` is false, evidence policy is `retain`, and no worktree, branch, lease, log, container, network, or volume changes.

A job is eligible only when every conservative check passes:

- the job and its latest attempt are explicitly `validated`, and all attempts are terminal;
- no identity-checked provider/runner process or active runtime lease remains;
- each write worktree is the exact canonical job/attempt path, uses the recorded Git common directory and generated branch, has the recorded validated HEAD when present, and is clean;
- `process.log`, `result.json`, and `log-retention.json` exist at their canonical owner-only evidence paths;
- a no-change result is proven, or an immutable integration collection proves the exact head is still represented in the registered workspace HEAD by ancestry or a rechecked single-commit patch ID;
- integration-class jobs have no container, network, or volume with the exact Compose project label `com.docker.compose.project=agent_<job-id>`; an unavailable Docker CLI/daemon blocks eligibility.

If a registered workspace moved, Git identity changed, evidence is corrupt, or one job cannot be inspected, global inventory records a blocker for that job and continues with the others. The command never uses broad Docker prune discovery.

## Failure and retry

Provider nonzero exit, malformed JSON, fake head SHA, scope escape, broker commit failure, and reported `failed` / `blocked` all become terminal failure evidence. They never become success because a process disappeared.

Retry is explicit and creates a new attempt, branch, worktree, log, and result path from the original base:

```bash
agentctl job run <job-id> --provider codex --clean-retry
```

The prior attempt is not overwritten or automatically deleted.

`trusted-fast` needs two independent opt-ins: the task envelope must request it and the operator must pass the flag at dispatch.

```bash
agentctl job run <job-id> --provider codex --allow-trusted-fast
```

Lane I is intentionally rejected in version 0.7; it never falls back into the shared container.

## Current boundary

Version 0.7 provides terminal-disconnect continuity, deterministic recovery, bounded local scheduling, collision-resistant execution namespaces, immutable integration handoff reports, bounded operational log views, terminal provider/runner retention, live supervisor-log rotation, read-only cleanup eligibility, and symmetric Codex / Claude / Grok foreground and detached dispatch. It does not claim that a process survives a container or host restart, that a same-UID process is a security boundary, that path overlap predicts all semantic conflicts, that best-effort redaction removes every secret, that a live provider raw log is already size-bounded, or that a port probe reserves the operating system socket for the provider. Verified job-scoped Docker teardown, destructive worktree/branch GC, and evidence expiry remain unimplemented. Until those land, treat `gc --dry-run` as evidence for a primary-owned manual decision, never as authorization for broad deletion.
