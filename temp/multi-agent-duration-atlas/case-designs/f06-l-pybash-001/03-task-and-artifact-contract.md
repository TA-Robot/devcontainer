# F06-L-PYBASH-001: task and artifact contract

## Agent-visible task

Complete the lifecycle integration harness without changing production. It must deterministically exercise concurrency, forced crash, restart, lease expiry/ownership, and cleanup, with bounded timeouts and no broad process/resource deletion.

## Required result

- Synchronization uses barriers/polls on explicit state, not arbitrary sleeps.
- Each phase starts/stops only owned processes and records diagnostics on failure.
- Harness kills all lifecycle mutant groups and passes the correct implementation repeatedly.

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

- `bash -n tests/lifecycle.sh`
- `python3 -m unittest discover -s tests -v`
- `bash tools/run-lifecycle-repeat.sh 5`
- `python3 tools/check_test_only.py`

## Completion signal

必要artifactを所定pathへ書き、public validationを実行し、commandと結果をfinal responseへ短く記載する。hidden criterionは推測せず、明示契約とrepository evidenceへ適合させる。
