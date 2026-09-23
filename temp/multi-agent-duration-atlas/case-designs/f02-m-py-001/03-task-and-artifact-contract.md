# F02-M-PY-001: task and artifact contract

## Agent-visible task

Review the proposed multi-file change. Produce ranked `review.json` findings with separate triggers, interaction impact, evidence, and remediation constraints; do not modify source.

## Required result

- Both seeded defects are distinct findings with reproducible triggers.
- Ranking explains why the interaction increases blast radius.
- Evidence maps findings to changed lines and affected callers.
- No unsupported blocking finding targets the safe logging change.

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
