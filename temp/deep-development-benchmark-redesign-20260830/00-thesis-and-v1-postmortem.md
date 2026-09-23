# High-ceiling development benchmark: thesis and v1 postmortem

## 1. Decision

DevRelay v1 is retained as a smoke-test fixture and rejected as the main
development-capability benchmark. Finishing it in 33:56 and scoring 100/100 is
not evidence that the environment is near an optimum. It is evidence that the
task and oracle saturated before the allotted development time did.

The replacement benchmark must measure a curve:

```text
additional development time
  -> additional investigation / competing hypotheses / implementation
  -> materially stronger artifact
  -> stronger performance on unseen software-development campaigns
```

The benchmark is useful only if this chain remains observable beyond the first
working vertical slice.

## 2. What v1 actually measured

The v1 evaluator established that the generated product could:

- serve a native local UI and JSON API;
- persist channels, messages, threads, and runs;
- launch two provider adapters concurrently;
- isolate cancellation;
- survive malformed output and provider failure;
- restore state after restart.

These are valuable infrastructure gates. They do not measure whether the
product improves software development. A forwarding chat with robust process
management can pass them without making better task decompositions, choosing
better agent interactions, resolving code conflicts, finding better designs,
or delivering more accepted project milestones.

The 100 points therefore represented protocol coverage, not product quality.

## 3. Why the ceiling appeared early

### Closed world

The visible specification enumerated nearly all required behaviors. Once each
endpoint and lifecycle transition existed, little uncertainty remained about
what to build next.

### Binary criteria

Most checks returned all-or-nothing points. A merely adequate implementation
and an exceptionally usable, extensible, and effective implementation looked
the same.

### No externalized utility

The app was not judged by the quality of development it enabled. The small
CausalBuffer canary proved invocation and feedback repair, but one six-minute
task could not discriminate sophisticated orchestration from prompt
forwarding.

### Weak search pressure

There was no meaningful architecture tournament. Several designs could satisfy
the same contract, yet the evaluator provided no outcome on which one could
dominate another.

### Assurance dominated refinement

Independent reviewers added real value by finding lifecycle and security
defects. After these were repaired, however, there was no remaining scored
frontier. The rational action was to stop rather than explore stronger product
behavior.

### Score semantics hid headroom

Calling conformance `100/100` implied completion even though live Grok was not
validated, browser interaction was not measured, and no development-speed
effect was established.

## 4. What the replacement must measure

The object under test is the current devcontainer's outer orchestration
capability. It will be asked to develop a Git-native AI software studio. That
studio is then frozen and used as the instrument for several unseen software
development campaigns.

There are therefore two distinct layers:

```text
L0: current devcontainer orchestrator
    develops, tests, critiques, and refines the studio

L1: produced studio
    orchestrates Codex/Grok on unseen Git projects

Evaluator
    measures the software outcomes produced by L1
    and traces which L0 interventions changed the studio
```

L0 is not rewarded for spawning agents or writing long design documents. L1 is
not rewarded for displaying agents or messages. The reward comes from accepted
software outcomes under fixed provider, time, and permission budgets.

## 5. The quality frontier

The artifact can improve along interacting dimensions:

- task framing and requirement extraction;
- repository reconnaissance and context selection;
- decomposition into real dependency DAGs;
- provider/model/effort routing;
- read-only consultation, evidence dialogue, and maker-verifier workflows;
- isolated implementation and single-writer integration;
- candidate competition and empirical selection;
- failure detection, retry, cancellation, and recovery;
- prompt/context freshness and stale-result rejection;
- test/evaluator use without overfitting;
- conflict resolution and regression containment;
- human-visible progress, decision evidence, and low-interruption operation;
- extensibility when a new provider or project type arrives.

A thin forwarding implementation may satisfy the launch gate. More development
time can still improve the above dimensions, and those improvements can change
downstream task outcomes.

## 6. Time is an experimental variable, not only a deadline

One run at one hour cannot reveal whether deeper development helped. The
research program should compare matched runs from the same immutable base at
multiple stopping budgets, initially:

- 30 minutes: working vertical slice pressure;
- 60 minutes: original target budget;
- 120 minutes: architecture, search, and assurance headroom;
- optionally 240 minutes after evaluator calibration.

Every run receives the same visible specification, provider/model/effort
stratum, environment, and hidden evaluation population. The output is a quality
curve `Q(t)`, not a single pass mark.

The decisive questions are:

- Does `Q(60) > Q(30)` for reasons traceable to artifact changes?
- Does `Q(120) > Q(60)`, or does the method plateau?
- Which stages consume added time: architecture, implementation, search,
  assurance, or operational waiting?
- Did multi-agent activity change critical decisions or merely increase work?
- Is marginal quality gain larger than added integration and review cost?

## 7. Completion is a floor

The studio must launch and accept a campaign before quality scoring begins.
Failure to cross that floor is important. Crossing it does not imply a high
score.

```text
Gate A: process/API validity
Gate B: safe Git and provider execution
Gate C: one end-to-end development campaign
Quality frontier: outcome portfolio, robustness, adaptation, efficiency
```

Higher-layer performance cannot compensate for destructive Git behavior,
workspace escape, fabricated success, or unrecoverable state corruption.

## 8. Non-goals

- selecting a universal number of agents;
- rewarding dialogue length, agent count, or token consumption;
- making UI polish the dominant quality axis;
- letting the candidate inspect hidden repositories or evaluator internals;
- using subjective “sophistication” as a substitute for downstream outcomes;
- proving causal multi-agent speedup from one natural episode;
- forcing all runs to consume the full budget after marginal value has ended.

## 9. Calibration criterion

The new benchmark is not accepted until known variants occupy meaningfully
different regions:

- a prompt-forwarding baseline should launch but perform modestly;
- a sequential/no-isolation mutant should lose throughput or correctness;
- a test-only optimizer should overfit development tasks and lose heldout;
- a robust but slow implementation should trade throughput for reliability;
- a reference orchestration implementation should be strong but not saturate;
- an additional hour of competent development must have plausible scored work
  remaining.

If a fresh strong agent again reaches the evaluator ceiling well before the
budget, the evaluator—not the agent—is considered to have failed calibration.
