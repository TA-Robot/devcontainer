# `agentctl` job fabric

`agentctl` is the provider-neutral execution boundary for finite structured jobs. It does not plan tasks or normalize provider conversations. Safe Lane R jobs run in the registered checkout without a worktree and provide a cross-provider Codex / Claude / Grok consultation or verification path; Lane W jobs use broker-owned worktrees and commits. Version 0.7 implements the Phase 3a–3e job fabric and all three provider adapters: stable project identity, immutable jobs, attempts, worktree leases, foreground or detached provider execution, broker-owned commits, result validation, explicit retry, cancellation, heartbeat, orphan reconciliation, bounded resource-class capacity, a durable priority queue, per-job Compose/port namespaces, read-only integration collection, bounded/redacted operational log views, provider / runner terminal-log retention, live supervisor-log rotation, and conservative dry-run GC inventory.

## Readiness before dispatch

Run `agentctl doctor --json` before a benchmark or unattended batch. Provider capability and authentication are separate checks: a pinned executable may support every required flag while still being unable to start a job. Codex and Claude authentication use their local, request-free status commands. Grok currently has no equivalent status command, so doctor only reports whether an API key, credential file, or external auth provider is configured and leaves `ready` as `null` until the first request verifies it. No token value or credential file content is read or printed.

Missing authentication is a provider-specific warning rather than a global doctor failure because another configured provider can still execute jobs. Automation should inspect `capabilities.<provider>.auth`: require `ready: true` for Codex / Claude, and for Grok distinguish `verification: configuration-only` from a completed live canary. Authentication repair remains an explicit human action; the broker never starts an interactive login flow.

Doctor does not make model requests and does not prove that a particular model
accepts the pinned CLI version. Before comparing development runs, verify the
requested model with a bounded invocation and retain any pre-task rejection as
readiness evidence. If a newer CLI is required, update and verify both comparison
conditions explicitly; do not silently substitute an older model.

## Persistent state

The devcontainer mounts a named volume at `/var/lib/agentctl` and sets `AGENTCTL_STATE_DIR` to that path. The directory and SQLite database are owner-only. Rebuilding the container preserves metadata, attempt evidence, and job worktrees.

Each Git project gets a UUID in local Git config:

```bash
agentctl project register
agentctl project show --json
```

The UUID is shared by linked worktrees through the Git common config, survives a repository move, and is not copied by a normal clone. `agentctl` records both the UUID and resolved Git common directory and refuses an ambiguous remap.

## Create one job

Create a task JSON for the target project. It must satisfy `.agent/schemas/task.schema.json`; use `agentctl job id` and a full commit SHA rather than a branch name. `job create` accepts task and collaboration-decision inputs only from inside the registered project, then copies their validated envelopes into private state. For controller-generated transient packets in a main checkout, use a bounded directory such as `.git/agentctl-inputs/<run>/`: it remains inside the project boundary without dirtying the worktree. Do not use this convention when `.git` is a worktree pointer file, and do not treat repository metadata as a general artifact store. A tracked packet must be committed before fixing a Lane R base because the provider shares that checkout and validation rejects unrelated dirty state.

```bash
agentctl job id
git rev-parse HEAD
agentctl job create --task docs/agents/tasks/task-0001.json
agentctl job list
```

Collaboration participantを作る場合は、primaryが生成したproject-local decision packetを同時に渡します。brokerがpacket schema、selected candidate、immutable baseを検証し、digestとcontent-free task projectionを導出します。source taskへの手書き転記は不要です。

```bash
agentctl job create \
  --task docs/agents/tasks/task-0001.json \
  --collaboration-decision docs/agents/decisions/plan-0001.json
agentctl job show <job-id> --json  # collaboration_correlatedを確認
```

`job create` copies a validated, immutable envelope into private state. It verifies the full base commit exists, the role/lane pair is declared in `.agent/config.json`, dependencies belong to the same project, and project-relative paths do not escape the contract.

Lane R additionally assumes that the registered checkout is clean from job
creation through result validation. This is part of the evidence contract:
without a clean baseline, the broker cannot attribute a shared-checkout change
to the user, primary, provider, or another process. Run consultation before the
primary edits. To verify an implementation, first create a controller-owned
checkpoint commit and use its full SHA as the review job's base. Reviewing an
uncommitted diff requires an explicitly permitted native advisory child or a
separately prepared snapshot; a useful report from a dirty Lane R attempt still
has terminal state `failed` or `blocked` and must not be relabelled successful.

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

