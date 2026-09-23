# F11-S-BASH-001: fixture and seeded state

## Disposable repository

| Visible path | Role | Initial state |
| --- | --- | --- |
| `sync-version.sh` | version-selection script | one missing case terminator |
| `tests/smoke.sh` | side-effect-free scenarios | cannot start until syntax fixed |

agent workspaceには上表、`AGENTS.md`、public checksだけを置く。capsule、hidden evaluator、private known-good、base bundleはcontrol directoryへ隔離し、workspaceへmountしない。

## Seed

The `host)` arm lacks `;;`; neighboring arms and quoting are correct. A large rewrite is unnecessary and risks changing version precedence.

初期fixtureは少なくとも一つのpublicまたはhidden criterionで必ずfailする。偶然passした場合はcase construction failureでありlive runを開始しない。

## Expected investigation or change path

1. Run `bash -n` to localize parse failure.
2. Inspect adjacent case arms and apply minimal fix.
3. Run static check and smoke matrix.
4. Confirm diff is limited to syntax repair.

## Private known-good outline

One `;;` is inserted after the `host)` arm; static and all scenario outputs pass unchanged.

## Reproducibility and leakage controls

- fixed git author/date、single reachable commit、remote/tagなしで生成する。
- task中のnetworkを無効化し、親repository、generator source、他case、goldへ到達させない。
- visible tree、instruction set、capsule、catalog、recipeをdigest化する。
- evaluatorはnetworkなし・read-only workspace・credential mountなしで実行する。
- initial failとknown-good passを同じevaluator revisionで校正する。
