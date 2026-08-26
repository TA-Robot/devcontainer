# F08-M-MDJSON-001: task and artifact contract

## Agent-visible task

Design the scheduler/supervisor/store responsibility split. Produce `PROPOSAL.md` and `proposal.json` with invariants, state ownership, APIs, failure transitions, option comparison, counterexamples, migration outline, and unresolved unknowns.

## Required result

- Every durable versus ephemeral datum has one owner.
- Restart/cancel/retry/timeout traces preserve at-least-once and bounded retry invariants.
- Rejected options have fixture-grounded counterexamples.
- Migration and observability requirements are explicit.

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

- `python3 tools/validate_proposal.py proposal.json PROPOSAL.md`
- `python3 simulator.py --proposal proposal.json --all-scenarios`

## Completion signal

必要artifactを所定pathへ書き、public validationを実行し、commandと結果をfinal responseへ短く記載する。hidden criterionは推測せず、明示契約とrepository evidenceへ適合させる。
