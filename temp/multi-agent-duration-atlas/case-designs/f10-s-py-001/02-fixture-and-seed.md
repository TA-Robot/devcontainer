# F10-S-PY-001: fixture and seeded state

## Disposable repository

| Visible path | Role | Initial state |
| --- | --- | --- |
| `report.py` | report generation | repeats canonical serialization |
| `bench.py` | counter and timing harness | working |
| `tests/test_report.py` | correctness | passing |
| `performance.json` | required diagnosis | absent |

agent workspaceには上表、`AGENTS.md`、public checksだけを置く。capsule、hidden evaluator、private known-good、base bundleはcontrol directoryへ隔離し、workspaceへmountしない。

## Seed

Output correctness is unaffected, but `canonical_json` is called N times for N fields instead of once. A nearby list sort consumes some time but is not the scaling cause.

初期fixtureは少なくとも一つのpublicまたはhidden criterionで必ずfailする。偶然passした場合はcase construction failureでありlive runを開始しない。

## Expected investigation or change path

1. Run correctness and benchmark/counter baselines.
2. Vary field count and compare call-count scaling.
3. Localize the repeated canonicalization and rule out the sort using evidence.
4. Record command, raw observations, diagnosis, and bounded optimization direction.

## Private known-good outline

The report captures 8/64/512-field runs, shows serialization calls scale with fields while sort calls do not, cites the loop, and proposes caching canonical bytes once per object under equivalence validation.

## Reproducibility and leakage controls

- fixed git author/date、single reachable commit、remote/tagなしで生成する。
- task中のnetworkを無効化し、親repository、generator source、他case、goldへ到達させない。
- visible tree、instruction set、capsule、catalog、recipeをdigest化する。
- evaluatorはnetworkなし・read-only workspace・credential mountなしで実行する。
- initial failとknown-good passを同じevaluator revisionで校正する。
