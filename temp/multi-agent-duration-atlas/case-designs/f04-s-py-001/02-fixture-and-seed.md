# F04-S-PY-001: fixture and seeded state

## Disposable repository

| Visible path | Role | Initial state |
| --- | --- | --- |
| `tag_normalizer.py` | implementation target | only strip/lower/space replacement |
| `tests/test_tag_normalizer.py` | public behavior | one simple and one separator test |

agent workspaceには上表、`AGENTS.md`、public checksだけを置く。capsule、hidden evaluator、private known-good、base bundleはcontrol directoryへ隔離し、workspaceへmountしない。

## Seed

The initial implementation mishandles mixed separators, unsupported/non-ASCII characters, empty results, non-string inputs, and the 32-character bound.

初期fixtureは少なくとも一つのpublicまたはhidden criterionで必ずfailする。偶然passした場合はcase construction failureでありlive runを開始しない。

## Expected investigation or change path

1. Read the complete normalization contract.
2. Implement one deterministic character-state pass.
3. Run public tests and add/adjust only contract-relevant tests.
4. Check error behavior and boundary lengths.

## Private known-good outline

A one-pass state machine records pending separators, accepts ASCII alphanumerics, raises `TypeError` for non-string input, and validates final emptiness/length.

## Reproducibility and leakage controls

- fixed git author/date、single reachable commit、remote/tagなしで生成する。
- task中のnetworkを無効化し、親repository、generator source、他case、goldへ到達させない。
- visible tree、instruction set、capsule、catalog、recipeをdigest化する。
- evaluatorはnetworkなし・read-only workspace・credential mountなしで実行する。
- initial failとknown-good passを同じevaluator revisionで校正する。
