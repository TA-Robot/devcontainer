# F07-S-MD-001: profile and measurement question

## Scenario

A CLI already supports `doctor --json --workspace PATH`, but its README shows an obsolete option order and omits the workspace-boundary constraint. The task is one accurate documentation patch.

## Measurement question

How do source-of-truth breadth and executable recovery obligations affect accurate documentation time?

| Axis | Value |
| --- | --- |
| case ID | `F07-S-MD-001` |
| family | `documentation-runbook` |
| size | `S` |
| profile ID | `S-local-executable-doc-markdown` |
| ambiguity | `exact` |
| oracle | `deterministic` |
| decomposability | `serial` |
| artifact | `runbook` |
| risk | `low` |
| lane | `write` |
| environment | `local-tool` |
| knowledge | `repository-contained` |
| stack | `markdown, python` |

## Structural size evidence

| Descriptor | Designed value |
| --- | --- |
| context surface | one CLI parser, README section, and smoke helper |
| artifact surface | one documentation section |
| coupling | local command contract |
| validation depth | link, command-replay, fact-check |
| environment setup | none |
| failure distance | direct |
| statefulness | stateless |

このlabelは予想時間ではなく上記構造から決める。実測が長い・短いだけではsizeを変更しない。

## What this case can reveal

- first contract-valid artifactとuser-resultまでの差。
- public validation、hidden quality score、offline scoringの時間境界。
- documentation-runbookのS profileで、探索・生成・検証のどこが支配項になるか。

## Scope boundary

- provider/modelの総合rankingを作らない。
- この一件からfamily typical timeやmulti-agent routing ruleを作らない。
- fixture外の現行product behaviorを変更しない。

このcaseの結果は同じrevision/profileの観測であり、family全体、別stack、natural projectへ自動一般化しない。
