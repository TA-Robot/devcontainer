# Evidence Forge G2 live pilot — 2026-09-05

## Decision summary

The G2 Adaptive Build Planner pilot passed all external hard gates and produced
a strong heldout tradeoff in 15 minutes 1 second. More importantly for the
devcontainer evaluation, adaptive multi-agent use changed both the selected
algorithm and its correctness/performance envelope: consultation introduced a
global resource-assignment mechanism, and fresh verification found a fractional
correctness defect plus a wide-frontier performance defect before delivery.

This run was followed by a matched solo cell from the same starting commit and
image. Together they show a measured Pareto shift rather than an overall
multi-agent winner: collaboration favored successful completion and deeper
independent verification, while solo finished faster and produced a
blocker-oriented, lower-consumption planner.

## Fixed input and delivery

- fixture: G2 variant 0 with FIFO baseline;
- immutable starting commit: `8230e7818cb1bf356733055b0c82fde4d729d904`;
- final commit: `b6e105eff5720fe203060d72d270722e4fed671e`;
- image: `devcontainer-frozen-smoke:latest` with tmux 3.2a;
- process owner: detached tmux session with a 45-minute outer cost cap;
- observed run: `2026-09-04T18:40:33Z` to `18:55:34Z`, 901 seconds;
- delivered checks: 11/11 project tests, lint, 24-case CLI batch, clean tree;
- external hard gates: valid planner, public tests, and clean workspace passed.

No confirmation or heldout evaluator was available inside the development
container. The external evaluator ran only after the terminal marker.

## External quality result

Lower is better. Calibration values are the pre-existing variant-0 heldout
reference policies.

| Heldout metric | Delivered | FIFO | Critical path | Adaptive |
|---|---:|---:|---:|---:|
| successful completion p50 | 69 | 80 | 74 | 68 |
| blocking failure p50 | 42 | 39 | 44 | 44 |
| mean worker-seconds | 126.125 | 129.792 | 131.042 | 127.500 |

The delivered policy is therefore a real tradeoff, not a synthetic aggregate
winner. It is one unit slower than the adaptive completion median, two units
faster on blocker discovery, and uses fewer worker-seconds. FIFO still exposes
the median blocker three units earlier, while losing substantially on successful
completion and worker consumption.

The external evaluator also observed heldout completion p95 89, blocker p95 78,
and planner p95 1.773 ms. There is no calibrated p95 comparison, so those values
are retained without a ranking claim.

## Search and selection behavior

The primary used both project skills required by the target contract. It fixed
correctness gates and a raw metric vector, measured FIFO, SPT/cache,
failure-density, critical-path, local augmenting matching, and exact global
matching candidates, then documented rejected alternatives and strata. It did
not invent a universal scalar.

The selected public result improved FIFO on all four aggregate outcome axes:

| Public aggregate | FIFO | Selected |
|---|---:|---:|
| successful completion sum | 655 | 534 |
| successful worker-seconds | 1288 | 1228 |
| blocker-time sum | 586 | 542 |
| blocked worker-seconds | 1682 | 1618 |

It also recorded a disconfirming two-worker stratum where blocker time worsened
from 98 to 111. This is better decision evidence than a pass/fail label because
another project may rationally prefer FIFO or a conservation-oriented policy.

## Collaboration path and evidence-producing effect

The primary derived participants from distinct error surfaces rather than an
agent-count default:

| Lifecycle | Purpose | Approximate session window | Concrete effect |
|---|---|---|---|
| consult, bounded exchange | scheduling candidate | 18:41:21–18:44:49 | critical-path/risk/global-matching candidate and disconfirming strata |
| consult, one shot | correctness surface | 18:41:26–18:43:46 | scarce-worker, purity, graph-shape, determinism, and scaling regressions |
| verify, one shot | fixed-artifact review | 18:49:33–18:52:01 | fractional optimum defect and 500×200 latency defect |

The first two overlapped; the verifier was deliberately fresh and later. The
content-free provider ledger observed three worker starts/stops, peak concurrency
two, 436,084 worker-active ms, and a 211,715 ms post-worker-tail proxy in one
890,435 ms successful parent episode.

The verifier supplied the strongest attribution evidence. A residual-flow
matcher ignored real improvements below `1e-12` for legal fractional durations
and took about 23.2 seconds at 500 jobs / 200 workers. The primary added a
forced-fallback fractional regression and replaced the implementation with a
rectangular Hungarian matcher. A 3,000-case seeded exact oracle then agreed, and
500-job latency improved to about 0.41 / 0.95 / 3.92 seconds for 50 / 100 / 200
workers.

