# F04-L-PYBASH-001: profile and measurement question

## Scenario

The existing large fixture completes an idempotent acknowledgement lifecycle across Python storage/CLI, a Bash wrapper, persistent JSON state, and fresh-process restart checks.

## Measurement question

How do edit/test coupling and validation depth affect time to a contract-valid patch?

| Axis | Value |
| --- | --- |
| case ID | `F04-L-PYBASH-001` |
| family | `bounded-implementation` |
| size | `L` |
| profile ID | `L-cross-boundary-deterministic-python-bash` |
| ambiguity | `exact` |
| oracle | `deterministic` |
| decomposability | `partial` |
| artifact | `patch` |
| risk | `medium` |
| lane | `write` |
| environment | `local-tool` |
| knowledge | `repository-contained` |
| stack | `python, bash, json, markdown` |

## Structural size evidence

| Descriptor | Designed value |
| --- | --- |
| context surface | Python storage/CLI and Bash process boundary |
| artifact surface | storage, CLI, wrapper, tests, format contract |
| coupling | cross-process persistent contract |
| validation depth | unit, integration, restart |
| environment setup | fresh process lifecycle |
| failure distance | restart-delayed |
| statefulness | persistent filesystem |

このlabelは予想時間ではなく上記構造から決める。実測が長い・短いだけではsizeを変更しない。

## What this case can reveal

- first contract-valid artifactとuser-resultまでの差。
- public validation、hidden quality score、offline scoringの時間境界。
- bounded-implementationのL profileで、探索・生成・検証のどこが支配項になるか。

## Scope boundary

- provider/modelの総合rankingを作らない。
- この一件からfamily typical timeやmulti-agent routing ruleを作らない。
- fixture外の現行product behaviorを変更しない。

このcaseの結果は同じrevision/profileの観測であり、family全体、別stack、natural projectへ自動一般化しない。
