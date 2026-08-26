# F05-M-PY-001: profile and measurement question

## Scenario

A module-level `encode_event(dict)` API is migrated to an `EventCodec` object so schema policy can be injected, while callers and a deprecated compatibility shim must remain coherent.

## Measurement question

How do caller discovery, compatibility, and rollback obligations affect a behavior-preserving migration?

| Axis | Value |
| --- | --- |
| case ID | `F05-M-PY-001` |
| family | `refactor-migration` |
| size | `M` |
| profile ID | `M-coupled-interface-migration-python` |
| ambiguity | `exact` |
| oracle | `deterministic` |
| decomposability | `partial` |
| artifact | `patch` |
| risk | `medium` |
| lane | `write` |
| environment | `local-tool` |
| knowledge | `repository-contained` |
| stack | `python` |

## Structural size evidence

| Descriptor | Designed value |
| --- | --- |
| context surface | codec module, three callers, compatibility layer, tests |
| artifact surface | interface migration patch |
| coupling | caller and compatibility contract |
| validation depth | unit, caller, compatibility |
| environment setup | none |
| failure distance | cross-module |
| statefulness | configuration object state |

このlabelは予想時間ではなく上記構造から決める。実測が長い・短いだけではsizeを変更しない。

## What this case can reveal

- first contract-valid artifactとuser-resultまでの差。
- public validation、hidden quality score、offline scoringの時間境界。
- refactor-migrationのM profileで、探索・生成・検証のどこが支配項になるか。

## Scope boundary

- provider/modelの総合rankingを作らない。
- この一件からfamily typical timeやmulti-agent routing ruleを作らない。
- fixture外の現行product behaviorを変更しない。

このcaseの結果は同じrevision/profileの観測であり、family全体、別stack、natural projectへ自動一般化しない。
