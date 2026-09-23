# F05-S-PY-001: fixture and seeded state

## Disposable repository

| Visible path | Role | Initial state |
| --- | --- | --- |
| `events.py` | two duplicate public functions | behavior correct but duplicated |
| `tests/test_events.py` | public behavior | passing |

agent workspaceには上表、`AGENTS.md`、public checksだけを置く。capsule、hidden evaluator、private known-good、base bundleはcontrol directoryへ隔離し、workspaceへmountしない。

## Seed

Both functions contain nearly identical normalization with one subtle difference: one validates before prefixing. Naive extraction can change the exception type/order or double-prefix names.

初期fixtureは少なくとも一つのpublicまたはhidden criterionで必ずfailする。偶然passした場合はcase construction failureでありlive runを開始しない。

## Expected investigation or change path

1. Inventory public signatures and behavior matrix.
2. Identify truly common normalization while retaining caller-specific ordering.
3. Extract a private helper and update both callers.
4. Run equivalence tests against the frozen baseline behavior.

## Private known-good outline

A narrowly scoped `_normalize_event_name` handles common character normalization while each public caller preserves its original validation/prefix sequence.

## Reproducibility and leakage controls

- fixed git author/date、single reachable commit、remote/tagなしで生成する。
- task中のnetworkを無効化し、親repository、generator source、他case、goldへ到達させない。
- visible tree、instruction set、capsule、catalog、recipeをdigest化する。
- evaluatorはnetworkなし・read-only workspace・credential mountなしで実行する。
- initial failとknown-good passを同じevaluator revisionで校正する。
