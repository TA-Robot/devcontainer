# F10-L-PYBASH-001: task and artifact contract

## Agent-visible task

Instrument and diagnose the multi-stage job simulator. Produce raw ledgers and `performance.json` separating queue, image probe, worker setup, provider wait, validation, cleanup, user wall time, worker union, and aggregate time across width blocks.

## Required result

- Events correlate by job/stage and maintain monotonic ordering.
- Parallel union and aggregate time are both computed without calling either true critical path unless reconstructable.
- Report distinguishes tail-causing global probe lock from per-job provider active time.
- Width/order/workload/environment and censoring are explicit; no real provider or Docker access is needed.

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

- `python3 -m unittest discover -s tests -v`
- `bash bin/run-batch --matrix visible --output observations`
- `python3 tools/validate_performance.py performance.json observations`

## Completion signal

必要artifactを所定pathへ書き、public validationを実行し、commandと結果をfinal responseへ短く記載する。hidden criterionは推測せず、明示契約とrepository evidenceへ適合させる。
