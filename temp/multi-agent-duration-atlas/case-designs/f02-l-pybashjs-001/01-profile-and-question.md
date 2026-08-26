# F02-L-PYBASHJS-001: profile and measurement question

## Scenario

A proposed provider-hook feature crosses a Bash wrapper, Python redaction/persistence, JavaScript rendering, and container cleanup. Three lifecycle defects are seeded across normal, error, and restart paths.

## Measurement question

How do diff surface and hidden lifecycle interactions affect review time and seeded-finding quality?

| Axis | Value |
| --- | --- |
| case ID | `F02-L-PYBASHJS-001` |
| family | `code-review` |
| size | `L` |
| profile ID | `L-cross-boundary-lifecycle-review` |
| ambiguity | `bounded-open` |
| oracle | `structured` |
| decomposability | `independent` |
| artifact | `findings` |
| risk | `high` |
| lane | `read` |
| environment | `local-tool` |
| knowledge | `repository-contained` |
| stack | `bash, python, javascript, docker, json` |

## Structural size evidence

| Descriptor | Designed value |
| --- | --- |
| context surface | Bash wrapper, Python adapter/store, JS extension, container lifecycle diff |
| artifact surface | ranked findings with lifecycle evidence |
| coupling | cross-language lifecycle and cleanup |
| validation depth | schema, seeded-defect, lifecycle-replay, restart |
| environment setup | simulated container lifecycle |
| failure distance | restart-delayed |
| statefulness | persistent state and cleanup ownership |

このlabelは予想時間ではなく上記構造から決める。実測が長い・短いだけではsizeを変更しない。

## What this case can reveal

- first contract-valid artifactとuser-resultまでの差。
- public validation、hidden quality score、offline scoringの時間境界。
- code-reviewのL profileで、探索・生成・検証のどこが支配項になるか。

## Scope boundary

- provider/modelの総合rankingを作らない。
- この一件からfamily typical timeやmulti-agent routing ruleを作らない。
- fixture外の現行product behaviorを変更しない。

このcaseの結果は同じrevision/profileの観測であり、family全体、別stack、natural projectへ自動一般化しない。
