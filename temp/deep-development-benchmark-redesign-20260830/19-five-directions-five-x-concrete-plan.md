# Making each of the five chat-system directions genuinely five-times harder

## 1. Baseline being multiplied

DevRelay v1 was completed in 2,036 seconds (33:56) and scored 100/100. That
result is the reference point, but its score covered a closed protocol surface:

- native page and health;
- channels, messages, threads, and persistence;
- concurrent Codex/Grok adapter execution;
- malformed output, cancellation, and restart.

It did not establish better software-development outcomes. Its one real Codex
canary took roughly six minutes and received explicit hidden-test feedback. The
evaluator had almost no frontier after conformance and lifecycle correctness.

“Five-times harder” therefore does not mean five times as many endpoints. A new
direction earns that label only after calibration shows substantially more
useful technical decisions and refinement after its first working chat.

## 2. Five-times difficulty contract

Each direction below must meet all of these fixture-design targets:

1. **Fast floor:** a competent implementation can launch chat and execute one
   truthful provider-backed development task within 20–30 minutes.
2. **Long frontier:** a strong fresh single-agent developer still has useful
   scored work at 120 minutes; the intended full calibration budget is B180.
3. **Five interacting mechanisms:** at least five concerns must cross product
   layers rather than appear as independent checklist features.
4. **Three viable solution families:** no single prescribed architecture should
   dominate public, confirmation, and heldout situations.
5. **Downstream utility:** at least half of the quality surface comes from real
   software artifacts or human development tasks, not chat protocol conformance.
6. **Change pressure:** V1 is frozen and then receives a declared-domain product
   change that reveals architecture quality.
7. **Fault pressure:** provider, process, Git, state, or user-timing faults are
   composed with normal work.
8. **Automatic evidence:** humans do not fill in routine success labels.
9. **Mutant separation:** forwarding, UI-rich forwarding, indiscriminate
   parallelism, review theatre, unsafe integration, and volatile state occupy
   different failure profiles.
10. **Ceiling alarm:** if a fresh strong run clears every criterion before 75%
    of B120, the task is still not accepted as five-times harder.

The 5x claim is provisional until matched runs validate these targets.

## 3. Shared evaluation shape

Every option uses five evaluation layers:

```text
P0  protocol and safety conformance
P1  public development/user episodes
P2  confirmation episodes with changed names, order, and workload
P3  heldout episodes from the same declared problem domain
P4  product-change continuation against the frozen V1 artifact
```

P0 is a gate, not a 100-point score. P1–P4 retain criterion-level vectors and a
quality-time curve. An option is rejected when P0 dominates its ranking.

---

# Option A — RoomOS ×5

## 4. Harder thesis

Build a native development room where conversation, goal state, decisions,
tasks, artifacts, and accepted delivery remain one coherent truth under edits,
concurrency, branching, compaction, and restart. The challenge is not rendering
typed cards. It is keeping natural chat and machine-actionable state mutually
consistent as history evolves.

## 5. Five load-bearing interactions

### A1 — correction propagation

A user corrects the broad objective after tasks, assumptions, and one artifact
were derived. The system must identify what is invalidated, what remains useful,
what needs review, and why. It may not silently rewrite the original message or
continue stale work.

### A2 — conversation branch and evidence merge

Two agents investigate incompatible approaches in separate semantic branches.
The room later merges a selected decision, one test from the rejected branch,
and residual dissent without duplicating or losing provenance.

### A3 — concurrent human/agent state

Two humans and several agents operate from stale views. Message correction,
task claim, decision acceptance, and artifact update overlap. Current truth must
converge while each losing or superseded action remains understandable.

### A4 — compaction with live references

A long room exceeds the active context budget. Compaction must preserve
requirements, unresolved cruxes, source anchors, artifact versions, and rejected
assumptions while allowing fresh agents and returning users to complete tasks.

### A5 — crash between truth layers

The server crashes after a Git artifact changes but before its chat projection
is stored, and again after an event is stored but before a response reaches the
client. Recovery reconciles actual workspace truth and room state without
fabricating delivery.

