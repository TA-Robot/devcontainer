# F04-S-PY-001: task and artifact contract

## Agent-visible task

Implement `normalize_tag` so it accepts only ASCII alphanumerics, collapses space/underscore/hyphen/tab runs to one hyphen, lowercases, rejects empty/non-string results, and enforces 1–32 output characters. Run the listed tests.

## Required result

- Patch changes the normalizer and may update its public tests only.
- Output is deterministic and dependency-free.
- Error types distinguish non-string input from invalid normalized result.

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

## Completion signal

必要artifactを所定pathへ書き、public validationを実行し、commandと結果をfinal responseへ短く記載する。hidden criterionは推測せず、明示契約とrepository evidenceへ適合させる。
