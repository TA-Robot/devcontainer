# Duration atlas case designs

このdirectoryは、`02-size-model-and-task-corpus.md`の12 family × S/M/L、合計36 candidateを、実装可能なversioned fixtureへ落とすための設計正本です。36件は今回のcorpus completion scopeですが、1件の実測をfamilyの代表値へ昇格したり、未測定configurationを補間したりはしません。

## 一件あたりの6文書

各case directoryは、必ず次の6文書だけを持ちます。

1. `01-profile-and-question.md`: 測定質問、構造size、profile axis、scope
2. `02-fixture-and-seed.md`: disposable repository、初期状態、seed、gold隔離
3. `03-task-and-artifact-contract.md`: agentへ見せるtask、成果物、path/tool境界
4. `04-oracle-and-quality-rubric.md`: public/hidden criterion、negative mutant、採点限界
5. `05-execution-and-analysis.md`: model/effort/collaboration block、timeout、順序、解釈
6. `06-implementation-handoff.md`: 実装所有範囲、必要file、test、Definition of Done

`01`〜`05`はprimary agentが測定意図を所有する設計です。`06`はその設計を変更せずに実装するためのbounded handoffです。実装担当はcaseの意味、rubric、case ID、capsule wordingを独断で変更しません。変更が必要なら実装せずprimaryへ差し戻します。

## Corpus completionとmeasurement maturity

- `designed`: 6文書が揃い、内部矛盾・placeholderがない
- `implemented`: capsule、catalog entry、recipe、hidden evaluator、known-good calibrationがある
- `calibrated`: initial fixtureがfailし、private known-goodが全criterion passする
- `observed`: 少なくとも一つのvalid live runがある
- `characterized`: 複数case/観測blockなど、atlas本体のpromotion条件を満たす

今回「全ケースを終える」とは、36件を最低でも`calibrated`へ到達させ、明示した有限execution matrixを実行して各観測を正直なevidence stateで残すことです。`characterized`はsample diversityが満たされたcellだけに付け、件数を埋めるために捏造しません。

## Parallel implementation contract

family実装は次のexclusive pathへ分離します。

- recipe: `scripts/agent_duration_cases/fXX.py`
- catalog fragment: `experiments/multi-agent-duration/catalog/families/fXX.json`
- capsule: `experiments/multi-agent-duration/capsules/fXX-*.md`
- focused test: `scripts/test-agent-duration-case-fXX.py`

共有registry、schema、aggregate catalog、runner、cross-family testはprimaryだけが編集します。これにより、複数subagentが同じcentral fileへ同時編集する事故を避けます。

## Design audit

`_render_case_designs.py`はprimaryが作成した構造化設計から6文書を再生成し、次を検査します。

- 12 family × 3 sizeが一意に存在する
- 各caseに6文書がある
- 必須profile axis、seed、requirements、public/hidden criterion、negative mutant、known-good、handoffが空でない
- `TBD`、`TODO`、`FIXME`を残さない
- case ID、family、size、profile IDが文書間で一致する

生成物は設計review対象であり、generatorが妥当性を保証するわけではありません。rubricがtaskを識別できるか、深い推論のquality差を潰していないかは、primaryがnegative mutantとknown-good calibrationをreviewします。
