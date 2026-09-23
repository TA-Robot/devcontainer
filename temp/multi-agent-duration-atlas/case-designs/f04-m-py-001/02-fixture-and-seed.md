# F04-M-PY-001: fixture and seeded state

## Disposable repository

| Visible path | Role | Initial state |
| --- | --- | --- |
| `kvtool/store.py` | JSON persistence | set operation unimplemented |
| `kvtool/cli.py` | get/set exit contract | empty-key/error handling incomplete |
| `tests/test_store.py` | public unit tests | partial coverage |
| `USAGE.md` | CLI contract | get-only documentation |

agent workspaceには上表、`AGENTS.md`、public checksだけを置く。capsule、hidden evaluator、private known-good、base bundleはcontrol directoryへ隔離し、workspaceへmountしない。

## Seed

Persistence is missing. The complete contract requires preserving keys, canonical sorted JSON with newline, atomic replacement, parent creation, distinct exit codes, state integrity on errors, and synchronized usage docs.

初期fixtureは少なくとも一つのpublicまたはhidden criterionで必ずfailする。偶然passした場合はcase construction failureでありlive runを開始しない。

## Expected investigation or change path

1. Map store, CLI, test, and documentation constraints.
2. Implement atomic canonical persistence with cleanup.
3. Align CLI validation and exit codes without corrupting state.
4. Update tests/docs and run the full contract.

## Private known-good outline

The existing private known-good uses tempfile+fsync+replace, canonical JSON, explicit key validation/error mapping, and two-command usage documentation.

## Reproducibility and leakage controls

- fixed git author/date、single reachable commit、remote/tagなしで生成する。
- task中のnetworkを無効化し、親repository、generator source、他case、goldへ到達させない。
- visible tree、instruction set、capsule、catalog、recipeをdigest化する。
- evaluatorはnetworkなし・read-only workspace・credential mountなしで実行する。
- initial failとknown-good passを同じevaluator revisionで校正する。
