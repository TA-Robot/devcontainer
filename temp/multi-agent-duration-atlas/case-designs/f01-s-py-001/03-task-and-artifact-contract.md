# F01-S-PY-001: task and artifact contract

## Agent-visible task

Explain where `--state-dir` is defined and how its value reaches ownership validation. Produce `trace.json` using the documented node/edge schema and cite repository paths plus symbols; do not edit production code.

## Required result

- Ordered nodes for definition, parsed field, dispatch argument, normalization, marker validation, and consumer.
- Directed edges whose endpoints reference declared node IDs.
- Every node cites an existing path and symbol; uncertainty is explicit rather than invented.

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
- `python3 tools/validate_trace.py trace.json`

## Completion signal

必要artifactを所定pathへ書き、public validationを実行し、commandと結果をfinal responseへ短く記載する。hidden criterionは推測せず、明示契約とrepository evidenceへ適合させる。
