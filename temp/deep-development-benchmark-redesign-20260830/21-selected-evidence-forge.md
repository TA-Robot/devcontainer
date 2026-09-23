# Selected direction: Evidence Forge

> This is the adoption record. The critical review and tightened v2 design are
> in `22-evidence-forge-v2-critical-design.md`.

## 1. Adoption decision

**Evidence Forge is the single adopted direction for the five-times-harder chat
development system.** It becomes the benchmark profile and product thesis for
ForgeRoom; it is not a separate demo application or a product rename.

Evidence Forge combines:

- ForgeLab's adaptive multi-agent collaboration;
- Shipyard's controller-owned Git delivery and evidence;
- a minimal RoomOS chat/state substrate;
- one Quiet Room continuation as later change pressure.

Project Brain is explicitly deferred. Learning from episodes is not part of V1
because reliable delivery evidence and repeated campaigns do not yet exist.

## 2. One-sentence thesis

> A human states a broad software goal in native chat; ForgeRoom determines which
> collaboration method is worth using, creates independent executable evidence,
> selects and integrates the strongest supported result, and truthfully delivers
> a clean accepted Git artifact under real provider, process, and workspace
> failure.

## 3. Why this direction wins

Evidence Forge is the closest match to the original question: what additional
value can relationships among agents produce?

It can exercise:

- delegated parallel implementation when real seams exist;
- independent advice before anchoring;
- repeated dialogue around an unresolved technical crux;
- specialist review;
- candidate implementation competition;
- empirical selection and ablation;
- fresh maker/verifier separation;
- safe fallback to sequential work when collaboration would hurt.

Unlike a chat-only proposal, these mechanisms are judged by downstream code,
tests, experiments, integration, and heldout outcomes. Unlike a Git-only
proposal, it tests whether agent interaction improves the selected artifact.

## 4. What happens to the other two plans

### Quiet Room

Not discarded. Its most valuable property—development through long human
silence with one scarce intervention—is retained as the pre-registered V2
product change. It tests whether Evidence Forge can reduce interruption without
weakening delivery safety.

### Learning Forge

Deferred until at least several trustworthy Evidence Forge episodes exist. It
may later become a longitudinal benchmark. V1 receives no credit for memory,
routing priors, or generated skills without matched later outcome improvement.

## 5. Public objective draft

The candidate receives a broad objective rather than the internal benchmark
mechanisms:

> Build ForgeRoom: the strongest local, Git-native development room you can
> create for a human and multiple AI coding agents to develop software together.
>
> A developer should be able to state a broad project goal in native chat,
> understand meaningful progress, risk, and decisive evidence, and receive a
> tested, reviewable Git outcome with minimal routine interruption. Determine
> when sequential work, consultation, independent verification, competing
> implementations, or experiments will improve the result. Preserve user work,
> respect supplied authority, and remain truthful under provider, process,
> server, and integration failure.
>
> Codex, Claude, and Grok are available through supplied provider adapters. Build
> and dogfood the most valuable coherent product you can. Revise your own product
> requirements when development evidence exposes a missing or incorrect
> assumption.

## 6. Minimum public constraints

1. Deliver a working local application with a native chat-like control surface.
2. Accept a Git workspace and broad objective as a campaign.
3. Use only supplied provider adapters and report their exact readiness/version.
4. Preserve staged, unstaged, and untracked user-owned initial changes.
5. Constrain file, process, network, and external actions to supplied authority.
6. Persist conversation, campaign state, artifacts, and terminal outcomes.
7. Distinguish provider output, candidate artifact, accepted artifact, and final
   integrated commit.
8. Capture reproducible commands, tests, benchmarks, and exit evidence.
9. Recover truthfully after server/provider/process interruption.
10. Finish accepted work with a clean commit or an explicit non-accepted partial
    result; never equate dirty files with delivery.
11. Record discovered requirements, decisive experiments, rejected hypotheses,
    and residual unknowns compactly.
12. Support evaluator-readable events and terminal evidence without exposing
    hidden evaluator details.

## 7. Non-prescribed choices

The public task does not require:

- a fixed number of agents;
- fixed role names or a permanent team catalog;
- a fixed number of debate turns;
- a task-graph framework;
- worktrees rather than another safe isolation mechanism;
- candidate competition on every task;
- learned routing or a specific provider preference;
- an event-sourcing implementation;
- a particular module layout, database, or web framework;
- background or scheduled agents;
- Project Brain/memory features.

