# F11-M-BASH-001: fixture and seeded state

## Disposable repository

| Visible path | Role | Initial state |
| --- | --- | --- |
| `initialize-host.sh` | writes host version metadata | preserves CRLF input |
| `post-start.sh` | compares/installs/marks ready | raw compare and early marker |
| `install-cli` | simulated idempotent installer | working |
| `tests/lifecycle.sh` | start/restart/failure matrix | two failures |

agent workspaceには上表、`AGENTS.md`、public checksだけを置く。capsule、hidden evaluator、private known-good、base bundleはcontrol directoryへ隔離し、workspaceへmountしない。

## Seed

CRLF/trailing space makes equal versions differ. `post-start` writes ready before install verification, so a failed install makes the next restart skip recovery. Reinstalling every time or deleting all state are distractors.

初期fixtureは少なくとも一つのpublicまたはhidden criterionで必ずfailする。偶然passした場合はcase construction failureでありlive runを開始しない。

## Expected investigation or change path

1. Reproduce clean, CRLF, failed-install, and restart scenarios.
2. Define canonical version normalization and marker commit invariant.
3. Patch initialization/startup with idempotent recovery.
4. Run lifecycle twice and inventory residual state.

## Private known-good outline

A strict single-line normalizer strips terminal CR/space, marker content binds to verified version, temporary marker commits atomically after install verification, and restart resumes idempotently.

## Reproducibility and leakage controls

- fixed git author/date、single reachable commit、remote/tagなしで生成する。
- task中のnetworkを無効化し、親repository、generator source、他case、goldへ到達させない。
- visible tree、instruction set、capsule、catalog、recipeをdigest化する。
- evaluatorはnetworkなし・read-only workspace・credential mountなしで実行する。
- initial failとknown-good passを同じevaluator revisionで校正する。
