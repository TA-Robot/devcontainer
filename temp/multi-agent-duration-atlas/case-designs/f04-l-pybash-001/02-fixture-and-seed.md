# F04-L-PYBASH-001: fixture and seeded state

## Disposable repository

| Visible path | Role | Initial state |
| --- | --- | --- |
| `queue_store.py` | persistent queue state | acknowledgement missing and validation weak |
| `queue_cli.py` | process entrypoint | error mapping incomplete |
| `bin/queuectl` | Bash wrapper | drops all but one argument |
| `FORMAT.md` | state contract | partial |
| `tests/test_queue_store.py` | public unit behavior | minimal |

agent workspaceには上表、`AGENTS.md`、public checksだけを置く。capsule、hidden evaluator、private known-good、base bundleはcontrol directoryへ隔離し、workspaceへmountしない。

## Seed

Acknowledgement is unimplemented; duplicate IDs, malformed state, unknown items, idempotent re-ack, atomic persistence, wrapper argv, exit contracts, and restart behavior must all align.

初期fixtureは少なくとも一つのpublicまたはhidden criterionで必ずfailする。偶然passした場合はcase construction failureでありlive runを開始しない。

## Expected investigation or change path

1. Model state invariants and restart contract.
2. Implement validated atomic storage and idempotent acknowledgement.
3. Align CLI errors and full Bash argv forwarding.
4. Validate fresh-process restart, malformed-state integrity, and documentation.

## Private known-good outline

The existing private implementation validates full state, writes atomically, rejects duplicate/unknown items, makes repeat ack a no-op, maps CLI errors, forwards `"$@"`, and updates tests/docs.

## Reproducibility and leakage controls

- fixed git author/date、single reachable commit、remote/tagなしで生成する。
- task中のnetworkを無効化し、親repository、generator source、他case、goldへ到達させない。
- visible tree、instruction set、capsule、catalog、recipeをdigest化する。
- evaluatorはnetworkなし・read-only workspace・credential mountなしで実行する。
- initial failとknown-good passを同じevaluator revisionで校正する。
