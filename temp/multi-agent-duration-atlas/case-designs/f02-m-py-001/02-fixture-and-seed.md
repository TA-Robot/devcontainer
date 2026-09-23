# F02-M-PY-001: fixture and seeded state

## Disposable repository

| Visible path | Role | Initial state |
| --- | --- | --- |
| `change.diff` | four-file review surface | two seeded defects |
| `jobs/paths.py` | workspace path validation | pre-resolve containment |
| `jobs/cleanup.py` | cleanup ownership | trusts caller label |
| `jobs/runner.py` | combines both contracts | working benign path |
| `tests/` | public happy-path tests | passing |
| `review.json` | required ranked findings | absent |

agent workspaceには上表、`AGENTS.md`、public checksだけを置く。capsule、hidden evaluator、private known-good、base bundleはcontrol directoryへ隔離し、workspaceへmountしない。

## Seed

A symlink can escape after lexical validation, and a reused caller label can delete another job's directory. The combined path makes exploitation more damaging. A logging change is a safe distractor.

初期fixtureは少なくとも一つのpublicまたはhidden criterionで必ずfailする。偶然passした場合はcase construction failureでありlive runを開始しない。

## Expected investigation or change path

1. Map changed contracts and callers across the diff.
2. Reproduce the symlink-after-check escape.
3. Reproduce cleanup ownership collision and assess interaction.
4. Rank distinct findings and avoid treating the logging change as a defect.

## Private known-good outline

Two high/critical findings provide executable temp-directory triggers, cite validators/cleanup callers, link the combined blast radius, and leave the logging hunk unflagged.

## Reproducibility and leakage controls

- fixed git author/date、single reachable commit、remote/tagなしで生成する。
- task中のnetworkを無効化し、親repository、generator source、他case、goldへ到達させない。
- visible tree、instruction set、capsule、catalog、recipeをdigest化する。
- evaluatorはnetworkなし・read-only workspace・credential mountなしで実行する。
- initial failとknown-good passを同じevaluator revisionで校正する。
