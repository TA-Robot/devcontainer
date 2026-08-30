# From 1,000 chat-system ideas to five product directions

> This document selects the five directions. Their concrete five-times-hard
> scenario packs, time curves, mutants, and proof gates are defined in
> `19-five-directions-five-x-concrete-plan.md`.

## 1. Decision

The chat-development-system inventory is reduced to five coherent product
directions:

1. **RoomOS** — chat-native development state and shared understanding;
2. **ForgeLab** — adaptive multi-agent deliberation, candidate competition, and
   empirical selection;
3. **Shipyard** — Git-native evidence-based delivery, integration, and recovery;
4. **Quiet Autopilot** — low-interruption autonomous development over long
   periods;
5. **Project Brain** — project-local learning and adaptive orchestration.

They are alternative product bets for comparison, but they also form a sensible
depth sequence. RoomOS and Shipyard establish trustworthy execution. ForgeLab
adds multi-agent quality. Quiet Autopilot changes the human relationship.
Project Brain attempts to improve later campaigns from accumulated evidence.

## 2. What was actually selected

The 1,000 entries are generated from 200 core capabilities across five depths:

1. human/agent experience;
2. typed state and contract;
3. conflict and failure;
4. automatic evaluation;
5. compatible evolution.

Selecting individual rows would produce a feature checklist. The useful unit is
a causal product bundle:

```text
user/development problem
 -> chat-native workflow
 -> explicit durable truth
 -> autonomous or multi-agent mechanism
 -> observable software outcome
 -> failure/recovery behavior
 -> later-compatible evolution
```

Each final direction spans that entire chain.

## 3. Selection criteria

| Criterion | Weight | Question |
|---|---:|---|
| Development outcome | 20 | Does it increase accepted software delivery rather than chat activity? |
| Multi-agent leverage | 15 | Can agent interaction change decisions or artifacts? |
| Human attention | 15 | Does it reduce interruption without hiding risk? |
| Trust and recoverability | 15 | Can truth survive conflict, failure, and restart? |
| Automatic evaluation | 15 | Can usefulness be measured without human forms? |
| Product coherence | 10 | Does it feel like one system rather than many controls? |
| Evolution ceiling | 10 | Do later requirements expose architecture quality? |

Scores below are design estimates, not measured benchmark results.

## 4. Shortlist before consolidation

The inventory initially yielded twelve candidate bundles:

- Slack-like multi-agent room;
- typed development event system;
- goal/requirement discovery workspace;
- task graph and execution scheduler;
- agent debate and consultation room;
- candidate implementation arena;
- provider/model router;
- context and project memory system;
- Git/worktree integration control plane;
- test/evidence assurance system;
- low-interruption autonomous assistant;
- self-learning orchestration system.

Several are mechanisms rather than products. The following consolidations were
made:

- Slack-like room + typed events + goal state became **RoomOS**;
- task graph + debate + candidates + provider routing became **ForgeLab**;
- Git + terminal + tests + evidence + recovery became **Shipyard**;
- attention policy + assumptions + scheduled work became **Quiet Autopilot**;
- context memory + evidence learning + adaptive routing became **Project Brain**.

## 5. Ideas deliberately not promoted alone

### Provider router

Routing by itself optimizes labels and latency but does not guarantee a better
artifact. It belongs inside ForgeLab and Project Brain, where a downstream
decision can validate it.

### Scheduled agents

Recurrence alone risks infinite credit consumption and duplicated work. It
belongs inside Quiet Autopilot with finite jobs, dedupe, yield measurement, and
stop conditions.

### Memory system

Memory can create context bloat and stale authority. It belongs inside Project
Brain, which must demonstrate an improved later decision and support forgetting.

### Plugin platform

Extensibility without a valuable extension is speculative architecture. Plugin
contracts are evaluated through provider, artifact, evaluator, and skill changes
inside the five directions.

### Decorative chat richness

Emoji, animation, dashboards, and extra panes are options only when they improve
task comprehension, attention, or intervention. They are not independent bets.

### Permanent named agent teams

Fixed roles and fixed agent counts reproduce a preset rather than discover a
useful collaboration structure. ForgeLab chooses roles and depth from current
uncertainty.

## 6. Comparative view

