# F08-L-MDJSON-001: fixture and seeded state

## Disposable repository

| Visible path | Role | Initial state |
| --- | --- | --- |
| `requirements/` | functional/security/operations constraints | complete |
| `proposals/` | three competing fabric/persistence options | complete |
| `evidence/` | incident traces and benchmark summaries | complete |
| `simulator.py` | topology/failure/migration checks | working |
| `DESIGN.md` | target design record | absent |
| `design.json` | machine-readable topology/lifecycle | absent |

agent workspaceには上表、`AGENTS.md`、public checksだけを置く。capsule、hidden evaluator、private known-good、base bundleはcontrol directoryへ隔離し、workspaceへmountしない。

## Seed

Each proposal wins on one axis and fails another: direct subprocess lacks durable recovery, a database queue centralizes credentials/cleanup ownership, and per-provider daemons complicate migration/observability. Hidden scenarios combine crash, stale lease, credential rotation, partial migration, and UI disconnect.

初期fixtureは少なくとも一つのpublicまたはhidden criterionで必ずfailする。偶然passした場合はcase construction failureでありlive runを開始しない。

## Expected investigation or change path

1. Normalize constraints and evidence confidence without choosing early.
2. Model each option across topology, trust, persistence, failure, migration, and operations.
3. Select or compose a design with explicit invariants/APIs/ownership and rollback.
4. Run visible/hidden scenario classes, record counterexamples, unknowns, and operational signals.

## Private known-good outline

A finite job fabric separates durable intent/leases/events from provider adapters and fail-open UI, assigns credentials/cleanup explicitly, stages migration with dual-read and rollback export, simulates failure cuts, and records unresolved provider semantics.

## Reproducibility and leakage controls

- fixed git author/date、single reachable commit、remote/tagなしで生成する。
- task中のnetworkを無効化し、親repository、generator source、他case、goldへ到達させない。
- visible tree、instruction set、capsule、catalog、recipeをdigest化する。
- evaluatorはnetworkなし・read-only workspace・credential mountなしで実行する。
- initial failとknown-good passを同じevaluator revisionで校正する。
