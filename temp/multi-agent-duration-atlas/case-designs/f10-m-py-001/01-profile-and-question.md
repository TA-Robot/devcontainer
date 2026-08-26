# F10-M-PY-001: profile and measurement question

## Scenario

An event summarizer repeatedly reads the same ledger, decodes each line twice, and misses a valid per-file cache due to keying on a mutable path object. The agent must instrument I/O, serialization, and cache behavior and compare hypotheses.

## Measurement question

How do instrumentation breadth and measurement noise affect time to a reproducible bottleneck diagnosis?

| Axis | Value |
| --- | --- |
| case ID | `F10-M-PY-001` |
| family | `performance-resource` |
| size | `M` |
| profile ID | `M-coupled-instrumented-performance-python` |
| ambiguity | `bounded-open` |
| oracle | `deterministic` |
| decomposability | `partial` |
| artifact | `synthesis` |
| risk | `medium` |
| lane | `isolated` |
| environment | `local-tool` |
| knowledge | `repository-contained` |
| stack | `python, json` |

## Structural size evidence

| Descriptor | Designed value |
| --- | --- |
| context surface | reader, decoder, cache, benchmark/report modules |
| artifact surface | instrumentation plus experiment report |
| coupling | I/O/cache/serialization interaction |
| validation depth | unit, instrumentation, benchmark-distribution |
| environment setup | temporary ledger files |
| failure distance | cross-module |
| statefulness | file cache state |

このlabelは予想時間ではなく上記構造から決める。実測が長い・短いだけではsizeを変更しない。

## What this case can reveal

- first contract-valid artifactとuser-resultまでの差。
- public validation、hidden quality score、offline scoringの時間境界。
- performance-resourceのM profileで、探索・生成・検証のどこが支配項になるか。

## Scope boundary

- provider/modelの総合rankingを作らない。
- この一件からfamily typical timeやmulti-agent routing ruleを作らない。
- fixture外の現行product behaviorを変更しない。

このcaseの結果は同じrevision/profileの観測であり、family全体、別stack、natural projectへ自動一般化しない。
