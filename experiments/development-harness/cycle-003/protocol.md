# Cycle 003: verification access, speed and quality

Owner: primary/integrator. Small-02 is frozen before its live runs. The sustained
development task below is selected but its staged acceptance is not yet frozen;
it must not start until its separate task contract and evaluator are calibrated.
Past lifecycle candidates are evaluator-calibration data only.

## Hypotheses and intervention

H-speed: allowing required verification to execute reduces wasted attempts and
time to a declared behavioral quality threshold.
H-quality: executing relevant checks helps the developer remove defects and
regressions within the same development budget. Successful command startup is
not itself evidence of better generated code.

Both conditions use source `0b1ad1e950a0c90edf8dc9fcc493bdd9de680792`, image
`sha256:6d77b4bab77a27aafd05a859058c4c12519b4fec9d0d240202a4dcff9c80f14e`,
requested GPT-6 Astra/high and Codex 0.153.0. Applied model/effort remain unknown
unless the provider reports them. Each starts from a fresh identical checkout.
No completed candidate or new evaluator/reference implementation is copied in.

The declared intervention is command network access in the existing
workspace-write sandbox: control `false`, improved `true`, through the pinned
CLI's `sandbox_workspace_write.network_access` setting. This changes network
authority and is not a comparison at identical network permissions. Filesystem
mode, approval policy `never`, disabled subagents, provider/model, source and
prompt are held fixed. Use only dedicated trusted-development containers with
private nested-Docker storage, no host Docker socket, and no external publishing.
Normal user/project policy is not changed. Network access is not a narrow Unix
socket permission; its broader authority is an explicit study limitation.

Both conditions set `DOCKER_CONFIG=/tmp/development-harness-docker`, avoiding a
read-only home path for Docker's local client state. Existing builds may retrieve
their declared packages. External evaluators get no credentials or network.
Container setup/probes and independent evaluation are recorded separately from
development time. No simultaneous live provider runs or heavy builds during a
live small run; ordinary primary planning/evaluator work may continue.

## Small-02: structured-log redaction

The [public task](small-02.md) fixes an observed leak of synthetic JSON secret
values from the real log-redaction path. This differs from the earlier numeric
validation family. Scope is a local repair with existing caller compatibility.

The [evaluator](evaluate_redaction.py) checks secret removal, preservation of
ordinary JSON structure, useful log context and legacy formats. Calibration uses
the defective starting code, a valid independent test double, hiding-the-whole-log
and incorrect-count variants. The reference stays outside candidate source.
The behavioral quality threshold requires every named observation to pass,
complete measurement and unchanged source. No weighted overall score.
Relevant agentctl regressions and code review remain separate release checks.
In-session versus outside check results are reported separately.

Study-local settings, fixed before launch:

- One improved run followed by one control run, serial. This exploratory cost
  cap reverses cycle-002's order; it is not a statistical replication design.
- One session, at most 1,200 seconds and 20,000 observed output tokens per run.
  These cost caps cover the local task and its regressions; no automatic retry.
  Observed output is an admission cap, not exact billing enforcement within a turn.
- Snapshot every 120 cumulative seconds and on submission, at most 64 MiB of
  source payload per snapshot. These are a planning prior for the observed
  several-minute small tasks and a storage cost cap for the roughly 40 MiB base.
  Record actual trigger times; do not round them into exact sample times.
- Identical task information throughout. After early submission the unchanged
  terminal artifact can be carried to later planned timepoints; waiting is not
  added to development time. Missing observations remain unknown.
- Report quality by dimension at observed times, first observed behavioral
  threshold crossing as an interval where necessary, final quality and usage.
  Nonattainment is censored, never a fast successful completion. Do not aggregate
  small and sustained development results into one speed percentage.

Prompt, evaluator, runner, source and image hashes are saved in outer provenance
before either run. Every run, failure and setup recovery is retained. Any change
to these settings requires a recorded prospective amendment. The primary owns
updates if calibration, resource limits or new evidence invalidates these priors.
All requirements concerning secret preservation are task-local hard guards.

## Selected sustained-development problem

`agentctl_jobs.verify_result` currently independently checks Git state, but its
command-acceptance check trusts matching successful entries in the model result.
The selected real need is independent execution evidence for immutable task
acceptance commands, with bounded execution, source identity, stale-proof
rejection and usable diagnostics. Commands must come from the original task,
never executable strings supplied by a model's result.

The intended staged development is execution/evidence, compatibility and evidence
freshness, then integration and recovery/distribution. Existing job semantics and
user work must be preserved; no generic scheduler or automatic broad cleanup.
Follow-up changes will test maintaining the implementation, not just the number
of test files. Detailed stages, quality criteria, release schedule and budgets
must be frozen before this task's first live run. Selection alone is not a
completed comparison or authorization to skip its preflight.
