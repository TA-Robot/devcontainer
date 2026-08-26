# F06-L-PYBASH-001: profile and measurement question

## Scenario

A lease-based worker has concurrency, crash, restart, and cleanup contracts. The agent must add a deterministic Python/Bash integration harness that rejects lost-wakeup, stale-lock, duplicate-owner, and broad-cleanup mutants.

## Measurement question

How do mutation surface and lifecycle nondeterminism affect time to a test suite that rejects known-bad behavior?

| Axis | Value |
| --- | --- |
| case ID | `F06-L-PYBASH-001` |
| family | `test-design` |
| size | `L` |
| profile ID | `L-cross-process-lifecycle-test-design` |
| ambiguity | `bounded-open` |
| oracle | `deterministic` |
| decomposability | `independent` |
| artifact | `tests` |
| risk | `high` |
| lane | `write` |
| environment | `local-tool` |
| knowledge | `repository-contained` |
| stack | `python, bash, json` |

## Structural size evidence

| Descriptor | Designed value |
| --- | --- |
| context surface | Python worker/lease store, Bash process harness, integration tests |
| artifact surface | lifecycle integration suite |
| coupling | concurrency and restart ownership |
| validation depth | unit, integration, concurrency, crash, restart, mutation |
| environment setup | multiple fresh subprocesses |
| failure distance | race/restart-delayed |
| statefulness | lease and process state |

このlabelは予想時間ではなく上記構造から決める。実測が長い・短いだけではsizeを変更しない。

## What this case can reveal

- first contract-valid artifactとuser-resultまでの差。
- public validation、hidden quality score、offline scoringの時間境界。
- test-designのL profileで、探索・生成・検証のどこが支配項になるか。

## Scope boundary

- provider/modelの総合rankingを作らない。
- この一件からfamily typical timeやmulti-agent routing ruleを作らない。
- fixture外の現行product behaviorを変更しない。

このcaseの結果は同じrevision/profileの観測であり、family全体、別stack、natural projectへ自動一般化しない。
