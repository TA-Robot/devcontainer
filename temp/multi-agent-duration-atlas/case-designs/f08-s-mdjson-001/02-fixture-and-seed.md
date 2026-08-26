# F08-S-MDJSON-001: fixture and seeded state

## Disposable repository

| Visible path | Role | Initial state |
| --- | --- | --- |
| `options.md` | two API proposals | complete |
| `constraints.json` | five visible constraints | complete |
| `callers.py` | usage evidence | working examples |
| `DECISION.md` | human-readable result | absent |
| `decision.json` | structured result | absent |

agent workspaceには上表、`AGENTS.md`、public checksだけを置く。capsule、hidden evaluator、private known-good、base bundleはcontrol directoryへ隔離し、workspaceへmountしない。

## Seed

The builder appears extensible but retains state across requests in one real caller; the pure merge appears simpler but cannot express deletion without an explicit sentinel. A good decision recognizes both and selects a bounded pure API with sentinel semantics.

初期fixtureは少なくとも一つのpublicまたはhidden criterionで必ずfailする。偶然passした場合はcase construction failureでありlive runを開始しない。

## Expected investigation or change path

1. Map both proposals to all visible constraints/call sites.
2. Construct one counterexample for each unmodified option.
3. Choose a bounded variant and record rejected alternatives.
4. Keep Markdown and JSON claims/evidence synchronized.

## Private known-good outline

The decision selects a pure merge with explicit deletion sentinel, explains request isolation, evaluates all constraints, demonstrates builder leakage and raw-merge deletion failure, and records one open typing question.

## Reproducibility and leakage controls

- fixed git author/date、single reachable commit、remote/tagなしで生成する。
- task中のnetworkを無効化し、親repository、generator source、他case、goldへ到達させない。
- visible tree、instruction set、capsule、catalog、recipeをdigest化する。
- evaluatorはnetworkなし・read-only workspace・credential mountなしで実行する。
- initial failとknown-good passを同じevaluator revisionで校正する。
