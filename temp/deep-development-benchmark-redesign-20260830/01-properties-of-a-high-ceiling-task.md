# Properties of a high-ceiling development task

## 1. Required shape

A suitable benchmark task has both a hard completion floor and a broad quality
frontier. It must be possible to build a coherent minimum product, yet difficult
to exhaust the meaningful improvements available within the longest tested
budget.

The task should reward thinking only when thinking changes experiments,
architecture, code, or assurance. It should also reward implementation volume
only when the resulting pieces form a coherent, tested system.

## 2. Eleven necessary properties

### 2.1 External utility

The artifact should produce something independently measurable. For an AI
development studio, that output is accepted code on unseen projects. Internal
feature counts are secondary.

### 2.2 Multiple interacting bottlenecks

Quality should depend on several layers at once: provider invocation, context,
planning, Git isolation, integration, verification, and recovery. Solving one
layer must not complete the task.

### 2.3 Architecture matters

A quick monolith should work but encounter identifiable limits. Better module
boundaries and state models should make later changes, concurrency, and failure
recovery materially easier.

### 2.4 Cheap development feedback

Most local checks should finish in seconds. If every product experiment takes
twenty minutes of provider time, the outer agent cannot perform enough design
and implementation iterations within the budget.

The harness therefore needs deterministic fake providers and campaign replays
for infrastructure development, while reserving real providers for semantic
quality evaluation.

### 2.5 Expensive final truth

The cheap probes must not be the entire oracle. Hidden real-provider campaigns,
fault injection, and change requests should expose overfitting to mocks.

### 2.6 Meaningful competing approaches

There should be several plausible architectures:

- direct chat-forwarding with manual coordination;
- central planner with task DAG and provider workers;
- event-sourced workflow engine;
- project-state machine with specialized consultation/review phases;
- candidate portfolio with isolated branches and empirical selection.

The evaluator must be capable of distinguishing them by outcome.

### 2.7 Refinement after correctness

Once the app works, useful work must remain: better context packets, lower
latency, safer merging, stronger review, more effective task routing, clearer
failure diagnosis, and adaptation to new campaign classes.

### 2.8 Robust hidden variation

The exact repositories, task wording, fault timing, provider failure, and
change request should be withheld. Public fixtures teach the protocol and
failure categories, not the heldout answers.

### 2.9 Traceable causal mechanisms

The outer orchestrator's consultation or competition should be linkable to a
decision, code change, and downstream outcome. Private reasoning is not needed;
event, artifact, commit, test, and finding links are.

### 2.10 Low mandatory human input

The run should continue without a person labeling quality or resolving routine
prompts. Human-visible controls may exist in the product, but benchmark success
cannot depend on a human noticing hidden approval dialogs.

### 2.11 No single magic metric

The result must retain functional quality, robustness, throughput, resource
cost, and human interruption separately. A scalar utility can be published for
ranking only after hard gates and criterion-level evidence are preserved.

## 3. Tensions that must be designed, not wished away

### Openness versus reproducibility

An entirely open product brief creates rich design space but makes matched
comparison difficult. A detailed feature checklist is reproducible but creates
a low ceiling.

Resolution: specify a small stable campaign protocol and safety contract, then
score downstream outcomes rather than prescribing internal features.

### Real providers versus cheap iteration

Real providers give ecological validity but introduce latency, version drift,
authentication, and stochastic output.

Resolution: use three evaluator populations and never pool them blindly:

1. deterministic protocol/fault fixtures;
2. recorded or scripted campaign replays;
3. matched live-provider campaigns.

### Surprise changes versus fairness

An unexpected requirement measures adaptability, but a vague surprise can
become arbitrary.

Resolution: pre-register the class of change and scoring dimensions while
withholding the concrete payload. Examples include adding a provider adapter,
changing a task contract version, and recovering an interrupted campaign.

### Quality versus complexity theater

A sophisticated architecture can impress a reviewer while worsening outcomes.

Resolution: require ablation or downstream evidence for claimed mechanisms.
Do not score module count, design-document length, or named algorithms.

### Multi-agent opportunity versus forced multi-agent use

The task must contain separable investigation, competing hypotheses, and
verification opportunities, but the outer agent should be allowed to decide
that some stages are better handled alone.

Resolution: score artifact outcomes and trace method choice; do not award
points for using every available agent.

## 4. Why ordinary app themes are weak

CRUD systems, dashboards, chat clones, and static workflow tools often have a
large feature surface but a shallow quality frontier. Additional time adds more
screens or endpoints, not deeper problem solving. Hidden tests can make them
larger, but size is not the desired difficulty.

A good task is difficult because its layers interact and because better
decisions change outcomes, not because its requirements list is long.

## 5. Why pure optimization tasks are also insufficient

Robot soccer and numerical optimization have continuous performance and cheap
evaluation, but they can over-measure domain R&D and parameter search. The user
wants general software-development capability: framing, architecture, coding,
integration, review, and delivery.

The replacement should borrow optimization's non-saturating outcome curve while
remaining a real software product.

## 6. Desired development dynamics

An excellent run should look roughly like:

```text
map requirements and campaign objective
 -> build thin end-to-end studio
 -> use public campaigns and fault fixtures
 -> identify bottleneck/failure taxonomy
 -> compare architecture or policy interventions
 -> implement the most discriminating improvement
 -> re-evaluate across campaign families
 -> freeze and run independent assurance
 -> adapt to a versioned surprise change
```

A weak run may still produce a working forwarder, but it will plateau on unseen
campaigns. A strong run will use remaining time to increase repeatable
downstream utility rather than accumulate decorative features.

## 7. Evidence that a task has enough headroom

Before adoption, perform a calibration pilot and require:

- no reference or strong pilot reaches all frontier criteria;
- at least three architecture/policy variants produce distinguishable outcomes;
- public development score and heldout score are correlated but not identical;
- known failure mutants are separated;
- the 60-minute artifact improves materially over the 30-minute artifact;
- plausible work remains at 120 minutes;
- evaluator runtime is low enough to support repeated product experiments;
- failure reports identify where additional thought or implementation could
  improve the artifact.

## 8. Rejection conditions

Reject or revise a candidate task when:

- a forwarding baseline scores near the reference;
- one framework choice solves most criteria automatically;
- evaluator results are mostly subjective;
- provider luck dominates architecture effects;
- the public suite reveals hidden answers;
- more time increases code volume but not downstream outcomes;
- task completion requires routine human intervention;
- a single agent can finish every independent workstream before parallelism
  could affect the critical path;
- the longest-budget pilot has no credible next improvement.
