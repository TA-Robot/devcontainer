# Objective-driven product discovery

## 1. Benchmark thesis

The benchmark should not ask an agent to fill in a nearly complete product
specification. It should ask the agent to turn a broad product objective into a
better specification and then into a working product.

The primary capability under evaluation is:

```text
broad objective and sparse requirements
 -> discover user workflows, bottlenecks, risks, and latent needs
 -> propose and prioritize product hypotheses
 -> implement a coherent vertical slice
 -> dogfood and measure it
 -> revise the specification and architecture from evidence
 -> deliver the strongest product reachable within the budget
```

This is closer to real product development than endpoint completion. It gives
additional thought somewhere useful to go.

## 2. Proposed public task brief

The visible brief should be approximately this sparse:

> Build ForgeRoom: the best local, Git-native environment you can create for a
> human and multiple AI coding agents to develop software together. Its primary
> objective is to maximize the rate at which high-quality, maintainable, safe
> project outcomes are delivered while minimizing routine human interruption.
> The human should have a native chat-like place to state goals, understand what
> is happening, and intervene when intervention is genuinely valuable. Codex
> and Grok are available through the supplied adapters. Determine what product
> behavior, workflow, architecture, and safeguards are needed; implement and
> validate the most valuable system you can within the time budget.

Minimum constraints, not a complete feature list:

- it must be a usable local application, not a design-only submission;
- it must operate on a supplied Git workspace without escaping its authority;
- provider execution must use the supplied adapters and report real state;
- conversation and development campaigns must survive restart;
- destructive or externally visible actions require explicit authority;
- the evaluator must be able to submit a campaign and observe artifacts,
  status, and terminal outcome through a stable local interface;
- the candidate must leave evidence of the requirements it discovered, the
  product decisions it made, and the experiments that changed those decisions.

The brief intentionally does not require task DAGs, worktrees, debate, review,
candidate competition, schedules, or a particular framework. Those are product
hypotheses. A strong developer should add only the mechanisms that improve the
objective.

## 3. What the agent must discover

The exact discovery path is open, but the domain contains real latent needs.

### Human workflow

- How does a broad goal become actionable without turning the human into a
  project manager?
- What information deserves attention, and what should remain ambient?
- When should the system proceed with reversible assumptions versus block?
- How can progress, uncertainty, and risk be understood without reading raw
  agent logs?

### Development planning

- Which work is genuinely parallel-ready?
- When is consultation more valuable than implementation?
- How are milestones, dependencies, acceptance, and stop conditions represented?
- How does the system detect that local tuning has plateaued and architecture
  should be revisited?

### Agent collaboration

- How should independent opinions remain independent long enough to decorrelate
  errors?
- When should agents exchange evidence rather than repeat full answers?
- How are maker, verifier, competing candidate, and integrator responsibilities
  separated without a rigid global workflow?
- How are useful findings connected to adopted decisions and code?

### Repository execution

- How are concurrent changes isolated?
- Who owns integration and conflict resolution?
- How are stale artifacts, dirty initial state, generated files, and unexpected
  modifications distinguished?
- How does a task resume after the server or provider dies?

### Quality and learning

- How is “done” grounded in tests, requirements, and downstream behavior?
- How does the system choose between competing approaches?
- Which observations should change future orchestration decisions?
- What evidence can be retained automatically without storing private reasoning
  or flooding future context?

### Provider and resource reality

- What happens when one provider is absent, unauthenticated, slow, or wrong?
- Which model/effort/tool should be used for which task?
- How are concurrency, rate limits, CPU, memory, and integration capacity
  balanced?
- How is unbounded agent or scheduled activity prevented?

The benchmark never says that every subsection needs a feature. It exposes
workflows where neglecting important needs has measurable consequences.

## 4. Requirements discovery as an artifact

The product repository should contain a compact, evolving requirement and
hypothesis ledger. A suggested schema is:

```yaml
requirement_id: R-...
derived_from:
  objective: faster accepted development with low human interruption
user_or_system_need: ...
hypothesis: ...
priority_basis: expected outcome / risk / uncertainty / implementation cost
planned_evidence: ...
status: proposed | implemented | rejected | revised
product_location: ...
observed_result: ...
residual_unknown: ...
```

