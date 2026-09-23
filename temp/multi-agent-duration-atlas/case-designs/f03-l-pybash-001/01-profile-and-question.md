# F03-L-PYBASH-001: profile and measurement question

## Scenario

A Bash lifecycle test intermittently reports duplicate delivery after a worker crash. The deterministic trigger requires a process boundary, an acknowledgement journal, forced termination, restart, and replay.

## Measurement question

How do reproduction cost and failure distance affect time to a defensible root cause and regression strategy?

| Axis | Value |
| --- | --- |
| case ID | `F03-L-PYBASH-001` |
| family | `failing-test-diagnosis` |
| size | `L` |
| profile ID | `L-cross-process-restart-diagnosis` |
| ambiguity | `bounded-open` |
| oracle | `deterministic` |
| decomposability | `partial` |
| artifact | `tests` |
| risk | `high` |
| lane | `read` |
| environment | `local-tool` |
| knowledge | `repository-contained` |
| stack | `python, bash, json` |

## Structural size evidence

| Descriptor | Designed value |
| --- | --- |
| context surface | Python worker/store plus Bash crash/restart harness |
| artifact surface | diagnosis, deterministic reproducer, regression harness |
| coupling | cross-process journal ordering |
| validation depth | unit, integration, crash, restart, repeat |
| environment setup | fresh subprocess lifecycle |
| failure distance | restart-delayed |
| statefulness | persistent acknowledgement journal |

このlabelは予想時間ではなく上記構造から決める。実測が長い・短いだけではsizeを変更しない。

## What this case can reveal

- first contract-valid artifactとuser-resultまでの差。
- public validation、hidden quality score、offline scoringの時間境界。
- failing-test-diagnosisのL profileで、探索・生成・検証のどこが支配項になるか。

## Scope boundary

- provider/modelの総合rankingを作らない。
- この一件からfamily typical timeやmulti-agent routing ruleを作らない。
- fixture外の現行product behaviorを変更しない。

このcaseの結果は同じrevision/profileの観測であり、family全体、別stack、natural projectへ自動一般化しない。
