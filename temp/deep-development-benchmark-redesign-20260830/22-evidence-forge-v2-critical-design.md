# Evidence Forge v2 — critical review and tightened design

## 1. Outcome of the additional review

Evidence Forge remains the selected direction, but the v1 proposal was still too
broad and too easy to misbuild as orchestration feature theatre. V2 narrows the
required product kernel, makes the inner episodes concrete and generative,
separates provider compute from orchestration quality, and defines an evaluator-
first calibration that can falsify the five-times-hard claim cheaply.

## 2. Problems found in the v1 proposal

### 2.1 Too many visible mechanisms

Seven quality mechanisms and five episode families could become a checklist.
Candidates might implement a task graph, reviews, worktrees, candidate cards,
and provider routing without establishing one coherent path to better software.

### 2.2 Episodes were shapes, not fixtures

“Tight seam” and “design fork” explained intent but not how public evidence,
variant generation, fast evaluation, and heldout parity would work. A weak
fixture could saturate exactly like H1.

### 2.3 Extra compute could masquerade as orchestration value

A multi-agent candidate may win merely because it receives more provider calls
or tokens. The benchmark needs raw outcome, provider active time, run count, and
wall time, plus matched budget envelopes. It should not claim causal multi-agent
benefit from one natural run.

### 2.4 Git integration could dominate everything

Controller-owned delivery is necessary, but if every failure comes from Git and
process plumbing, the task measures a robust wrapper rather than better agent
relationships.

### 2.5 Outer and inner clocks were underspecified

Outer B30/B60/B120/B180 measures development of ForgeRoom. Inner episode time
measures the frozen ForgeRoom developing another project. Mixing them makes the
quality curve and cost comparison uninterpretable.

### 2.6 Human UX could remain untested decoration

A native room may exist only to satisfy a launch gate while all useful work
happens through JSON. UX needs bounded task-based evaluation without becoming
the dominant subjective score.

### 2.7 The V2 human-silence change was too synthetic

“One answer allowed” is useful experimentally but arbitrary as a product change
unless connected to an actual blocked development decision and safe fallback.

### 2.8 Evidence schemas could prescribe architecture

Overly detailed task, candidate, or debate objects would reward implementing the
evaluator's ontology. The stable contract should expose outcomes and provenance,
not internal orchestration classes.

## 3. V2 product kernel: only three responsibilities

V2 requires three coherent responsibilities. Every other mechanism must justify
itself through these.

### K1 — Campaign room and truthful current state

Accept a broad goal in native chat, expose compact meaningful progress/risk, and
persist enough conversation and evidence for a human or evaluator to understand
the current campaign after restart.

### K2 — Evidence-producing development execution

Use supplied providers to investigate, implement, test, compare, or verify as
appropriate. Retain source-linked evidence that explains decisive changes to the
selected approach or artifact.

### K3 — Controller-owned acceptance and delivery

Preserve user work, accept or reject candidate changes, reproduce required
checks, integrate under controller authority, and finish with a clean commit or
truthful non-accepted partial result.

Task graphs, roles, worktrees, debates, candidate tournaments, and routing
systems are optional internal strategies. They receive no direct feature credit.

## 4. Tightened public objective

> Build ForgeRoom: a local, Git-native development room where a human can state
> a broad software goal and receive the strongest tested, reviewable outcome that
> available AI coding agents can produce within the supplied time and authority.
>
> The room should decide how to investigate, implement, compare alternatives,
> and verify risky work. Show meaningful progress, decisive evidence, and
> residual risk without making the human coordinate routine agent work. Preserve
> user-owned changes, distinguish provider claims from accepted software, and
> remain truthful through provider, process, server, and integration failure.
>
> Codex, Claude, and Grok are available through supplied adapters. Determine the
> product requirements and collaboration methods that best improve real software
> delivery. Dogfood the room when useful and revise assumptions when evidence
> contradicts them.

The public constraints retain the existing campaign/authority/event/terminal
protocols. They do not publish inner episode categories or require orchestration
method names.

## 5. Minimal evaluator-visible evidence

The stable evaluator surface requires only:

- campaign identity, objective, authority, budget, and workspace base digest;
- timestamped human/system/provider activity events;
- provider attempts with exact adapter identity and terminal state;
- artifact references with digest, base digest, producer, and disposition;
- reproduced command/test/benchmark evidence with exit state;
- final workspace digest, cleanliness, accepted/partial state, and residual
  unknowns;
- human interruptions and external/destructive actions.

The candidate may expose richer tasks, decisions, claims, or candidates, but the
evaluator does not demand their field names. Method attribution is reconstructed
from event/artifact relations and source trace where possible; unknown remains a
valid result.

## 6. Three initial episode generators

The proof slice uses three generators rather than three one-off repositories.
Each generator emits public, confirmation, and heldout variants with renamed
symbols, reordered files, changed constants, and different combinations of the
same declared semantics.

### G1 — Coupled Contract Migration

#### Supplied project

A small typed service has a core protocol, two internal consumers, one generated
artifact, migration compatibility tests, and a dirty user-owned note/change. The
goal is an outcome-level protocol evolution rather than a named class change.

