# F10-L-PYBASH-001: profile and measurement question

## Scenario

A deterministic job simulator models admission queue, serialized image probe, concurrent worker setup, provider wait, validation, and cleanup. Tail latency rises with width because image probing holds a global lock, while provider wait dominates per-job active time.

## Measurement question

How do instrumentation breadth and measurement noise affect time to a reproducible bottleneck diagnosis?

| Axis | Value |
| --- | --- |
| case ID | `F10-L-PYBASH-001` |
| family | `performance-resource` |
| size | `L` |
| profile ID | `L-multistage-resource-diagnosis` |
| ambiguity | `bounded-open` |
| oracle | `deterministic` |
| decomposability | `independent` |
| artifact | `synthesis` |
| risk | `medium` |
| lane | `isolated` |
| environment | `local-tool` |
| knowledge | `repository-contained` |
| stack | `python, bash, json, docker` |

## Structural size evidence

| Descriptor | Designed value |
| --- | --- |
| context surface | Python queue/worker simulator, Bash batch launcher, stage ledger |
| artifact surface | instrumentation, bottleneck model, experiment report |
| coupling | queue/concurrency/container/provider stages |
| validation depth | unit, multi-stage-instrumentation, concurrency, distribution |
| environment setup | multi-process simulator |
| failure distance | queue/tail-delayed |
| statefulness | job/lock/stage event state |

このlabelは予想時間ではなく上記構造から決める。実測が長い・短いだけではsizeを変更しない。

## What this case can reveal

- first contract-valid artifactとuser-resultまでの差。
- public validation、hidden quality score、offline scoringの時間境界。
- performance-resourceのL profileで、探索・生成・検証のどこが支配項になるか。

## Scope boundary

- provider/modelの総合rankingを作らない。
- この一件からfamily typical timeやmulti-agent routing ruleを作らない。
- fixture外の現行product behaviorを変更しない。

このcaseの結果は同じrevision/profileの観測であり、family全体、別stack、natural projectへ自動一般化しない。
