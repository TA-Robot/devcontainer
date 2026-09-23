# F01-M-PYJS-001: profile and measurement question

## Scenario

A hook event enters a Python adapter, is reduced into an atomic state file, then is consumed by a JavaScript world renderer. The required trace crosses modules and a file-format boundary.

## Measurement question

How long does evidence-backed repository tracing take as the required path crosses more contracts and runtimes?

| Axis | Value |
| --- | --- |
| case ID | `F01-M-PYJS-001` |
| family | `repository-trace` |
| size | `M` |
| profile ID | `M-coupled-gold-trace-python-js` |
| ambiguity | `bounded-open` |
| oracle | `deterministic` |
| decomposability | `partial` |
| artifact | `answer` |
| risk | `low` |
| lane | `read` |
| environment | `local-tool` |
| knowledge | `repository-contained` |
| stack | `python, javascript, json` |

## Structural size evidence

| Descriptor | Designed value |
| --- | --- |
| context surface | four Python modules, state schema, and two JS modules |
| artifact surface | trace graph with success and fail-open branches |
| coupling | cross-module producer/consumer contract |
| validation depth | schema, gold-trace, branch-coverage |
| environment setup | local subprocess |
| failure distance | cross-language |
| statefulness | atomic JSON state |

このlabelは予想時間ではなく上記構造から決める。実測が長い・短いだけではsizeを変更しない。

## What this case can reveal

- first contract-valid artifactとuser-resultまでの差。
- public validation、hidden quality score、offline scoringの時間境界。
- repository-traceのM profileで、探索・生成・検証のどこが支配項になるか。

## Scope boundary

- provider/modelの総合rankingを作らない。
- この一件からfamily typical timeやmulti-agent routing ruleを作らない。
- fixture外の現行product behaviorを変更しない。

このcaseの結果は同じrevision/profileの観測であり、family全体、別stack、natural projectへ自動一般化しない。
