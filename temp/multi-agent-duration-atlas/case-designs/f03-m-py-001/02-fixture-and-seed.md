# F03-M-PY-001: fixture and seeded state

## Disposable repository

| Visible path | Role | Initial state |
| --- | --- | --- |
| `jobs/model.py` | timestamp serialization | writes UTC suffix |
| `jobs/store.py` | reload/deserialization | drops timezone awareness |
| `jobs/scheduler.py` | expiry decision | correct for aware datetimes |
| `tests/test_expiry.py` | integration failure | fails after reload |
| `diagnosis.json` | required artifact | absent |

agent workspaceには上表、`AGENTS.md`、public checksだけを置く。capsule、hidden evaluator、private known-good、base bundleはcontrol directoryへ隔離し、workspaceへmountしない。

## Seed

Fresh in-memory jobs expire correctly; reloaded jobs become naive and comparison falls into a compatibility branch that retains them. A scheduler boundary condition looks suspicious but is correct.

初期fixtureは少なくとも一つのpublicまたはhidden criterionで必ずfailする。偶然passした場合はcase construction failureでありlive runを開始しない。

## Expected investigation or change path

1. Reproduce both fresh and reload paths.
2. Compare serialized and deserialized timestamp properties.
3. Trace the compatibility branch in scheduler.
4. Design regression coverage at store and integration layers.

## Private known-good outline

The artifact includes fresh/reload commands, shows aware-to-naive transition in `load_job`, traces the retention fallback, and proposes unit plus reload integration regressions.

## Reproducibility and leakage controls

- fixed git author/date、single reachable commit、remote/tagなしで生成する。
- task中のnetworkを無効化し、親repository、generator source、他case、goldへ到達させない。
- visible tree、instruction set、capsule、catalog、recipeをdigest化する。
- evaluatorはnetworkなし・read-only workspace・credential mountなしで実行する。
- initial failとknown-good passを同じevaluator revisionで校正する。
