# F04-L-PYBASH-001: implementation handoff

## Exclusive implementation scope

- recipe module: `scripts/agent_duration_cases/f04.py`
- catalog fragment: `experiments/multi-agent-duration/catalog/families/f04.json`
- capsule: `experiments/multi-agent-duration/capsules/f04-l-python-bash-restart.md`
- focused test: `scripts/test-agent-duration-case-f04.py`

同familyの3 sizeは一つのmodule/fragment/testへまとめてよい。共有registry、schema、aggregate `cases.json`、generic fixture runner、reporterは変更しない。

## Implementation requirements

- Preserve all existing evidence and revision identifiers.
- Add revisioned criterion granularity and mutant calibration without relabeling prior runs.
- Use the recorded Sol/Grok depth curve as historical evidence; execute collaboration blocks only after the new rubric discriminates.

## Definition of Done

1. catalog fragmentとcase schemaがvalidateする。
2. 同一時刻で二回生成したfixtureのsnapshot inventory/digestが再現する。
3. initial evaluatorがfailし、private known-goodがpublic/hidden全criterionをpassする。
4. 各negative mutantが意図したcriterionでrejectされるfocused testがある。
5. network-disabled read-only isolated evaluatorで同じscoreが得られる。

## Stop and return to primary when

- 現行recipe interfaceではrubricを安全に表現できない。
- hidden evaluatorをagent workspaceへ見せないと評価できない。
- network、host credential、shared Docker socket、親workspace writeが必要になる。
- case wording、profile、criterionを変えないとknown-good calibrationが通らない。
- 同family外または共有fileの変更が必要になる。

返却時は変更file、校正結果、実行したtest、残るriskを簡潔に報告する。case設計の再解釈やglobal recommendationはprimaryが担当する。
