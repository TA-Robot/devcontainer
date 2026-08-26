# F08-S-MDJSON-001: task and artifact contract

## Agent-visible task

Compare the two configuration APIs against the supplied constraints and callers. Write `DECISION.md` and `decision.json` with choice, tradeoffs, counterexamples, and unresolved assumptions; do not implement either API.

## Required result

- All five constraints are evaluated with evidence.
- At least one executable or concrete counterexample challenges each raw option.
- The selected design states deletion and request-isolation semantics.
- Unknowns remain explicit rather than invented.

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

- `python3 tools/validate_decision.py decision.json DECISION.md`
- `python3 -m unittest discover -s tests -v`

## Completion signal

必要artifactを所定pathへ書き、public validationを実行し、commandと結果をfinal responseへ短く記載する。hidden criterionは推測せず、明示契約とrepository evidenceへ適合させる。
