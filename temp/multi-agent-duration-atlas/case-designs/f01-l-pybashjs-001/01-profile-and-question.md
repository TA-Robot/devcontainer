# F01-L-PYBASHJS-001: profile and measurement question

## Scenario

A devcontainer lifecycle installs host-sourced wrappers, starts `agentctl`, receives provider activity, persists companion state, and renders a VS Code world. The trace must label host/container/extension trust boundaries and recovery edges.

## Measurement question

How long does evidence-backed repository tracing take as the required path crosses more contracts and runtimes?

| Axis | Value |
| --- | --- |
| case ID | `F01-L-PYBASHJS-001` |
| family | `repository-trace` |
| size | `L` |
| profile ID | `L-cross-boundary-structured-trace-devcontainer` |
| ambiguity | `bounded-open` |
| oracle | `structured` |
| decomposability | `partial` |
| artifact | `answer` |
| risk | `medium` |
| lane | `read` |
| environment | `local-tool` |
| knowledge | `repository-contained` |
| stack | `docker, bash, python, javascript, json` |

## Structural size evidence

| Descriptor | Designed value |
| --- | --- |
| context surface | devcontainer JSON/Dockerfile, Bash lifecycle, Python control plane/hook, JS extension |
| artifact surface | multi-boundary graph plus recovery paths |
| coupling | lifecycle and trust-boundary coupling |
| validation depth | schema, structured-trace, lifecycle, recovery |
| environment setup | simulated host/container lifecycle |
| failure distance | restart-delayed and boundary-crossing |
| statefulness | persistent volume plus extension global state |

このlabelは予想時間ではなく上記構造から決める。実測が長い・短いだけではsizeを変更しない。

## What this case can reveal

- first contract-valid artifactとuser-resultまでの差。
- public validation、hidden quality score、offline scoringの時間境界。
- repository-traceのL profileで、探索・生成・検証のどこが支配項になるか。

## Scope boundary

- provider/modelの総合rankingを作らない。
- この一件からfamily typical timeやmulti-agent routing ruleを作らない。
- fixture外の現行product behaviorを変更しない。

このcaseの結果は同じrevision/profileの観測であり、family全体、別stack、natural projectへ自動一般化しない。