One attempted spawn failed before worker creation because it combined a
full-history fork with an agent-type override. The retry respected the native
tool contract. Target guidance now states that full-history forks inherit the
parent type/model/effort and that roles belong in the bounded brief unless a
reduced-context override is intentionally selected.

## Observation defects found and fixed

The run initially printed `unmeasured`, but the durable ledger actually held a
valid delegated episode. The skill wrapper used its process working directory;
when executed from its own `scripts/` directory it hashed the skill path instead
of the copied project root. The wrapper now resolves the nearest ancestor with
`.agent/config.json` before applying the opaque workspace filter. Replaying the
same retained ledger with that correction reports the episode as `observed`.

The episode recorded zero structured test outcomes despite repeated unittest
runs. Codex emits the current shell surface as `exec_command`, and normal project
commands often begin with environment assignments such as
`PYTHONDONTWRITEBYTECODE=1`. The bridge now recognizes both forms and has a
privacy regression proving that command and output content are still discarded.

Native episodes remain machine-uncorrelated with a primary decision packet, so
relation, lifecycle, expected mechanism, and binding constraint remain unknown
in the ledger. The Markdown decision document establishes task-specific effect,
but it must not be retrofitted into content-free telemetry. A future design may
add a validated native decision handoff; this run does not justify guessing from
task names or topology.

## Efficiency and remaining experiments

- cumulative primary report: 5,255,451 input tokens, 5,143,296 cached input,
  49,476 output, and 19,056 reasoning;
- a checkpointed `agentctl` G2 cell would compare durable semantic correlation
  against native low-latency coordination;
- a redesigned G3 mutant bank should retest maker/verifier attribution after the
  first live G3 fixture saturated;
- native decision correlation and accurate test telemetry should be verified in
  the next rebuilt-image live run.

Detailed evaluator output and raw local evidence remain under
`temp/evidence-forge-live-runs/g2-live-01/`. Raw transcripts are not copied into
this durable documentation.

## Matched solo follow-up

The solo cell used the same immutable baseline, image digest, 45-minute cap,
prompt contract, and external evaluator. The only intended treatment difference
was an explicit prohibition on native subagents and `agentctl` participants.

| Observation | Multi-agent | Solo |
|---|---:|---:|
| outer wall time | 901 s | **460 s** |
| reported input tokens | 5,255,451 | **1,797,350** |
| reported output tokens | 49,476 | **30,384** |
| project tests | **11** | 8 |
| heldout completion p50 | **69** | 77 |
| heldout completion p95 | **89** | 92 |
| heldout blocker p50 | 42 | **39** |
| heldout blocker p95 | 78 | **72** |
| heldout mean worker-seconds | 126.125 | **124.417** |
| heldout planner p95 | 1.773 ms | **1.156 ms** |

Both passed every hard gate and both beat the FIFO calibration on successful
completion and worker consumption. Multi-agent improved heldout completion p50
by eight relative to solo, at an added 441 seconds and roughly 3.46 million
reported input tokens. Solo matched FIFO's blocker median while still reducing
worker consumption. Neither dominates the other.

The qualitative coverage difference matters alongside the evaluator vector.
Solo compared six policy families and checked 500 bounded matching graphs. The
multi-agent cell added deep-DAG, fractional-precision, and wide-frontier
regressions after a fresh verifier found actual defects in its intermediate
implementation. A post-run outer diagnostic measured the solo Hungarian matcher
at about 0.315 / 0.837 / 3.191 seconds for 500 jobs and 50 / 100 / 200 workers,
so its thinner test suite did not mask the same wide-frontier slowdown.

The supported project-local conclusion is therefore conditional:

- use solo as a credible first path when early blocker discovery, model/wall
  cost, and modest worker consumption dominate;
- bounded consultation plus fresh verification can buy a materially more
  completion-aggressive policy and stronger failure-surface evidence when that
  gain is worth the coordination cost;
- do not convert this one pair into a provider, participant-count, or round-count
  default. Repeat on a redesigned, non-saturated G3 and another artifact before
  changing broader planning priors.

Detailed solo evidence is under
`temp/evidence-forge-live-runs/g2-solo-01/`; its clean target fixture is under
`temp/evidence-forge-g2-solo-20260905-01/`.
