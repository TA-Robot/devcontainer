# F09-S-PY-001: profile and measurement question

## Scenario

A name validator rejects slashes before percent-decoding, then uses the decoded value as a directory name. The task is to find the bypass and add a negative test, without implementing a fix.

## Measurement question

How do adversarial combinations and environment boundaries affect time to identify and prove isolation failures?

| Axis | Value |
| --- | --- |
| case ID | `F09-S-PY-001` |
| family | `security-isolation` |
| size | `S` |
| profile ID | `S-local-seeded-bypass-python` |
| ambiguity | `bounded-open` |
| oracle | `deterministic` |
| decomposability | `serial` |
| artifact | `findings` |
| risk | `high` |
| lane | `isolated` |
| environment | `local-tool` |
| knowledge | `repository-contained` |
| stack | `python` |

## Structural size evidence

| Descriptor | Designed value |
| --- | --- |
| context surface | one validator, one decoder caller, tests |
| artifact surface | finding plus negative test |
| coupling | validation/normalization order |
| validation depth | unit, seeded-exploit |
| environment setup | temporary filesystem |
| failure distance | direct bypass |
| statefulness | path state |

このlabelは予想時間ではなく上記構造から決める。実測が長い・短いだけではsizeを変更しない。

## What this case can reveal

- first contract-valid artifactとuser-resultまでの差。
- public validation、hidden quality score、offline scoringの時間境界。
- security-isolationのS profileで、探索・生成・検証のどこが支配項になるか。

## Scope boundary

- provider/modelの総合rankingを作らない。
- この一件からfamily typical timeやmulti-agent routing ruleを作らない。
- fixture外の現行product behaviorを変更しない。

このcaseの結果は同じrevision/profileの観測であり、family全体、別stack、natural projectへ自動一般化しない。
