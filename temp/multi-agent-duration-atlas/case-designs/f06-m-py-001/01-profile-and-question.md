# F06-M-PY-001: profile and measurement question

## Scenario

A retry policy depends on HTTP status, method idempotency, attempt number, and server delay. The agent must design table/property-style tests that kill interacting policy mutants without changing production.

## Measurement question

How do mutation surface and lifecycle nondeterminism affect time to a test suite that rejects known-bad behavior?

| Axis | Value |
| --- | --- |
| case ID | `F06-M-PY-001` |
| family | `test-design` |
| size | `M` |
| profile ID | `M-coupled-mutation-test-python` |
| ambiguity | `bounded-open` |
| oracle | `deterministic` |
| decomposability | `partial` |
| artifact | `tests` |
| risk | `low` |
| lane | `write` |
| environment | `local-tool` |
| knowledge | `repository-contained` |
| stack | `python` |

## Structural size evidence

| Descriptor | Designed value |
| --- | --- |
| context surface | policy module, clock abstraction, test harness |
| artifact surface | table/property test suite |
| coupling | four-axis decision contract |
| validation depth | unit, table, mutation |
| environment setup | fake clock |
| failure distance | interaction-only |
| statefulness | attempt counter state |

このlabelは予想時間ではなく上記構造から決める。実測が長い・短いだけではsizeを変更しない。

## What this case can reveal

- first contract-valid artifactとuser-resultまでの差。
- public validation、hidden quality score、offline scoringの時間境界。
- test-designのM profileで、探索・生成・検証のどこが支配項になるか。

## Scope boundary

- provider/modelの総合rankingを作らない。
- この一件からfamily typical timeやmulti-agent routing ruleを作らない。
- fixture外の現行product behaviorを変更しない。

このcaseの結果は同じrevision/profileの観測であり、family全体、別stack、natural projectへ自動一般化しない。
