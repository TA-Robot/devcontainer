# F06-S-PY-001: profile and measurement question

## Scenario

A correct `parse_port` function has a precise type/range contract but only one happy-path test. The agent may add tests only; hidden calibration replaces production with plausible mutants.

## Measurement question

How do mutation surface and lifecycle nondeterminism affect time to a test suite that rejects known-bad behavior?

| Axis | Value |
| --- | --- |
| case ID | `F06-S-PY-001` |
| family | `test-design` |
| size | `S` |
| profile ID | `S-local-mutation-test-python` |
| ambiguity | `exact` |
| oracle | `deterministic` |
| decomposability | `serial` |
| artifact | `tests` |
| risk | `low` |
| lane | `write` |
| environment | `local-tool` |
| knowledge | `repository-contained` |
| stack | `python` |

## Structural size evidence

| Descriptor | Designed value |
| --- | --- |
| context surface | one Python function and test module |
| artifact surface | unit tests only |
| coupling | local behavior matrix |
| validation depth | unit, mutation |
| environment setup | none |
| failure distance | direct |
| statefulness | stateless |

このlabelは予想時間ではなく上記構造から決める。実測が長い・短いだけではsizeを変更しない。

## What this case can reveal

- first contract-valid artifactとuser-resultまでの差。
- public validation、hidden quality score、offline scoringの時間境界。
- test-designのS profileで、探索・生成・検証のどこが支配項になるか。

## Scope boundary

- provider/modelの総合rankingを作らない。
- この一件からfamily typical timeやmulti-agent routing ruleを作らない。
- fixture外の現行product behaviorを変更しない。

このcaseの結果は同じrevision/profileの観測であり、family全体、別stack、natural projectへ自動一般化しない。
