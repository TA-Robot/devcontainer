# Large 01: project-template lifecycle development

Status: task sequence and external acceptance fixed before live execution.
Runner/evaluator preflight passed 18 tests, including a real Docker transport
with a fake provider. The initial source passed 0/35 semantic scenarios in a
read-only, network-disabled container. No large-scale comparison result exists yet.

## Selection and scope

The repository distributes 45 tracked files under `project/`; its recent history
contains repeated native-contract and runbook updates. README currently requires
manual copying and preservation of project configuration. The selected feature
turns installation, local customization, upstream update and crash recovery into
one usable lifecycle. This is actual infrastructure development. Target-project
fixtures are created outside the repository; no demo application is added.

The same implementation evolves through [initial delivery](phase-1.md),
[customization/adoption](phase-2.md), and [recovery/distribution](phase-3.md).
Ownership state, planned changes, merge semantics, crash handling, native
contracts and installed/checkout behavior are coupled. The outer evaluator
rechecks earlier behavior at every stage. A stage is not an independent sample.
Fast correct completion remains valid; duration alone does not establish scale.

Starting tracked source: `1fe36d325d4050f1e3a702139973478f059b63a7`.
Starting image: `sha256:ed9053a8df20ae4c43b83740af5e13d9337c4e92e508e35e8ee80e326deba64d`.
Archive this revision into an external checkout, excluding subsequent evaluator,
runner, future detailed requirements and completed candidate implementations.
Both conditions start from identical task source plus the declared harness-only
intervention in the improved condition.

## Execution and caps

The primary owns these study-local choices. They are fixed for the first pilot;
changes require a recorded amendment before the affected comparison, never
silent extension or replacement of a failed observation.

- Model/effort/CLI: GPT-6 Astra, high, Codex 0.153.0 (planning prior, continuity
  with the first cycle). Applied provider values remain unknown unless observed.
- Three released requirement stages (task structure); each uses a fresh
  ephemeral session with the released requirements, persistent source and the
  candidate-authored DEVELOPMENT_HANDOFF.md. Future stage text is not supplied.
  This explicitly tests artifact-based continuity, not native session resume.
- Each stage: at most 7,200 seconds. Campaign: 28,800 seconds and four sessions
  (cost caps: three deliveries plus at most one explicit retry). No automatic
  retry. Unknown usage blocks further admission pending review.
- Output usage: 200,000 observed output tokens per condition (admission cap,
  not a hard billing cap). The CLI reports usage at turn completion; overshoot
  by a turn is possible. Wall limits independently bound an unreported turn.
  Cached/input/output usage is recorded separately; no monetary estimate.
- Source snapshots: every 1,800 cumulative live seconds and terminal stage
  submission (planning prior; finer than the preliminary hourly grid to retain
  useful partial results). Quiesce the dedicated container during copying.
  Snapshot overhead is included in live wall time; evaluator time is separate.
- Each workspace snapshot: at most 512 MiB of filesystem payload (cost cap,
  about 40 MiB of initial tracked source plus headroom). Exceeding it is a
  recorded infrastructure interruption, not successful artifact collection.
- One control and one improved campaign, serial, with one primary development
  agent in each and no delegated agents. This is an exploratory cost cap,
  not statistical evidence of broad superiority.

The intervention is selected from the control's observed waste. That makes this
an adaptive exploration. A new small task must also check the chosen intervention;
cycle-001's solved task is historical evidence only. Any later generalized claim
needs independent tasks and counterbalanced repeated runs.

## Authority and evidence

Use the same workspace-write authority, source mount and environment in both
conditions. The dedicated container has a bounded remote `timeout` around the
provider and is stopped after each observed stage. Evidence is stored outside
its workspace. State-file expiry never licenses a duplicate provider process.
Recovery first verifies the exact container is stopped; lost recorder time is
conservatively charged at the reserved stage cap, usage remains unknown, and
recovered source does not become accepted merely because it was saved.

`campaign.py` stores only command metadata, public agent messages, errors and
usage; reasoning items are discarded. The stderr tail and source snapshots are
private. Future requirement text stays in outer state until its release. CLI
event semantics were checked against the installed binary and the
[official noninteractive documentation](https://learn.chatgpt.com/docs/non-interactive-mode).

The evaluator must invoke the actual CLI against independent temporary sources
and target states, inspect bytes/modes/state transitions, and preserve its own
tests. Candidate-reported statuses alone are insufficient. Stale plans, existing
user changes, both-side edits, injected interruption, corruption and symlinks
must be tested as well as successful installation. Freeze evaluator identities
before the first live run. Source snapshots are evaluated read-only in a
separate execution environment; no hidden failure details are fed back during
the campaign. Source Git bundles and dirty/ignored files are retained together.

Completion needs external scenario acceptance, relevant regressions, real
installed-container verification, reviewed integration, and separate small/large
results. No live run or feature is declared complete by this protocol alone.

## Evidence amendment before the first candidate evaluation

While the control's first development stage was running, the primary noticed
that the acceptance JSON reported source immutability but did not embed source
identity. The evaluator now also records the candidate tree and evaluator
SHA-256 digests. No scenario, requirement, score or feedback policy changed.
The initial missing-implementation probe keeps its original evaluator identity;
candidate evaluations use the new identity, recorded in provenance. An added
provider-free regression checks that changing source changes that digest.
