# F08-L-MDJSON-001: task and artifact contract

## Agent-visible task

Produce `DESIGN.md` and `design.json` for the execution fabric/persistence architecture. Cover alternatives, topology, trust boundaries, durable/ephemeral state, failure recovery, migration/rollback, credential ownership, cleanup, observability, and unresolved evidence gaps.

## Required result

- All requirement/evidence IDs receive supported disposition.
- Topology and state transitions have single ownership and bounded lifecycle.
- Migration is staged, observable, abortable, and non-destructive.
- Threat/failure counterexamples challenge the selected and rejected options.
- Companion/UI is fail-open and never controls job correctness.

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

- `python3 tools/validate_design.py design.json DESIGN.md`
- `python3 simulator.py --design design.json --scenario-set visible`
- `bash tools/replay_migration.sh design.json visible`

## Completion signal

必要artifactを所定pathへ書き、public validationを実行し、commandと結果をfinal responseへ短く記載する。hidden criterionは推測せず、明示契約とrepository evidenceへ適合させる。
