# F01-M-PYJS-001: task and artifact contract

## Agent-visible task

Trace a successful `tool_end` event from hook input to the renderer and document both malformed-input and atomic-write failure behavior. Write the versioned `trace.json`; make no code changes.

## Required result

- Success graph crosses Python-to-JSON-to-JavaScript with required schema fields.
- Malformed input and store failure have separate branch records.
- Evidence locations identify symbols and contract field names, not line numbers alone.

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
- `node --test media/test/*.test.js`
- `python3 tools/validate_trace.py trace.json`

## Completion signal

必要artifactを所定pathへ書き、public validationを実行し、commandと結果をfinal responseへ短く記載する。hidden criterionは推測せず、明示契約とrepository evidenceへ適合させる。