#### Why the task shape matters

Most implementation touches share one semantic contract. Indiscriminate parallel
writers create stale assumptions, duplicate migrations, or generated-file
conflicts. Read-only reconnaissance, contract review, and late verification can
still run independently.

#### Variant generation

- rename protocol/domain symbols;
- permute consumer locations and generated artifact type;
- vary which user-owned file is dirty;
- vary compatibility direction and one edge-case invariant;
- preserve the same observable migration outcome.

#### Evaluation

- old/new compatibility behavior;
- preservation of initial user work;
- generated artifact consistency;
- regression and clean commit;
- duplicate work and integration tail;
- whether parallel writers were avoided or safely isolated.

### G2 — Adaptive Build Planner

#### Supplied project

A complete local developer tool schedules a dependency graph of build/test jobs
on heterogeneous workers using a fast deterministic simulator. The existing
baseline is correct but mediocre. The candidate must deliver a usable planning
component and improve time-to-failure, total completion, and compute without
missing blocking failures.

#### Why the task shape matters

Critical-path, failure-first, cache-aware, and resource-aware strategies are all
plausible. Public regimes have no universal winner. Prototype competition and
measurement can change the selected implementation; prose cannot.

#### Variant generation

- graph/name permutation;
- changed worker/resource mix;
- changed runtime/failure correlations;
- cache transfer and cold-start variation;
- public, confirmation, and heldout regime mixtures.

#### Evaluation

- dependency/resource correctness hard gates;
- blocking-failure recall;
- p50/p95 time to first blocker and completion;
- worker-seconds and wasted work;
- planner overhead;
- robustness to regime shift;
- evidence that the chosen approach was actually measured.

The simulator suite must finish in seconds. This is the main candidate-search
episode and the main defense against another one-architecture ceiling.

### G3 — Concurrent Invariant Repair

#### Supplied project

A compact concurrency/state component is mostly implemented and has strong
public tests. One high-loss invariant family is absent from maker-visible tests,
and several tempting but incorrect repairs pass the public suite. The goal is to
complete and harden the component, not guess a hidden convention.

#### Why the task shape matters

A fresh verifier using an obligation/threat model should create a reproducer the
maker did not. Generic lint or repeating the maker tests should not suffice.

#### Variant generation

- rename entities and reorder operations;
- select one defect family from an audited mutant bank;
- vary scheduling seed and surface symptom;
- retain the same public invariant statement;
- ensure every hidden expectation passes an ambiguity audit.

#### Evaluation

- public functionality and hidden invariant groups;
- reproducible verifier-only finding;
- false/duplicate review findings;
- exact regression test and repair closure;
- thread/process safety under repeated schedules;
- clean integrated commit and evidence.

## 7. Why these three episodes are jointly sufficient for proof

| Episode | Collaboration that should help | Collaboration that should hurt |
|---|---|---|
| G1 migration | reconnaissance, contract review, verification | multiple overlapping writers |
| G2 planner | independent algorithms and empirical selection | redundant minor variants |
| G3 repair | fresh obligation-driven verifier | review theatre and maker repetition |

They create different causal profiles. A fixed serial system should be safe but
miss G2 quality. Indiscriminate parallelism should lose on G1 integration. A
maker-only system should lose specifically on G3 assurance.

## 8. Separate outer and inner clocks

### Outer clock

The current devcontainer orchestration develops ForgeRoom from one immutable
base at B30, B60, B120, and B180. Each stop produces a frozen candidate digest.

### Inner clock

Each frozen digest receives the same episode variants and fixed envelopes:

- maximum episode wall time;
- provider-run and concurrency caps;
- provider/model/effort stratum;
- workspace and authority;
- human-message policy;
- evaluator feedback visibility.

Initial live calibration can use approximately 12–15 minutes per episode, but
the final limit is set from a noise pilot rather than intuition.

Reports present raw episode outcome, wall time, provider active time, run count,
and human interruptions. A normalized reference-gap view may aid comparison but
never replaces raw results.

## 9. Separating compute from method value

No claim of causal multi-agent improvement comes from one run. Use:

1. direct forwarding candidate under the same episode envelope;
2. robust serial reference;
3. indiscriminate parallel mutant;
4. adaptive reference;
5. the frozen candidate with all providers available;
6. where feasible, the same frozen candidate under a single-provider capability
   envelope rather than a hidden internal feature toggle.

Interpretation distinguishes:

- quality from extra provider compute;
- wall-time benefit from safe overlap;
- unique evidence from redundant output;
- method selection from provider identity;
- integration/review cost from generation speed.

This is comparative evidence, not a universal causal theorem.

## 10. Quality reporting without a misleading 100 points

Keep raw vectors by episode and population:

- `outcome`: accepted obligations and hidden invariant groups;
- `quality`: performance/search result where applicable;
- `delivery`: clean integrated artifact and preserved user work;
- `assurance`: reproduced unique defects and false-finding cost;
- `throughput`: first-valid, best-integrated, wall/provider time;
- `recovery`: provider/process/server fault truth;
- `attention`: interruptions and operator comprehension;
- `adaptability`: V2 time, regression, and change amplification.

