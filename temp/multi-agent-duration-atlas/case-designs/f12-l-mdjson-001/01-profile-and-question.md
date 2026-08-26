# F12-L-MDJSON-001: profile and measurement question

## Scenario

Four execution-fabric proposals, benchmark distributions, two incident reports, security findings, and migration constraints must be integrated into a design decision record. Evidence conflicts by workload and confidence, so no proposal wins every axis.

## Measurement question

How do claim count, contradiction, and evidence quality affect time to a supported decision record?

| Axis | Value |
| --- | --- |
| case ID | `F12-L-MDJSON-001` |
| family | `evidence-synthesis` |
| size | `L` |
| profile ID | `L-cross-evidence-decision-record` |
| ambiguity | `open` |
| oracle | `calibrated` |
| decomposability | `independent` |
| artifact | `synthesis` |
| risk | `high` |
| lane | `read` |
| environment | `local-tool` |
| knowledge | `repository-contained` |
| stack | `markdown, json, python` |

## Structural size evidence

| Descriptor | Designed value |
| --- | --- |
| context surface | four proposals, metrics, incidents, security/migration evidence |
| artifact surface | decision record and claim/evidence graph |
| coupling | multi-source tradeoff and conflict resolution |
| validation depth | schema, entailment, distribution, incident, security, migration, counterfactual |
| environment setup | deterministic evidence query tools |
| failure distance | cross-source and incident-delayed |
| statefulness | versioned proposal/evidence ledger |

このlabelは予想時間ではなく上記構造から決める。実測が長い・短いだけではsizeを変更しない。

## What this case can reveal

- first contract-valid artifactとuser-resultまでの差。
- public validation、hidden quality score、offline scoringの時間境界。
- evidence-synthesisのL profileで、探索・生成・検証のどこが支配項になるか。

## Scope boundary

- provider/modelの総合rankingを作らない。
- この一件からfamily typical timeやmulti-agent routing ruleを作らない。
- fixture外の現行product behaviorを変更しない。

このcaseの結果は同じrevision/profileの観測であり、family全体、別stack、natural projectへ自動一般化しない。
