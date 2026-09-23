# F03-S-PY-001: profile and measurement question

## Scenario

One unit test fails because a parser treats explicit zero as a missing value through a truthiness fallback. The task is diagnosis and regression-test design, not repair.

## Measurement question

How do reproduction cost and failure distance affect time to a defensible root cause and regression strategy?

| Axis | Value |
| --- | --- |
| case ID | `F03-S-PY-001` |
| family | `failing-test-diagnosis` |
| size | `S` |
| profile ID | `S-local-deterministic-diagnosis-python` |
| ambiguity | `exact` |
| oracle | `deterministic` |
| decomposability | `serial` |
| artifact | `answer` |
| risk | `low` |
| lane | `read` |
| environment | `local-tool` |
| knowledge | `repository-contained` |
| stack | `python, json` |

## Structural size evidence

| Descriptor | Designed value |
| --- | --- |
| context surface | one Python module and one failing test |
| artifact surface | structured diagnosis |
| coupling | local expression |
| validation depth | failing-test, gold-root-cause |
| environment setup | none |
| failure distance | direct |
| statefulness | stateless |

このlabelは予想時間ではなく上記構造から決める。実測が長い・短いだけではsizeを変更しない。

## What this case can reveal

- first contract-valid artifactとuser-resultまでの差。
- public validation、hidden quality score、offline scoringの時間境界。
- failing-test-diagnosisのS profileで、探索・生成・検証のどこが支配項になるか。

## Scope boundary

- provider/modelの総合rankingを作らない。
- この一件からfamily typical timeやmulti-agent routing ruleを作らない。
- fixture外の現行product behaviorを変更しない。

このcaseの結果は同じrevision/profileの観測であり、family全体、別stack、natural projectへ自動一般化しない。
