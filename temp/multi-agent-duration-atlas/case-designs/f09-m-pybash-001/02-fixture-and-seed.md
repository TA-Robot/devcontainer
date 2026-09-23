# F09-M-PYBASH-001: fixture and seeded state

## Disposable repository

| Visible path | Role | Initial state |
| --- | --- | --- |
| `isolation/paths.py` | lexical workspace containment | checks before resolving symlink |
| `bin/run-task` | workspace environment override | trusts inherited variable |
| `tests/` | benign isolation behavior | passing |
| `security-review.json` | required findings | absent |
| `security_regression.py` | standalone negative-test target | skeleton |

agent workspaceには上表、`AGENTS.md`、public checksだけを置く。capsule、hidden evaluator、private known-good、base bundleはcontrol directoryへ隔離し、workspaceへmountしない。

## Seed

An in-workspace symlink escapes after lexical validation. Separately, inherited `TASK_WORKSPACE` points the launcher outside before Python sees its expected root. Combining them bypasses a superficial one-layer patch.

初期fixtureは少なくとも一つのpublicまたはhidden criterionで必ずfailする。偶然passした場合はcase construction failureでありlive runを開始しない。

## Expected investigation or change path

1. Model trusted root source and path normalization order.
2. Reproduce symlink and environment override escapes separately.
3. Add negative tests at launcher-to-resolver boundary.
4. Specify layered invariants and verify peers/owned paths remain allowed.

## Private known-good outline

Two reproducible findings and a composition note prove root provenance plus post-resolution containment are both necessary; tests cover external/internal symlinks and trusted/untrusted launcher roots.

## Reproducibility and leakage controls

- fixed git author/date、single reachable commit、remote/tagなしで生成する。
- task中のnetworkを無効化し、親repository、generator source、他case、goldへ到達させない。
- visible tree、instruction set、capsule、catalog、recipeをdigest化する。
- evaluatorはnetworkなし・read-only workspace・credential mountなしで実行する。
- initial failとknown-good passを同じevaluator revisionで校正する。
