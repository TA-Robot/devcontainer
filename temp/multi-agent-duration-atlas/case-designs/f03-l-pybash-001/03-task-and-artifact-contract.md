# F03-L-PYBASH-001: task and artifact contract

## Agent-visible task

Turn the intermittent duplicate-delivery failure into a deterministic crash/restart reproducer. Write `diagnosis.json` and `regression.sh` that demonstrate the causal ordering and fail on the seeded implementation; do not fix the worker.

## Required result

- Reproducer uses an explicit synchronization barrier rather than probabilistic sleeps.
- Diagnosis identifies side-effect-before-durable-ack ordering and retained offset on restart.
- Regression runs multiple lifecycle phases, cleans only owned resources, and has bounded timeout.
- Artifact distinguishes at-least-once semantics from an unsupported exactly-once claim.

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

- `bash -n regression.sh`
- `python3 tools/validate_diagnosis.py diagnosis.json`
- `bash tools/check-regression.sh regression.sh` (returns zero only when the exact seeded crash/restart failure is reproduced)

## Completion signal

必要artifactを所定pathへ書き、public validationを実行し、commandと結果をfinal responseへ短く記載する。hidden criterionは推測せず、明示契約とrepository evidenceへ適合させる。
