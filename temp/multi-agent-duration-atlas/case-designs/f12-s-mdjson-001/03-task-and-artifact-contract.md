# F12-S-MDJSON-001: task and artifact contract

## Agent-visible task

Synthesize the two analyses into `SYNTHESIS.md` and `synthesis.json`. Preserve agreements, adjudicate disagreements only from supplied sources, mark unsupported/unknown claims, and cite evidence IDs.

## Required result

- Every input claim receives a disposition.
- Environment-override disagreement is corrected to conditional behavior.
- Unsupported logging claim is not converted into fact.
- No new recommendation is added beyond evidence.

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

- `python3 tools/validate_synthesis.py synthesis.json SYNTHESIS.md`

## Completion signal

必要artifactを所定pathへ書き、public validationを実行し、commandと結果をfinal responseへ短く記載する。hidden criterionは推測せず、明示契約とrepository evidenceへ適合させる。
