# F02-L-PYBASHJS-001: task and artifact contract

## Agent-visible task

Review the complete lifecycle change and write ranked findings with concrete reproduction evidence for normal/error/restart/cleanup paths. Do not patch the proposal.

## Required result

- All three seeded lifecycle defects are separate, reachable findings.
- Each trigger names boundary inputs and observed unsafe outcome.
- Findings cite cross-stack evidence and propose constraints that preserve fail-open behavior.
- Distractor CSS/comments are not blocking findings.

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

- `bash tests/replay-review-surface.sh`
- `python3 -m unittest discover -s tests -v`
- `node --test extension/test/*.test.js`
- `python3 tools/validate_review.py review.json`

## Completion signal

必要artifactを所定pathへ書き、public validationを実行し、commandと結果をfinal responseへ短く記載する。hidden criterionは推測せず、明示契約とrepository evidenceへ適合させる。
