# F08-L-MDJSON-001: profile and measurement question

## Scenario

The fixture asks for a future execution fabric and persistence design spanning provider adapters, job orchestration, workspace isolation, event ledger, recovery, migration, credentials, operations, and companion observability.

## Measurement question

How do ambiguity, constraint breadth, and counterexamples affect time and coverage of a design decision?

| Axis | Value |
| --- | --- |
| case ID | `F08-L-MDJSON-001` |
| family | `architecture-design` |
| size | `L` |
| profile ID | `L-cross-boundary-calibrated-execution-design` |
| ambiguity | `open` |
| oracle | `calibrated` |
| decomposability | `independent` |
| artifact | `design` |
| risk | `high` |
| lane | `read` |
| environment | `local-tool` |
| knowledge | `repository-contained` |
| stack | `markdown, json, python, bash, docker` |

## Structural size evidence

| Descriptor | Designed value |
| --- | --- |
| context surface | execution fabric, persistence, provider, isolation, UI/operations evidence |
| artifact surface | multi-section design record and machine model |
| coupling | security/migration/operations coupling |
| validation depth | schema, constraint, threat, failure-simulation, migration, operations |
| environment setup | deterministic topology/lifecycle simulator |
| failure distance | multi-stage restart/migration |
| statefulness | durable jobs, leases, event ledger |

このlabelは予想時間ではなく上記構造から決める。実測が長い・短いだけではsizeを変更しない。

## What this case can reveal

- first contract-valid artifactとuser-resultまでの差。
- public validation、hidden quality score、offline scoringの時間境界。
- architecture-designのL profileで、探索・生成・検証のどこが支配項になるか。

## Scope boundary

- provider/modelの総合rankingを作らない。
- この一件からfamily typical timeやmulti-agent routing ruleを作らない。
- fixture外の現行product behaviorを変更しない。

このcaseの結果は同じrevision/profileの観測であり、family全体、別stack、natural projectへ自動一般化しない。