| Direction | Estimated fit /100 | Strongest signal | Main risk |
|---|---:|---|---|
| ForgeLab | 94 | multi-agent interaction changes selected implementation | coordination theatre |
| Shipyard | 92 | accepted, tested, integrated software outcome | plumbing dominates UX |
| RoomOS | 90 | chat becomes trustworthy development state | sophisticated Slack clone |
| Quiet Autopilot | 86 | lower human interruption over long campaigns | silent unsafe autonomy |
| Project Brain | 81 | later campaigns improve from evidence | sparse-data self-deception |

The order reflects value for the original objective, not implementation order.
RoomOS and Shipyard must exist before ForgeLab can be trusted.

---

# Direction 1 — RoomOS

## 7. Thesis

The room should not be a transcript with agent messages. It should be the native
development state shared by humans and agents. A broad goal, requirement,
decision, task, artifact, experiment, approval, and terminal outcome all appear
through chat, while retaining explicit machine-readable identity and lifecycle.

The product succeeds when a developer can understand and steer real work from
the conversation without reconstructing truth from raw logs or hidden files.

## 8. User experience

- one room begins from a broad development objective;
- conversational messages can create or update goals, decisions, tasks, and
  artifact references without slash-command ceremony;
- important objects appear inline as compact native cards, not separate admin
  forms;
- threads represent semantic scope such as goal, investigation, candidate, or
  incident rather than arbitrary reply chains;
- humans and agents can correct, retract, supersede, branch, and merge thinking;
- the room shows current truth and history separately;
- code remains the main workspace, with ambient progress and risk rather than a
  dominant dashboard;
- after absence, the user receives a delta of decisions, artifacts, failures,
  and genuinely valuable intervention points.

## 9. State contract

RoomOS needs an append-only typed event model with stable identities for:

- room, campaign, goal, requirement, milestone, task;
- message, correction, decision, assumption, approval;
- agent/provider attempt and consultation;
- artifact, commit, test, benchmark, experiment;
- interruption, failure, recovery, and terminal evidence.

Editable projections may exist, but original messages and evidence remain
auditable. A displayed “done” state must be derivable from accepted obligations
and artifacts, not from an agent's prose.

## 10. Hard interactions

- a user corrects a message after two tasks were derived from it;
- two agents create competing decisions from stale room views;
- one candidate thread is abandoned while its useful test is retained;
- a message is retracted after an external side effect already occurred;
- the server restarts between artifact creation and chat notification;
- one room branches for an experiment and later merges selected evidence;
- a second user returns with a different local unread state;
- a referenced commit is rebased or replaced;
- a long room is compacted without erasing decisive dissent.

## 11. Evaluation

- task success for “what is being built, why, what changed, what remains?”;
- time and actions needed to find current accepted truth;
- stale or contradictory projection count;
- restart/replay equivalence;
- message-to-decision-to-artifact trace completeness;
- interruption count and unnecessary UI actions;
- accessibility and keyboard-only task completion;
- change amplification when a new object or lifecycle is introduced.

## 12. Why this is five-times harder

A basic chat UI can cross the floor quickly. The ceiling comes from maintaining
coherent human interaction and typed truth across edits, branches, artifacts,
concurrency, compaction, and restart. No single additional endpoint solves all
of those relationships.

## 13. Traceability

Primary inventory ranges: C0001–C0050, C0101–C0200, C0401–C0450,
C0651–C0750, and C0951–C1000.

---

# Direction 2 — ForgeLab

## 14. Thesis

The room should actively improve difficult technical decisions by forming an
appropriate temporary team, obtaining independent evidence, running competing
implementations or experiments, resolving cruxes, and integrating the best
supported result. It must optimize accepted outcome and critical path, not agent
count or discussion volume.

## 15. Collaboration modes

ForgeLab selects among modes instead of always using one orchestration recipe:

- delegated bounded implementation;
- independent proposals before anchoring;
- specialist consultation;
- repeated dialogue around a named crux;
- blind/fresh artifact verification;
- parallel candidate implementation;
- experiment and ablation tournament;
- red-team/adversarial review;
- single-writer integration;
- sequential deep work when parallelism would not help.

No default “three agents” or “two rounds” is encoded. Fanout and dialogue depth
are bounded by uncertainty, dependency, budget, and observed information gain.

## 16. Provider and role selection

