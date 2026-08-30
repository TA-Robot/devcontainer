# From 1,000 ideas to five high-ceiling campaigns

## 1. Decision

The 1,000-entry inventory was reduced to five campaign concepts:

1. **TraceForge** — trace-driven adaptive monorepo CI;
2. **BugFoundry** — fuzzing, reduction, and repair for a mini compiler;
3. **FaultLens** — causal incident diagnosis and safe remediation;
4. **MergeLab** — semantic merge and repository-wide API migration;
5. **QueryCraft** — a self-tuning query planner and index advisor.

TraceForge is the recommended next principal campaign. BugFoundry is the best
second campaign because it measures a different development loop. The remaining
three should first receive a small fixture prototype rather than all being fully
built at once.

These are not five arbitrary large applications. Each combines a clear software
completion floor with an empirical quality surface that should continue to move
after the first valid implementation.

## 2. What the H1 result changed

H1-r2 looked structurally difficult but one strong provider found a coherent
event-log model and completed every composed coordination scenario in 583.677
seconds. Once the correct abstraction was found, almost every remaining problem
was another state transition in the same architecture.

The next campaign therefore must not rely on:

- more endpoints or workflow states;
- a longer visible feature list;
- one hidden edge case;
- a single elegant abstraction that collapses the task;
- UI polish as the remaining quality gradient.

It should instead contain several plausible approaches whose ranking is unknown
until they are implemented and measured. A strong first architecture should
cross the floor, but not determine the final quality by itself.

## 3. Reclassification of the 1,000 ideas

The inventory mixes three different things that must not be voted on as peers.

### Problem domains

- developer build/test systems;
- compilers, static analysis, and transformation;
- distributed storage and runtime systems;
- observability and incident response;
- performance engineering;
- data/ML decision systems;
- security and policy;
- human-agent development systems;
- simulation and combinatorial optimization.

### Difficulty mechanisms

- multiple viable architectures;
- public and heldout workload regimes;
- cheap repeated experiments;
- stochastic or noisy outcomes;
- candidate competition and ablation;
- late evidence that invalidates an early choice;
- interacting correctness, quality, and resource limits;
- an explicit completion floor below the quality ceiling.

### Evaluation mechanisms

- deterministic hard gates;
- distributional quality vectors;
- time-to-first-valid and time-to-best;
- robustness under workload shift;
- task-based product use;
- anti-hardcoding permutation;
- independent command and artifact evidence;
- B30/B60/B120 quality curves.

A final campaign needs one strong problem domain, at least three difficulty
mechanisms, and a fair evaluator. Combining many domain features without the
second layer recreates H1's ceiling problem.

## 4. Elimination rules

The following families were not promoted to the final five.

### Human-agent chat room as the benchmark task

It directly resembles ForgeRoom, so the candidate under evaluation already has
strong domain priors and may optimize for its own visible interface. The oracle
also becomes circular: the system is judged by another version of the system it
is trying to become. Keep it as the outer product, not the principal inner task.

### Full distributed database

The quality ceiling is high, but a one-hour completion floor is unreliable.
Crash-safe storage plumbing can consume the whole budget before meaningful
algorithm comparison begins. QueryCraft retains the empirical planning problem
while supplying the execution engine.

### Robot control or pure optimization simulator

These have excellent iteration curves but over-weight R&D policy search. They do
not sufficiently require delivery of a maintainable developer-facing software
system. They remain useful as a specialist campaign, not the principal one.

### Authentication, policy, and security platform

These create real design depth, but subtle unsafe alternatives are difficult to
score cheaply and fairly. A shallow security implementation can also cross no
credible floor. Security remains a fault overlay on every finalist.

### Pure UI or workflow product

Additional time tends to add breadth and polish, while automated quality becomes
subjective. H1 already measures product discovery and coherent workflow at an
easy/medium level.

### Generic resilient workflow runtime

Despite many failure cases, one event-log plus lease architecture can again
collapse much of the task. It is valuable infrastructure work but has the same
one-abstraction saturation risk as H1.

### Data repair and entity resolution

