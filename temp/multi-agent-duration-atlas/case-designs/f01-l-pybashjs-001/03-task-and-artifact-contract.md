# F01-L-PYBASHJS-001: task and artifact contract

## Agent-visible task

Produce a cross-boundary lifecycle trace from devcontainer rebuild through Mira world rendering. Include host/container/extension trust labels, success edges, restart recovery, and failure ownership. Do not modify the fixture.

## Required result

- Required lifecycle nodes cover rebuild, host initialize, container post-start, provider event, agentctl envelope, hook state, extension state read, and render.
- Every cross-boundary edge declares transported artifact and owner.
- Recovery graph covers missing wrapper, stale runtime state, and extension restart without inventing legacy-wrapper participation.

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
- `bash tests/lifecycle-smoke.sh`
- `node --test extension/test/*.test.js`
- `python3 tools/validate_trace.py trace.json`

## Completion signal

必要artifactを所定pathへ書き、public validationを実行し、commandと結果をfinal responseへ短く記載する。hidden criterionは推測せず、明示契約とrepository evidenceへ適合させる。
