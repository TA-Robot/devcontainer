# F07-L-MDPYBASH-001: fixture and seeded state

## Disposable repository

| Visible path | Role | Initial state |
| --- | --- | --- |
| `src/backend.py` | current/new backend contracts | working staged implementation |
| `src/migration.py` | phase and rollback semantics | working |
| `bin/backendctl` | operator commands | working |
| `docs/ARCHITECTURE.md` | target current architecture | stale direct-file description |
| `docs/MIGRATION.md` | target rollout guide | partial |
| `docs/RECOVERY.md` | target rollback/recovery | missing |
| `docs-index.json` | fact/link/command manifest | missing |

agent workspaceには上表、`AGENTS.md`、public checksだけを置く。capsule、hidden evaluator、private known-good、base bundleはcontrol directoryへ隔離し、workspaceへmountしない。

## Seed

Existing docs disagree about the default backend, imply the compatibility shim can be removed immediately, omit a non-destructive rollback export, and assign cleanup to the wrong component. Every fact is derivable from visible code/tests.

初期fixtureは少なくとも一つのpublicまたはhidden criterionで必ずfailする。偶然passした場合はcase construction failureでありlive runを開始しない。

## Expected investigation or change path

1. Build one source-of-truth fact/ownership table.
2. Partition current architecture, rollout, and incident recovery concerns.
3. Update all documents and cross-links from the shared facts.
4. Replay upgrade, mixed-version, interrupted, and rollback commands; validate no contradiction.

## Private known-good outline

A shared index maps source facts to synchronized architecture, rollout, and recovery sections; executable scenario DAG covers mixed-version, interruption, abort, rollback export, and evidence-gated shim removal.

## Reproducibility and leakage controls

- fixed git author/date、single reachable commit、remote/tagなしで生成する。
- task中のnetworkを無効化し、親repository、generator source、他case、goldへ到達させない。
- visible tree、instruction set、capsule、catalog、recipeをdigest化する。
- evaluatorはnetworkなし・read-only workspace・credential mountなしで実行する。
- initial failとknown-good passを同じevaluator revisionで校正する。
