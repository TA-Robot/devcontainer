# Outer orchestration trace and causal interpretation

## 1. Objective

The hidden campaign score says whether ForgeRoom is good. It does not explain
how the current devcontainer's outer orchestration produced it. A lightweight
trace connects collaboration interventions to artifact changes without storing
private chain-of-thought.

## 2. Required automatic events

- outer goal submitted/terminal;
- plan and milestone transitions;
- agent spawn, task scope, role, and stop condition;
- provider/model/effort identity;
- task start/end and active overlap;
- approval requested/resolved and waiting duration;
- artifact returned, validity, freshness, and adoption;
- claim/decision/finding summaries when explicitly produced;
- test/evaluator run with source digest;
- commit/checkpoint;
- user interruption or external controller intervention;
- environment/provider readiness changes.

## 3. Minimal semantic packets

### Delegation packet

```yaml
purpose: shorten critical path | broaden evidence | verify | compare
artifact: bounded expected result
independence: shared and withheld context
consumer: primary or downstream task
stale_if: condition
stop: condition
```

### Return packet

```yaml
execution: completed | failed | cancelled | timed-out
artifact_validity: valid | partial | invalid
freshness: fresh | rebaseable | knowledge-only | stale
unique_findings: []
evidence: []
recommended_decision: optional
```

### Adoption packet

```yaml
artifact_or_claim: ...
decision: adopted | partial | rejected | pending
material_effect: ...
commit_test_links: []
```

These may be inferred from tool events when explicit forms would slow work.

## 4. Time decomposition

For each episode reconstruct:

- task-entry and context preparation;
- independent worker wall;
- actual active union;
- primary overlapping work;
- synthesis/review;
- integration;
- aggregate validation;
- approval/blocked wait;
- provider/tool queue;
- rework after findings;
- final assurance tail.

The goal is to identify binding constraints, not to maximize utilization.

## 5. Collaboration-value evidence grades

### E0 — Activity only

An agent ran or messages were exchanged.

### E1 — Unique valid contribution

A non-duplicate claim, artifact, or reproduced finding was returned.

### E2 — Decision/artifact effect

The contribution changed a plan, implementation, test, or rejection decision.

### E3 — Evaluated outcome effect

The changed artifact improved a matched criterion or closed a reproduced hidden
failure.

### E4 — Matched causal evidence

Same task/stratum with and without the intervention supports the effect.

Natural benchmark runs commonly reach E2–E3. Universal orchestration guidance
requires repeated E4-like evidence.

## 6. Important negative observations

- duplicate consultation;
- stale patch;
- primary reimplementation of worker output;
- architecture proposals with no discriminating probe;
- verifier false positives;
- candidate fan-out after insufficient integration budget remains;
- hidden approval waits;
- model/provider unavailable after dispatch;
- parallel workers contending on the same execution resource;
- longer design records with no requirement or outcome change.

Negative results are necessary to learn when not to use a method.

## 7. Intervention accounting

The DevRelay v1 trial included an external `/agent` switch that interrupted the
primary and required a continuation prompt. Future benchmark reports must mark
such controller interventions explicitly. They are part of operational reality
but break a claim of fully autonomous completion.

## 8. Interpreting B30/B60/B120

Compare not only final artifacts but where added time went:

- B60 discovers new requirements absent at B30;
- B120 tests competing architecture or merely polishes UI;
- verification finds new defects or repeats known checks;
- agent width shortens critical path or increases integration tail;
- additional time improves heldout/change outcomes or overfits public cases.

This is how “考えに考えた” becomes observable without inspecting private
reasoning: its external decisions and artifacts move the quality frontier.

## 9. Compact final report

The orchestrator-facing report should include:

- task fingerprint and environment stratum;
- Q-vector and hard gates;
- quality delta from matched time/method cells;
- top three material collaboration effects;
- top three wasted/negative interventions;
- binding constraint and plateau diagnosis;
- evidence grade and limits;
- smallest next discriminating experiment;
- links to raw event/artifact data.