## 6. Completion floor

- chat from broad goal to one provider-backed artifact;
- typed identities for goal, task, decision, and artifact;
- restart persistence;
- current-state view plus immutable history;
- one clean accepted Git outcome.

## 7. Quality frontier

- correction invalidation precision and missed stale work;
- branch/merge evidence retention;
- concurrent convergence and actionable conflicts;
- fresh-user comprehension after compaction;
- room/workspace reconciliation after crash;
- chat actions required for normal steering;
- accessible coding-adjacent UI;
- product-change cost for cross-room references or a new artifact type.

## 8. Viable architecture families

- append-only event log with derived projections;
- document/CRDT conversation plus typed side ledger;
- Git-backed room objects with chat projections;
- hybrid event log and content-addressed artifact graph.

## 9. Why DevRelay's solution fails

A persisted message list and run list cannot express invalidation, branch/merge,
artifact reconciliation, or safe compaction. Adding card types without causal
links creates contradictory decoration rather than development truth.

## 10. B30/B60/B120/B180 expectation

- **B30:** floor and basic typed projection;
- **B60:** correction propagation and artifact linkage;
- **B120:** branch/merge, concurrent users, fault reconciliation;
- **B180:** compaction dogfood, task-based UX refinement, change adaptation.

## 11. Rejection gate

Reject if task-based users perform no better than plain transcript search, or if
the best implementation is simply “DevRelay plus more JSON object types.”

---

# Option B — ForgeLab ×5

## 12. Harder thesis

Build a chat-native studio that chooses and executes an appropriate collaboration
method for uncertain software work. It must create independent technical
evidence, run competing artifacts or experiments, synthesize a decision, and
deliver an accepted result. Agent count and debate length receive no credit.

## 13. Five load-bearing interactions

### B1 — method selection before knowing the answer

The studio receives campaigns that benefit respectively from sequential work,
specialist consultation, independent verification, parallel implementation, and
empirical candidate competition. It must avoid applying one fixed team shape to
all five.

### B2 — executable disagreement

Two plausible architectures disagree on a measurable crux. The system converts
the crux into a bounded experiment, preserves each prior, and changes the final
decision only from evidence—not majority vote.

### B3 — candidate portfolio and integration

Several agents produce genuinely different implementations from the same frozen
base. The system compares them under one contract, extracts useful tests from
losers, selects a winner, and integrates it without stale or conflicting work.

### B4 — maker/verifier reopening

A fresh verifier reproduces a high-loss defect after the maker claimed
completion. The campaign reopens, assigns repair ownership, closes the exact
finding, reruns integrated acceptance, and retains truthful terminal history.

### B5 — provider degradation

Codex, Claude, and Grok differ in availability, latency, context, and task
quality. One becomes unavailable and another returns malformed/late output. The
studio replans bounded work without silently weakening the objective or
duplicating already accepted effort.

## 14. Completion floor

- broad goal accepted through native chat;
- at least two bounded tasks with explicit artifacts;
- one provider execution and one independent verification;
- clean integrated commit with command evidence;
- truthful terminal state and residual unknowns.

## 15. Quality frontier

- accepted milestones versus direct forwarding;
- unique decision-changing evidence;
- best integrated candidate quality;
- time-to-first-valid and time-to-best;
- duplicate work and integration tail;
- verifier-only defects and false findings;
- method-routing regret;
- provider failure recovery;
- marginal gain per dialogue turn/run;
- later change success on the same project.

## 16. Viable architecture families

- explicit dependency DAG and dynamic roles;
- blackboard/artifact-market coordination;
- primary-led opportunistic consultation;
- candidate portfolio with staged elimination;
- evidence-event workflow without a fixed task graph.

## 17. Required inner episode portfolio

One task cannot validate ForgeLab. The frozen evaluator supplies at least:

1. a tightly coupled implementation where fanout hurts;
2. a multi-module task with real parallel seams;
3. an ambiguous architecture task with cheap experiments;
4. a high-loss defect task benefiting from fresh verification;
5. a continuation task that tests context and prior decisions.

