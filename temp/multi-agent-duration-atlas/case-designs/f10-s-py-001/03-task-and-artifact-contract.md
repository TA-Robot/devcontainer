# F10-S-PY-001: task and artifact contract

## Agent-visible task

Diagnose the local report hot path and write `performance.json` with reproducible commands, raw observations, scaling evidence, root cause, and a safe optimization hypothesis. Do not patch production.

Revision 2 requires the author to use the identifiers published in `performance-contract.json`. The public contract fixes vocabulary and shape while the benchmark counters determine which candidate is primary.

## Required result

- Measurements include multiple input sizes and deterministic call counts.
- Root cause identifies repeated canonical serialization, not timing noise alone.
- The sort distractor is ruled out by comparative evidence.
- No universal speedup claim is made from one machine.

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
- `python3 bench.py --json > observed.json`
- `python3 tools/validate_performance.py performance.json observed.json`

## Completion signal

必要artifactを所定pathへ書き、public validationを実行し、commandと結果をfinal responseへ短く記載する。hidden criterionは推測せず、明示契約とrepository evidenceへ適合させる。
