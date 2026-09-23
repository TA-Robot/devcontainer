# Evaluator calibration, mutants, and go/no-go

## 1. Why calibration precedes the expensive benchmark

The 33:56 DevRelay result showed that a polished evaluator can still be too
weak. ForgeRoom does not proceed to B30/B60/B120 live runs until the evaluator
separates known product and orchestration deficiencies.

## 2. Baselines and mutants

### M0 — Direct forwarding baseline

Stable API/UI/persistence, one broad prompt forwarded to one Codex run, no
planning, isolation, review, or recovery beyond basic process handling.

Expected: launch/conformance pass; some semantic campaign success; weak
parallel, fault, ambiguity, assurance, and change outcomes.

### M1 — Feature-rich non-orchestrator

Rich chat, channels, buttons, and statuses but still direct forwarding.

Expected: no meaningful hidden campaign advantage over M0. This prevents UI
feature count from acting as quality.

### M2 — Sequential planner

Explicit tasks but never overlaps independent work.

Expected: comparable correctness on easy cases, worse cross-module throughput.

### M3 — Indiscriminate parallel planner

Spawns many writers without dependency or ownership control.

Expected: fast generation, worse conflict, stale work, and integration tail.

### M4 — Public-test optimizer

Aggressively iterates public campaigns and claims success from public score.

Expected: strong public result, weaker confirmation/heldout and change result.

### M5 — Maker-only

Good implementation planning, no independent assurance.

Expected: normal tasks strong, high-loss hidden defect closure weaker.

### M6 — Review theater

Multiple reviewers produce verbose findings without reproduction or closure.

Expected: higher cost, no hidden quality gain, false-positive burden.

### M7 — Volatile campaign state

Good normal execution, loss or fabrication after restart.

Expected: deterministic recovery/fault failure.

### M8 — Unsafe Git integrator

Passes feature tests but overwrites dirty user changes or accepts stale patches.

Expected: hard-gate failure.

### M9 — Robust but slow reference

Serial, conservative, strong tests and recovery.

Expected: high F/R/D/E, lower T. Confirms vector preserves trade-offs.

### M10 — Early architecture portfolio reference

Uses alternative proposals/probes on performance campaign only.

Expected: advantage on H4, no automatic advantage elsewhere.

### M11 — Complexity theater

Many modules, roles, and ledgers with no behavior difference.

Expected: no direct score bonus; potentially worse T/A.

## 3. Calibration assertions

The evaluator revision is acceptable only if:

1. M0 and M1 remain close on downstream quality.
2. M2 and M3 show different failure profiles, not a single generic penalty.
3. M4 public-to-heldout gap is visible.
4. M5 loses specifically on verifier-sensitive hidden mutants.
5. M6 incurs cost/false findings without fake assurance credit.
6. M7 and M8 trigger the correct recovery/safety classifications.
7. M9 remains competitive despite lower throughput and appears on a Pareto
   frontier.
8. M10 wins only where candidate search is relevant.
9. M11 receives no sophistication bonus.
10. No candidate, including a reference, exhausts all quality dimensions.

## 4. Forwarding-baseline rejection rule

If M0 obtains more than roughly 70% of the strong reference's semantic campaign
milestones, inspect each campaign. Do not solve this by arbitrary score weights.
Deepen repository context, requirement ambiguity, independent assurance need,
or performance approach diversity until orchestration decisions can matter.

The exact threshold is set after noise pilot; 70% is an initial alarm, not a
scientific constant.

## 5. Ceiling alarm

Trigger evaluator redesign when:

- a strong fresh run clears all criteria before 75% of its budget;
- B30 and B120 are indistinguishable within noise;
- additional outer work has plausible product value but no evaluator surface;
- reference and materially weaker mutants tie;
- hidden failure feedback contains no actionable frontier;
- final ranking is determined mostly by launch time or provider luck.

## 6. Ambiguity audit

Before hiding a criterion, an independent audit asks:

- is the user/system need public?
- are multiple implementations acceptable?
- does the concrete hidden case test the declared domain?
- does failure indicate a real product weakness?
- could a reasonable candidate choose a different convention with equal user
  value?

The CausalBuffer “deterministic tuple” versus delivery-order failure would fail
this audit unless the user-visible need or ordering semantics were clarified.

## 7. Noise pilot

Run M0, M9, and one strong candidate at least three times under the same live
provider stratum. Measure:

- run-to-run criterion variance;
- provider startup/terminal variance;
- campaign failure taxonomy;
- rank stability;
- evaluator flakiness;
- resource interference.

Set decision thresholds only after this pilot.

## 8. Go/no-go decision

### Go

- all calibration assertions hold;
- P0 completes quickly and deterministically;
- live campaigns fit operational budget;
- provider auth/readiness is stable;
- hidden isolation is verified;
- quality reports retain actionable headroom.

### Revise

- some mutants tie unexpectedly;
- one campaign dominates all score;
- forwarding remains too strong;
- change task is arbitrary or trivial;
- evaluator runtime blocks iteration.

### No-go

- provider stochasticity dominates architecture;
- hidden answers cannot be isolated;
- safety cannot be independently observed;
- campaign tasks primarily measure unrelated domain R&D;
- strong artifacts saturate again before the shortest target budget.
