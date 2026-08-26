# F06-S-PY-001: fixture and seeded state

## Disposable repository

| Visible path | Role | Initial state |
| --- | --- | --- |
| `ports.py` | frozen production function | correct implementation |
| `tests/test_ports.py` | test target | one happy-path test |

agent workspaceには上表、`AGENTS.md`、public checksだけを置く。capsule、hidden evaluator、private known-good、base bundleはcontrol directoryへ隔離し、workspaceへmountしない。

## Seed

Missing tests allow inclusive 65536, boolean-as-integer, whitespace-only strings, and silent float coercion mutants to survive. Production changes are forbidden.

初期fixtureは少なくとも一つのpublicまたはhidden criterionで必ずfailする。偶然passした場合はcase construction failureでありlive runを開始しない。

## Expected investigation or change path

1. Read the behavior contract and current implementation.
2. Partition valid/invalid types and boundaries.
3. Add concise tests that distinguish each mutant.
4. Run public tests without touching production.

## Private known-good outline

A table/subtest matrix covers valid integers/strings, both boundaries, adjacent invalids, bool, float, empty/whitespace, and malformed strings while leaving production bytes unchanged.

## Reproducibility and leakage controls

- fixed git author/date、single reachable commit、remote/tagなしで生成する。
- task中のnetworkを無効化し、親repository、generator source、他case、goldへ到達させない。
- visible tree、instruction set、capsule、catalog、recipeをdigest化する。
- evaluatorはnetworkなし・read-only workspace・credential mountなしで実行する。
- initial failとknown-good passを同じevaluator revisionで校正する。