Codex, Claude, and Grok are represented through capability/version contracts.
Roles are temporary responsibilities with an artifact and stop condition, not
personas. Routing uses project-local observations of quality, duration,
availability, and failure, while preserving an explicit fallback and the option
to use only the primary agent.

## 17. Candidate and experiment lifecycle

```text
hypothesis
 -> independent candidate or analysis
 -> frozen comparison contract
 -> public/confirmation evidence
 -> decision with dissent
 -> selected integration
 -> independent acceptance
 -> residual unknowns
```

Discarded candidates retain useful tests, measurements, and failure evidence.
The winning idea is not credited until integrated and accepted in the actual
workspace.

## 18. Hard interactions

- two agents unknowingly implement semantic duplicates;
- the minority design wins the heldout workload;
- consultation improves prose but not the implementation;
- a fast provider returns a weak candidate before a strong one completes;
- candidate tests use incompatible assumptions;
- the best algorithm is expensive to integrate;
- a verifier finds a defect after the winner was declared;
- provider authentication fails midway through a planned quorum;
- model/effort labels change between environment versions;
- discussion continues after marginal information gain reaches zero.

## 19. Evaluation

- accepted milestone quality versus forwarding baseline;
- time-to-first-valid and time-to-best-integrated;
- unique claims, defects, tests, and candidate families;
- decision changes caused by independent evidence;
- duplicate effort and synthesis/integration tail;
- verifier-only escaped-defect reduction;
- candidate selection stability on confirmation data;
- provider/model routing regret;
- marginal benefit per consultation turn and agent run;
- clean final artifact and truthful terminal evidence.

## 20. Why this is five-times harder

It requires the system to decide whether collaboration is useful, construct it,
compare executable evidence, and integrate the result. More agents can make the
outcome worse, so success cannot be achieved by simple fanout or a static team.

## 21. Traceability

Primary inventory ranges: C0151–C0350, C0551–C0600, C0701–C0750,
C0851–C0950.

---

# Direction 3 — Shipyard

## 22. Thesis

The chat room should own the complete path from a broad objective to a clean,
tested, reviewable Git result. Provider output and dirty files are not delivery.
Shipyard preserves user changes, isolates writers, executes commands safely,
captures assurance evidence, integrates selected work, and recovers truthfully
after interruption.

## 23. Delivery model

- snapshot initial HEAD and dirty user state;
- derive artifacts, ownership, dependencies, and authority;
- create isolated worktrees or equivalent writer boundaries;
- supervise terminal processes under scoped run identities;
- link commands, tests, benchmarks, and results to candidate commits;
- freeze artifacts for independent review;
- integrate through one explicit authority;
- rerun acceptance on the integrated tree;
- produce a final commit, reproducible instructions, and residual risks.

## 24. Trust boundaries

Shipyard distinguishes:

- provider success from accepted software;
- test claim from captured command evidence;
- dirty artifact from integrated commit;
- pre-existing failure from regression;
- user-owned change from campaign change;
- source branch from candidate worktree;
- cancellation request from confirmed descendant termination;
- local reversible action from external or destructive action.

## 25. Hard interactions

- the provider sandbox can edit files but cannot write `.git`;
- the initial workspace already contains uncommitted user changes;
- two candidates modify one shared schema and generated output;
- a test passes in the worktree but fails after integration;
- a long-running child survives provider cancellation;
- the server crashes after commit but before terminal persistence;
- the base branch moves while candidates are running;
- a second repository must change atomically with the first;
- rollback crosses a data/schema migration;
- verification evidence contradicts the provider summary.

## 26. Evaluation

- accepted functional and quality obligations;
- lost or silently overwritten user changes as a hard failure;
- correct base/final digests and clean integration;
- reproduced tests and exact command evidence;
- merge conflict, rework, and integration-tail time;
- process leak and authority escape tests;
- restart/cancel/replay truthfulness;
- recovery time and retained partial value;
- multi-repository consistency;
- change cost for a new provider/workspace/permission contract.

## 27. Why this is five-times harder

Every development feature eventually crosses Git, process, test, authority, and
recovery boundaries. These interact in ways that a chat transcript or provider
wrapper cannot hide. The product must remain trustworthy when the happy path
ends, while still keeping normal development fast.

## 28. Traceability

Primary inventory ranges: C0401–C0750, C0801–C0850, C0951–C1000.

---

# Direction 4 — Quiet Autopilot