It has a good empirical surface but requires domain-specific labels and often
makes the oracle or dataset construction the real project. It narrowly missed
the final five in favor of FaultLens and QueryCraft, which provide clearer user
outcomes and reusable deterministic simulation.

## 5. Shared selection rubric

Every shortlisted concept was judged on eight dimensions. Scores are directional
design estimates, not benchmark results.

| Dimension | Weight | Required property |
|---|---:|---|
| Quality ceiling | 15 | useful improvement remains after first completion |
| Multi-agent leverage | 15 | independent work can alter the selected solution |
| Objective oracle | 15 | quality can be replayed without schema guessing |
| Development relevance | 15 | requires shipping and improving real software |
| Iteration speed | 10 | confirmation loop normally completes in seconds |
| Completion floor | 10 | a credible product can exist in roughly 20 minutes |
| One-shot resistance | 10 | one architecture does not collapse the entire task |
| Fixture feasibility | 10 | local, reproducible, and practical to build |

## 6. Shortlist comparison

| Candidate | Estimated fit /100 | Main reason retained or rejected |
|---|---:|---|
| TraceForge adaptive CI | 93 | strongest combination of development relevance and empirical search |
| BugFoundry compiler fuzzing | 91 | extremely fast feedback and naturally parallel discovery |
| FaultLens incident diagnosis | 89 | multiple inference methods plus a coherent operational product |
| MergeLab semantic migration | 86 | rich correctness surface and real repository development |
| QueryCraft query planning | 84 | high algorithmic ceiling with supplied execution floor |
| PulseDB embedded storage | 80 | strong ceiling, but completion floor is too risky |
| RepoEvolution migration control | 78 | valuable, but overlaps MergeLab with weaker fast iteration |
| Human-agent development room | 77 | circular with ForgeRoom and difficult to judge independently |
| PolicyShield agent sandbox | 75 | important but fair security oracle is expensive |
| DataRepair studio | 74 | label and dataset design dominate too easily |
| Resilient workflow runtime | 72 | one-architecture saturation risk remains high |
| Robot/traffic policy league | 68 | measures R&D policy search more than software development |

The numeric spacing should not be interpreted as validated precision. It records
the decision ordering and the assumptions to test in mini calibration.

## 6.1 Traceability to the 1,000 ideas

- **TraceForge:** H0114–H0115, H0155–H0156, H0189, H0199, H0409,
  H0411, H0430, H0449–H0450, H0801, H0809, H0819, H0957, H0979;
- **BugFoundry:** H0163, H0166, H0188, H0232–H0235, H0810, H0952,
  H0961, H0986;
- **FaultLens:** H0123–H0124, H0351–H0400, H0804, H0822–H0824,
  H0956, H0965;
- **MergeLab:** H0129, H0151, H0153, H0161–H0162, H0178, H0194,
  H0198, H0802–H0803, H0834–H0835, H0958, H0966;
- **QueryCraft:** H0117, H0139, H0203, H0271, H0413–H0414, H0432,
  H0806, H0812, H0951, H0963, H0984, H0987.

All five also inherit the cross-cutting mechanisms in H0001–H0100,
H0601–H0700, and H0851–H0950. Traceability does not mean every referenced idea
is a required feature; it shows which seeds were combined into each product bet.

## 6.2 What “five times harder” means

It does not mean five times as many files or requirements. Before full fixture
promotion, each finalist should demonstrate approximately:

- at least five materially different viable solution families;
- at least three public workload/fault regimes with no universal winner;
- 20 or more useful experiment iterations within B60;
- four or more interacting product layers: algorithm, runtime, evidence, and
  operator surface;
- six or more bounded independent investigation/implementation lanes;
- a deterministic completion floor plus a distributional quality frontier;
- evaluator runtime below ten seconds for the normal confirmation suite;
- measurable improvement opportunities after the first valid artifact.

These are fixture-design targets, not automatic score requirements. The
single-provider calibration decides whether they produce a real gradient.

---

# Finalist 1 — TraceForge

## 7. Product objective

