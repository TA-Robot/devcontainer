# Campaign suite and latent needs

## 1. Purpose

ForgeRoom is evaluated by the development campaigns it completes, not by an
internal feature checklist. The campaign suite creates situations in which
better product discovery, architecture, implementation, and collaboration can
improve outcomes.

The first calibrated revision should contain a small number of deep campaign
families rather than dozens of shallow unit tasks.

## 2. Campaign contract

Every campaign provides:

- an immutable Git base;
- a broad project goal and authority boundary;
- public acceptance commands or observable milestones;
- a provider/model/effort and total execution budget;
- a maximum wall time;
- no routine human replies;
- a hidden evaluator and fault schedule;
- artifact and event capture outside the candidate's authority.

The candidate may plan, consult, implement, test, review, and revise within the
budget. It may not read hidden evaluator files or reuse state from another
candidate.

## 3. Family A — Ambiguous greenfield service

Visible goal example:

> Build a local service that ingests a stream of project events and presents a
> useful operational view for a small development team. It must be reliable and
> easy to extend. Determine the detailed behavior needed.

The repository contains skeletal domain types and a few realistic event traces,
not a complete product specification.

Latent needs exercised:

- identify user workflows and information hierarchy;
- derive a coherent data model and API;
- choose useful behavior rather than maximize feature count;
- build an end-to-end product with tests;
- handle malformed, duplicate, and reordered events;
- provide usable empty/error/recovery states;
- preserve extensibility for a later change request.

Evaluation:

- hard functional and safety gates;
- task-based UI/API scenarios rather than pixel taste alone;
- hidden event properties and restart cases;
- version-two feature change applied after the first accepted result;
- change amplification and regression count.

Why one-shot forwarding is insufficient: the goal does not enumerate the
product, so repository reading, requirements discovery, architecture, and
feedback matter.

## 4. Family B — Context-heavy cross-module feature

The fixture is a medium repository with several plausible modification points,
domain invariants, generated boundaries, and incomplete documentation. The goal
requires coordinated changes across API, core logic, persistence, and tests.

Latent needs exercised:

- evidence-partitioned reconnaissance;
- context capsule construction;
- dependency-aware implementation planning;
- avoidance of duplicate/conflicting edits;
- single-writer integration and aggregate validation;
- detection of stale findings after code changes.

Evaluation:

- percentage of hidden behavior criteria;
- unexpected-change and generated-file audit;
- integration defects and rework;
- time to first acceptable partial milestone and final result;
- change made to the correct architectural seam;
- follow-up change requiring the same abstraction to extend cleanly.

## 5. Family C — High-loss repair and assurance

The repository contains an intermittent concurrency, lifecycle, security, or
data-integrity defect. Visible tests are incomplete. Several plausible root
causes exist.

Latent needs exercised:

- independent hypotheses rather than anchored consensus;
- reproduction and evidence gathering before patching;
- maker-verifier separation;
- adversarial tests and fixed-artifact review;
- distinguishing infrastructure failure from task failure;
- preserving unrelated behavior.

Evaluation:

- hidden mutant/fault schedule coverage;
- reproduction quality;
- actual defect closure rather than log manipulation;
- verifier-only finding and repair closure;
- false-positive or unnecessary-change rate;
- heldout stress and platform variation.

## 6. Family D — Competing performance architecture

The project must satisfy correctness and improve a measurable service objective,
such as scheduling quality, query planning, incremental build invalidation, or
cache admission. Each evaluation is fast, but there are meaningfully different
algorithm and architecture families.

Latent needs exercised:

- explicit problem map and objective hierarchy;
- competing hypotheses and cheap discriminating probes;
- common evaluator and isolated candidates;
- exploration versus exploitation allocation;
- confirmation and heldout discipline;
- implementation quality after empirical selection.

Evaluation:

- correctness gates;
- performance distribution across hidden workloads;
- runtime/resource budget;
- robustness and worst-case behavior;
- architecture family diversity and winner stability;
- whether a hybrid was revalidated as a new candidate.

This family supplies the continuous quality frontier that ordinary app tasks
lack, without turning the entire benchmark into domain R&D.

## 7. Family E — Failure, interruption, and recovery

This family wraps one of A–D and injects operational faults:

- provider executable unavailable at start;
- provider returns malformed or partial output;
- one of two parallel tasks is cancelled;
- process is terminated mid-edit;
- result arrives after its base commit is stale;
- server restarts with queued/running work;
- Git workspace begins dirty with user-owned changes;
- CPU or concurrency capacity is temporarily reduced.

Latent needs exercised:

- provider preflight and fallback routing;
- durable campaign state;
- process identity and scoped cancellation;
- checkpoint/recovery semantics;
- stale artifact rejection or rebaseable knowledge salvage;
- truthful multi-axis status;
- zero-human-input continuation.

Evaluation separates execution status, contract validity, artifact freshness,
task outcome, and integration. A useful result from a failed process is not
automatically zero; a clean process with a wrong artifact is not success.

## 8. Family F — Requirement evolution

After an accepted initial artifact, the harness reveals one pre-registered class
of change:

- add a new provider with a different streaming protocol;
- introduce project-level role/permission boundaries;
- support two repositories in one campaign;
- change event ordering or persistence requirements;
- require offline replay and audit export;
- enforce a lower human-interruption budget.

Latent needs exercised:

- whether the candidate discovered extensibility as a real need;
- architecture boundaries and testability;
- ability to revisit a prior product decision;
- requirement versioning;
- regression containment.

Evaluation:

- time to adapt;
- files/components touched;
- regressions;
- migration and compatibility;
- whether the original architecture enabled or impeded the change;
- whether the system can use its own evidence to plan the adaptation.

## 9. Human-interruption pressure

Campaigns should provide no routine answers after submission. Questions and
approval requests are recorded but not serviced unless they concern an
explicitly pre-declared authority gate.

This makes the following product choices measurable:

- reversible assumptions and autonomous continuation;
- risk-based escalation;
- consolidated approval handling;
- timeout/fallback behavior;
- concise human summaries.

The score does not reward never asking. It penalizes unnecessary blocked time
and unsafe autonomous action separately.

## 10. Public, development, confirmation, and heldout populations

### Public examples

Small fixtures demonstrate the campaign protocol and fault categories. The
candidate can inspect and repeat them freely.

### Development campaigns

Larger visible cases support dogfood and product iteration. Their score is
reported immediately. They must not be used for final claims alone.

### Confirmation campaigns

Same domain, different repositories/seeds. Access is limited and results are
recorded against exact artifact digests.

### Heldout campaigns

Concrete task, fault timing, and change payload remain inaccessible until the
candidate artifact is frozen. Failures can be reported for final evaluation but
not used to mutate the same candidate in a claimed heldout result.

## 11. Campaign depth over campaign count

One campaign should permit several milestones:

```text
valid repository understanding
 -> first partial feature
 -> complete visible behavior
 -> hidden robustness
 -> independent assurance
 -> requirement evolution
```

This exposes how the product uses time and feedback. Ten trivial repairs would
mostly measure provider throughput.

## 12. Initial corpus recommendation

For the first calibration:

1. one greenfield ambiguous service with a version-two change;
2. one context-heavy cross-module feature;
3. one high-loss concurrency/security repair;
4. one fast performance architecture problem;
5. deterministic fault overlays reusable across the above.

Run a forwarding baseline first. If it solves most heldout criteria, deepen the
campaigns before running the expensive outer benchmark.
