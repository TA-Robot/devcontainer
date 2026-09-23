# F06-M-PY-001: fixture and seeded state

## Disposable repository

| Visible path | Role | Initial state |
| --- | --- | --- |
| `retry/policy.py` | frozen correct policy | correct |
| `retry/clock.py` | fake delay surface | working |
| `tests/test_policy.py` | test target | three simple cases |
| `POLICY.md` | behavior contract | complete |

agent workspaceには上表、`AGENTS.md`、public checksだけを置く。capsule、hidden evaluator、private known-good、base bundleはcontrol directoryへ隔離し、workspaceへmountしない。

## Seed

Known-bad variants retry non-idempotent POST, retry 400, exceed max attempts, ignore capped server delay, or mishandle the intersection of 429+idempotency+last attempt.

初期fixtureは少なくとも一つのpublicまたはhidden criterionで必ずfailする。偶然passした場合はcase construction failureでありlive runを開始しない。

## Expected investigation or change path

1. Convert prose contract into an axis/partition matrix.
2. Select boundary and interaction rows with traceable expected outcomes.
3. Use fake clock for delay assertions.
4. Run mutation calibration and reduce redundant cases without losing kills.

## Private known-good outline

A named case table covers status/method/attempt combinations, explicit boundary rows, fake-clock delay/cap assertions, and kills all five mutant groups without production edits.

## Reproducibility and leakage controls

- fixed git author/date、single reachable commit、remote/tagなしで生成する。
- task中のnetworkを無効化し、親repository、generator source、他case、goldへ到達させない。
- visible tree、instruction set、capsule、catalog、recipeをdigest化する。
- evaluatorはnetworkなし・read-only workspace・credential mountなしで実行する。
- initial failとknown-good passを同じevaluator revisionで校正する。
