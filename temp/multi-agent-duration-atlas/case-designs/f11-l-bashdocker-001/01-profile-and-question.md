# F11-L-BASHDOCKER-001: profile and measurement question

## Scenario

A simulated devcontainer rebuild migrates a persistent volume, synchronizes host CLI metadata, installs a companion extension, and starts runtime hooks. An interrupted schema migration plus stale host/extension markers can destroy recoverable state or suppress repair.

## Measurement question

How do lifecycle boundaries, persistent state, and recovery obligations affect operational change time?

| Axis | Value |
| --- | --- |
| case ID | `F11-L-BASHDOCKER-001` |
| family | `devcontainer-operations` |
| size | `L` |
| profile ID | `L-cross-boundary-rebuild-recovery` |
| ambiguity | `bounded-open` |
| oracle | `deterministic` |
| decomposability | `independent` |
| artifact | `patch` |
| risk | `high` |
| lane | `write` |
| environment | `local-tool` |
| knowledge | `repository-contained` |
| stack | `bash, python, docker, json, markdown` |

## Structural size evidence

| Descriptor | Designed value |
| --- | --- |
| context surface | devcontainer config, Bash host/container lifecycle, Python state migrator, extension marker |
| artifact surface | cross-boundary patch and recovery runbook |
| coupling | rebuild/persistence/host-extension ownership |
| validation depth | static, unit, rebuild, migration, restart, residual-inventory |
| environment setup | simulated rebuild/reopen with persistent volume |
| failure distance | rebuild/restart-delayed |
| statefulness | persistent volume and host/container markers |

このlabelは予想時間ではなく上記構造から決める。実測が長い・短いだけではsizeを変更しない。

## What this case can reveal

- first contract-valid artifactとuser-resultまでの差。
- public validation、hidden quality score、offline scoringの時間境界。
- devcontainer-operationsのL profileで、探索・生成・検証のどこが支配項になるか。

## Scope boundary

- provider/modelの総合rankingを作らない。
- この一件からfamily typical timeやmulti-agent routing ruleを作らない。
- fixture外の現行product behaviorを変更しない。

このcaseの結果は同じrevision/profileの観測であり、family全体、別stack、natural projectへ自動一般化しない。
