# F07-L-MDPYBASH-001: profile and measurement question

## Scenario

A backend migration needs synchronized architecture, migration, and recovery documents covering current state, compatibility layer, staged rollout, rollback, ownership, and operational boundaries across Python and Bash tools.

## Measurement question

How do source-of-truth breadth and executable recovery obligations affect accurate documentation time?

| Axis | Value |
| --- | --- |
| case ID | `F07-L-MDPYBASH-001` |
| family | `documentation-runbook` |
| size | `L` |
| profile ID | `L-cross-document-migration-runbook` |
| ambiguity | `bounded-open` |
| oracle | `structured` |
| decomposability | `partial` |
| artifact | `runbook` |
| risk | `high` |
| lane | `write` |
| environment | `local-tool` |
| knowledge | `repository-contained` |
| stack | `markdown, python, bash, json` |

## Structural size evidence

| Descriptor | Designed value |
| --- | --- |
| context surface | implementation sources, three documentation targets, command tooling |
| artifact surface | multi-document set plus index manifest |
| coupling | cross-document lifecycle consistency |
| validation depth | fact-check, link, command-replay, migration, rollback |
| environment setup | simulated migration sandbox |
| failure distance | rollback/restart-delayed |
| statefulness | versioned persistent state |

このlabelは予想時間ではなく上記構造から決める。実測が長い・短いだけではsizeを変更しない。

## What this case can reveal

- first contract-valid artifactとuser-resultまでの差。
- public validation、hidden quality score、offline scoringの時間境界。
- documentation-runbookのL profileで、探索・生成・検証のどこが支配項になるか。

## Scope boundary

- provider/modelの総合rankingを作らない。
- この一件からfamily typical timeやmulti-agent routing ruleを作らない。
- fixture外の現行product behaviorを変更しない。

このcaseの結果は同じrevision/profileの観測であり、family全体、別stack、natural projectへ自動一般化しない。
