# F03-M-PY-001: profile and measurement question

## Scenario

An integration test observes expired jobs being retained. The symptom is in a scheduler, but the cause is a timezone-naive deserializer in another module and only appears after a serialize/reload cycle.

## Measurement question

How do reproduction cost and failure distance affect time to a defensible root cause and regression strategy?

| Axis | Value |
| --- | --- |
| case ID | `F03-M-PY-001` |
| family | `failing-test-diagnosis` |
| size | `M` |
| profile ID | `M-coupled-deterministic-diagnosis-python` |
| ambiguity | `bounded-open` |
| oracle | `deterministic` |
| decomposability | `partial` |
| artifact | `answer` |
| risk | `medium` |
| lane | `read` |
| environment | `local-tool` |
| knowledge | `repository-contained` |
| stack | `python, json` |

## Structural size evidence

| Descriptor | Designed value |
| --- | --- |
| context surface | scheduler, serializer, store, integration test |
| artifact surface | root-cause chain plus regression design |
| coupling | cross-module data contract |
| validation depth | unit, integration, reload |
| environment setup | temporary filesystem |
| failure distance | cross-module reload |
| statefulness | serialized job state |

このlabelは予想時間ではなく上記構造から決める。実測が長い・短いだけではsizeを変更しない。

## What this case can reveal

- first contract-valid artifactとuser-resultまでの差。
- public validation、hidden quality score、offline scoringの時間境界。
- failing-test-diagnosisのM profileで、探索・生成・検証のどこが支配項になるか。

## Scope boundary

- provider/modelの総合rankingを作らない。
- この一件からfamily typical timeやmulti-agent routing ruleを作らない。
- fixture外の現行product behaviorを変更しない。

このcaseの結果は同じrevision/profileの観測であり、family全体、別stack、natural projectへ自動一般化しない。