## 18. Why DevRelay's solution fails

Mention-triggered parallel Codex/Grok runs provide concurrency but no method
selection, artifact ownership, candidate comparison, synthesis, integration, or
downstream outcome advantage. Richer messages cannot substitute for those.

## 19. B30/B60/B120/B180 expectation

- **B30:** forwarding-compatible floor plus basic task/verification flow;
- **B60:** dependency-aware work and clean integration;
- **B120:** candidate competition, crux experiments, provider degradation;
- **B180:** portfolio dogfood, routing refinement, change continuation.

## 20. Rejection gate

Reject if the strongest reference does not beat forwarding on at least three
different inner episode mechanisms, or if extra agents mostly produce prose and
coordination cost.

---

# Option C — Shipyard ×5

## 21. Harder thesis

Build a chat-native delivery system that owns the path from objective to clean,
accepted Git result under dirty user state, concurrent candidates, process
failure, verification disagreement, and repository evolution. Provider success
is never equivalent to software delivery.

## 22. Five load-bearing interactions

### C1 — dirty user state and isolated writers

The initial workspace contains staged, unstaged, and untracked user work. Two
agents need overlapping files. The system preserves ownership, creates safe
isolation, and integrates only authorized task changes.

### C2 — provider cannot commit

A provider can edit the workspace but `.git` is read-only, matching the observed
ForgeRoom failure. Shipyard owns staging, diff review, acceptance, commit, and
attribution without crediting unverified provider claims.

### C3 — evidence disagreement

The provider reports tests and lint passing. Captured full-suite evidence
disagrees, with both pre-existing failures and a regression. The room must scope
claims correctly, repair the regression, and not demand unrelated cleanup.

### C4 — integration and process race

A long-running test and child server survive while the base branch moves. A
candidate completes late after cancellation. Shipyard rejects stale success,
terminates owned descendants, rebases or regenerates safely, and reruns
acceptance on the integrated tree.

### C5 — multi-repository product change

V1 handles one repository. The continuation adds a second repository with
separate authorities and a compatibility contract. Delivery must be coordinated
without pretending filesystem atomicity or losing rollback evidence.

## 23. Completion floor

- initial ownership snapshot;
- scoped provider execution;
- command/test evidence;
- safe commit of one accepted change;
- cancellation and restart truth;
- reproducible final instructions.

## 24. Quality frontier

- lost/overwritten user work as a hard gate;
- accepted obligations and escaped regressions;
- commit/evidence attribution correctness;
- conflict and integration-tail time;
- stale-result rejection;
- descendant process cleanup;
- restart at every delivery boundary;
- partial-result salvage;
- rollback and compatibility quality;
- continuation change amplification.

## 25. Viable architecture families

- worktree-per-writer with integration queue;
- patch/candidate store plus controller-owned apply;
- content-addressed artifact graph and final materialization;
- single working tree with strict staged ownership and serial commits.

## 26. Why DevRelay's solution fails

DevRelay delegates Git completion to the provider and records run status. It does
not own artifact acceptance, integration, stale base handling, command evidence,
or repair after a provider cannot commit.

## 27. B30/B60/B120/B180 expectation

- **B30:** safe single-workspace delivery floor;
- **B60:** controller-owned Git integration and evidence;
- **B120:** concurrent candidates, dirty state, process/fault matrix;
- **B180:** two-repository continuation and rollback dogfood.

## 28. Rejection gate

Reject if Git/process plumbing consumes the full budget before any downstream
development campaign can run, or if a simple serialized controller matches the
reference on throughput and quality.

---

# Option D — Quiet Autopilot ×5

## 29. Harder thesis

Build a chat development partner that maximizes accepted progress while treating
human attention as a scarce resource. It must work through long human silence,
continue reversible safe tasks, consolidate high-value decisions, and prevent
proactive/scheduled work from becoming unbounded low-yield agent activity.

## 30. Five load-bearing interactions

### D1 — silent human campaign

