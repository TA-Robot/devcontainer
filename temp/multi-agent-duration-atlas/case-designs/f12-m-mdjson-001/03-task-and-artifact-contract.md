# F12-M-MDJSON-001: task and artifact contract

## Agent-visible task

Adjudicate the independent reviews using only supplied source/test/exploit evidence. Write `ADJUDICATION.md` and `adjudication.json` with claim provenance, disposition, decisive evidence, narrowed severity, and unresolved unknowns.

## Required result

- Duplicate claims are merged without losing reviewer provenance.
- Race finding is accepted and canonicalization-is-sufficient claim rejected by replay.
- Windows junction claim remains unknown with a stated missing test surface.
- Credential impact is narrowed to evidence-supported workspace escape.

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

- `bash evidence/exploit.sh`
- `python3 tools/validate_adjudication.py adjudication.json ADJUDICATION.md`

## Completion signal

必要artifactを所定pathへ書き、public validationを実行し、commandと結果をfinal responseへ短く記載する。hidden criterionは推測せず、明示契約とrepository evidenceへ適合させる。
