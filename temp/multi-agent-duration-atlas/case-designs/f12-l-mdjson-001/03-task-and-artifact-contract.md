# F12-L-MDJSON-001: task and artifact contract

## Agent-visible task

Integrate all proposals and evidence into `DECISION-RECORD.md` and `decision-record.json`. Preserve workload conditions and uncertainty, reject invalid/unsupported claims, state the selected or staged design, alternatives, gates, rollback, risks, unknowns, and evidence refresh conditions.

## Required result

- Every material proposal claim and hard constraint has provenance/disposition.
- Benchmark distributions retain workload, sample, censoring, and invalid-run boundaries.
- Incidents/security findings affect the decision rather than appearing as appendices only.
- Decision gates and rollback triggers are testable; unknown recovery/provider assumptions remain explicit.
- No provider/model/global architecture winner is inferred beyond evidence.

## Allowed work

- fixture内のsource、tests、docsを読み、repository-containedなlocal commandを実行する。
- taskで指定されたartifact pathだけを作成・変更する。
- 一時fileはfixture内またはprocess-owned temporary directoryだけに作る。

## Forbidden work

- network、親directory、control directory、hidden/gold artifactを読むこと。
- commit、push、remote追加、credential探索、別caseの参照。
- public checkやproduction behaviorを削除・skip・緩和してpassさせること。
- 契約外pathの変更。必要性を発見した場合は成果物へunknown/blockerとして残す。

## Public validation

- `python3 tools/validate_decision_record.py decision-record.json DECISION-RECORD.md`
- `python3 tools/recompute_metrics.py evidence/benchmarks decision-record.json`
- `python3 tools/check_entailment.py decision-record.json`

## Completion signal

必要artifactを所定pathへ書き、public validationを実行し、commandと結果をfinal responseへ短く記載する。hidden criterionは推測せず、明示契約とrepository evidenceへ適合させる。
