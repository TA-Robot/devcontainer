# Candidate themes and selection

## 1. Candidate set

The theme must be chosen by how well it exposes general development capability,
not by novelty. Six candidates were considered.

## 2. A — Rich collaboration chat

Build a Slack-like app with providers, threads, artifacts, and review actions.

Strengths:

- clear product completion;
- UI, backend, lifecycle, and provider integration;
- easy to understand and demonstrate.

Weaknesses:

- forwarding is already useful enough to satisfy many scenarios;
- features become checklist items;
- downstream development quality is indirect;
- v1 demonstrated an early ceiling.

Decision: reject as the complete benchmark; retain chat as one interaction
surface of a deeper system.

## 3. B — Generic workflow engine

Build an event-sourced task graph engine with retries, queues, schedules, and
plugins.

Strengths:

- deep systems architecture;
- rich concurrency and failure behavior;
- many meaningful design trade-offs.

Weaknesses:

- mostly measures distributed-systems implementation;
- semantic collaboration quality is weak;
- can be evaluated without real coding agents.

Decision: useful subsystem, insufficient as the overarching theme.

## 4. C — Automated code-repair service

Build a service that accepts failing repositories, invokes agents, and returns
patches.

Strengths:

- downstream outcomes are measurable;
- hidden mutant/repository suites provide headroom;
- iterative critique and candidate comparison can help.

Weaknesses:

- biases toward bug repair;
- under-represents greenfield architecture, feature development, and project
  planning;
- a strong single Codex call may dominate easy cases.

Decision: include repair as one campaign family, not the whole benchmark.

## 5. D — Agentic code-review and assurance platform

Build a system that finds and validates defects in candidate repositories.

Strengths:

- excellent hidden-mutant oracle;
- independent verification has clear value;
- findings can be scored by reproduction and repair.

Weaknesses:

- measures assurance more than end-to-end development;
- may reward exhaustive criticism without delivery;
- less opportunity for implementation DAGs.

Decision: include assurance as one stage/campaign, not the whole benchmark.

## 6. E — Git-native AI software studio

Build a local system where a human can submit a project goal and Codex/Grok can
jointly develop the repository. The system owns campaign state, context,
orchestration, isolated work, integration, testing, review, recovery, and a
compact human-visible interaction surface.

Strengths:

- directly aligned with the repository's purpose;
- combines app completion, architecture, algorithms, Git, provider control,
  multi-agent methods, assurance, and UX;
- can be evaluated by actual unseen development outcomes;
- more time can improve both product mechanisms and downstream utility;
- successful components may later inform the real devcontainer.

Weaknesses:

- recursive: an orchestrator builds an orchestrator;
- real-provider evaluation is expensive and stochastic;
- candidate can bypass its own sophistication by forwarding prompts;
- evaluation needs multiple campaign families and strong isolation.

Decision: select, with anti-forwarding calibration and layered evaluators.

## 7. F — Multi-repository software delivery organization

Build a system that handles several services, dependencies, releases, and
cross-repository changes.

Strengths:

- very high ceiling;
- realistic planning and integration;
- strong parallelism opportunities.

Weaknesses:

- fixture and evaluator construction are large projects themselves;
- a one-hour pilot may fail to cross the product floor;
- environment and build costs can dominate cognition.

Decision: reserve as a later campaign extension after E is calibrated.

## 8. Selection matrix

Scores are design judgments used to expose trade-offs, not benchmark results.

| Theme | Completion floor | Continuous headroom | General development | Multi-agent opportunity | Oracle feasibility | Calibration cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Rich chat | high | low | medium | medium | high | low |
| Workflow engine | medium | medium | low-medium | low | high | medium |
| Code repair | high | high | medium | medium-high | high | medium |
| Assurance platform | high | medium-high | medium | high | high | medium |
| Git-native AI studio | medium | very high | very high | very high | medium | high |
| Multi-repo delivery | low-medium | very high | very high | very high | low-medium | very high |

## 9. Selected theme: ForgeRoom

Working name: **ForgeRoom**.

ForgeRoom is not “a chat app with AI messages.” It is a Git-native software
development room with chat as its human control surface. A submitted campaign
has an objective, workspace, authority boundary, provider budget, state,
evidence, and terminal outcome.

The visible product contract stays deliberately small:

- launch locally;
- accept a Git workspace and development objective;
- expose human/agent activity and terminal state;
- invoke only supplied provider adapters;
- preserve and recover campaign state;
- never escape the workspace or fabricate success;
- provide a stable campaign API used by the evaluator.

Everything else is a design opportunity. A candidate may add task graphs,
roles, worktrees, review loops, candidate tournaments, context capsules,
provider routing, or other mechanisms when they improve campaign outcomes.

## 10. Why this theme avoids the v1 error

The evaluator does not award points for implementing “task graph,” “debate,” or
“Ask both.” It submits unseen projects and measures what the resulting studio
delivers. A forwarding baseline remains valid and establishes the floor. More
capable orchestration must beat that floor through accepted software outcomes.

Chat/UI can be minimal but usable. The product's center of gravity becomes
development execution rather than visual feature accumulation.

## 11. Principal risk: provider dominance

If one direct Codex invocation already solves every hidden campaign, ForgeRoom
again cannot discriminate. The campaign corpus must therefore contain tasks
where one-shot forwarding predictably leaves value on the table:

- context-heavy repository reconnaissance;
- independently reviewable high-loss invariants;
- separable implementation DAGs;
- competing architecture/performance approaches;
- conflicting edits and integration;
- provider interruption and stale output;
- a versioned change request after the first acceptable artifact;
- quality criteria revealed through public feedback but not hidden answers.

The forwarding baseline must be run before accepting the corpus.

## 12. Secondary risk: building the evaluator becomes the task

ForgeRoom evaluation is more expensive than v1. To control scope, the first
revision should use three compact campaign repositories rather than a giant
enterprise fixture, plus deterministic infrastructure fault scenarios. Expand
only after discrimination is demonstrated.

## 13. Final selection rationale

ForgeRoom is selected because it creates a direct chain from outer development
quality to downstream software outcomes, while preserving the app-development
nature of the benchmark. It is complex for the right reason: architecture,
implementation, experimentation, and assurance interact. It is not made hard
by multiplying screens or requirements.
