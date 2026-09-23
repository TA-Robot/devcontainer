# Synthesis: from 1,000 ideas to product bets

## 1. How ideas are reduced

The 1,000 entries are not independently scored features. Many are necessary
parts of one causal mechanism. Selection happens in three levels:

```text
idea
 -> mechanism bundle
 -> product bet with a falsifiable downstream outcome
```

Every product bet is judged on:

1. direct connection to faster accepted software outcomes;
2. plausible differentiation from prompt forwarding;
3. observable effect in hidden campaigns;
4. opportunity for deeper design and implementation;
5. feasibility of cheap public feedback;
6. usefulness across several project types;
7. low dependence on mandatory human input;
8. resistance to feature-count and complexity gaming.

## 2. Bet 1 — Objective-to-requirement discovery loop

Representative ideas: 0006, 0011–0015, 0026–0035, 0042–0049, 0658, 0842,
0977, 0995–0997.

Hypothesis: a studio that explicitly derives, tests, revises, and prioritizes
requirements from a broad objective will deliver stronger ambiguous greenfield
and evolving-requirement outcomes than a system that forwards the initial
prompt.

Minimum experiment: ambiguous service campaign followed by a version-two
change. Compare hidden workflow completion, late rework, and change
amplification.

Reject when: the ledger becomes retrospective prose or does not change code,
tests, priorities, or campaign results.

## 3. Bet 2 — Low-interruption human control plane

Representative ideas: 0051–0069, 0073–0094, 0111–0115, 0128–0132, 0823–0825,
0978–0980.

Hypothesis: reversible assumptions, consolidated approvals, truthful blocked
state, and risk-based escalation reduce idle wall time without increasing
unsafe actions.

Minimum experiment: run campaigns with no routine human replies and injected
approval/provider delays. Measure blocked time, question count, safety gates,
and accepted completion.

Reject when: autonomy merely suppresses questions while making unsafe or
incorrect choices.

## 4. Bet 3 — Dependency-aware adaptive planning

Representative ideas: 0151–0200, 0401, 0407–0418, 0445–0449, 0968–0970.

Hypothesis: explicit artifacts, dependencies, ready/stale/stop conditions, and
stage transitions improve critical-path use and avoid premature fan-out.

Minimum experiment: context-heavy cross-module campaign with separable and
non-separable work. Compare time-to-accepted, duplicate work, conflict, and
integration tail against sequential and indiscriminate-parallel baselines.

Reject when: planning overhead exceeds saved critical-path time or the task graph
does not reflect actual dependencies.

## 5. Bet 4 — Context capsules and freshness

Representative ideas: 0251–0276, 0285–0299, 0164, 0192–0193, 0237–0239,
0667, 0839, 0957.

Hypothesis: versioned, task-specific context reduces redundant reading,
anchoring, and stale implementation while preserving enough evidence to work
correctly.

Minimum experiment: medium repository with changing base commits and parallel
investigation. Measure task-entry time, stale artifacts, duplicate reads,
primary corrections, and hidden criteria.

Reject when: capsule construction costs more than it saves or removes decisive
repository context.

## 6. Bet 5 — Safe isolated implementation and single-writer integration

Representative ideas: 0301–0350, 0908–0910, 0781–0788.

Hypothesis: explicit ownership, isolated writers, fixed bases, and one
integration authority let real parallel implementation shorten the critical
path without sacrificing user changes or aggregate correctness.

Minimum experiment: multi-module feature with two parallel-ready shards, one
shared seam, generated files, and a dirty initial checkout.

Reject when: worktree/merge overhead exceeds parallel savings or writers still
conflict semantically.

## 7. Bet 6 — Evidence-based collaboration protocols

Representative ideas: 0201–0250, 0904–0907, 0959–0965.

Hypothesis: blind proposals, source/perspective partition, claim-centered
dialogue, and fresh fixed-artifact verification improve decisions by
decorrelating errors, not by adding agent volume.

Minimum experiment: matched architecture and high-loss repair campaigns. Trace
unique claims, decision changes, verifier-only defects, false positives, repair
time, and heldout outcome.

Reject when: outputs are redundant, decisions do not change, or synthesis cost
dominates.

## 8. Bet 7 — Candidate portfolio and empirical selection

Representative ideas: 0501–0550, 0789–0790, 0833–0834, 0910–0913.

