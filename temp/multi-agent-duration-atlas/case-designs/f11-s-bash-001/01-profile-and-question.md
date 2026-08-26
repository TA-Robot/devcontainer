# F11-S-BASH-001: profile and measurement question

## Scenario

A short version-sync shell script has a missing `;;` in one `case` arm and therefore fails static parsing before any side effect. The task is a minimal syntax repair and smoke validation.

## Measurement question

How do lifecycle boundaries, persistent state, and recovery obligations affect operational change time?

| Axis | Value |
| --- | --- |
| case ID | `F11-S-BASH-001` |
| family | `devcontainer-operations` |
| size | `S` |
| profile ID | `S-local-static-operations-bash` |
| ambiguity | `exact` |
| oracle | `deterministic` |
| decomposability | `serial` |
| artifact | `patch` |
| risk | `low` |
| lane | `write` |
| environment | `local-tool` |
| knowledge | `repository-contained` |
| stack | `bash` |

## Structural size evidence

| Descriptor | Designed value |
| --- | --- |
| context surface | one Bash script and smoke test |
| artifact surface | minimal patch |
| coupling | local syntax |
| validation depth | bash-static, smoke |
| environment setup | none |
| failure distance | parse-time |
| statefulness | stateless |

このlabelは予想時間ではなく上記構造から決める。実測が長い・短いだけではsizeを変更しない。

## What this case can reveal

- first contract-valid artifactとuser-resultまでの差。
- public validation、hidden quality score、offline scoringの時間境界。
- devcontainer-operationsのS profileで、探索・生成・検証のどこが支配項になるか。

## Scope boundary

- provider/modelの総合rankingを作らない。
- この一件からfamily typical timeやmulti-agent routing ruleを作らない。
- fixture外の現行product behaviorを変更しない。

このcaseの結果は同じrevision/profileの観測であり、family全体、別stack、natural projectへ自動一般化しない。
