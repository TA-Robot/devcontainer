# F04-M-PY-001: profile and measurement question

## Scenario

The existing medium fixture adds atomic JSON persistence, CLI exit contracts, tests, and usage documentation to a small key/value tool.

## Measurement question

How do edit/test coupling and validation depth affect time to a contract-valid patch?

| Axis | Value |
| --- | --- |
| case ID | `F04-M-PY-001` |
| family | `bounded-implementation` |
| size | `M` |
| profile ID | `M-coupled-deterministic-python` |
| ambiguity | `exact` |
| oracle | `deterministic` |
| decomposability | `partial` |
| artifact | `patch` |
| risk | `low` |
| lane | `write` |
| environment | `local-tool` |
| knowledge | `repository-contained` |
| stack | `python, markdown` |

## Structural size evidence

| Descriptor | Designed value |
| --- | --- |
| context surface | multi-module CLI and storage |
| artifact surface | storage, CLI, tests, and usage |
| coupling | cross-module contract |
| validation depth | unit, contract |
| environment setup | temporary filesystem |
| failure distance | cross-module |
| statefulness | filesystem state |

このlabelは予想時間ではなく上記構造から決める。実測が長い・短いだけではsizeを変更しない。

## What this case can reveal

- first contract-valid artifactとuser-resultまでの差。
- public validation、hidden quality score、offline scoringの時間境界。
- bounded-implementationのM profileで、探索・生成・検証のどこが支配項になるか。

## Scope boundary

- provider/modelの総合rankingを作らない。
- この一件からfamily typical timeやmulti-agent routing ruleを作らない。
- fixture外の現行product behaviorを変更しない。

このcaseの結果は同じrevision/profileの観測であり、family全体、別stack、natural projectへ自動一般化しない。
