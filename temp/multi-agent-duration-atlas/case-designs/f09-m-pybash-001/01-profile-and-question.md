# F09-M-PYBASH-001: profile and measurement question

## Scenario

Workspace isolation combines a Python path resolver, a Bash environment override, and symlink-capable temporary directories. Three individually plausible controls compose into two seeded escapes.

## Measurement question

How do adversarial combinations and environment boundaries affect time to identify and prove isolation failures?

| Axis | Value |
| --- | --- |
| case ID | `F09-M-PYBASH-001` |
| family | `security-isolation` |
| size | `M` |
| profile ID | `M-coupled-seeded-isolation-review` |
| ambiguity | `bounded-open` |
| oracle | `deterministic` |
| decomposability | `partial` |
| artifact | `findings` |
| risk | `high` |
| lane | `isolated` |
| environment | `local-tool` |
| knowledge | `repository-contained` |
| stack | `python, bash` |

## Structural size evidence

| Descriptor | Designed value |
| --- | --- |
| context surface | Python resolver, Bash launcher, filesystem fixtures |
| artifact surface | review plus exploit tests |
| coupling | symlink/environment/containment composition |
| validation depth | unit, integration, seeded-exploit, negative-test |
| environment setup | temporary filesystem and subprocess |
| failure distance | cross-boundary |
| statefulness | filesystem and environment state |

このlabelは予想時間ではなく上記構造から決める。実測が長い・短いだけではsizeを変更しない。

## What this case can reveal

- first contract-valid artifactとuser-resultまでの差。
- public validation、hidden quality score、offline scoringの時間境界。
- security-isolationのM profileで、探索・生成・検証のどこが支配項になるか。

## Scope boundary

- provider/modelの総合rankingを作らない。
- この一件からfamily typical timeやmulti-agent routing ruleを作らない。
- fixture外の現行product behaviorを変更しない。

このcaseの結果は同じrevision/profileの観測であり、family全体、別stack、natural projectへ自動一般化しない。
