# F07-L-MDPYBASH-001: task and artifact contract

## Agent-visible task

Bring `ARCHITECTURE.md`, `MIGRATION.md`, and `RECOVERY.md` into agreement with the visible implementation. Add `docs-index.json` linking facts, commands, owners, and cross-document anchors. Commands must replay safely.

## Required result

- Current versus target state and compatibility window are explicit.
- Rollout, verification, abort, rollback export, and recovery ownership are consistent across documents.
- Every executable command maps to a real CLI surface and ordered preconditions.
- Links/anchors resolve and no document silently contradicts the manifest.

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

- `python3 tools/check_docs_index.py docs-index.json`
- `python3 tools/check_links.py docs`
- `bash tools/replay_migration_docs.sh docs-index.json`

## Completion signal

必要artifactを所定pathへ書き、public validationを実行し、commandと結果をfinal responseへ短く記載する。hidden criterionは推測せず、明示契約とrepository evidenceへ適合させる。
