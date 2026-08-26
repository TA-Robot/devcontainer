# F08-M-MDJSON-001: fixture and seeded state

## Disposable repository

| Visible path | Role | Initial state |
| --- | --- | --- |
| `system.md` | current behavior and constraints | complete |
| `options/` | three responsibility splits | complete |
| `simulator.py` | failure/event trace | working |
| `scenarios.json` | restart/cancel/retry evidence | complete |
| `PROPOSAL.md` | target proposal | absent |
| `proposal.json` | structured design | absent |

agent workspaceには上表、`AGENTS.md`、public checksだけを置く。capsule、hidden evaluator、private known-good、base bundleはcontrol directoryへ隔離し、workspaceへmountしない。

## Seed

Putting retry ownership in scheduler duplicates attempts after supervisor restart; putting cancellation only in supervisor loses intent across restart; store-driven execution over-couples persistence and process control. The design must assign durable intent and ephemeral process ownership coherently.

初期fixtureは少なくとも一つのpublicまたはhidden criterionで必ずfailする。偶然passした場合はcase construction failureでありlive runを開始しない。

## Expected investigation or change path

1. Extract invariants and durable/ephemeral state.
2. Simulate each option through restart, cancellation, timeout, and retry traces.
3. Define responsibilities, APIs, transitions, and failure ownership.
4. Record rejected options, migration impact, unknowns, and counterexamples.

## Private known-good outline

Durable job intent/attempt budget/cancellation live in store; scheduler admits work from durable state; supervisor owns processes/heartbeats and reports outcomes; transitions are simulated, with migration/metrics and explicit idempotency unknowns.

## Reproducibility and leakage controls

- fixed git author/date、single reachable commit、remote/tagなしで生成する。
- task中のnetworkを無効化し、親repository、generator source、他case、goldへ到達させない。
- visible tree、instruction set、capsule、catalog、recipeをdigest化する。
- evaluatorはnetworkなし・read-only workspace・credential mountなしで実行する。
- initial failとknown-good passを同じevaluator revisionで校正する。