The candidate chooses mechanisms and must demonstrate their value.

## 8. Common completion floor

Evidence Forge crosses the floor when it can:

1. launch and restore its native room;
2. accept one broad development campaign;
3. inspect the workspace and preserve initial ownership;
4. run one real provider under authority;
5. show compact progress and artifact evidence;
6. independently verify at least one acceptance obligation;
7. integrate an accepted change through controller-owned authority;
8. rerun acceptance on the integrated tree;
9. finish with a clean commit and truthful terminal record;
10. restart without losing or fabricating any of the above.

This is expected around B30. Crossing it is not a high score.

## 9. The seven quality mechanisms

### 9.1 Adaptive collaboration selection

The system chooses sequential work, consultation, independent verification,
parallel implementation, or candidate competition based on task dependency,
uncertainty, risk, budget, and observed information gain.

### 9.2 Executable disagreement

Technical disagreement becomes a prototype, reproduction, test, measurement,
or other frozen evidence. Consensus prose alone cannot close a crux.

### 9.3 Candidate portfolio and empirical selection

Materially different candidates share a frozen base and comparison contract.
The system selects from confirmation evidence, retains useful losing artifacts,
and records selection uncertainty.

### 9.4 Independent assurance and reopening

A fresh verifier works against a frozen artifact. Reproducible high-loss findings
reopen completion. False or duplicate findings incur review cost and do not earn
assurance credit.

### 9.5 Controller-owned Git delivery

The controller owns diff review, staging, integration, commit, and final rerun.
Provider inability to write `.git` is recoverable; provider claims cannot bypass
acceptance.

### 9.6 Dirty/stale/concurrent workspace safety

Initial user changes, overlapping candidates, generated files, moving base, and
late provider success are handled without silent overwrite or stale acceptance.

### 9.7 Provider/process/server recovery

Readiness failure, malformed output, timeout, cancellation, orphan descendants,
server crash, and replay produce bounded recovery and truthful partial value.

## 10. Required inner episode portfolio

The full evaluator ultimately needs five episode families. Initial proof builds
the first three.

### E1 — Tight Seam

A coupled cross-module task where two writers would touch the same semantic
invariant. Good systems avoid or carefully sequence parallel implementation.

Purpose: distinguish adaptive planning from indiscriminate fanout.

### E2 — Design Fork

A complete software component with at least two plausible architectures and a
cheap, non-obvious workload experiment. Public examples do not reveal the
heldout winner.

Purpose: distinguish executable candidate search from early intuition and
discussion theatre.

### E3 — Escaped Defect

A credible implementation task whose maker-visible tests miss one high-loss
behavior that a fresh, obligation-driven verifier can reproduce.

Purpose: distinguish independent assurance from maker-only review and generic
linting.

### E4 — Parallel Modules

A multi-module task with genuinely independent work plus one shared integration
seam and generated artifact.

Purpose: measure critical-path improvement and integration tail.

### E5 — Continuation

A later user outcome extends the same project and invalidates one earlier
assumption without naming a required implementation.

Purpose: measure context continuity, architecture quality, and truthful revision.

## 11. Fault overlays

Faults are composed with episodes rather than scored as isolated API tricks:

- provider executable missing or unauthenticated before routing;
- provider succeeds but cannot commit;
- provider returns malformed and newline-free oversized output;
- cancellation races with late success;
- child process survives provider exit;
- server crashes before/after artifact and terminal persistence;
- base digest moves while a candidate runs;
- initial tree is dirty;
- two candidates conflict semantically;
- reported test success disagrees with independent rerun;
- pre-existing failure coexists with a new regression;
- state/event contract upgrades across restart.

## 12. Quality vector

### F — accepted software outcome

- completed public, confirmation, and heldout obligations;
- artifact behavior and regression containment;
- V2 continuation success.

### T — development throughput

- time-to-first-valid;
- time-to-best-integrated;
- accepted milestones per wall/provider time;
- critical-path overlap and integration tail.

### Q — decision and search quality

- unique candidate families and decision-changing evidence;
- experiment validity and selection regret;
- residual uncertainty and rejected-hypothesis quality.

### A — assurance

- verifier-only reproduced defects;
- false/duplicate finding burden;
- exact repair and closure;
- escaped high-loss failures.

### G — Git and artifact integrity

- preserved user changes;
- correct base/final digests;
- clean accepted commits;
- stale/dirty/unintegrated artifact rejection.

