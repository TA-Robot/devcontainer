# F02-M-PY-001: profile and measurement question

## Scenario

A multi-file change validates a workspace path before symlink resolution and changes cleanup ownership from generated IDs to caller-supplied labels. Two defects interact across modules.

## Measurement question

How do diff surface and hidden lifecycle interactions affect review time and seeded-finding quality?

| Axis | Value |
| --- | --- |
| case ID | `F02-M-PY-001` |
| family | `code-review` |
| size | `M` |
| profile ID | `M-coupled-seeded-review-python` |
| ambiguity | `bounded-open` |
| oracle | `deterministic` |
| decomposability | `partial` |
| artifact | `findings` |
| risk | `high` |
| lane | `read` |
| environment | `local-tool` |
| knowledge | `repository-contained` |
| stack | `python, json` |

## Structural size evidence

| Descriptor | Designed value |
| --- | --- |
| context surface | four Python modules and multi-file diff |
| artifact surface | ranked multi-finding review |
| coupling | filesystem and cleanup contract interaction |
| validation depth | schema, seeded-defect, exploit-replay |
| environment setup | temporary filesystem |
| failure distance | cross-module |
| statefulness | filesystem ownership state |

このlabelは予想時間ではなく上記構造から決める。実測が長い・短いだけではsizeを変更しない。

## What this case can reveal

- first contract-valid artifactとuser-resultまでの差。
- public validation、hidden quality score、offline scoringの時間境界。
- code-reviewのM profileで、探索・生成・検証のどこが支配項になるか。

## Scope boundary

- provider/modelの総合rankingを作らない。
- この一件からfamily typical timeやmulti-agent routing ruleを作らない。
- fixture外の現行product behaviorを変更しない。

このcaseの結果は同じrevision/profileの観測であり、family全体、別stack、natural projectへ自動一般化しない。