Hard safety failures remain explicit. A scalar may be generated for tournament
convenience only after calibration, and must not be described as completeness.

## 11. V2 change refined

Replace the abstract “one answer allowed” change with a realistic outcome:

> A developer now leaves ForgeRoom unattended for most of a long campaign and
> expects safe reversible work to continue. Related questions must be
> consolidated. When one genuinely blocking high-loss decision arises, the room
> should present consequence, evidence, a recommended default, response deadline,
> and safe no-response fallback. Background work must be finite, deduplicated,
> budgeted, and justified by accepted downstream yield.

The evaluator may simulate long silence and one response, but the public change
is phrased as a team outcome. Old P0–P3 delivery/safety criteria rerun unchanged.

## 12. Product architecture pressure without architecture prescription

The episode portfolio naturally pressures boundaries around:

- provider adapters;
- campaign/event persistence;
- artifact candidate versus accepted artifact;
- evidence/verification;
- workspace authority and integration;
- process supervision;
- human room projection.

Candidates may implement a monolith. Modularity receives no direct score. It is
valuable only when it reduces faults, integration cost, or V2 change effort.

## 13. Reduced mutant set for the first calibration

Do not build ten full mutants first. The proof slice needs four:

- **M0 forwarding:** persisted room and one provider pass-through;
- **M2 serial delivery:** strong safe integration, no adaptive collaboration;
- **M3 parallel fanout:** multiple overlapping writers, weak dependency logic;
- **M5 maker-only:** competent execution/integration, no fresh verification.

Expected separation:

- M0 is modest on all semantic episodes;
- M2 is safe on G1/G3 but weaker on G2 quality/time;
- M3 may look fast but loses G1 integration and stale-work criteria;
- M5 is competitive on G1/G2 but loses G3 hidden invariant closure.

Only after this separation exists should rich-forwarding, review-theatre,
volatile-state, unsafe-integration, and adaptive-reference variants be added.

## 14. Evidence-backed five-times gate v2

The label remains unproven until:

1. all four proof mutants cross P0;
2. G1–G3 produce the expected distinct failure profiles;
3. M0 stays materially below the safe/adaptive frontier on raw outcomes;
4. B30 crosses the product floor;
5. B60 improves delivery or assurance, not only UI/tests;
6. B120 improves confirmation/heldout outcomes over B60;
7. at least one useful candidate-search or verifier improvement appears after the
   first valid artifact;
8. provider active time/run count cannot fully explain the outcome ordering;
9. evaluator runtime and flakiness permit repeated calibration;
10. one strong fresh run does not clear all non-P0 criteria before 75% of B120;
11. V2 exposes meaningful architecture/change differences without a hidden noun;
12. ambiguity audit approves every hidden invariant.

## 15. Evaluator-first build sequence

### Slice 1 — contracts and fake drivers

- freeze campaign, authority, activity, artifact, test, and terminal evidence;
- use deterministic mock providers for lifecycle/fault tests;
- validate restart, cancellation, dirty Git, and controller-owned commit.

### Slice 2 — G1 and M0/M2/M3

- generate several Coupled Contract Migration variants;
- confirm serial versus parallel integration profiles;
- repair any schema-dependent evaluator assumptions.

### Slice 3 — G2 candidate search

- freeze the fast simulator and reference baselines;
- prove at least three policy families occupy different regimes;
- confirm public results do not reveal the heldout winner.

### Slice 4 — G3 maker/verifier

- construct and ambiguity-audit a mutant bank;
- confirm maker-only versus fresh-verifier separation;
- measure false findings and closure cost.

### Slice 5 — live noise pilot

- run M0, M2, and one adaptive/reference candidate repeatedly under one provider
  stratum;
- set thresholds from observed variance;
- only then run expensive outer B30/B60/B120 development.

## 16. Stop rules

- Stop if G2 becomes a pure R&D contest and no complete developer tool is
  required; strengthen delivery/product obligations.
- Stop if G1/G3 are solved by fixture-name hardcoding; improve variant grammar.
- Stop if Git/process faults dominate every semantic outcome; reduce fault
  frequency after proving the hard gates.
- Stop if the public task prescribes candidate competition or verifier internals;
  return to outcome language.
- Stop if inner live evaluation cost prevents repeated calibration; substitute
  deterministic replays for lifecycle and reserve live calls for semantic cells.
- Stop if M0 and adaptive reference remain close; revise episodes, not weights.

## 17. Final v2 formulation

Evidence Forge is not a large chat feature set. It is a three-kernel development
instrument evaluated by three complementary project generators:

```text
truthful campaign room
 + evidence-producing execution
 + controller-owned accepted delivery
 tested on
 coupled migration
 + empirical design fork
 + verifier-sensitive repair
```

This is a materially stronger and more falsifiable design than the v1 list of
orchestration capabilities. It still does not prove five-times difficulty; it
makes that claim testable before the full product is built.
