# F03-S-PY-001: fixture and seeded state

## Disposable repository

| Visible path | Role | Initial state |
| --- | --- | --- |
| `limits.py` | configuration parser | truthiness defect |
| `tests/test_limits.py` | failing behavior | one failure |
| `diagnosis.json` | required artifact | absent |

agent workspaceには上表、`AGENTS.md`、public checksだけを置く。capsule、hidden evaluator、private known-good、base bundleはcontrol directoryへ隔離し、workspaceへmountしない。

## Seed

`raw.get('retries') or 3` maps an explicit zero to three. A nearby integer conversion is correct and serves as a distractor.

初期fixtureは少なくとも一つのpublicまたはhidden criterionで必ずfailする。偶然passした場合はcase construction failureでありlive runを開始しない。

## Expected investigation or change path

1. Run the exact failing test.
2. Trace expected and actual value into the parser expression.
3. Confirm a minimal input reproducer.
4. Specify a regression test that distinguishes missing from explicit zero.

## Private known-good outline

The diagnosis cites the `or 3` expression, reproduces `parse_limits({'retries': 0}) == 3`, and proposes paired missing/zero assertions.

## Reproducibility and leakage controls

- fixed git author/date、single reachable commit、remote/tagなしで生成する。
- task中のnetworkを無効化し、親repository、generator source、他case、goldへ到達させない。
- visible tree、instruction set、capsule、catalog、recipeをdigest化する。
- evaluatorはnetworkなし・read-only workspace・credential mountなしで実行する。
- initial failとknown-good passを同じevaluator revisionで校正する。