This is not scored by length. It provides a public chain from purpose to product
decision and allows later analysis of whether additional deliberation produced
better specifications or only more prose.

## 5. The specification is versioned during development

The initial visible brief is version zero. The candidate should be allowed and
expected to create its own product specification, then revise it when dogfood
or evaluation evidence contradicts an assumption.

Useful events include:

- `R-new`: a previously missing need is discovered;
- `R-split`: one vague requirement is separated into distinct obligations;
- `R-reprioritize`: evidence changes expected value or urgency;
- `R-reject`: a plausible feature is shown not to help;
- `R-reopen`: a verifier or campaign failure invalidates completion;
- `R-defer`: valuable but outside the current critical path.

The benchmark should observe these transitions without rewarding churn.

## 6. Product discovery must compete for time with implementation

Unlimited planning is not the goal. Every discovery activity has an opportunity
cost. A useful run chooses when an additional architecture proposal, user-flow
analysis, or adversarial review is likely to change a high-cost decision.

Evaluation should therefore report:

- time to first end-to-end campaign;
- time to coherent product architecture;
- number of implemented requirements with downstream evidence;
- number of discovered requirements that changed accepted outcomes;
- rejected/deferred features and saved implementation cost;
- architecture rewrites caused by late discovery;
- quality gain after each major requirement revision.

A run that writes an excellent product strategy but never ships fails the
completion floor. A run that ships a thin forwarder immediately may cross the
floor but score poorly on unseen workflows.

## 7. How to evaluate missing specifications without gotchas

The evaluator must not hide arbitrary feature requirements and punish the
candidate for failing to guess them. Instead, it declares evaluation domains
publicly while withholding concrete scenarios.

Public domains:

- ambiguous greenfield goal;
- context-heavy feature change;
- parallelizable multi-module change;
- high-loss defect requiring independent assurance;
- competing implementation/performance choice;
- provider and process failure;
- interrupted campaign recovery;
- changing requirement or provider contract;
- human-interruption pressure;
- Git conflict and stale artifact handling.

The concrete repositories, goals, faults, and timings are hidden. Any product
mechanism that handles the domain is acceptable. This makes product discovery
real while keeping comparison fair.

## 8. Rewarding useful invention

A candidate may invent a valuable mechanism the benchmark designer did not
anticipate. It should receive credit when the mechanism changes one or more
observable outcomes:

- more hidden criteria satisfied;
- shorter accepted completion time;
- fewer regressions or destructive changes;
- recovery from a fault that defeated the baseline;
- lower human prompt/approval demand;
- better performance under the same provider budget;
- easier successful adaptation to the change request.

No separate “creativity points” are required. Outcome-based open credit is more
robust than a feature bonus.

## 9. Product decisions that should remain open

- whether chat is the primary execution primitive or only the control surface;
- task representation and planning algorithm;
- agent role taxonomy;
- static versus adaptive orchestration;
- use of worktrees, patches, or single-writer queues;
- review and dialogue protocols;
- persistence technology;
- provider fallback and retry policy;
- scheduling and recurring work;
- UI density and notification design;
- method-learning and memory representation.

Prescribing these would turn the exercise back into specification fulfillment.

## 10. Bad forms of “self-directed improvement”

- adding many visible buttons without validating a workflow;
- creating permanent agent roles because they sound organizationally complete;
- generating requirements after implementation to justify existing code;
- optimizing the public campaign examples while ignoring heldout domains;
- treating every agent suggestion as a feature request;
- measuring improvement by files, lines, agents, or tokens;
- continuing dialogue after it stops producing new evidence;
- hiding failure behind optimistic status or verbose summaries.

## 11. Desired final evidence

A high-quality submission should let an evaluator reconstruct:

```text
broad objective
 -> discovered high-value need
 -> product hypothesis
 -> discriminating dogfood/test
 -> implementation or rejection
 -> downstream campaign effect
 -> remaining uncertainty
```

That chain is the benchmark's evidence that the agent did more than complete a
given specification: it helped create the right specification and then built
it.
