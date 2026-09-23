# F01-L-PYBASHJS-001: fixture and seeded state

## Disposable repository

| Visible path | Role | Initial state |
| --- | --- | --- |
| `.devcontainer/devcontainer.json` | lifecycle entrypoints | working fixture config |
| `scripts/initialize-host.sh` | host preparation | working |
| `scripts/post-start.sh` | container startup | working |
| `scripts/agentctl.py` | job/activity envelope | working |
| `scripts/mira_hook.py` | state bridge | working |
| `extension/world.js` | state read and rendering | working |
| `trace.json` | required cross-boundary trace | absent |

agent workspaceには上表、`AGENTS.md`、public checksだけを置く。capsule、hidden evaluator、private known-good、base bundleはcontrol directoryへ隔離し、workspaceへmountしない。

## Seed

All lifecycle simulations pass. The trace is absent and must separate rebuild-time host provisioning, container start, runtime provider events, persistent-state recovery, and extension rendering. A legacy second-agent path is a deliberate distractor.

初期fixtureは少なくとも一つのpublicまたはhidden criterionで必ずfailする。偶然passした場合はcase construction failureでありlive runを開始しない。

## Expected investigation or change path

1. Map rebuild and reopen lifecycle events with execution location labels.
2. Follow wrapper/version material into the container and `agentctl` runtime.
3. Trace provider activity through the hook and atomic companion state.
4. Trace extension consumption and restart recovery; record failure ownership at each boundary.

## Private known-good outline

A location-labelled DAG separates rebuild, startup, runtime, and extension phases; every boundary carries a concrete file/event, and three failure subgraphs terminate in explicit owner/recovery outcomes.

## Reproducibility and leakage controls

- fixed git author/date、single reachable commit、remote/tagなしで生成する。
- task中のnetworkを無効化し、親repository、generator source、他case、goldへ到達させない。
- visible tree、instruction set、capsule、catalog、recipeをdigest化する。
- evaluatorはnetworkなし・read-only workspace・credential mountなしで実行する。
- initial failとknown-good passを同じevaluator revisionで校正する。
