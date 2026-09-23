# F11-L-BASHDOCKER-001: task and artifact contract

## Agent-visible task

Repair the simulated devcontainer rebuild/reopen lifecycle. Preserve persistent state through interrupted migration, verify host/extension markers, resume or roll back non-destructively, and document operator recovery in `RECOVERY.md`.

## Required result

- Migration stages outside the only source and commits version/data atomically.
- Every marker contains/verifies the artifact version it represents and has one owner.
- Reopen repairs interrupted host, extension, or volume stages idempotently.
- No broad volume/workspace deletion; rollback/export and diagnostics are documented/executable.

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

- `bash -n initialize-host.sh post-create.sh post-start.sh tests/rebuild.sh`
- `python3 -m unittest discover -s tests -v`
- `bash tests/rebuild.sh --scenario visible-all`
- `python3 tools/check_recovery_docs.py RECOVERY.md`

## Completion signal

必要artifactを所定pathへ書き、public validationを実行し、commandと結果をfinal responseへ短く記載する。hidden criterionは推測せず、明示契約とrepository evidenceへ適合させる。
