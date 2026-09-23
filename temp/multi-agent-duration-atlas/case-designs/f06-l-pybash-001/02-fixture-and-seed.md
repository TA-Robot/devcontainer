# F06-L-PYBASH-001: fixture and seeded state

## Disposable repository

| Visible path | Role | Initial state |
| --- | --- | --- |
| `lease/worker.py` | frozen correct worker | correct |
| `lease/store.py` | frozen lease state | correct |
| `bin/lease-worker` | process wrapper | working |
| `tests/test_unit.py` | unit coverage | passing but lifecycle-thin |
| `tests/lifecycle.sh` | integration target | skeleton |
| `tests/test_lifecycle.py` | orchestration target | skeleton |

agent workspaceには上表、`AGENTS.md`、public checksだけを置く。capsule、hidden evaluator、private known-good、base bundleはcontrol directoryへ隔離し、workspaceへmountしない。

## Seed

Mutants lose wakeups under two workers, retain a stale lease after crash, allow simultaneous owners after restart, or clean peer resources by prefix. Random sleeps can hide every defect.

初期fixtureは少なくとも一つのpublicまたはhidden criterionで必ずfailする。偶然passした場合はcase construction failureでありlive runを開始しない。

## Expected investigation or change path

1. Define observable synchronization points and ownership markers.
2. Build bounded two-worker, forced-crash, and fresh-restart phases.
3. Assert journal/lease state and cleanup after each phase.
4. Run each known-bad implementation repeatedly to prove deterministic rejection.

## Private known-good outline

Barrier-driven subprocess tests cover overlap, crash cut, lease expiry, fresh restart, owner uniqueness, scoped cleanup, repeated calibration, and preserve all production bytes.

Revision 2 renders the multi-path test-only allowlist in sorted order. Revision 1 used `repr(set(...))`, so different Python hash seeds could create distinct bundle digests under the same revision; those observations remain operational evidence but are not pooled across identities.

## Reproducibility and leakage controls

- fixed git author/date、single reachable commit、remote/tagなしで生成する。
- task中のnetworkを無効化し、親repository、generator source、他case、goldへ到達させない。
- visible tree、instruction set、capsule、catalog、recipeをdigest化する。
- evaluatorはnetworkなし・read-only workspace・credential mountなしで実行する。
- initial failとknown-good passを同じevaluator revisionで校正する。
