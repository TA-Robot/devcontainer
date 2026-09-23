# F12-S-MDJSON-001: fixture and seeded state

## Disposable repository

| Visible path | Role | Initial state |
| --- | --- | --- |
| `analysis-a.md` | first review | three claims |
| `analysis-b.md` | second review | three claims |
| `sources/` | authoritative snippets | complete |
| `SYNTHESIS.md` | human result | absent |
| `synthesis.json` | claim disposition | absent |

agent workspaceには上表、`AGENTS.md`、public checksだけを置く。capsule、hidden evaluator、private known-good、base bundleはcontrol directoryへ隔離し、workspaceへmountしない。

## Seed

Both agree the wrapper forwards argv. A says `ALLOW_OUTSIDE=1` is active by default; B says it is ignored. Source shows it is read only when explicitly set, so neither blanket claim is correct. A separate logging claim is unsupported.

初期fixtureは少なくとも一つのpublicまたはhidden criterionで必ずfailする。偶然passした場合はcase construction failureでありlive runを開始しない。

## Expected investigation or change path

1. Atomize claims from both analyses.
2. Map each claim to exact source entailment/contradiction/absence.
3. Record agreements, corrected disagreement, unsupported claim, and unknowns.
4. Keep JSON and Markdown synchronized.

## Private known-good outline

All six input claims map to source IDs; argv forwarding is agreed, override behavior is conditional on explicit environment setting, logging remains unsupported, and no extra decision is invented.

## Reproducibility and leakage controls

- fixed git author/date、single reachable commit、remote/tagなしで生成する。
- task中のnetworkを無効化し、親repository、generator source、他case、goldへ到達させない。
- visible tree、instruction set、capsule、catalog、recipeをdigest化する。
- evaluatorはnetworkなし・read-only workspace・credential mountなしで実行する。
- initial failとknown-good passを同じevaluator revisionで校正する。
