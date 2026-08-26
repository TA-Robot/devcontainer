# F01-M-PYJS-001: fixture and seeded state

## Disposable repository

| Visible path | Role | Initial state |
| --- | --- | --- |
| `bridge/adapter.py` | provider event normalization | working |
| `bridge/reducer.py` | state transition | working |
| `bridge/store.py` | atomic write and fail-open | working |
| `media/state.js` | state decoding | working |
| `media/world.js` | render-state mapping | working |
| `trace.json` | required graph | absent |

agent workspaceには上表、`AGENTS.md`、public checksだけを置く。capsule、hidden evaluator、private known-good、base bundleはcontrol directoryへ隔離し、workspaceへmountしない。

## Seed

Production behavior passes. The missing trace must distinguish the successful `tool_end` path from malformed-event and atomic-write failure paths; two similarly named telemetry files are distractors.

初期fixtureは少なくとも一つのpublicまたはhidden criterionで必ずfailする。偶然passした場合はcase construction failureでありlive runを開始しない。

## Expected investigation or change path

1. Start at provider-specific event normalization.
2. Trace normalized category and status into reducer state.
3. Cross the atomic JSON file boundary into JS decoding.
4. Map state to the renderer and separately record fail-open error branches.

## Private known-good outline

The graph contains adapter, canonical envelope, reducer, atomic store, JSON schema, JS decoder, state mapper, and renderer nodes plus two explicit last-good-state fail-open branches.

## Reproducibility and leakage controls

- fixed git author/date、single reachable commit、remote/tagなしで生成する。
- task中のnetworkを無効化し、親repository、generator source、他case、goldへ到達させない。
- visible tree、instruction set、capsule、catalog、recipeをdigest化する。
- evaluatorはnetworkなし・read-only workspace・credential mountなしで実行する。
- initial failとknown-good passを同じevaluator revisionで校正する。
