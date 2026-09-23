# F05-S-PY-001: profile and measurement question

## Scenario

Two public functions duplicate the same event-name normalization. The task extracts one private helper while preserving signatures, exceptions, call order, and observable output.

## Measurement question

How do caller discovery, compatibility, and rollback obligations affect a behavior-preserving migration?

| Axis | Value |
| --- | --- |
| case ID | `F05-S-PY-001` |
| family | `refactor-migration` |
| size | `S` |
| profile ID | `S-local-equivalence-refactor-python` |
| ambiguity | `exact` |
| oracle | `deterministic` |
| decomposability | `serial` |
| artifact | `patch` |
| risk | `low` |
| lane | `write` |
| environment | `local-tool` |
| knowledge | `repository-contained` |
| stack | `python` |

## Structural size evidence

| Descriptor | Designed value |
| --- | --- |
| context surface | one Python module and tests |
| artifact surface | local refactor patch |
| coupling | shared private logic |
| validation depth | unit, behavior-equivalence |
| environment setup | none |
| failure distance | direct |
| statefulness | stateless |

このlabelは予想時間ではなく上記構造から決める。実測が長い・短いだけではsizeを変更しない。

## What this case can reveal

- first contract-valid artifactとuser-resultまでの差。
- public validation、hidden quality score、offline scoringの時間境界。
- refactor-migrationのS profileで、探索・生成・検証のどこが支配項になるか。

## Scope boundary

- provider/modelの総合rankingを作らない。
- この一件からfamily typical timeやmulti-agent routing ruleを作らない。
- fixture外の現行product behaviorを変更しない。

このcaseの結果は同じrevision/profileの観測であり、family全体、別stack、natural projectへ自動一般化しない。
