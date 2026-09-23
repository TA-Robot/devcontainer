# F08-M-MDJSON-001: profile and measurement question

## Scenario

A local job system must divide responsibilities among scheduler, supervisor, and durable job store under at-least-once execution, cancellation, restart, and bounded retry. Three plausible component splits are provided.

## Measurement question

How do ambiguity, constraint breadth, and counterexamples affect time and coverage of a design decision?

| Axis | Value |
| --- | --- |
| case ID | `F08-M-MDJSON-001` |
| family | `architecture-design` |
| size | `M` |
| profile ID | `M-coupled-calibrated-architecture` |
| ambiguity | `open` |
| oracle | `calibrated` |
| decomposability | `independent` |
| artifact | `design` |
| risk | `high` |
| lane | `read` |
| environment | `local-tool` |
| knowledge | `repository-contained` |
| stack | `markdown, json, python` |

## Structural size evidence

| Descriptor | Designed value |
| --- | --- |
| context surface | three components, option sketches, failure traces, invariants |
| artifact surface | architecture proposal and responsibility matrix |
| coupling | component ownership and failure transitions |
| validation depth | schema, constraint, failure-simulation, counterexample |
| environment setup | deterministic event simulator |
| failure distance | cross-component restart |
| statefulness | durable job state |

このlabelは予想時間ではなく上記構造から決める。実測が長い・短いだけではsizeを変更しない。

## What this case can reveal

- first contract-valid artifactとuser-resultまでの差。
- public validation、hidden quality score、offline scoringの時間境界。
- architecture-designのM profileで、探索・生成・検証のどこが支配項になるか。

## Scope boundary

- provider/modelの総合rankingを作らない。
- この一件からfamily typical timeやmulti-agent routing ruleを作らない。
- fixture外の現行product behaviorを変更しない。

このcaseの結果は同じrevision/profileの観測であり、family全体、別stack、natural projectへ自動一般化しない。
