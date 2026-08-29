---
name: develop-evaluated-optimization
description: Develop or improve a program against a repeatable quantitative evaluator while preserving robustness. Use for controllers, planners, search heuristics, ML pipelines, performance tuning, simulations, games, or other tasks where many cheap trials, noisy or seeded outcomes, hidden parameters, and alternative algorithms can cause narrow-test overfitting or long sequential tuning loops.
---

# Develop evaluated optimization

Own the final strategy, integration and evidence. Use
`$orchestrate-agent-collaboration` when delegation is allowed and independent
hypotheses or implementations have positive expected value.

## Fix the evaluation contract

Before tuning, record the objective, correctness constraints, evaluator command,
observable outputs, trial cost and stochastic dimensions. Separate:

- development coverage used repeatedly for diagnosis;
- confirmation coverage used to reject narrow gains before integration;
- held-out acceptance owned outside the tuning loop when available.

Do not change the score or acceptance rule after seeing candidates. Treat the
sets, compute concurrency, wall-time and storage bounds by their actual roles:
hard guard, cost cap, planning prior or hypothesis. Never turn a convenient seed
count or agent count into a global quality default.

## Establish broad evidence first

Run a representative multi-condition baseline before deep local tuning. Confirm
that the evaluator distinguishes useful changes and retain the exact source
digest, conditions, result and trace pointers. When evaluation is cheap, keep a
warm evaluator available so strategy-level saves receive broad feedback without
container or process startup on the critical path.

Use narrow trials to reproduce and diagnose a named failure. A narrow success is
not adoption evidence; return to the common development coverage before keeping
the change.

## Allocate search by evidence

Summarize failure classes from retained traces instead of watching one episode
repeatedly. For each proposed change, state:

```text
hypothesis
failure class it should change
implementation or parameter surface
disconfirming observation
common evaluation contract
```

Prefer deterministic parallel compute for seed, scenario or parameter coverage.
Use agents only for materially different reasoning, implementation or checking:
distinct control architectures, estimators, planners, failure hypotheses or an
independent verifier. Give write candidates the same immutable base and separate
worktrees. Do not fan out cosmetic variations or duplicate prompts.

Re-evaluate the search relation when evidence changes: a strategy is falsified,
revisions remain in one failure class without a new claim transition, candidates
become comparable, or a selected artifact becomes ready for verification. Switch
between solo diagnosis, consultation, competing implementations and verification
according to expected evidence gain and integration cost—not elapsed time or a
fixed revision threshold.

## Compare without leaking the answer

Evaluate candidates on the same conditions and retain failures as well as wins.
Reject invalid or clearly dominated candidates early. Re-run the selected source
digest to detect evaluator noise or nondeterminism; do not select a one-off peak.
Use confirmation coverage before integration and held-out acceptance only after
the tuning decision is fixed. If held-out evidence causes another tuning cycle,
treat that set as development evidence and obtain fresh acceptance coverage.

Keep a compact machine-readable or Markdown search record owned by the agent:
source digest, hypothesis, conditions, score, failure distribution, runtime,
candidate provenance and disposition. Do not ask the user to maintain it.

## Finish honestly

Report the best reproducible result, comparison contract, rejected approaches,
trial and wall time, collaboration that changed the result, and remaining
uncertainty. Distinguish completed software from optimization quality. If the
cost cap arrives before held-out acceptance, return an incomplete result rather
than converting the best development score into a pass.
