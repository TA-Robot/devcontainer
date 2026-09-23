# F10-S-PY-001: profile and measurement question

## Scenario

A local report function canonicalizes the same JSON object once per output field. A deterministic instrumentation counter and microbenchmark allow the agent to identify the repeated serialization hot path without relying on noisy absolute thresholds.

## Measurement question

How do instrumentation breadth and measurement noise affect time to a reproducible bottleneck diagnosis?

| Axis | Value |
| --- | --- |
| case ID | `F10-S-PY-001` |
| family | `performance-resource` |
| size | `S` |
| profile ID | `S-local-benchmark-diagnosis-python` |
| ambiguity | `exact` |
| oracle | `deterministic` |
| decomposability | `serial` |
| artifact | `synthesis` |
| risk | `low` |
| lane | `isolated` |
| environment | `local-tool` |
| knowledge | `repository-contained` |
| stack | `python, json` |

## Structural size evidence

| Descriptor | Designed value |
| --- | --- |
| context surface | one Python hot path and benchmark |
| artifact surface | diagnosis plus measurement JSON |
| coupling | local repeated work |
| validation depth | unit, counter, benchmark |
| environment setup | none |
| failure distance | direct |
| statefulness | stateless |

このlabelは予想時間ではなく上記構造から決める。実測が長い・短いだけではsizeを変更しない。

## What this case can reveal

- first contract-valid artifactとuser-resultまでの差。
- public validation、hidden quality score、offline scoringの時間境界。
- performance-resourceのS profileで、探索・生成・検証のどこが支配項になるか。

## Scope boundary

- provider/modelの総合rankingを作らない。
- この一件からfamily typical timeやmulti-agent routing ruleを作らない。
- fixture外の現行product behaviorを変更しない。

このcaseの結果は同じrevision/profileの観測であり、family全体、別stack、natural projectへ自動一般化しない。