Lane R acceptance commands must themselves be read-safe. In particular,
`python -m py_compile` writes `__pycache__` even when
`PYTHONDONTWRITEBYTECODE=1`; use an AST/`compile()` parse, a disposable snapshot,
or leave compilation to the primary. Result `checks` represent commands that
actually ran: `passed` requires integer exit code `0`. Put manual review evidence
in the summary, risks, or follow-ups instead of inventing a command check with a
null exit code.

```text
1 job
└─ attempt N
   ├─ branch: agentctl/<job-id>[-aN]
   ├─ worktree: $AGENTCTL_STATE_DIR/projects/<project-id>/worktrees/<job-id>/attempt-N
   ├─ process.log
   ├─ provider-result.json
   └─ result.json
```

The provider runs in the attempt worktree. Codex safe jobs use `workspace-write` with approvals set to `never`; Claude safe write jobs use `acceptEdits`; Grok safe jobs use `dontAsk` plus explicit allow/deny rules and `read-only` or `workspace` sandboxing. All three receive the same role, task envelope, and canonical result contract. Their structured-output implementations accept different JSON Schema subsets, so the broker derives a private transport schema for generation and normalizes only transport-added nullable optional fields. It then validates the result against the unchanged project schema and broker-observed Git state. The transport projection is never the authority for completion.

Grok is invoked through its documented headless surface with `--agent`, `--cwd`, `--prompt-file`, `--output-format json`, and `--json-schema`; `structuredOutput` is the normal result path. Grok 1.0.3 can concatenate JSON-shaped progress turns in `text` while leaving `structuredOutput` empty. In that case every top-level text segment must decode as an object, only the final document is a result candidate, and it still must pass the local schema, every command acceptance, and broker-observed Git checks. See xAI's [headless/scripting](https://docs.x.ai/build/cli/headless-scripting), [permissions](https://docs.x.ai/build/features/permissions), and [sandbox](https://docs.x.ai/build/features/sandbox) references.

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

`agentctl job validate` repeats result and Git verification and moves `succeeded` to `validated`. Without `--require-checks`, command evidence remains provider-reported; the validation JSON explicitly labels it `command_evidence: "provider-reported"` with no `verification_id`. Dependency jobs must reach `validated`, not merely exit, before a dependent job can start.

Validation writes an owner-only `validation.json` beside the attempt result and records it in the SQLite `validations` ledger. It contains only broker-observed identity/Git evidence, not prompts, transcripts, or credentials.

## Independently execute acceptance commands

```bash
agentctl --state-dir STATE job check JOB_ID --timeout 60 --json
```

`job check` runs the original `kind: "command"` acceptance entries from the stored
immutable task, in task order, in the latest successful terminal attempt's actual
workspace. It accepts `succeeded` and `validated` attempts. It refuses unknown
jobs, missing or active attempts, an unexpected submitted HEAD, dirty source,
and missing or unsafe workspaces before executing any acceptance command.
It never reads commands from the provider result or starts a provider session.
`job run` and `job validate` without `--require-checks` retain their existing behavior: their command evidence
is the provider's report, whereas `job check` measures command exits independently.

Commands run with the POSIX shell `/bin/sh -c`, closed stdin, and the caller's
environment and execution permissions. Each optional `cwd` is relative to the
attempt workspace (default `.`). All command directories must exist and have no
symlink components or parent traversal; absolute and escaping values are refused.
All directories are checked before the sequence and each is checked again before
launch. The report includes each validated absolute `cwd`.

**Authority:** the original task commands are trusted code running in the caller's
execution context. Directory checks, source snapshots, and the cooperating
agentctl ownership locks are not an isolation boundary against a malicious
same-UID process. Commands can access anything the caller can access. The checker
does not authenticate, push, merge, repair source, or change the task; trusted
commands are responsible for their own effects.

