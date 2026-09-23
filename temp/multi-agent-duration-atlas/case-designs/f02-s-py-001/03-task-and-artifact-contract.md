# F02-S-PY-001: task and artifact contract

## Agent-visible task

Review `change.diff` for correctness/security regressions. Write `review.json` with ranked findings, concrete trigger, impact, and source evidence. Do not patch the code.

## Required result

- Finding identifies the prefix-containment flaw on the changed line.
- Trigger uses a concrete peer-prefix path and explains why it passes.
- Severity and remediation direction are justified; unrelated safe lines are not flagged.

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
- `python3 tools/validate_review.py review.json`

## Completion signal

必要artifactを所定pathへ書き、public validationを実行し、commandと結果をfinal responseへ短く記載する。hidden criterionは推測せず、明示契約とrepository evidenceへ適合させる。
