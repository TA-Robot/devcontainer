# F07-M-MDBASH-001: task and artifact contract

## Agent-visible task

Create `RUNBOOK.md` and `runbook.json` for state-corruption diagnosis and recovery. Commands must be copyable, bounded, evidence-preserving, and replayable by the provided sandbox; do not change runtime code.

## Required result

- Diagnosis precedes mutation and captures evidence.
- Backup existence and digest are verified before atomic restore.
- Only the fixture-owned service is restarted, followed by state and health validation.
- Failure branches cover missing/invalid backup without deleting current evidence.

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

- `python3 tools/check_runbook.py RUNBOOK.md runbook.json`
- `bash tools/replay_runbook.sh runbook.json healthy`
- `bash tools/replay_runbook.sh runbook.json corrupt`

## Completion signal

必要artifactを所定pathへ書き、public validationを実行し、commandと結果をfinal responseへ短く記載する。hidden criterionは推測せず、明示契約とrepository evidenceへ適合させる。
