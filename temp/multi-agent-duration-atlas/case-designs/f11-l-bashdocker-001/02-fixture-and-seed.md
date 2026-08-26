# F11-L-BASHDOCKER-001: fixture and seeded state

## Disposable repository

| Visible path | Role | Initial state |
| --- | --- | --- |
| `.devcontainer/devcontainer.json` | lifecycle order | working entrypoints |
| `initialize-host.sh` | host metadata/extension stage | marks installed before verification |
| `post-create.sh` | volume migration | destructive in-place update |
| `post-start.sh` | runtime readiness/recovery | trusts stale markers |
| `migrate_state.py` | schema conversion | version marker first |
| `tests/rebuild.sh` | rebuild/reopen fault harness | seeded failures |
| `RECOVERY.md` | operator recovery target | missing |

agent workspaceには上表、`AGENTS.md`、public checksだけを置く。capsule、hidden evaluator、private known-good、base bundleはcontrol directoryへ隔離し、workspaceへmountしない。

## Seed

A forced cut after v2 marker/before data conversion makes state unreadable; retry deletes the volume as 'corrupt'. Host and extension ready markers can remain stale, causing runtime to skip reinstall. Correct recovery preserves original data and scopes ownership across host/container.

初期fixtureは少なくとも一つのpublicまたはhidden criterionで必ずfailする。偶然passした場合はcase construction failureでありlive runを開始しない。

## Expected investigation or change path

1. Map rebuild/create/start execution locations, durable state, and marker owners.
2. Reproduce fault cuts at migration and install stages across reopen.
3. Implement staged migration, verified markers, idempotent resume/rollback, and bounded cleanup.
4. Write recovery commands and run repeated rebuild/reopen plus residual inventory.

## Private known-good outline

Lifecycle ownership graph drives staged copy/validate/atomic commit, version-bound verified markers, idempotent reopen repair, non-destructive rollback export, scoped cleanup, and replayable recovery docs.

## Reproducibility and leakage controls

- fixed git author/date、single reachable commit、remote/tagなしで生成する。
- task中のnetworkを無効化し、親repository、generator source、他case、goldへ到達させない。
- visible tree、instruction set、capsule、catalog、recipeをdigest化する。
- evaluatorはnetworkなし・read-only workspace・credential mountなしで実行する。
- initial failとknown-good passを同じevaluator revisionで校正する。
