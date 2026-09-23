# F04-L-PYBASH-001: task and artifact contract

## Agent-visible task

Complete the queue acknowledgement feature across storage, CLI, wrapper, tests, and format contract. It must be durable, atomic, idempotent, restart-safe, and preserve malformed/unknown state on error.

## Required result

- All cross-process artifacts follow one state/exit contract.
- Wrapper forwards arbitrary CLI arguments exactly.
- Restart validation uses fresh processes and the same persistent store.
- Unknown/malformed operations do not rewrite bytes.

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
- `bash -n bin/queuectl`

## Completion signal

必要artifactを所定pathへ書き、public validationを実行し、commandと結果をfinal responseへ短く記載する。hidden criterionは推測せず、明示契約とrepository evidenceへ適合させる。
