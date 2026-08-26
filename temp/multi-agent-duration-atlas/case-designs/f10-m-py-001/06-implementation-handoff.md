# F10-M-PY-001: implementation handoff

## Exclusive implementation scope

- recipe module: `scripts/agent_duration_cases/f10.py`
- catalog fragment: `experiments/multi-agent-duration/catalog/families/f10.json`
- capsule: `experiments/multi-agent-duration/capsules/f10-m-event-cache-performance.md`
- focused test: `scripts/test-agent-duration-case-f10.py`

同familyの3 sizeは一つのmodule/fragment/testへまとめてよい。共有registry、schema、aggregate `cases.json`、generic fixture runner、reporterは変更しない。

## Implementation requirements

- recipeは`case_id/files/hidden/good/executable`の共通interfaceを満たし、stdlibだけで構成する。
- initial state、plausible negative mutant、private known-goodを同じsource contractから校正できるようにする。
- hidden check IDはこの設計と一致させ、criterionごとのpass/failを保持する。
- capsule digest、catalog descriptor、visible path allowlistを実体と一致させる。

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