`--timeout` must be a finite positive number of seconds and defaults to 60. A
single monotonic deadline covers the command sequence, including time between
commands; it is never reset per command. Initial preflight and final source
inspection/cleanup can add wall time. At timeout the shell's process group is
killed, including children holding output pipes after the shell exits. A nonzero
exit, timeout, or detected source change stops the sequence. Later commands remain
`unexecuted`. This operation stores independent observations but never seals a
job or writes a successful job-validation claim.

The JSON has `schema_version: 1`, `job_id`, `attempt_id`, `status`, `head_sha`,
`source_changed`, and `checks`. `head_sha` always identifies the submitted HEAD
captured before execution, even when a command changes HEAD. Overall status is
`passed`, `failed`, `timed-out`, `source-changed`, `interrupted`, or `no-checks`; only `passed`
exits zero (verification failure exits 1; option/preflight errors exit 2 with a
diagnostic on stderr). An empty command list is `no-checks`. File and manual
acceptance entries are omitted from `checks` and remain unverified; `passed`
means only that all command entries passed on unchanged source.

Each check contains `command`, `cwd`, execution `status` (`passed`, `failed`,
`timed-out`, `interrupted`, or `unexecuted`), actual `exit_code` (null when unavailable; negative
for a signal), finite nonnegative `elapsed_seconds`, `stdout_tail`, and
`stderr_tail`. Unexecuted commands have null exit code, zero elapsed time, and
empty tails. Output is continuously drained with at most 32 KiB retained per
stream (64 KiB total per command), uses the existing best-effort log redaction,
and creates no raw output files. Output text cannot override an exit status.

Source checks compare HEAD, index bytes, tracked file bytes and modes, and
nonignored untracked paths before and after execution (also after each command).
They inspect files hidden by `assume-unchanged` or `skip-worktree`; ignored caches
are allowed. Raw tracked bytes must match committed blobs, without invoking Git
clean/smudge filters. Transformed checkouts, absent sparse-checkout files, and
submodules are conservatively refused. Changes are left in place. Zero exit with
changed source is `source-changed`; nonzero exit remains `failed` and timeout
remains `timed-out`, with `source_changed: true` if mutation is also detected.

## Inspect independent evidence and require it before sealing

```bash
agentctl --state-dir STATE job checks JOB_ID --json
agentctl --state-dir STATE job validate JOB_ID --require-checks --json
```

Every `job check` that passes preflight creates an opaque `verification_id` and a
new observation. Completed reports include `task_digest`, `source_fingerprint`,
`started_at`, `finished_at`, and `report_path`. The private JSON artifact lives at
`projects/<project>/jobs/<job>/checks/<verification_id>.json` under the state root,
with directory mode 0700 and file mode 0600. Its SHA-256 integrity digest is stored
separately in SQLite with task/attempt/source identities. The reader verifies that
metadata before trusting the artifact; changing a file's `status` to `passed`
cannot manufacture evidence. Prior reports remain intact after later checks.
Stored tails use the same bounded, redacted executor output; no raw output logs
are added.

An `incomplete` SQLite observation is committed before command execution. The
artifact is atomically written before the row is finalized. Interruption during
execution or publication leaves incomplete evidence that blocks an earlier pass;
reading never repairs or completes it. A preflight refusal executes nothing and
does not create an observation. Explicitly run `job check` again for new evidence;
unfinished crash records require the recovery procedure below.

`job checks` returns `schema_version: 1`, `job_id`, `latest`, `fresh`, `in_progress`, and
`stale_reasons`. With no history, `latest` is null, `fresh` is false, and the reason
states that evidence is absent. Incomplete or corrupted history is identified
explicitly and never replaced with an older successful report. `fresh` describes
whether the latest complete observation matches the current task, latest attempt,
workspace and exact source fingerprint; **fresh does not mean passed**. A current
failed, timed-out or no-checks observation still cannot seal a job. A source change
during execution invalidates freshness even if the source is later restored.
Inspection exits zero for a readable job, including absent/stale evidence, and
never executes acceptance commands. Unknown jobs/state return an error; inspection
does not create a missing state root, verification record, or repair any file.
While a checker owns an attempt, `in_progress` is true and `fresh` is false,
even if `latest` still names a previous passing artifact during preflight or
publication. With no active checker/retained execution lock, `in_progress` is
false; an incomplete crash record remains explicitly stale. Ownership probing
opens existing locks only and never creates lock files or observations.

