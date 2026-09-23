# F12-M-MDJSON-001: fixture and seeded state

## Disposable repository

| Visible path | Role | Initial state |
| --- | --- | --- |
| `reviews/` | three independent findings | conflicting |
| `change.diff` | patch under review | complete |
| `evidence/tests.json` | test outcomes | complete |
| `evidence/exploit.sh` | replay | working |
| `sources/` | implementation facts | complete |
| `ADJUDICATION.md` | target human record | absent |
| `adjudication.json` | target claim ledger | absent |

agent workspaceには上表、`AGENTS.md`、public checksだけを置く。capsule、hidden evaluator、private known-good、base bundleはcontrol directoryへ隔離し、workspaceへmountしない。

## Seed

Review A correctly finds a post-check symlink race. Review B claims canonicalization fully fixes it, contradicted by replay. Review C flags Windows junction behavior, but the Linux-only fixture cannot resolve that claim. One severity assertion overstates credential access.

初期fixtureは少なくとも一つのpublicまたはhidden criterionで必ずfailする。偶然passした場合はcase construction failureでありlive runを開始しない。

## Expected investigation or change path

1. Normalize duplicate/contradictory claims and provenance.
2. Replay tests/exploit and map outcomes to each claim.
3. Accept, reject, narrow, or leave unknown with decisive evidence.
4. Produce a decision-support summary without turning unknown platform behavior into fact.

## Private known-good outline

The ledger merges provenance, uses the exploit to accept the race/refute sufficiency, leaves junction behavior unknown with a test need, narrows severity, and ties every disposition to evidence.

## Reproducibility and leakage controls

- fixed git author/date、single reachable commit、remote/tagなしで生成する。
- task中のnetworkを無効化し、親repository、generator source、他case、goldへ到達させない。
- visible tree、instruction set、capsule、catalog、recipeをdigest化する。
- evaluatorはnetworkなし・read-only workspace・credential mountなしで実行する。
- initial failとknown-good passを同じevaluator revisionで校正する。