## 29. Thesis

The system should make useful progress while the human is coding, away, or
unwilling to answer routine questions. It asks only when intervention has high
expected value, continues reversible safe work, and reports important deltas in
a compact ambient form. Autonomy is judged by outcomes and avoided interruption,
not by silence.

## 30. Autonomy policy

Every uncertainty is classified by:

- expected loss if guessed wrong;
- reversibility and rollback cost;
- effect on the critical path;
- available project evidence;
- confidence and disagreement;
- deadline for useful human input;
- safe fallback if no answer arrives.

Low-risk assumptions proceed and remain visible. High-risk irreversible actions
stop or request one consolidated decision. Lack of human response never grants
new authority.

## 31. Ambient experience

- a thin coding-adjacent strip shows current milestone, meaningful risk, and
  next useful intervention;
- long agent logs remain collapsed;
- returning users receive a decision/artifact/failure delta;
- approvals are consolidated with consequence and default;
- milestones and failures surface naturally without pet-like manual rituals;
- drafts and annotations are preserved without interrupting active agents;
- work can be reprioritized at the next safe point.

## 32. Proactive and scheduled work

Background agents run only as finite, deduplicated, budgeted jobs with a yield
hypothesis. Examples include dependency review, flaky-test repair, benchmark
watch, stale-documentation detection, and unfinished-task recovery. Each job has
an identity, scope, stop condition, next eligible time, and measured downstream
effect. A deterministic script remains preferable when no agent judgment is
needed.

## 33. Hard interactions

- the user ignores every noncritical question;
- several agents request related approvals simultaneously;
- a reversible assumption becomes costly after later evidence;
- background work overlaps an active foreground edit;
- scheduled work repeatedly finds nothing useful;
- a provider outage turns a finite job into a retry risk;
- a high-risk ambiguity occurs minutes before deadline;
- the user changes priority while an integration is in progress;
- notification dedupe hides a materially changed failure;
- a silent agent made progress but left no accepted artifact.

## 34. Evaluation

- accepted milestones per wall hour;
- number, timing, and value of human interruptions;
- blocked time attributable to unanswered questions;
- unsafe or high-rework assumptions;
- recoverable work completed during human absence;
- notification precision/recall for intervention-worthy events;
- time for a returning human to regain correct understanding;
- scheduled-job yield and provider consumption;
- collision with foreground work;
- autonomy policy change under matched later campaigns.

## 35. Why this is five-times harder

The system must optimize two coupled objectives: development outcome and scarce
human attention. Suppressing questions trivially improves one metric while
damaging the other. Value depends on project risk, timing, reversibility, and
actual downstream work.

## 36. Traceability

Primary inventory ranges: C0051–C0150, C0601–C0800, C0851–C0950.

---

# Direction 5 — Project Brain

## 37. Thesis

The system should learn compact, conditional orchestration knowledge from its
own project evidence and use it to improve later development. It must not turn a
few episodes into universal presets, leak heldout answers, or accumulate stale
context. Learning is credited only when it changes a later decision and improves
an independently evaluated outcome.

## 38. Learning targets

- task duration and variance by project stage;
- provider/model/effort quality for bounded task classes;
- useful versus wasteful parallelism;
- verifier defect yield and false-positive cost;
- experiment family success under workload properties;
- common failure and recovery paths;
- human preference and interruption value;
- context capsule usefulness and staleness;
- stop/continue marginal return;
- project-specific methods worth packaging as skills.

## 39. Knowledge contract

Every learned item records:

- scope and applicability conditions;
- source campaign/artifact/outcome evidence;
- sample count and uncertainty;
- creation and last-validation version;
- contrary examples;
- consumers and observed decision changes;
- expiry, forgetting, and rollback rules.

Raw transcripts are not injected wholesale. Compact method cards and priors are
retrieved only for relevant decisions.

## 40. Adaptive orchestration loop

```text
observe automatic evidence
 -> derive a bounded hypothesis
 -> shadow or low-risk use
 -> compare against baseline/counterfactual
 -> promote project-local guidance
 -> monitor drift and adverse outcomes
 -> revise, expire, or package as a skill
```

The primary agent remains responsible for current evidence and can override a
prior. Learned routing never grants authority.

## 41. Hard interactions