`validate --require-checks` requires a complete, integrity-checked, fresh **passing**
observation before sealing. It also retains the existing result/Git validation.
Missing, failed, timed-out, empty, incomplete, corrupted or stale evidence is
rejected before changing validation or job/attempt state. Neither `checks` nor
`validate` reruns acceptance commands or starts a model session. Successful strict
validation records `command_evidence: "independently-executed"`, `verification_id`
and `independent_report_path`. Narrative/file acceptance still requires operator
review; this flag proves only command acceptance.

Freshness includes immutable task bytes, latest attempt identity, submitted HEAD,
index entries/flags/permissions, and tracked bytes/modes (including paths hidden
by index flags). New nonignored files invalidate it; ignored test caches do not.
Git stat-cache refreshes of unchanged source preserve freshness for new
`sha256-v2:` fingerprints. Earlier `sha256:` evidence retains its original raw
index identity rule; it remains readable and usable while unchanged, but an
index refresh requires a new check. No historical evidence is rewritten.
A later retry always needs
its own evidence. The retry state machine is unchanged: after editing a succeeded
delivery, legacy `job validate` can fail post-validation; `job run --clean-retry`
then creates the next attempt. Strict evidence rejection itself leaves the job
unchanged. Already validated jobs cannot be retried unrestrictedly.

On first open, an additive, schema-v2-compatible migration adds
`verification_tasks` and `command_verifications` plus an index. Existing database
v1 upgrade remains supported. Job/attempt states, leases, queues, result/task
contracts and validation records retain their earlier representation, readable by
old clients. Existing immutable tasks are pinned by digest when first encountered
(including jobs subsequently created by an older client); no historical command
execution is inferred. New jobs pin their task digest at creation. An unreadable
legacy task receives no usable digest and is not automatically repaired. This
compatible schema/identity migration is allowed on a read-only first open; later
inspection does not change job, task, source or verification content.

Digest metadata is an integrity check in the caller's trusted private state,
not authentication against a malicious same-UID process that can rewrite both
SQLite and files. Original task commands remain trusted code in that same caller
context. Legacy migration trusts the existing immutable task as found; it cannot
detect edits made before its digest was first recorded.

## Unattended checking, interruption, and recovery

The installed runtime includes the checker in `/usr/local/lib/agentctl/agentctl_jobs.py`;
it needs only the existing Python standard library, Git and `/bin/sh`. These
instructions also ship at `/usr/local/share/agentctl/README.md`. After installing
the project contract with `manage-agent-project` and writing a task as above,
the ordinary workflow in a fresh devcontainer user account is:

```bash
state="${AGENTCTL_STATE_DIR:-$HOME/.local/state/agentctl}"
job_id=$(agentctl --state-dir "$state" job create \
  --workspace "$PWD" --task "$PWD/.git/agentctl-inputs/task.json" \
  --base "$(git rev-parse HEAD)" --json | jq -er .job_id)
agentctl --state-dir "$state" job run "$job_id" --provider codex --json
agentctl --state-dir "$state" job check "$job_id" --timeout 60 --json
agentctl --state-dir "$state" job checks "$job_id" --json
agentctl --state-dir "$state" job validate "$job_id" --require-checks --json
```

Run these steps only after the preceding step succeeds (use `set -e` in a
script). `job run` is the provider invocation; the last three operations require
no provider, authentication flow or model session. `checks` is inspection and
never reruns tests. `validate` without the flag preserves legacy provider-reported
command authority. Neither form of validation pushes, merges or repairs source.

Each attempt has a nonblocking kernel ownership lock under
`STATE/locks/check-ATTEMPT_ID.lock`. A second checker fails promptly before any
command side effect or new observation. Separate attempts can execute concurrently;
they have independent budgets. Validation also holds the attempt lock while
sealing so a checker cannot start between the freshness check and state change.
The global preparation lock is held briefly, never for command execution.

SIGTERM, SIGINT and SIGHUP during execution stop the shell process group, retain
the bounded/redacted tails already observed, mark the report `interrupted`, and
leave later commands unexecuted. The CLI exits nonzero and a new explicit check
is needed. Group cleanup also covers ordinary background children after a shell
exits; acceptance commands should wait for their children and must not daemonize.
Only the original process group is managed. A trusted command that creates a
separate session, closes inherited ownership descriptors, or otherwise escapes
that group is outside this containment contract.

