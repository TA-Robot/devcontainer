# F11-M-BASH-001: task and artifact contract

## Agent-visible task

Fix version synchronization and restart recovery. Normalize metadata safely, install only when versions differ, commit ready only after verification, and recover from an interrupted install without broad state deletion.

## Required result

- Canonical comparison handles CRLF/trailing whitespace but rejects multiline/invalid values.
- Ready marker is atomic and tied to verified installed version.
- Failed install/restart retries safely; matching version performs no install.
- Cleanup touches only fixture-owned temporary artifacts.

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

- `bash -n initialize-host.sh post-start.sh install-cli tests/lifecycle.sh`
- `bash tests/lifecycle.sh`

## Completion signal

必要artifactを所定pathへ書き、public validationを実行し、commandと結果をfinal responseへ短く記載する。hidden criterionは推測せず、明示契約とrepository evidenceへ適合させる。