Hypothesis: early diversity in core assumptions plus cheap staged elimination
beats premature commitment and local tuning on performance/architecture tasks.

Minimum experiment: fast correctness-plus-performance component with public,
confirmation, and heldout workloads. Measure family coverage, selected quality,
discarded time, winner stability, and integration cost.

Reject when: the evaluator cannot distinguish families or all candidates are
minor variations.

## 9. Bet 8 — Provider-aware routing and graceful degradation

Representative ideas: 0351–0400, 0593–0596, 0774, 0792–0794.

Hypothesis: preflight, exact identity, task-conditioned routing, bounded
fallback, and truthful unavailable states prevent wasted time and allow useful
campaign progress when providers differ or fail.

Minimum experiment: matched campaigns with ready, unauthenticated, absent,
slow, and malformed providers.

Reject when: routing is based on labels rather than project-local outcomes, or
fallback silently changes the task contract.

## 10. Bet 9 — Durable campaign and process supervision

Representative ideas: 0551–0600, 0373–0387, 0473–0480, 0785–0786.

Hypothesis: multi-axis state, atomic persistence, identity-safe descendant
control, bounded recovery, and partial-result handling convert infrastructure
faults into recoverable events instead of lost campaigns.

Minimum experiment: kill server/provider at controlled points, inject stale and
partial results, restart twice, and inspect both artifact and campaign state.

Reject when: a clean status hides wrong artifacts, recovery damages user work,
or retry loops consume the budget.

## 11. Bet 10 — Evidence-linked assurance

Representative ideas: 0451–0500, 0216–0220, 0831–0832, 0851–0900.

Hypothesis: obligation-driven tests and independent reproduced findings catch
late high-loss failures that maker self-review misses, while finding-specific
closure limits assurance cost.

Minimum experiment: known mutant corpus and one natural high-loss defect.
Compare maker-only, self-review, fresh verifier, and cross-provider verifier.

Reject when: findings are duplicate/false, targets are not frozen, or review
cost exceeds avoided failure.

## 12. Bet 11 — Automatic evidence and project-local learning

Representative ideas: 0651–0700, 0983–0990, 0920, 0946–0950.

Hypothesis: automatic claim/decision/artifact/outcome links can turn episodes
into compact conditional method guidance without human forms or raw-log context
overload.

Minimum experiment: synthetic provenance cases plus repeated matched campaigns.
Test whether the generated method card changes a later routing decision and
improves an outcome.

Reject when: adoption inference is unreliable, cards grow stale, or guidance
becomes an unjustified global preset.

## 13. Bet 12 — Evolvable product architecture

Representative ideas: 0701–0750, 0796–0800, 0835–0838.

Hypothesis: interfaces aligned with provider, campaign, state, and authority
boundaries allow new requirements to be implemented faster with fewer
regressions than a forwarding monolith.

Minimum experiment: pre-registered surprise classes—new provider protocol,
second workspace, permission boundary, or offline audit—applied after an initial
accepted artifact.

Reject when: extension points add upfront complexity but do not reduce measured
change cost.

## 14. Ideas deliberately not promoted as standalone bets

### Decorative UI

Animation, visual density, and extra controls are implementation options. They
matter only through comprehension, interruption, or task outcomes.

### Permanent role catalogs

Named teams are not inherently valuable. Roles should follow current
uncertainty, artifact, and authority.

### Generic scheduled agents

Recurring work is deferred until finite execution, dedupe, budgets, and yield
measurement exist. A deterministic script remains the control.

### Universal routing optimizer

There is not enough matched local evidence. Begin with transparent conditional
retrieval and provider readiness.

### One global quality score

Criterion vectors and Pareto surfaces remain primary. Scalar ranking is a view,
not the evidence store.

## 15. First build scope versus frontier scope

The benchmark should not require all twelve bets. The candidate chooses. The
evaluator should nevertheless expose where each bet could improve an outcome.

For the harness itself, the first revision needs only:

1. sparse objective-driven public brief;
2. stable campaign API and safety gates;
3. forwarding baseline;
4. four deep campaign families;
5. fault overlays;
6. 30/60/120-minute matched-run support;
7. criterion-level reports and raw trace;
8. known mutants proving evaluator discrimination.

The candidate product remains open. The harness is precise about observable
outcomes, not prescribed features.