For unattended execution, record and wait for the actual foreground checker PID:

```bash
agentctl --state-dir "$state" job check "$job_id" --timeout 60 --json &
checker_pid=$!
# To interrupt this owned execution from the controlling shell:
# kill -TERM "$checker_pid"
wait "$checker_pid"
agentctl --state-dir "$state" job checks "$job_id" --json
```

SIGKILL, loss of the containing runtime, or interrupted artifact publication may
leave `incomplete` metadata without a completed artifact. This supersedes any old
pass. The execution lock is inherited by ordinary command descendants, so it can
remain held after the checker dies. No PID or process is claimed to survive a
container restart, and lock-file existence alone is not proof of a live owner.
The database's incomplete record survives as evidence that completion was never
established. Reads and validation never clear it.

Before recovering, establish that the old checker **and its command descendants**
have stopped: wait for the owned foreground process after SIGTERM and inspect
its process tree/groups with the host's process tools, or stop and wait for the
entire dedicated execution container/runtime to exit. A confirmed full container
stop establishes termination of its contained processes; restarting a CLI alone
does not. Do not signal a stale numeric PID without checking process identity.
If termination cannot be established, leave the evidence incomplete. Inspect
source changes without restoring them automatically. Once the source is a valid
submitted delivery and the old execution is known stopped:

```bash
agentctl --state-dir "$state" job checks "$job_id" --json
agentctl --state-dir "$state" job check "$job_id" --recover-incomplete --timeout 60 --json
agentctl --state-dir "$state" job validate "$job_id" --require-checks --json
```

`--recover-incomplete` is the operator's assertion of that termination check.
It cannot bypass an active ownership lock. It creates a **new observation** and
executes the entire original sequence with an explicit new budget; it never
resumes an old command, resets an old deadline, deletes old records, or turns
unfinished evidence into a pass. Do not delete lock files to force recovery.
This also applies to unfinished phase-2 observations, which had no per-attempt
ownership tracking. Complete earlier passing reports remain usable when intact
and fresh; no new database schema version or historic checks are fabricated.

Failure diagnosis:

| Observation | Operator action |
| --- | --- |
| `in_progress: true` / already in progress | Wait for or interrupt the owned checker. Do not launch another copy. |
| `interrupted` | Inspect tails/source and explicitly check again after cleanup. |
| `incomplete` | Establish termination, then use the explicit recovery procedure. |
| `failed` / `timed-out` | Inspect actual exit codes and bounded tails at `report_path`; fix through the job workflow and explicitly recheck. A previous pass cannot hide this observation. |
| `source-changed` / stale fingerprint | Preserve edits; deliver an updated attempt via the existing retry workflow described above, then recheck it. |
| Missing/corrupted artifact | Preserve evidence for diagnosis; run a new check after investigating private-state integrity. Editing JSON cannot validate a job. |
| `no-checks` | The task has no command acceptance; it cannot provide independent command verification. Narrative review remains separate. |

The artifact retains at most 64 KiB of redacted output per command, regardless of
output volume. This bounds retained output, not the number of explicit historical
observations. No new raw stdout/stderr files are written. The original command
string is retained verbatim as task identity; put credentials in the execution
environment, never directly in task command text. Private state and trusted task
commands share the caller's authority; they are not protection against a malicious
same-UID process.

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

Complete JSON objects and arrays are recognized both on their own and after text prefixes, including across multiple lines. Nonempty string values under decoded keys matching `SECRET_ENV_NAME` (API key, token, secret, password, passwd, credential, or private key forms), plus `Authorization`, are redacted case-insensitively at every nesting level. JSON escapes are decoded for matching; existing text rules also apply within string values. JSON syntax, ordinary fields, Unicode, and non-string values are preserved. Incomplete or malformed payloads fall back to best-effort text handling; the bounded view can omit part of a payload. `redaction_count` remains a nonnegative integer counting redaction operations, not unique secrets.

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
- no independent checker owns an attempt, no unfinished verification remains,
  and existing ownership markers can be inspected safely; an absent/free lock
  alone does not resolve an unfinished older check;
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
