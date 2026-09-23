# F04-S-PY-001: profile and measurement question

## Scenario

The existing calibration case asks the agent to complete a dependency-free tag normalizer with an exact ASCII, separator, emptiness, and length contract.

## Measurement question

How do edit/test coupling and validation depth affect time to a contract-valid patch?

| Axis | Value |
| --- | --- |
| case ID | `F04-S-PY-001` |
| family | `bounded-implementation` |
| size | `S` |
| profile ID | `S-local-deterministic-python` |
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
| context surface | single Python module |
| artifact surface | one function and unit tests |
| coupling | local |
| validation depth | unit |
| environment setup | none |
| failure distance | local |
| statefulness | stateless |

このlabelは予想時間ではなく上記構造から決める。実測が長い・短いだけではsizeを変更しない。

## What this case can reveal

- first contract-valid artifactとuser-resultまでの差。
- public validation、hidden quality score、offline scoringの時間境界。
- bounded-implementationのS profileで、探索・生成・検証のどこが支配項になるか。

## Scope boundary

- provider/modelの総合rankingを作らない。
- この一件からfamily typical timeやmulti-agent routing ruleを作らない。
- fixture外の現行product behaviorを変更しない。

このcaseの結果は同じrevision/profileの観測であり、family全体、別stack、natural projectへ自動一般化しない。
