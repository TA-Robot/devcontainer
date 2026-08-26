# F10-M-PY-001: task and artifact contract

## Agent-visible task

Instrument the summarizer and produce `performance.json` comparing I/O, decoding, and cache hypotheses across cold and warm workloads. Preserve output behavior; include reproducible commands and raw observation file paths.

## Required result

- Counters and phase timing are attributable without changing functional output.
- Cold and warm/repeated workloads are separated.
- Report identifies cache-key dominance conditionally and quantifies decode/I/O secondary costs.
- Measurement order, run count, environment, and uncertainty are recorded.

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
- `python3 bench.py --instrument instrumentation.py --output observations.json`
- `python3 tools/validate_performance.py performance.json observations.json`

## Completion signal

必要artifactを所定pathへ書き、public validationを実行し、commandと結果をfinal responseへ短く記載する。hidden criterionは推測せず、明示契約とrepository evidenceへ適合させる。