### R — recovery and authority

- process/provider/server fault outcomes;
- partial-value salvage;
- workspace/network/external-action containment;
- restart and replay truthfulness.

### H — human control

- meaningful progress/risk comprehension;
- routine interruption count;
- intervention value;
- return-to-context task success.

No scalar total may compensate for destructive Git behavior, authority escape,
fabricated success, or unrecoverable state corruption.

## 13. Required baselines and mutants

- **M0 Direct forwarding:** safe persisted chat, one Codex prompt, no owned
  orchestration/integration;
- **M1 Rich forwarding:** channels/cards/statuses but same development behavior;
- **M2 Serial reference:** conservative single writer with strong integration;
- **M3 Indiscriminate parallel:** many writers, weak dependencies/integration;
- **M4 Public optimizer:** overfits public episodes;
- **M5 Maker-only:** no independent verifier;
- **M6 Review theatre:** verbose findings without reproduction/closure;
- **M7 Unsafe integration:** accepts dirty/stale/provider-owned success;
- **M8 Volatile recovery:** loses or fabricates state after restart;
- **M9 Adaptive reference:** uses collaboration selectively and owns delivery.

The evaluator is not accepted unless these variants occupy meaningfully
different failure profiles.

## 14. Time curve

- **B30:** common floor and conservative provider-backed delivery;
- **B60:** task/artifact ownership, independent assurance, controller-owned Git;
- **B120:** method selection across E1–E3, candidate experiments, fault recovery;
- **B180:** E4–E5 portfolio, dogfood refinement, coordination-cost control, V2
  human-silence change.

The same immutable base, provider/model/effort stratum, authority, and episode
population are used for matched comparisons.

## 15. V2 change: scarce-human Evidence Forge

After V1 is frozen, reveal a declared-domain product outcome:

> Continue comparable development when the human provides no routine replies
> and can answer only one consolidated intervention. Preserve every V1 safety
> and delivery guarantee. Continue reversible work, surface the highest-value
> unresolved decision, and bound proactive/background work by measured yield.

This absorbs the valuable Quiet Room pressure without making ambient UX the V1
implementation focus.

Scored V2 evidence includes interruption value, blocked time, unsafe assumptions,
progress during absence, scheduled-job yield, V1 regression, change
amplification, and migration/restart correctness.

## 16. Explicitly deferred

- cross-campaign learned routing;
- task-duration priors as product behavior;
- automatically generated method skills;
- long-term Project Brain memory;
- permanent scheduled maintenance agents;
- multi-repository atomic delivery unless selected as a later change;
- external collaboration services;
- decorative room/game features unrelated to development outcomes.

## 17. Five-times proof gate

Evidence Forge is called five-times harder only after all of these are observed:

1. B30 crosses the floor but leaves at least three of Q/A/G/R weak.
2. B60 improves an integrated artifact, not only tests or UI.
3. B120 improves confirmation/heldout software outcomes over B60.
4. Plausible scored work remains at B120.
5. M0 and M1 remain materially below M9 on semantic episodes.
6. M2 and M3 show different throughput/integration failure profiles.
7. M5 loses specifically on E3; M6 incurs cost without fake credit.
8. M7 and M8 trip the intended hard gates.
9. Multi-agent B120 contributes unique executable evidence and repays overhead.
10. Provider variance does not determine ranking.
11. V2 distinguishes useful architecture from speculative abstraction.
12. No candidate clears every criterion before 75% of B120.

If these do not hold, revise the episodes/evaluator; do not add arbitrary
features or manipulate score weights.

## 18. Immediate implementation boundary

Do not implement the complete B180 suite first. The next milestone is an
evaluator-first proof slice:

1. freeze the common P0 contract;
2. implement M0, M2, and M3 minimal variants;
3. create E1 Tight Seam, E2 Design Fork, and E3 Escaped Defect fixtures;
4. implement criterion-level evaluators and exact terminal evidence;
5. confirm the three variants separate for the intended reasons;
6. only then write the final public fixture and run a fresh live candidate.

## 19. Final scope statement

Evidence Forge is one coherent task:

```text
native chat goal
 -> adaptive collaboration choice
 -> executable evidence and candidate work
 -> independent assurance
 -> controller-owned Git integration
 -> accepted software outcome
 -> truthful recovery and V2 adaptation
```

The task is not “build every orchestration feature.” It is “build a development
room whose richer agent relationships demonstrably deliver better software.”