After the initial broad goal, the human provides no routine answers for 90
minutes. The system must make explicit assumptions, pursue safe work, avoid
inventing preferences, and reach the best defensible partial or complete result.

### D2 — one intervention opportunity

The evaluator permits one human response at a randomly selected time. The
system must have consolidated the highest-value unresolved decision with clear
consequence, default, and deadline rather than spending the opportunity on a
routine approval.

### D3 — foreground/background collision

A scheduled maintenance agent and an active feature agent touch related tests.
The system detects duplication and ownership conflict, yields background work,
and preserves useful findings without delaying the critical path.

### D4 — low-yield recurrence

A recurring review repeatedly finds nothing. Deduplication, minimum interval,
provider budget, and observed yield must cause suspension or replacement by a
deterministic check.

### D5 — risk inversion

An initially reversible assumption becomes expensive after a migration begins,
while a previously risky unknown becomes safely testable. The autonomy policy
must reclassify both from evidence rather than keep the original labels.

## 31. Completion floor

- broad goal and autonomous plan;
- visible assumptions and authority boundaries;
- safe progress without human replies;
- consolidated intervention queue;
- ambient return summary;
- finite background-job contract.

## 32. Quality frontier

- accepted milestones per wall hour;
- interruption count and information value;
- blocked time due to unanswered routine questions;
- unsafe/rework-heavy assumptions;
- useful progress during absence;
- return-to-correct-understanding time;
- notification precision/recall;
- scheduled-job yield and provider use;
- foreground collision cost;
- policy adaptation after risk inversion.

## 33. Viable architecture families

- explicit value-of-information decision policy;
- risk/reversibility rules with learned calibration;
- milestone-based autonomy state machine;
- primary-agent judgment with auditable assumption ledger.

## 34. Why DevRelay's solution fails

DevRelay waits for explicit mentions and forwards them. It neither discovers
safe next work nor values interruptions, consolidates approvals, schedules finite
jobs, or adapts assumptions as project risk changes.

## 35. B30/B60/B120/B180 expectation

- **B30:** assumption ledger and basic autonomous floor;
- **B60:** ambient UX and consolidated escalation;
- **B120:** scheduled work, collision control, silent-human dogfood;
- **B180:** value-of-information calibration and risk-inversion change.

## 36. Rejection gate

Reject if “fewer questions” is achieved by silent risky action, or if background
agents consume budget without accepted downstream artifacts.

---

# Option E — Project Brain ×5

## 37. Harder thesis

Build a chat development system that learns bounded project-local orchestration
knowledge and proves its value on later matched campaigns. The hard part is not
storing memory; it is distinguishing reusable causal signal from episode noise,
using it safely, and forgetting it under drift.

## 38. Five load-bearing interactions

### E1 — duration and capability learning

The system observes automatically captured task durations, outcomes, provider
versions, and effort levels. It predicts future task cost and routing with
uncertainty, without requiring human labels.

### E2 — method-card promotion

A repeated project problem suggests a reusable workflow. The system derives a
compact method card, shadows it, compares against baseline, and promotes it only
after a later artifact improves.

### E3 — negative transfer

Guidance learned from an easy subsystem harms a different subsystem. Scope,
contrary evidence, and rollback must prevent the project prior from becoming a
global rule.

### E4 — provider/version drift

Codex, Claude, or Grok changes version/readiness and invalidates duration or
quality priors. The system detects drift, lowers confidence, explores safely,
and does not treat provider name as stable capability.

### E5 — contamination and forgetting

A public benchmark answer leaks into memory, while an old commit reference and
obsolete architecture decision remain retrievable. The system quarantines
contamination, expires stale anchors, compacts evidence, and preserves the audit
reason for forgetting.

## 39. Completion floor

- automatic evidence capture;
- scoped project memory with source anchors;
- one conditional duration/quality prior;
- one shadow decision;
- explicit uncertainty, expiry, and rollback;
- no authority gained from memory.

## 40. Quality frontier

