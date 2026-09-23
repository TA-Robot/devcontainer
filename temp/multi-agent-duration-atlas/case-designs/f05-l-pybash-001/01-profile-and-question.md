# F05-L-PYBASH-001: profile and measurement question

## Scenario

A file-backed job ledger is migrated behind a backend interface while moving state from schema v1 to v2. Python readers/writers, a Bash wrapper, rollback export, and interrupted-migration recovery must remain compatible.

## Measurement question

How do caller discovery, compatibility, and rollback obligations affect a behavior-preserving migration?

| Axis | Value |
| --- | --- |
| case ID | `F05-L-PYBASH-001` |
| family | `refactor-migration` |
| size | `L` |
| profile ID | `L-cross-boundary-backend-schema-migration` |
| ambiguity | `bounded-open` |
| oracle | `deterministic` |
| decomposability | `partial` |
| artifact | `patch` |
| risk | `high` |
| lane | `write` |
| environment | `local-tool` |
| knowledge | `repository-contained` |
| stack | `python, bash, json, markdown` |

## Structural size evidence

| Descriptor | Designed value |
| --- | --- |
| context surface | backend interface, file implementation, schema migrator, CLI, Bash wrapper |
| artifact surface | migration set plus rollback/recovery |
| coupling | backend and schema compatibility |
| validation depth | unit, contract, migration, rollback, restart |
| environment setup | fresh-process lifecycle |
| failure distance | migration/restart-delayed |
| statefulness | persistent versioned state |

このlabelは予想時間ではなく上記構造から決める。実測が長い・短いだけではsizeを変更しない。

## What this case can reveal

- first contract-valid artifactとuser-resultまでの差。
- public validation、hidden quality score、offline scoringの時間境界。
- refactor-migrationのL profileで、探索・生成・検証のどこが支配項になるか。

## Scope boundary

- provider/modelの総合rankingを作らない。
- この一件からfamily typical timeやmulti-agent routing ruleを作らない。
- fixture外の現行product behaviorを変更しない。

このcaseの結果は同じrevision/profileの観測であり、family全体、別stack、natural projectへ自動一般化しない。
