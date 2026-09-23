# Campaign protocol and evaluation populations

## 1. Two clocks

The benchmark separates product-development time from campaign-evaluation time.

```text
outer clock: L0 develops ForgeRoom
inner clock: frozen ForgeRoom runs L1 campaigns
```

Campaign runtime does not consume the outer development budget when it is part
of post-freeze hidden evaluation. Public dogfood invoked during development does
consume the outer budget. This prevents a candidate from being penalized for a
thorough external evaluator while still pricing its own experiments.

## 2. Artifact freeze

At the stopping budget:

1. terminate or finish active outer development actions;
2. record Git HEAD, tracked diff, untracked manifest, executable modes, and
   repository digest;
3. copy the candidate to an isolated evaluation root;
4. remove development-only credentials and hidden access;
5. run launch/conformance gates;
6. evaluate all campaigns against that exact digest.

No hidden feedback is used to modify the same frozen candidate.

## 3. Evaluation populations

### P0 — Deterministic conformance and faults

Scripted providers and workspaces validate API, persistence, isolation,
cancellation, output bounds, authority, restart, and truthful state. Runtime
target: under three minutes.

### P1 — Public development campaigns

Visible small repositories are reusable during development. Immediate
criterion-level feedback supports product iteration. They establish no final
quality claim.

### P2 — Confirmation campaigns

Same declared domains, new repositories and seeds. A candidate may invoke a
limited number during development; every invocation is recorded against the
artifact digest and consumes budget. These expose public overfitting without
revealing final heldout.

### P3 — Heldout live-provider campaigns

Concrete repositories, task wording, faults, and requirement changes remain
hidden until freeze. Codex/Grok model, effort, adapters, provider-run budget,
and environment are fixed per stratum.

### P4 — Change/adaptation campaigns

The frozen ForgeRoom code—not merely a project it controls—receives a versioned
product change request in a separate continuation run. This measures whether
earlier product discovery and architecture created real extensibility.

P4 is reported separately because it involves additional outer development.

## 4. Initial P3 campaign portfolio

### H1 — Ambiguous greenfield product

- sparse product goal;
- skeletal domain and realistic traces;
- hidden task-based workflow tests;
- malformed/reordered data and restart;
- one later project-level requirement revision.

### H2 — Context-heavy cross-module feature

- medium repository;
- API/core/persistence/test changes;
- generated boundary and dirty user file;
- two parallel-ready investigations but one shared integration seam;
- follow-up extension testing abstraction quality.

### H3 — High-loss defect

- intermittent lifecycle, concurrency, or security bug;
- several plausible causes;
- incomplete visible tests;
- hidden stress/mutant schedules;
- unnecessary edits and false findings counted.

### H4 — Performance architecture

- fast correctness/performance evaluator;
- multiple meaningful algorithm families;
- public/confirmation/heldout workloads;
- runtime and memory caps;
- worst-case robustness matters alongside mean score.

Each campaign permits multiple milestones so the evaluator can report partial
quality, not only success/failure.

## 5. Provider strata

The first study should not confound every variable. Use:

```text
primary live stratum: Codex, one fixed model, high effort
secondary availability stratum: Grok only after preflight/auth succeeds
deterministic fault stratum: scripted adapters
```

Cross-provider collaboration is a later matched cell, not a requirement for the
first valid quality curve. An unavailable Grok is recorded as environment
readiness, not silently replaced.

## 6. Campaign budget fairness

Every frozen candidate receives the same per-campaign:

- provider/model/effort identities;
- maximum provider runs;
- maximum concurrent runs;
- wall timeout;
- CPU/memory class;
- network and filesystem authority;
- initial repository digest;
- cache policy;
- visible objective and public acceptance information.

Early completion is allowed. Unused budget is reported, not forced to be spent.

## 7. Result collection outside candidate authority

The harness independently records:

- provider process start/end and exit;
- exact prompts by digest and bounded retained copy;
- filesystem and Git snapshots;
- test/evaluator commands and raw results;
- process descendants and cleanup;
- API events and response times;
- human questions/approval requests;
- resource consumption;
- campaign artifact digests.

Candidate events aid diagnosis but cannot overwrite these observations.

## 8. Milestone scoring within a campaign

Example H2 milestones:

1. repository launches and existing tests remain valid;
2. core domain behavior implemented;
3. API and persistence agree;
4. visible acceptance passes;
5. hidden invariants pass;
6. user-owned changes preserved;
7. follow-up extension passes without broad rewrite.

This allows a 70% artifact to remain distinguishable from zero and shows where
additional orchestration time could help.

## 9. Campaign feedback policy

Public campaigns provide detailed diagnostic feedback. Confirmation provides
criterion categories and failure stage but not exact hidden assertions. Heldout
provides complete reporting only after final scoring and cannot be used to
repair the same candidate.

This keeps development iterative without converting all truth into a public
test suite.

## 10. Replay and stochasticity

Live provider runs are repeated only after the deterministic corpus is stable.
For semantic campaigns:

- use at least three matched runs for a comparative claim;
- preserve every result rather than auto-retry;
- report median, range, lower bound, and failure categories;
- treat model/provider revision as a new stratum;
- distinguish run variance from source-digest change.

One rich natural episode can motivate a method but cannot establish a universal
routing rule.
