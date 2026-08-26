# F08-S-MDJSON-001: profile and measurement question

## Scenario

Two local APIs are proposed for merging layered configuration: `merge(base, override)` and a stateful `ConfigBuilder`. The fixture supplies exact call patterns and five constraints; the agent must choose or conditionally choose with a counterexample.

## Measurement question

How do ambiguity, constraint breadth, and counterexamples affect time and coverage of a design decision?

| Axis | Value |
| --- | --- |
| case ID | `F08-S-MDJSON-001` |
| family | `architecture-design` |
| size | `S` |
| profile ID | `S-local-constraint-design` |
| ambiguity | `bounded-open` |
| oracle | `structured` |
| decomposability | `serial` |
| artifact | `design` |
| risk | `low` |
| lane | `read` |
| environment | `local-tool` |
| knowledge | `repository-contained` |
| stack | `markdown, json, python` |

## Structural size evidence

| Descriptor | Designed value |
| --- | --- |
| context surface | two API sketches, call-site examples, constraint list |
| artifact surface | decision note and structured rationale |
| coupling | local API/constraint fit |
| validation depth | schema, constraint, counterexample |
| environment setup | none |
| failure distance | design-time |
| statefulness | configuration layering |

このlabelは予想時間ではなく上記構造から決める。実測が長い・短いだけではsizeを変更しない。

## What this case can reveal

- first contract-valid artifactとuser-resultまでの差。
- public validation、hidden quality score、offline scoringの時間境界。
- architecture-designのS profileで、探索・生成・検証のどこが支配項になるか。

## Scope boundary

- provider/modelの総合rankingを作らない。
- この一件からfamily typical timeやmulti-agent routing ruleを作らない。
- fixture外の現行product behaviorを変更しない。

このcaseの結果は同じrevision/profileの観測であり、family全体、別stack、natural projectへ自動一般化しない。