Build a local adaptive CI planner for a changing monorepo. Given a commit,
available workers, caches, dependency information, and historical test evidence,
TraceForge must produce and execute a trustworthy plan that finds blocking
failures quickly while reducing end-to-end CI time and compute.

It is not only a scheduler function. Deliver a usable CLI/API, plan explanation,
execution trace, failure accounting, and reproducible tuning workflow.

## 8. Supplied fixture

The fixture provides:

- a synthetic but realistic monorepo graph with roughly 150 packages;
- 500–800 build and test nodes with resource requirements;
- historical commits, changed files, runtimes, flakes, and failure outcomes;
- a deterministic Rust discrete-event simulator;
- eight virtual workers with heterogeneous CPU and memory;
- local and shared caches with explicit transfer costs;
- public development traces and separate confirmation/heldout regimes;
- a reference FIFO scheduler that is correct but slow;
- a frozen JSON protocol for submitting plans and reading results.

One simulated month should evaluate in under five seconds. No real compilation
or network is needed during policy experiments.

## 9. Public task

> Complete TraceForge as a dependable local CI planner. It must always respect
> dependency and resource constraints, produce useful failure evidence, and
> improve time-to-signal and completion cost across the supplied development
> history. Determine and validate the planning, test-selection, caching, and
> adaptation strategies that best serve a changing monorepo.

The brief does not prescribe critical-path scheduling, learned failure priority,
cache admission, speculative execution, or a portfolio router.

## 10. Completion floor

The product crosses the floor when it:

- accepts the frozen repository/workload protocol;
- creates a valid dependency-respecting plan;
- executes it through the simulator;
- reports detected blocking failures without fabrication;
- provides one human-readable explanation of the plan;
- persists experiment and terminal evidence;
- passes deterministic public correctness tests;
- leaves a reproducible committed artifact.

A dependency-aware greedy scheduler can cross this floor. It should not approach
the quality ceiling.

## 11. Quality vector

Hard gates:

- no task before its dependencies;
- no resource overcommit;
- no fabricated cache hit or test result;
- every omitted blocking test is explicitly attributable to a selection policy;
- deterministic replay for fixed seed and policy;
- bounded plan/runtime overhead.

Continuous outcomes:

- p50 and p95 time to first blocking signal;
- p50 and p95 full completion time;
- blocking-failure recall;
- total worker-seconds;
- cache bytes transferred and wasted work;
- fairness/starvation across packages;
- robustness under runtime and failure-distribution shift;
- plan explanation and operator task success;
- marginal improvement from B30 to B60 to B120.

Do not collapse a missed blocker into an average speed score. Correctness and
failure recall remain separate from efficiency.

## 12. Why several approaches remain viable

- critical-path-first scheduling;
- historical failure-probability priority;
- affected-test selection with conservative fallback;
- cache-locality-aware worker assignment;
- resource-aware list scheduling;
- speculative duplicates for heavy-tail tasks;
- online duration correction;
- regime-specific policy portfolio.

No one approach dominates every public regime. Confirmation changes the mix;
heldout changes it again without introducing a new semantic rule.

## 13. Why multi-agent work should matter

Useful independent lanes include:

- workload/data analysis and baseline characterization;
- scheduler and critical-path prototype;
- test-selection/failure model;
- cache/resource policy;
- experiment harness and statistical comparison;
- adversarial correctness verifier;
- product CLI and explanation surface;
- final portfolio integration.

These lanes can produce competing executable artifacts, not merely advice. The
primary agent must decide what to integrate from measured evidence.

## 14. Expected time curve

- **B30:** correct greedy scheduler, basic history use, usable CLI;
- **B60:** two or more policy families compared, shift-aware tuning, better
  time-to-signal;
- **B120:** dynamic portfolio, ablations, adversarial workload repair, stronger
  explanation and operator diagnostics.

If a forwarding run reaches the heldout Pareto frontier in 15 minutes, the
workload regimes or supplied baselines are too simple.

## 15. Main risks and controls

- **Risk:** simulator-specific hardcoding. **Control:** graph/name permutation,
  heldout scale and workload mixtures.
