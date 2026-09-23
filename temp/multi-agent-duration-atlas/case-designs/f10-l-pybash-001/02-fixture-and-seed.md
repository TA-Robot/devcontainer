# F10-L-PYBASH-001: fixture and seeded state

## Disposable repository

| Visible path | Role | Initial state |
| --- | --- | --- |
| `fabric/simulator.py` | job/stage simulation | working seeded global lock |
| `fabric/ledger.py` | event timestamps | missing stage correlation IDs |
| `bin/run-batch` | width/workload launcher | working |
| `tests/` | functional simulator behavior | passing |
| `instrumentation.py` | target stage instrumentation | skeleton |
| `performance.json` | target bottleneck model | absent |

agent workspaceには上表、`AGENTS.md`、public checksだけを置く。capsule、hidden evaluator、private known-good、base bundleはcontrol directoryへ隔離し、workspaceへmountしない。

## Seed

Width 1 hides queue growth. At higher widths the global image-probe lock creates admission/worker-start tail, while provider wait remains the largest individual active stage. Conflating wall tail with aggregate worker time yields the wrong optimization.

初期fixtureは少なくとも一つのpublicまたはhidden criterionで必ずfailする。偶然passした場合はcase construction failureでありlive runを開始しない。

## Expected investigation or change path

1. Add correlated timestamps/counters for all stages without double-counting parallel intervals.
2. Run rotated width/workload blocks and capture raw event ledgers.
3. Derive user wait, worker span/union/aggregate, queue, probe, provider, validation, and cleanup distributions.
4. Build a conditional bottleneck model and test removal/relocation hypotheses.

## Private known-good outline

Correlated ledgers and rotated width blocks yield correct wall/union/aggregate metrics, show the serialized probe lock drives queue/tail growth, preserve provider wait as per-job active dominant, and bound conclusions to the simulator.

## Reproducibility and leakage controls

- fixed git author/date、single reachable commit、remote/tagなしで生成する。
- task中のnetworkを無効化し、親repository、generator source、他case、goldへ到達させない。
- visible tree、instruction set、capsule、catalog、recipeをdigest化する。
- evaluatorはnetworkなし・read-only workspace・credential mountなしで実行する。
- initial failとknown-good passを同じevaluator revisionで校正する。
