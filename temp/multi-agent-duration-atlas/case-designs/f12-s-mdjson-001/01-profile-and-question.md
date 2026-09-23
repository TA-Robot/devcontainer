# F12-S-MDJSON-001: profile and measurement question

## Scenario

Two short analyses assess the same wrapper change. They agree on one fact, disagree on whether an environment override is active, and cite different source snippets. The agent must synthesize without resolving beyond evidence.

## Measurement question

How do claim count, contradiction, and evidence quality affect time to a supported decision record?

| Axis | Value |
| --- | --- |
| case ID | `F12-S-MDJSON-001` |
| family | `evidence-synthesis` |
| size | `S` |
| profile ID | `S-local-entailment-synthesis` |
| ambiguity | `exact` |
| oracle | `deterministic` |
| decomposability | `serial` |
| artifact | `synthesis` |
| risk | `low` |
| lane | `read` |
| environment | `local-tool` |
| knowledge | `repository-contained` |
| stack | `markdown, json, bash` |

## Structural size evidence

| Descriptor | Designed value |
| --- | --- |
| context surface | two analyses and three source snippets |
| artifact surface | structured synthesis and short note |
| coupling | claim/evidence reconciliation |
| validation depth | schema, entailment, conflict |
| environment setup | none |
| failure distance | direct evidence |
| statefulness | stateless |

このlabelは予想時間ではなく上記構造から決める。実測が長い・短いだけではsizeを変更しない。

## What this case can reveal

- first contract-valid artifactとuser-resultまでの差。
- public validation、hidden quality score、offline scoringの時間境界。
- evidence-synthesisのS profileで、探索・生成・検証のどこが支配項になるか。

## Scope boundary

- provider/modelの総合rankingを作らない。
- この一件からfamily typical timeやmulti-agent routing ruleを作らない。
- fixture外の現行product behaviorを変更しない。

このcaseの結果は同じrevision/profileの観測であり、family全体、別stack、natural projectへ自動一般化しない。
