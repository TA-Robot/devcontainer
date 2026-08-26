# F03-M-PY-001: task and artifact contract

## Agent-visible task

Diagnose why the expiry integration test fails only after reload. Produce a causal chain, reproducer commands, evidence, and regression-test plan in `diagnosis.json`; do not fix source.

## Required result

- Causal chain begins at deserialization and ends at retention branch.
- Reproducer contrasts fresh versus persisted state.
- Regression plan includes deserializer contract and end-to-end reload expiry.
- Scheduler boundary distractor is explicitly ruled out by evidence.

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

- `python3 tools/confirm_seeded_failure.py --test tests.test_expiry --signature reload-retained`
- `python3 tools/validate_diagnosis.py diagnosis.json`

## Completion signal

必要artifactを所定pathへ書き、public validationを実行し、commandと結果をfinal responseへ短く記載する。hidden criterionは推測せず、明示契約とrepository evidenceへ適合させる。
