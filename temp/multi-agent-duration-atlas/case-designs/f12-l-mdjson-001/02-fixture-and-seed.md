# F12-L-MDJSON-001: fixture and seeded state

## Disposable repository

| Visible path | Role | Initial state |
| --- | --- | --- |
| `proposals/` | four architecture proposals | complete |
| `evidence/benchmarks/` | raw distributions and summaries | complete |
| `evidence/incidents/` | failure/recovery reports | complete |
| `evidence/security/` | threat findings | complete |
| `constraints.json` | migration/operations requirements | complete |
| `decision-contract.json` | public vocabulary and bounded decision space | complete |
| `DECISION-RECORD.md` | target human artifact | absent |
| `decision-record.json` | target claim/evidence graph | absent |

agent workspaceには上表、`AGENTS.md`、public checksだけを置く。capsule、hidden evaluator、private known-good、base bundleはcontrol directoryへ隔離し、workspaceへmountしない。

## Seed

Proposal A has best warm median but poor cold tail and a cleanup incident. B is slower but strongest isolation. C's throughput claim uses invalid pooled samples. D eases migration but leaves recovery ownership unclear. A sound record uses D as the legacy-compatible bridge and may select A or B as a later target when the selected target's evidence and controls are explicit. It must not fabricate a universal winner.

初期fixtureは少なくとも一つのpublicまたはhidden criterionで必ずfailする。偶然passした場合はcase construction failureでありlive runを開始しない。

## Expected investigation or change path

1. Normalize claims, conditions, evidence confidence, distributions, and invalid samples.
2. Map each proposal to constraints, incidents, security, migration, and workload-specific metrics.
3. Resolve contradictions with decisive evidence; retain unknowns and rejected unsupported claims.
4. Construct decision, staged gates, rollback triggers, counterfactual risks, and evidence-refresh plan.

## Private known-good outline

A claim graph rejects invalid pooled metrics, conditions performance by workload, integrates cleanup/security incidents, selects a staged design with measured gates, defines migration/rollback/ownership, and leaves unmeasured recovery/provider semantics open.

Revision 2 calibrates two semantically distinct valid artifacts: a D→B target and a D→A target with different control, unknown, and trigger IDs.

## Reproducibility and leakage controls

- fixed git author/date、single reachable commit、remote/tagなしで生成する。
- task中のnetworkを無効化し、親repository、generator source、他case、goldへ到達させない。
- visible tree、instruction set、capsule、catalog、recipeをdigest化する。
- evaluatorはnetworkなし・read-only workspace・credential mountなしで実行する。
- initial fail、known-good pass、declared valid alternative passを同じevaluator revisionで校正する。
