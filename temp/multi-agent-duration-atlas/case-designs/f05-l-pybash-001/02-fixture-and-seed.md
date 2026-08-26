# F05-L-PYBASH-001: fixture and seeded state

## Disposable repository

| Visible path | Role | Initial state |
| --- | --- | --- |
| `jobs/backend.py` | new abstraction skeleton | methods incomplete |
| `jobs/file_backend.py` | v1 storage | direct callers remain |
| `jobs/migrate.py` | v1-to-v2 conversion | non-atomic and no resume |
| `jobs/cli.py` | backend selection | file path hard-coded |
| `bin/jobctl` | Bash wrapper | no rollback command forwarding |
| `MIGRATION.md` | operator contract | missing rollback/recovery |
| `tests/` | old/new lifecycle checks | partially failing |

agent workspaceには上表、`AGENTS.md`、public checksだけを置く。capsule、hidden evaluator、private known-good、base bundleはcontrol directoryへ隔離し、workspaceへmountしない。

## Seed

Naive migration breaks v1 read compatibility, commits the version marker before data, loses backend selection through the wrapper, and cannot recover/rollback after a forced interruption.

初期fixtureは少なくとも一つのpublicまたはhidden criterionで必ずfailする。偶然passした場合はcase construction failureでありlive runを開始しない。

## Expected investigation or change path

1. Freeze old/new schema and caller contracts.
2. Introduce backend interface without leaking file paths to callers.
3. Implement atomic resumable v1-to-v2 migration and v1 rollback export.
4. Update wrapper/docs and validate clean, interrupted, resumed, and rollback lifecycles.

## Private known-good outline

A protocol-backed backend owns persistence, migration stages into a temporary canonical v2 artifact before atomic commit, a journal enables idempotent resume, rollback exports a separate v1 file, and wrapper/docs preserve selection/recovery.

## Reproducibility and leakage controls

- fixed git author/date、single reachable commit、remote/tagなしで生成する。
- task中のnetworkを無効化し、親repository、generator source、他case、goldへ到達させない。
- visible tree、instruction set、capsule、catalog、recipeをdigest化する。
- evaluatorはnetworkなし・read-only workspace・credential mountなしで実行する。
- initial failとknown-good passを同じevaluator revisionで校正する。
