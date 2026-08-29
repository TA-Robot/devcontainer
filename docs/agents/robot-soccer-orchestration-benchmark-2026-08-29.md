# Robot soccer orchestration benchmark: 2026-08-29

## Status and interpretation

This benchmark was stopped by the operator after approximately 86 minutes and is
**incomplete**. It is useful as an orchestration trace and a development-system
diagnostic, but it is not a quality pass for the controller and must not be used
as a stable estimate of controller success probability.

The run used Codex CLI 0.146.0 with `gpt-5.6-sol`, high reasoning effort and fast
mode in the trusted devcontainer. The task was to implement a central controller
for two friendly robots against three defenders in the hidden-dynamics robot
soccer simulator. Evaluation was available as an eight-seed parallel run.

Raw benchmark worktrees and run artifacts were intentionally deleted after this
summary was recorded. The committed controller in the disposable benchmark
repository was not promoted into this repository.

## Measured result

| Measure | Observed value |
| --- | ---: |
| Wall time before termination | approximately 86 minutes |
| Recorded evaluation runs | 66 |
| Recorded episodes | 360 |
| `pass_and_goal` episodes | 35 (9.72% of all development episodes) |
| `ball_out` episodes | 313 |
| `episode_timeout` episodes | 8 |
| `pass_sequence_incomplete` episodes | 2 |
| Infrastructure/unknown result | 2 |
| Best eight-seed development run | 4/8 |
| Repeat of the same controller digest | 3/8 |
| Serial check of the same digest | 2/8 |
| Focused controller unit tests | 9 |
| Held-out acceptance run | not completed |

The aggregate 35/360 figure is not a generalization estimate. Seeds and
controller revisions were repeatedly selected during development, so the
episodes are neither independent nor held out. The fall from 4/8 to 3/8 and 2/8
for the same source digest also shows that the apparent best score was not
stable enough to select as a winner.

Simulator throughput was adequate for this style of search. Eight-way startup
and evaluation took roughly 4.5--5.7 seconds in observed runs; the average
episode real-time ratio was 1.13 and the maximum was 2.158. Evaluation throughput
was therefore not the principal bottleneck.

## Development timeline

- The goal started at about 10:53 JST.
- For roughly the first 27 revisions, evaluation concentrated on one or two
  development seeds. No warm evaluator or delegated candidate search was used.
- The first broad eight-seed check occurred around minute 37 and exposed the
  narrow-seed overfitting pattern. It produced 2/8 successes.
- The best observed 4/8 revision appeared around minute 42.
- Local tuning continued after the score plateaued. A 620-line controller,
  113-line focused test file and short design note were committed in the
  disposable repository at 12:05 JST.
- Independent candidate worktrees were started only after the main commit and
  more than an hour into the run. The benchmark was stopped before a held-out
  acceptance stage.

## Late candidate search

The late fan-out explored adaptive timing, control refinements, latency-aware
estimation, reversal, pre-clear, hybrid estimation, first-touch kicking and
fixed timing. Most variants scored 0/3. The strongest isolated signals were:

| Candidate | Development result | Integration decision |
| --- | ---: | --- |
| Latency-aware estimator variant | 1/3 | not integrated; evidence too weak |
| Hybrid estimator | 1/3 | not integrated; evidence too weak |
| First-touch kick | 1/8 | rejected |
| Fixed timing | 1/8 | rejected |

No candidate demonstrated a reliable improvement over the already unstable
baseline. Claude and Grok were not used in this run.

## What this says about orchestration

The main failure was search allocation, not raw simulator speed. The agent spent
most of the budget in sequential local tuning against a narrow seed sample,
then invoked independent candidate search after the critical-path decision had
largely been made. The environment made parallel evaluation cheap, but the
orchestrator did not exploit that fact early enough.

Future runs should treat the following as adaptive decisions rather than fixed
agent counts or turn limits:

- establish a multi-seed baseline before deep local tuning;
- keep a warm broad-seed evaluator available while implementation changes;
- detect score plateaus and seed-specific gains, then switch from local tuning
  to independent hypotheses while useful budget remains;
- compare candidates from the same base with the same seed set and source-tree
  snapshot contract;
- reserve a held-out acceptance set and require repeatability before declaring
  a winner;
- expose simulator affordances, such as the friendly robots' higher velocity
  ceiling, to the controller-design process without exposing hidden dynamics.

The controller mostly capped commanded speed around 1.4--1.45 despite the
friendly side having a substantially larger allowed ceiling. This is a concrete
example of an available design degree of freedom that the search did not exploit.

## Observability gaps found

The collaboration report observed one long episode but classified it as
`solo-observed`, reported zero worker starts and left semantic relations and test
outcomes unknown. Its coverage metadata simultaneously indicated one observed
worker start. This disagrees with the candidate worktrees and live subagent
activity seen during the run.

Consequently, current telemetry is good enough to reconstruct wall time, run
counts, score histories and artifacts, but not yet reliable enough to answer
which agent proposed a useful hypothesis, when work was delegated, or how that
result affected the integration decision. Worker lifecycle correlation and
decision/result linkage remain priority observability gaps.

## Repository changes prompted by the run

The benchmark exposed issues that were fixed separately in this repository:

- controller evaluation now snapshots source trees instead of only one file;
- the runner has a stable parallel streaming path and trace summarizer;
- trusted advisory fan-out and cross-provider read jobs are documented;
- the adaptive orchestration skill and warm-evaluation paths are surfaced;
- headless devcontainer attach and trusted Codex startup behavior are hardened.

These changes improve the next experiment, but this incomplete run does not
prove that the revised orchestration policy is effective. A fresh benchmark is
required for that conclusion.
