# F05-M-PY-001: fixture and seeded state

## Disposable repository

| Visible path | Role | Initial state |
| --- | --- | --- |
| `events/codec.py` | old function and new class skeleton | migration incomplete |
| `events/compat.py` | deprecated shim | forwards incorrectly |
| `producer.py` | caller one | old API |
| `ledger.py` | caller two | old API |
| `replay.py` | caller three | old API |
| `tests/` | new/old contract tests | partially failing |

agent workspaceには上表、`AGENTS.md`、public checksだけを置く。capsule、hidden evaluator、private known-good、base bundleはcontrol directoryへ隔離し、workspaceへmountしない。

## Seed

Callers must share an injected schema policy; constructing default codecs per call changes versioning. The old shim must emit one warning and preserve bytes. One reflective plugin still imports the old symbol.

初期fixtureは少なくとも一つのpublicまたはhidden criterionで必ずfailする。偶然passした場合はcase construction failureでありlive runを開始しない。

## Expected investigation or change path

1. Discover direct and reflective callers.
2. Define lifecycle/ownership of the injected codec.
3. Migrate callers and implement byte-compatible deprecated shim.
4. Validate warnings, schema version, and old/new behavior.

## Private known-good outline

Components receive one codec, all callers including plugin registry migrate, and the deprecated wrapper preserves canonical bytes/errors while emitting one `DeprecationWarning` per call.

## Reproducibility and leakage controls

- fixed git author/date、single reachable commit、remote/tagなしで生成する。
- task中のnetworkを無効化し、親repository、generator source、他case、goldへ到達させない。
- visible tree、instruction set、capsule、catalog、recipeをdigest化する。
- evaluatorはnetworkなし・read-only workspace・credential mountなしで実行する。
- initial failとknown-good passを同じevaluator revisionで校正する。