- **Risk:** skip tests for speed. **Control:** blocking recall and missed-failure
  hard reporting.
- **Risk:** fixture engineering is large. **Control:** reuse the existing
  deterministic job-fabric ideas and generate traces from a compact grammar.
- **Risk:** ML dominates. **Control:** strong non-ML policies remain competitive;
  score decision outcomes, not model use.

---

# Finalist 2 — BugFoundry

## 16. Product objective

Build a complete local defect-discovery system around a supplied mini-language
compiler and interpreter. BugFoundry must generate valuable programs, detect and
deduplicate semantic failures, minimize reproductions, turn them into durable
tests, and help produce verified repairs without regressing valid behavior.

## 17. Supplied fixture

- a small typed language with parser, type checker, optimizer, bytecode compiler,
  and VM;
- a slow trustworthy reference interpreter for the supported subset;
- seeded public defects across several compiler stages;
- hidden naturalistic defect families;
- a grammar and frozen process protocol;
- a starter random generator and crude line reducer;
- deterministic execution limits and sanitizer-like crash evidence;
- a corpus replay evaluator finishing in seconds.

The language must be rich enough for interacting types, control flow, mutable
state, and optimization, but small enough that one test executes in milliseconds.

## 18. Public task

> Complete BugFoundry as a practical compiler defect-discovery and repair
> workbench. Find diverse real failures efficiently, reduce them to useful
> reproductions, preserve discoveries as regression tests, and improve the
> supplied compiler without weakening valid behavior.

## 19. Completion floor

- launches through one command;
- discovers at least one non-public defect from the confirmation corpus;
- minimizes it while retaining the same failure class;
- deduplicates repeated manifestations;
- emits a replayable regression artifact;
- validates an attempted repair against public conformance and regression tests;
- documents the tested oracle boundary and residual uncertainty.

## 20. Quality vector

- unique defect families found;
- time to first and time to each new family;
- semantic defects versus trivial parser rejections;
- minimized reproduction size and stability;
- dedup precision and recall;
- accepted repairs and regression escape rate;
- corpus diversity and heldout-stage coverage;
- executions per second and timeout waste;
- explanation quality linking symptom, stage, test, and patch.

Invalid programs, duplicate crashes, and enormous unreduced examples earn little
or no discovery credit.

## 21. Viable approach families

- grammar generation with semantic constraints;
- mutation from valid corpus programs;
- coverage-guided corpus scheduling;
- differential execution against the interpreter;
- metamorphic relations when the reference is unavailable;
- stage-aware crash clustering;
- hierarchical or delta reduction;
- invariant-guided patch localization;
- independent patch candidates selected by the regression corpus.

## 22. Multi-agent leverage

Agents can independently own generator families, metamorphic properties,
coverage analysis, reducers, defect triage, competing patches, and regression
verification. Novel bugs from different generators are additive; duplicate work
is measurable. This makes parallelism useful without requiring concurrent edits
to the same core module.

## 23. Expected time curve

- **B30:** working differential loop, several easy defects, basic reducer;
- **B60:** coverage feedback, semantic generator, stable clustering, repairs;
- **B120:** generator portfolio, adaptive corpus scheduling, deeper optimizer/VM
  defects, better minimization and patch competition.

## 24. Main risks and controls

- **Risk:** agents simply inspect and patch seeded bugs. **Control:** natural
  hidden variants and scoring of the reusable discovery system.
- **Risk:** reference interpreter makes detection trivial. **Control:** some
  supported features use metamorphic or invariant oracles.
- **Risk:** random luck dominates. **Control:** multiple fixed seeds, family
  coverage, and confidence intervals.
- **Risk:** direct compiler work overshadows product delivery. **Control:** require
  one coherent campaign CLI, corpus store, reducer, and evidence model.

---

# Finalist 3 — FaultLens

## 25. Product objective

Build a local incident diagnosis and remediation workbench for a simulated
microservice system. From partial logs, metrics, traces, deployment history, and
operator reports, FaultLens must rank plausible causes, explain supporting and
contradicting evidence, recommend safe probes, and reduce time to mitigation
without taking harmful actions.