- matched later-campaign outcome improvement;
- routing/duration regret and calibration;
- task-entry time and stale-context defects;
- method adoption linked to artifact changes;
- negative transfer rate;
- drift-detection delay;
- context/memory overhead;
- contamination detection;
- rollback/forgetting correctness;
- improvement retained across restart and compaction.

## 41. Viable architecture families

- Bayesian/empirical project priors;
- case-based episodic retrieval with method cards;
- contextual routing rules learned from trace;
- shadow policy and bandit-like safe promotion;
- human-readable conditional skill synthesis.

## 42. Required repeated episodes

Project Brain cannot be evaluated in one run. Use at least:

1. two baseline episodes establishing evidence;
2. one matched repeat where guidance could help;
3. one superficially similar negative-transfer episode;
4. one provider/version drift episode;
5. one contamination/expiry episode.

## 43. Why DevRelay's solution fails

DevRelay persists conversation but does not infer scoped reusable knowledge,
compare later counterfactuals, calibrate routing, or forget stale guidance.
Transcript persistence is not learning.

## 44. B30/B60/B120/B180 expectation

- **B30:** evidence schema and scoped memory floor;
- **B60:** duration/provider priors and shadow routing;
- **B120:** method-card promotion and negative-transfer defense;
- **B180:** drift, contamination, forgetting, matched repeat evaluation.

## 45. Rejection gate

Reject if memory receives credit before improving a later matched outcome, or if
episode-specific answers can masquerade as general project knowledge.

---

## 46. Comparison of the five five-times plans

| Option | Primary difficulty source | Best downstream evidence | Biggest fixture risk |
|---|---|---|---|
| RoomOS ×5 | evolving shared truth | user task + artifact consistency | subjective UX creeping in |
| ForgeLab ×5 | choosing useful collaboration | multi-campaign software quality | inner episode portfolio cost |
| Shipyard ×5 | delivery across unsafe boundaries | clean accepted commits | plumbing dominates |
| Quiet Autopilot ×5 | outcome vs attention trade-off | silent-human campaign result | intervention value oracle |
| Project Brain ×5 | learning across time | matched later-campaign gain | long repeated evaluation |

## 47. Which plan should be built first

**ForgeLab ×5 remains the strongest primary choice**, but only if a minimal
Shipyard delivery substrate is supplied or required early. It most directly
tests whether richer agent relationships improve software development, the
original purpose of the environment.

**RoomOS ×5** is the best choice if product/chat design itself is the intended
focus. **Shipyard ×5** is the safest objective evaluator. **Quiet Autopilot ×5**
and **Project Brain ×5** are better as later product-change campaigns because
they require longer observation horizons.

Do not ask one B180 run to implement all five options completely. That creates a
feature-volume contest. Select one primary option, include only the shared P0
substrate, and use one other option as a pre-registered continuation change.

## 48. Concrete calibration protocol

For each option:

1. build a deterministic P0 fixture and one public episode;
2. run direct forwarding M0 and UI-rich forwarding M1;
3. run one strong reference and a deliberately flawed option-specific mutant;
4. verify different failure profiles before any live outer run;
5. run fresh single-agent B30/B60/B120 from the same base;
6. run one multi-agent B120 only after the single-agent curve exists;
7. reveal the option-specific P4 continuation for 30–60 minutes;
8. reject the 5x label if B30 and B120 tie or if P0 determines ranking.

## 49. Evidence required before saying “five times harder”

The label becomes evidence-backed only when:

- B30 crosses the floor but leaves at least three mechanism groups weak;
- B60 materially improves an accepted artifact rather than only adding tests;
- B120 materially improves over B60 on confirmation or heldout outcomes;
- a strong run still has plausible scored work at stop time;
- forwarding and feature-rich forwarding remain materially below the reference;
- the option-specific mutant fails where intended;
- a multi-agent run produces unique executable evidence and repays coordination;
- run-to-run provider variance does not dominate ranking;
- the P4 change distinguishes durable design from speculative abstraction.

Until those observations exist, these are five concrete 5x hypotheses—not five
proven five-times-hard tasks.
