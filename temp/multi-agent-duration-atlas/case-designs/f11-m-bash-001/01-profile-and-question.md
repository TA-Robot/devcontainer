# F11-M-BASH-001: profile and measurement question

## Scenario

A post-start hook compares host and container CLI versions. Host metadata may contain CRLF/trailing whitespace; raw comparison causes endless reinstall attempts and a stale ready marker across restarts.

## Measurement question

How do lifecycle boundaries, persistent state, and recovery obligations affect operational change time?

| Axis | Value |
| --- | --- |
| case ID | `F11-M-BASH-001` |
| family | `devcontainer-operations` |
| size | `M` |
| profile ID | `M-coupled-lifecycle-operations-bash` |
| ambiguity | `bounded-open` |
| oracle | `deterministic` |
| decomposability | `partial` |
| artifact | `patch` |
| risk | `medium` |
| lane | `write` |
| environment | `local-tool` |
| knowledge | `repository-contained` |
| stack | `bash, json` |

## Structural size evidence

| Descriptor | Designed value |
| --- | --- |
| context surface | initialize metadata, post-start hook, installer, lifecycle tests |
| artifact surface | Bash patch plus recovery evidence |
| coupling | host/container version and ready-marker contract |
| validation depth | static, unit, restart, lifecycle-smoke |
| environment setup | fresh subprocess lifecycle |
| failure distance | post-start/restart |
| statefulness | persistent version/ready markers |

このlabelは予想時間ではなく上記構造から決める。実測が長い・短いだけではsizeを変更しない。

## What this case can reveal

- first contract-valid artifactとuser-resultまでの差。
- public validation、hidden quality score、offline scoringの時間境界。
- devcontainer-operationsのM profileで、探索・生成・検証のどこが支配項になるか。

## Scope boundary

- provider/modelの総合rankingを作らない。
- この一件からfamily typical timeやmulti-agent routing ruleを作らない。
- fixture外の現行product behaviorを変更しない。

このcaseの結果は同じrevision/profileの観測であり、family全体、別stack、natural projectへ自動一般化しない。
