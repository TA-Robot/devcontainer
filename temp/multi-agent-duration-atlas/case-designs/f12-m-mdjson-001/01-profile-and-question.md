# F12-M-MDJSON-001: profile and measurement question

## Scenario

Three independent reviews disagree about a symlink-isolation patch. Public/hidden test transcripts, source, and an exploit replay support some findings, refute others, and leave one platform assumption unresolved.

## Measurement question

How do claim count, contradiction, and evidence quality affect time to a supported decision record?

| Axis | Value |
| --- | --- |
| case ID | `F12-M-MDJSON-001` |
| family | `evidence-synthesis` |
| size | `M` |
| profile ID | `M-coupled-calibrated-adjudication` |
| ambiguity | `bounded-open` |
| oracle | `calibrated` |
| decomposability | `independent` |
| artifact | `synthesis` |
| risk | `high` |
| lane | `read` |
| environment | `local-tool` |
| knowledge | `repository-contained` |
| stack | `markdown, json, python, bash` |

## Structural size evidence

| Descriptor | Designed value |
| --- | --- |
| context surface | three reviews, source diff, test/exploit evidence |
| artifact surface | adjudication record |
| coupling | conflicting claims and evidence strength |
| validation depth | schema, entailment, test-replay, conflict |
| environment setup | temporary filesystem replay |
| failure distance | cross-source |
| statefulness | filesystem semantics |

このlabelは予想時間ではなく上記構造から決める。実測が長い・短いだけではsizeを変更しない。

## What this case can reveal

- first contract-valid artifactとuser-resultまでの差。
- public validation、hidden quality score、offline scoringの時間境界。
- evidence-synthesisのM profileで、探索・生成・検証のどこが支配項になるか。

## Scope boundary

- provider/modelの総合rankingを作らない。
- この一件からfamily typical timeやmulti-agent routing ruleを作らない。
- fixture外の現行product behaviorを変更しない。

このcaseの結果は同じrevision/profileの観測であり、family全体、別stack、natural projectへ自動一般化しない。
