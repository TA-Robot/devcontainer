# F07-M-MDBASH-001: profile and measurement question

## Scenario

Operators need a runbook for a corrupt JSON state file: detect without mutation, preserve evidence, recover from a verified backup, restart one owned service, and prove health. Commands must be replayable in a sandbox.

## Measurement question

How do source-of-truth breadth and executable recovery obligations affect accurate documentation time?

| Axis | Value |
| --- | --- |
| case ID | `F07-M-MDBASH-001` |
| family | `documentation-runbook` |
| size | `M` |
| profile ID | `M-coupled-replayable-runbook` |
| ambiguity | `bounded-open` |
| oracle | `deterministic` |
| decomposability | `partial` |
| artifact | `runbook` |
| risk | `medium` |
| lane | `write` |
| environment | `local-tool` |
| knowledge | `repository-contained` |
| stack | `markdown, bash, python, json` |

## Structural size evidence

| Descriptor | Designed value |
| --- | --- |
| context surface | state validator, backup/recovery scripts, service wrapper, existing docs |
| artifact surface | runbook plus structured command manifest |
| coupling | diagnosis and recovery ordering |
| validation depth | fact-check, command-replay, failure-replay, recovery |
| environment setup | temporary service sandbox |
| failure distance | multi-step failure path |
| statefulness | persistent state and backup |

このlabelは予想時間ではなく上記構造から決める。実測が長い・短いだけではsizeを変更しない。

## What this case can reveal

- first contract-valid artifactとuser-resultまでの差。
- public validation、hidden quality score、offline scoringの時間境界。
- documentation-runbookのM profileで、探索・生成・検証のどこが支配項になるか。

## Scope boundary

- provider/modelの総合rankingを作らない。
- この一件からfamily typical timeやmulti-agent routing ruleを作らない。
- fixture外の現行product behaviorを変更しない。

このcaseの結果は同じrevision/profileの観測であり、family全体、別stack、natural projectへ自動一般化しない。
