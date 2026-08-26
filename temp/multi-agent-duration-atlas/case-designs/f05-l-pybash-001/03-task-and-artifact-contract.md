# F05-L-PYBASH-001: task and artifact contract

## Agent-visible task

Complete the backend/schema migration with v1 read compatibility, atomic resumable upgrade, rollback export, backend selection through Python and Bash, and operator documentation. Preserve old contract tests.

## Required result

- Callers depend on backend interface, not file implementation details.
- Migration order never exposes a v2 marker with incomplete v2 data.
- Interrupted migration resumes safely and rollback exports valid v1 state.
- Wrapper and docs expose exact selection/recovery commands.

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
- `bash -n bin/jobctl`
- `bash tests/migration-lifecycle.sh`
- `python3 tools/check_docs.py MIGRATION.md`

## Completion signal

必要artifactを所定pathへ書き、public validationを実行し、commandと結果をfinal responseへ短く記載する。hidden criterionは推測せず、明示契約とrepository evidenceへ適合させる。
