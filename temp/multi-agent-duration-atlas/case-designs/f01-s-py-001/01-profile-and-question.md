# F01-S-PY-001: profile and measurement question

## Scenario

A small Python CLI defines `--state-dir`, normalizes it, validates its ownership marker, and passes it to one command. The agent must trace the exact definition-to-validation path without changing code.

## Measurement question

How long does evidence-backed repository tracing take as the required path crosses more contracts and runtimes?

| Axis | Value |
| --- | --- |
| case ID | `F01-S-PY-001` |
| family | `repository-trace` |
| size | `S` |
| profile ID | `S-local-gold-trace-python` |
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
| context surface | two Python modules and one test |
| artifact surface | one structured trace plus evidence |
| coupling | local call chain |
| validation depth | schema, gold-trace |
| environment setup | none |
| failure distance | direct |
| statefulness | read-only filesystem semantics |

このlabelは予想時間ではなく上記構造から決める。実測が長い・短いだけではsizeを変更しない。

## What this case can reveal

- first contract-valid artifactとuser-resultまでの差。
- public validation、hidden quality score、offline scoringの時間境界。
- repository-traceのS profileで、探索・生成・検証のどこが支配項になるか。

## Scope boundary

- provider/modelの総合rankingを作らない。
- この一件からfamily typical timeやmulti-agent routing ruleを作らない。
- fixture外の現行product behaviorを変更しない。

このcaseの結果は同じrevision/profileの観測であり、family全体、別stack、natural projectへ自動一般化しない。