## 26. Supplied fixture

- a deterministic microservice simulator with 12–20 services;
- queue, cache, database, retry, rollout, and dependency behavior;
- controllable clock skew, sampling gaps, and correlated symptoms;
- 40+ fault scenarios with several observationally similar prefixes;
- safe diagnostic probes and bounded remediation actions;
- public incident episodes, confirmation combinations, and heldout topology
  permutations;
- a frozen telemetry/action protocol;
- a naive symptom-count baseline.

Each 30-minute virtual incident should replay in under two seconds.

## 27. Public task

> Complete FaultLens as a trustworthy incident workbench. Help an operator
> understand what is happening, decide what evidence to gather next, mitigate
> incidents safely, and preserve a causal record that remains useful when early
> hypotheses are wrong.

## 28. Completion floor

- ingests all frozen telemetry forms;
- produces a ranked diagnosis with evidence references;
- suggests at least one legal diagnostic action;
- can run an episode to a terminal mitigated or honestly unresolved outcome;
- never claims an unobserved action or result;
- shows a concise operator-facing timeline and residual uncertainty;
- persists replayable decision evidence.

## 29. Quality vector

- top-1/top-3 root-cause accuracy;
- virtual time and actions to mitigation;
- harmful or irrelevant action count;
- false certainty and calibration;
- evidence coverage and contradiction handling;
- robustness to missing/noisy telemetry and topology permutation;
- repeated-incident learning without leakage;
- operator task time and explanation usefulness;
- regression safety after adding a new fault class.

## 30. Viable approach families

- rule graph and causal propagation;
- dependency-aware Bayesian scoring;
- trace anomaly localization;
- change-point and deploy correlation;
- active diagnosis by information gain;
- case-based retrieval from past incidents;
- hypothesis portfolio with falsifying probes;
- safe model-predictive remediation.

## 31. Multi-agent leverage

Independent agents can analyze telemetry modalities, construct causal models,
design probes, red-team remediation safety, build the operator product, and
compare diagnosis policies. Dialogue is useful because plausible causes compete
and can be resolved through executable probes rather than consensus prose.

## 32. Expected time curve

- **B30:** working ingestion, rule baseline, causal timeline;
- **B60:** competing rankers, active probes, calibrated uncertainty;
- **B120:** policy portfolio, noisy/compound incidents, safe remediation
  dogfood, stronger operator explanations.

## 33. Main risks and controls

- **Risk:** becomes pure ML classification. **Control:** score active probes,
  mitigation, evidence, and the complete workbench.
- **Risk:** hidden fault names become trivia. **Control:** topology and symptom
  composition, not secret vocabulary.
- **Risk:** simulator is the real project. **Control:** small explicit service
  dynamics and reusable fault grammar.
- **Risk:** one causal rule set dominates. **Control:** ambiguous prefixes,
  missing data, compound faults, and costed probes.

---

# Finalist 4 — MergeLab

## 34. Product objective

Build a local semantic integration tool for concurrent feature work and a
repository-wide API migration. MergeLab must preserve independently valid intent,
apply compatible transformations automatically, expose genuine conflicts, and
produce a buildable, reviewable result with minimal manual intervention.

## 35. Supplied fixture

- a medium polyglot repository with frozen build/test commands;
- a supplied symbol/index protocol so parser construction is not the task;
- historical base/left/right edit triples with known intent labels;
- an API migration specification with compatibility stages;
- rename, move, signature, generated-file, config, and test edits;
- public merge examples and heldout combinations;
- a line-based baseline that is safe but produces many conflicts;
- a semantic validation harness completing in seconds.

## 36. Public task

> Complete MergeLab as a dependable integration and migration workbench. It
> should preserve compatible developer intent, avoid unsafe silent merges,
> explain unresolved conflicts, apply the API evolution consistently, and leave
> a tested repository that a maintainer can review and continue.

## 37. Completion floor