- one successful episode creates a misleading global rule;
- provider versions change after a routing prior was learned;
- an easy repeated task contaminates duration estimates;
- a method card encodes a public benchmark answer;
- user preference conflicts across projects;
- context memory points to a replaced commit;
- old failure guidance prevents trying a now-valid approach;
- shadow policy improves mean quality but worsens rare failures;
- a skill grows until it consumes more context than it saves;
- learning and evaluator versions change simultaneously.

## 42. Evaluation

- matched later-campaign improvement versus no-memory baseline;
- routing regret and calibration;
- task-entry time and stale-context defects;
- method-card adoption linked to artifact changes;
- false generalization and negative transfer;
- memory/context size and retrieval overhead;
- expiry and rollback correctness;
- heldout contamination detection;
- repeatability across provider/version changes;
- human correction required to undo bad learning.

## 43. Why this is five-times harder

It introduces a second time horizon. The product must deliver the current
campaign and create justified knowledge that helps later campaigns. Observing a
correlation is easy; scoping it, validating it, using it safely, and forgetting
it when conditions change is not.

## 44. Traceability

Primary inventory ranges: C0301–C0400, C0701–C0750, C0801–C0950,
C0991–C1000.

---

## 45. Portfolio coverage

| Target capability | RoomOS | ForgeLab | Shipyard | Quiet Autopilot | Project Brain |
|---|---:|---:|---:|---:|---:|
| Natural chat collaboration | very high | high | medium | high | low |
| Multi-agent quality gain | medium | very high | high | medium | high |
| Real software delivery | medium | high | very high | high | medium |
| Human attention reduction | high | medium | medium | very high | high |
| Failure/restart truth | high | high | very high | high | high |
| Objective automatic evaluation | high | high | very high | high | medium |
| Long-term adaptation | medium | high | medium | high | very high |
| One-shot saturation resistance | high | very high | high | high | very high |

## 46. Recommended product composition

The strongest single “five-times-harder chat system” specification should not
ask candidates to build five disconnected products. Compose them in stages:

### Initial public objective

RoomOS + Shipyard floor:

- native chat goal and development state;
- real provider execution;
- artifact/Git/test evidence;
- clean accepted delivery;
- truthful recovery.

The broad objective and user journeys should make ForgeLab and Quiet Autopilot
valuable discoveries without naming exact mechanisms.

### Confirmation campaigns

- architecture ambiguity where independent candidates can help;
- provider disagreement and verifier-found defects;
- human nonresponse and long-running work;
- dirty Git, integration conflict, and restart;
- scheduled maintenance with low or negative yield.

### Later evolution campaign

Add Project Brain only after enough automatic evidence exists. Require a later
matched campaign to demonstrate benefit; do not award points for a memory UI or
learning claim alone.

## 47. Promotion order

1. **Shipyard** — fix the current concrete gap: provider work must become an
   accepted commit with independent evidence.
2. **RoomOS** — make the chat surface reflect that real delivery state.
3. **ForgeLab** — add adaptive multi-agent methods on a trustworthy base.
4. **Quiet Autopilot** — reduce human interruption over long campaigns.
5. **Project Brain** — learn only after evidence and repeated campaigns exist.

This implementation order differs from the value ranking because later
directions depend on earlier truth.

## 48. Reject conditions

### RoomOS

Reject or shrink if typed objects require more manual interaction than plain
chat, or if projections do not improve task comprehension.

### ForgeLab

Reject mechanisms whose candidates, debates, or reviews do not change accepted
artifacts or heldout outcomes enough to repay coordination cost.

### Shipyard

Reject abstractions that add integration latency without preventing lost work,
false success, escaped defects, or recovery failure.

### Quiet Autopilot

Reject policies that reduce questions only by taking unsafe action, hiding risk,
or generating low-yield background work.

### Project Brain

Reject learned guidance until a matched later campaign shows improvement. Expire
guidance that produces negative transfer or cannot be traced to evidence.

## 49. Final recommendation

For the next full task specification, use **RoomOS + Shipyard as the required
completion floor**, **ForgeLab as the main quality ceiling**, **Quiet Autopilot
as the human-attention axis**, and **Project Brain as a later change campaign**.

This preserves one coherent chat development product while making quality depend
on agent relationships, real delivery, low-interruption autonomy, failure
recovery, and evidence-backed adaptation rather than the number of visible
features.
