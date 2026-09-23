# F11-S-BASH-001: task and artifact contract

## Agent-visible task

Fix the shell syntax defect in `sync-version.sh` with the smallest behavior-preserving change and run static plus smoke checks.

## Required result

- Patch fixes the exact parser error only.
- Version precedence/output in all smoke scenarios is unchanged.
- No dependency or unrelated formatting rewrite.

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

- `bash -n sync-version.sh`
- `bash tests/smoke.sh`

## Completion signal

必要artifactを所定pathへ書き、public validationを実行し、commandと結果をfinal responseへ短く記載する。hidden criterionは推測せず、明示契約とrepository evidenceへ適合させる。
