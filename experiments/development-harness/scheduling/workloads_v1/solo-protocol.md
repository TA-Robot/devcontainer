# H2: strong-solo difficulty calibration, first two runs

Status: question, workload, target and resource policy fixed; runtime source seal
and capability validation pending. No live run has been started or consumed.
Do not execute until the entry conditions below are fulfilled.

## Question and scope

Can a strong single developer, allowed self-testing, redesign, multiple policy
candidates and iterative experiments, attain the fixed rank_cache reference
vector on the qualification population after developing on public fixtures?
This is difficulty calibration, not a solo-versus-collaboration comparison.
No advisory agent, second model call, or independent LLM search is allowed.
Ordinary non-agent tools, generated tests and local algorithmic search are allowed.

The two runs are independent fresh sessions from the same neutral starting
projection. Neither receives the other's code, findings, or outcome. Model is
`gpt-6-astra`, effort high, with the pinned Codex CLI; no model/provider comparison.
Both runs remain in the record even when one succeeds. No failure-only subset,
winning retry, additional hidden feedback, or changed target is permitted.

## Fixed resource envelope

Per run: 1800 seconds of development elapsed time, including tool execution,
public checks, candidate comparison and final selection; 60000 observed output
tokens across the CLI session. Final model usage is required; this is not a
claim of exact in-turn token enforcement. Record input/cache/output separately.
Only one submitted source, at most 64 KiB as in the policy contract, is the final
attainment artifact. The number of local hypotheses, edits or experiments is not
artificially limited inside that envelope. Early submission is allowed.

Two runs is a bounded initial calibration design, not a sufficient universal
sample size. Thirty minutes reserves time for several design/experiment/revision
cycles: a complete 24-scenario external reference assessment took seconds to
tens of seconds in H1. It is a planning prior, not evidence that all strong solo
search should finish then. The output allowance is a cost cap; if reached, stop
and retain incomplete progress rather than pretending it proves inability.
Owner: primary/integrator. Scope: these first two solo starts only. If actual
runtime cost, tool failures, or uncertainty invalidate the envelope, close it
and design a separate finite calibration; do not extend a started run.

Each final independent qualification assessment is capped at 1200 seconds;
all candidate processes inherit v1's per-scenario limits. Reserve 60 seconds
per developer for stop/capture/cleanup. Total outer cap is 6120 seconds for both
runs, independent assessments and cleanup. Preflight is separate, provider-free,
and must complete before either start. No confirmation population is evaluated.

## Information and abilities

Public projection: interface TASK.md, WORKLOAD.md, public development fixtures,
public targets, FIFO starting policy, and working public experiment tools.
The actor must be able to edit files, execute Python/shell tests and compare
multiple implementations; it must be able to inspect exact public traces.
Public tool capabilities must match what will later be available to the
collaborative condition, apart from independent agents.

Exclude generator source/seeds, reference and contrast implementations,
qualification/confirmation inputs, old evaluated candidates, private calibration
results, evaluator private state, authoring checkout and host Docker socket.
Knowledge of authoring-side data in this orchestration session must not be
inherited by a measured developer. Release an explicit allowlist into a fresh
isolated runtime; use a fresh model context and ignore host rules/config/history.
A future public generator must use separately scoped seeds/failure sampling;
the current authoring generator is never released.

Freeze the final source before evaluation and do not repair it during scoring.
The developer receives no qualification feedback in either run. Self-selected
source is primary; any later diagnostic evaluation of rejected candidates is
separate and cannot replace the submission or consume confirmation data.

## Decision rules

Attainment requires valid measured outcomes for all 24 qualification cases and
values no greater than the fixed reference for all twelve family/metric cells.
The vector is a reachable reference level, not a universal optimum or overall
quality score. Retain exact values and the number/location of unmet axes.

- Both attain: this target has not exposed a stable solo attainment limitation.
  Record early versus late arrival and remaining quality headroom, but do not
  launch collaboration as a hard-task main evaluation merely on this result.
- One attains: difficulty/stability is uncertain; do not select only the failed
  run or claim stable inability. Use the evidence to decide a separately fixed
  calibration, not automatic repetition.
- Neither attains, with valid tools/evaluation: candidate hard-task evidence,
  not automatic admission. A tiny isolated miss is not enough to call the task
  very difficult; preserve gap size and the actual unresolved work.
  Inspect the observable missing outcomes and plausible exploration/selection/
  integration obstacles; causal proof is not a prerequisite for a later H3 test.
- Runtime/usage/authority failure or an envelope that prevents meaningful
  experiments: withhold difficulty judgment. Infrastructure failure is not an
  intellectual limit, and capped incomplete work is not a completed slow answer.

No live H3 comparison begins automatically from two failures. Fix its method,
all budgets and heldout boundary first. Confirmation stays unused; qualification
becomes known calibration data and is never relabelled pristine confirmation.

## Required entry evidence

Before starting, save exact image/CLI/config/contract/workload/evaluator/runner
hashes and the immutable reference-vector hash; verify existing credential
readiness without exposing or altering secrets. Run provider-free capability
checks using the actual CLI to show shell/Python editing and experiment tools,
absence of subagent tools, input isolation, public repair loop, unknown-usage
stop and owned-container cleanup. All checks must match the sealed live source.
Implement only this task's missing adapter against existing execution primitives.
Until that evidence exists, status remains not ready and run allowance unused.