- accepts a base and two branch worktrees;
- produces an isolated candidate integration;
- never mutates the supplied source branches;
- resolves a public nontrivial compatible edit;
- reports unresolved conflicts with source locations and intent evidence;
- runs frozen build/tests and records exact evidence;
- supports dry-run and reproducible apply;
- leaves a clean committed result when accepted.

## 38. Quality vector

- semantic-correct auto-merge rate;
- unsafe silent merge count as a hard gate;
- unnecessary conflict rate;
- retained independent behavior and tests;
- API migration coverage;
- diagnostic usefulness and review time;
- generated/configuration artifact consistency;
- runtime and repository-scale robustness;
- locality of repairs after heldout migration changes.

## 39. Viable approach families

- structured three-way edit scripts;
- symbol-aware operation matching;
- rename/move inference;
- dependency and call-site propagation;
- test-guided candidate competition;
- patch commutativity analysis;
- behavioral differential checks;
- conservative merge plus targeted codemods;
- multiple merge candidates ranked by validation evidence.

## 40. Multi-agent leverage

Agents can independently analyze branch intent, create semantic mappings, build
competing merge algorithms, own language/config adapters, author adversarial
cases, and independently verify the frozen integrated artifact. Parallel feature
branches are native to the task rather than an artificial decomposition.

## 41. Expected time curve

- **B30:** safe worktree flow, line baseline, basic symbol rename;
- **B60:** structured edit matching, migration propagation, reduced conflicts;
- **B120:** candidate merge portfolio, behavioral validation, better diagnostics,
  complex cross-file combinations.

## 42. Main risks and controls

- **Risk:** language parsing consumes the budget. **Control:** provide a stable
  symbol/index and structured-edit protocol.
- **Risk:** pass tests but lose untested intent. **Control:** hidden semantic
  probes and labelled intent relations.
- **Risk:** evaluator prefers one merge representation. **Control:** judge final
  repository behavior, conflict truthfulness, and source preservation.
- **Risk:** repository fixture becomes huge. **Control:** generated variants from
  a compact, understandable base repository.

---

# Finalist 5 — QueryCraft

## 43. Product objective

Build a self-tuning planner and index advisor for a supplied local relational
execution engine. QueryCraft must return exact results, choose effective plans
under imperfect statistics, adapt to changing workloads, explain important
choices, and avoid spending more on planning/indexes than it saves.

## 44. Supplied fixture

- a correct frozen relational execution engine;
- scan, filter, projection, hash/nested joins, aggregate, sort, and index APIs;
- compact generated datasets with correlations and skew;
- a query language/parser already supplied;
- public workload regimes and confirmation/heldout distribution shifts;
- deliberately imperfect cardinality statistics;
- an exhaustive planner usable only for small queries as a reference;
- a frozen plan/execution/metrics protocol.

All main evaluation workloads should finish in under ten seconds.

## 45. Public task

> Complete QueryCraft as a useful local planner and tuning workbench. Produce
> correct query results, improve execution across changing workloads, recommend
> indexes whose benefit exceeds their cost, and give developers enough evidence
> to understand and reproduce important planning decisions.

## 46. Completion floor

- plans and executes all public query forms correctly;
- beats the naive left-to-right baseline on the public mixed workload;
- respects memory/index budgets;
- reports plan structure, observed cost, and cardinality error;
- can run repeatable experiments and compare candidates;
- persists a workload/index recommendation artifact;
- passes result-equivalence and bounded-runtime gates.

## 47. Quality vector

- exact result equivalence as a hard gate;
- total and p95 execution cost across workload regimes;
- planning overhead;
- memory and persistent index budget;
- robustness to cardinality error and data skew;
- adaptation speed after workload shift;
- unnecessary index write/storage cost;
- plan explanation fidelity;
- B30/B60/B120 Pareto improvement.

## 48. Viable approach families

- greedy join ordering;
- dynamic programming for bounded join counts;
- beam search or randomized local search;
- observed-cardinality feedback;
- robust cost estimates and uncertainty penalties;
- workload clustering and plan caching;
- what-if index selection;
- portfolio routing by query shape;
- adaptive re-optimization after severe estimate error.

## 49. Multi-agent leverage

