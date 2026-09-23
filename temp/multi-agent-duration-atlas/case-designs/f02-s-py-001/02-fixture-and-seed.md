# F02-S-PY-001: fixture and seeded state

## Disposable repository

| Visible path | Role | Initial state |
| --- | --- | --- |
| `workspace.py` | path containment helper | proposed defect applied |
| `change.diff` | review surface | contains the six-line change |
| `tests/test_workspace.py` | existing public behavior | passes benign paths |
| `review.json` | required findings | absent |

agent workspaceには上表、`AGENTS.md`、public checksだけを置く。capsule、hidden evaluator、private known-good、base bundleはcontrol directoryへ隔離し、workspaceへmountしない。

## Seed

`str(candidate).startswith(str(root))` accepts a sibling such as `/work/project-other`. Existing tests cover only descendants. One seeded high-impact validation defect exists; style differences are non-findings.

初期fixtureは少なくとも一つのpublicまたはhidden criterionで必ずfailする。偶然passした場合はcase construction failureでありlive runを開始しない。

## Expected investigation or change path

1. Read the exact changed lines and containment contract.
2. Construct a concrete sibling-prefix counterexample.
3. Assess impact and reachable behavior.
4. Record one ranked finding with evidence and remediation direction.

## Private known-good outline

One high-severity finding cites the `startswith` hunk, supplies `/work/project` versus `/work/project-other/file`, explains workspace escape, and recommends canonical `relative_to` containment.

## Reproducibility and leakage controls

- fixed git author/date、single reachable commit、remote/tagなしで生成する。
- task中のnetworkを無効化し、親repository、generator source、他case、goldへ到達させない。
- visible tree、instruction set、capsule、catalog、recipeをdigest化する。
- evaluatorはnetworkなし・read-only workspace・credential mountなしで実行する。
- initial failとknown-good passを同じevaluator revisionで校正する。
