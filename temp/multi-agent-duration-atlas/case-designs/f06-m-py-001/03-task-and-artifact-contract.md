# F06-M-PY-001: task and artifact contract

## Agent-visible task

Expand the retry policy tests using a clear table/property organization. Kill the documented status/method/attempt/delay mutants, use the fake clock, and leave production untouched.

## Required result

- Decision rows cover individual axes and at least the critical multi-axis interactions.
- Delay assertions are deterministic and capped.
- Failure messages identify the input row; no wall-clock sleep is used.

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
- `python3 tools/check_test_only.py`

## Completion signal

必要artifactを所定pathへ書き、public validationを実行し、commandと結果をfinal responseへ短く記載する。hidden criterionは推測せず、明示契約とrepository evidenceへ適合させる。