Agents can separately characterize datasets, implement planner families, improve
statistics, explore index selection, build the benchmark harness, attack
correctness, and synthesize a portfolio. Candidate comparison is cheap and
objective, so independent exploration can materially change the final planner.

## 50. Expected time curve

- **B30:** correct planner, simple cost model, public baseline win;
- **B60:** DP/beam candidate comparison, feedback statistics, useful indexes;
- **B120:** robust portfolio, workload-shift adaptation, ablations, stronger
  explanations and adversarial skew handling.

## 51. Main risks and controls

- **Risk:** becomes a textbook optimizer exercise. **Control:** product workflow,
  shifting workloads, imperfect statistics, and index lifecycle.
- **Risk:** execution engine bugs contaminate results. **Control:** freeze and
  independently validate the supplied engine.
- **Risk:** exhaustive search wins all small fixtures. **Control:** larger heldout
  joins and strict planning budgets.
- **Risk:** hard-coded query templates. **Control:** generated equivalent query
  forms, renamed schemas, and heldout correlations.

---

## 52. Cross-campaign capability coverage

| Capability | TraceForge | BugFoundry | FaultLens | MergeLab | QueryCraft |
|---|---:|---:|---:|---:|---:|
| Sparse-objective discovery | high | medium | high | high | medium |
| Competing implementation families | high | high | high | high | high |
| Cheap empirical iteration | high | very high | high | medium | high |
| Independent parallel work | high | very high | high | high | high |
| Deterministic correctness | high | high | medium | high | high |
| Distributional quality | high | high | high | medium | high |
| Product/workflow quality | high | medium | high | high | medium |
| Change/adaptation potential | high | high | high | high | high |
| Direct developer-tool relevance | very high | very high | high | very high | high |

No single task covers the whole target. TraceForge and BugFoundry together give
the strongest first portfolio: the former emphasizes planning and resource
allocation; the latter emphasizes exploration, counterexamples, reduction, and
repair. Their failure modes and useful agent roles are substantially different.

## 53. Proposed calibration order

### Stage 1 — miniature fixtures

Build 10–15 minute toy fixtures for TraceForge and BugFoundry only. Run one
single-Codex forwarding trial on each. The purpose is not score validity; it is
to detect another immediate ceiling or a broken floor before large fixture work.

### Stage 2 — full fixture for the winner

Promote the task that shows:

- completion floor crossed;
- at least three viable solution families remain;
- one or more useful experiments after the first artifact;
- criterion failures that a specialist or independent verifier could improve;
- evaluator runtime below ten seconds;
- no dependence on a hidden noun or implementation schema.

### Stage 3 — matched candidate comparison

Run forwarding, planned single-agent, and multi-agent ForgeRoom candidates at
B30/B60/B120. Preserve time-to-first-valid, every experiment, candidate lineage,
independent defects, integration evidence, and quality curve.

### Stage 4 — second orthogonal campaign

After the first evaluator stabilizes, build the other of TraceForge/BugFoundry.
Do not tune ForgeRoom solely against one task family.

## 54. Stop and revision rules

- If forwarding reaches near-frontier quality within 15 minutes, deepen workload
  diversity or retire the campaign; do not add decorative features.
- If forwarding cannot cross the floor in 30 minutes, reduce fixture/setup work.
- If all approaches choose the same algorithm without experiment, the candidate
  families are not genuinely competitive.
- If score depends on implementation field names, repair the evaluator.
- If quality changes mainly through random seed luck, increase repeats or change
  the task.
- If multi-agent runs create only prose and no unique executable evidence, the
  task decomposition or orchestration is not adding value.
- If evaluator construction exceeds product construction, simplify the domain.

## 55. Final recommendation

Implement **TraceForge-mini** next, not all five full campaigns. It most directly
tests whether the devcontainer's orchestration can discover work, run parallel
algorithm candidates, use experiments to select and integrate them, verify hard
constraints, and improve a real software-development outcome.

In parallel only at the design level, specify **BugFoundry-mini** as the
orthogonal backup. Promote neither until a forwarding run demonstrates a real
quality gradient beyond first completion.
