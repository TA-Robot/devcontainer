# F09-L-PYBASHDOCKER-001: task and artifact contract

## Agent-visible task

Create `THREAT-MODEL.md` and `threat-model.json` for the worktree/container/credential/cleanup system. Include evidence-linked threats, attack paths, controls, negative tests, detection, recovery ownership, and residual unknowns.

## Required result

- All seeded assets/boundaries/lifecycle phases have an owner and trust assumption.
- Each seeded attack has reproducible evidence, impact, preventive/detective control, and negative test.
- Controls compose safely across Git, Docker, credentials, and cleanup; ownership tokens prevent peer deletion.
- Unknown kernel/provider guarantees remain explicit.

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

- `python3 tools/validate_threat_model.py threat-model.json THREAT-MODEL.md`
- `bash scenarios/run-visible-attacks.sh threat-model.json`
- `python3 -m unittest discover -s tests -v`

## Completion signal

必要artifactを所定pathへ書き、public validationを実行し、commandと結果をfinal responseへ短く記載する。hidden criterionは推測せず、明示契約とrepository evidenceへ適合させる。
