# F03-L-PYBASH-001: fixture and seeded state

## Disposable repository

| Visible path | Role | Initial state |
| --- | --- | --- |
| `worker.py` | delivery and acknowledgement | acks buffered after side effect |
| `journal.py` | persistent offset | flush API available |
| `bin/restart-repro` | crash/restart harness | nondeterministic default timing |
| `tests/test_lifecycle.py` | failing repeated lifecycle | reports occasional duplicate |
| `diagnosis.json` | required root-cause artifact | absent |
| `regression.sh` | required deterministic regression proposal | absent |

agent workspaceには上表、`AGENTS.md`、public checksだけを置く。capsule、hidden evaluator、private known-good、base bundleはcontrol directoryへ隔離し、workspaceへmountしない。

## Seed

The worker emits the external side effect before synchronously persisting its ack. A hidden deterministic barrier can terminate in that window. Guessing at random sleeps is a distractor and creates flaky tests.

初期fixtureは少なくとも一つのpublicまたはhidden criterionで必ずfailする。偶然passした場合はcase construction failureでありlive runを開始しない。

## Expected investigation or change path

1. Instrument/reason about delivery, side effect, ack append, and fsync ordering.
2. Use the provided barrier surface to force termination in the vulnerable window.
3. Restart and prove duplicate delivery from retained offset.
4. Write a deterministic regression harness and causal diagnosis without patching production.

## Private known-good outline

A barrier-driven script pauses after side effect/before durable ack, kills only the owned worker, restarts against the same journal, observes duplicate delivery, and records the causal journal states.

## Reproducibility and leakage controls

- fixed git author/date、single reachable commit、remote/tagなしで生成する。
- task中のnetworkを無効化し、親repository、generator source、他case、goldへ到達させない。
- visible tree、instruction set、capsule、catalog、recipeをdigest化する。
- evaluatorはnetworkなし・read-only workspace・credential mountなしで実行する。
- initial failとknown-good passを同じevaluator revisionで校正する。
