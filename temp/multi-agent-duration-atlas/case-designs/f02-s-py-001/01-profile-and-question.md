# F02-S-PY-001: profile and measurement question

## Scenario

A six-line change replaces canonical path containment with a string-prefix check. The reviewer must identify one traversal/peer-prefix defect in a small Python diff and avoid findings on unchanged safe code.

## Measurement question

How do diff surface and hidden lifecycle interactions affect review time and seeded-finding quality?

| Axis | Value |
| --- | --- |
| case ID | `F02-S-PY-001` |
| family | `code-review` |
| size | `S` |
| profile ID | `S-local-seeded-review-python` |
| ambiguity | `exact` |
| oracle | `deterministic` |
| decomposability | `serial` |
| artifact | `findings` |
| risk | `low` |
| lane | `read` |
| environment | `local-tool` |
| knowledge | `repository-contained` |
| stack | `python, json` |

## Structural size evidence

| Descriptor | Designed value |
| --- | --- |
| context surface | one Python diff and helper |
| artifact surface | structured review finding |
| coupling | local validation |
| validation depth | schema, seeded-defect |
| environment setup | none |
| failure distance | direct exploit |
| statefulness | stateless |

このlabelは予想時間ではなく上記構造から決める。実測が長い・短いだけではsizeを変更しない。

## What this case can reveal

- first contract-valid artifactとuser-resultまでの差。
- public validation、hidden quality score、offline scoringの時間境界。
- code-reviewのS profileで、探索・生成・検証のどこが支配項になるか。

## Scope boundary

- provider/modelの総合rankingを作らない。
- この一件からfamily typical timeやmulti-agent routing ruleを作らない。
- fixture外の現行product behaviorを変更しない。

このcaseの結果は同じrevision/profileの観測であり、family全体、別stack、natural projectへ自動一般化しない。
