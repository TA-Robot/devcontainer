# F03-S-PY-001: task and artifact contract

## Agent-visible task

Diagnose the failing test without modifying source. Write `diagnosis.json` with root cause, minimal reproducer command/input, evidence, and a concrete regression-test proposal.

## Required result

- Root cause identifies truthiness fallback and explicit-zero semantics.
- Reproducer is executable and yields the observed wrong value.
- Regression proposal covers both missing and zero, preventing a one-sided fix.

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

- `python3 tools/confirm_seeded_failure.py --test tests.test_limits --signature explicit-zero`
- `python3 tools/validate_diagnosis.py diagnosis.json`

## Completion signal

必要artifactを所定pathへ書き、public validationを実行し、commandと結果をfinal responseへ短く記載する。hidden criterionは推測せず、明示契約とrepository evidenceへ適合させる。
