# F09-L-PYBASHDOCKER-001: profile and measurement question

## Scenario

A multi-agent worktree/container system exposes Git worktree naming, Docker bind construction, provider credentials, process/resource cleanup, and recovery ownership. The task creates an evidence-linked threat model and negative tests for seeded attack paths.

## Measurement question

How do adversarial combinations and environment boundaries affect time to identify and prove isolation failures?

| Axis | Value |
| --- | --- |
| case ID | `F09-L-PYBASHDOCKER-001` |
| family | `security-isolation` |
| size | `L` |
| profile ID | `L-cross-boundary-threat-model` |
| ambiguity | `open` |
| oracle | `calibrated` |
| decomposability | `independent` |
| artifact | `design` |
| risk | `high` |
| lane | `isolated` |
| environment | `local-tool` |
| knowledge | `repository-contained` |
| stack | `python, bash, docker, git, json, markdown` |

## Structural size evidence

| Descriptor | Designed value |
| --- | --- |
| context surface | Git/worktree Python, Bash Docker launcher, credential adapter, cleanup supervisor |
| artifact surface | threat model, attack trees, negative test plan |
| coupling | multi-boundary trust and lifecycle ownership |
| validation depth | schema, seeded-exploit, negative-test, threat, cleanup, recovery |
| environment setup | simulated Docker/Git/process environment |
| failure distance | cross-boundary and cleanup-delayed |
| statefulness | worktrees, containers, credentials, PIDs |

このlabelは予想時間ではなく上記構造から決める。実測が長い・短いだけではsizeを変更しない。

## What this case can reveal

- first contract-valid artifactとuser-resultまでの差。
- public validation、hidden quality score、offline scoringの時間境界。
- security-isolationのL profileで、探索・生成・検証のどこが支配項になるか。

## Scope boundary

- provider/modelの総合rankingを作らない。
- この一件からfamily typical timeやmulti-agent routing ruleを作らない。
- fixture外の現行product behaviorを変更しない。

このcaseの結果は同じrevision/profileの観測であり、family全体、別stack、natural projectへ自動一般化しない。
