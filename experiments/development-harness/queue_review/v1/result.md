# Queue review pilot v1: 実測と採否

2026-09-06。固定した2組・全4conditionを完了。**この課題で常時の独立reviewは採用しない。**
全条件が外部の動作4項目を満たした一方、review付きは両組で時間とinput/outputが増えた。
一般的なreviewの価値や、未使用の確認条件への効果までは判断しない。

[protocol](protocol.md)・[実行入口](README.md)・[原結果に結び付いた集計](result.json)。
実行source commitは`89410fa`、taskは`queue-review-repair-v1`。
Codex CLI 0.153.0、要求model gpt-6-astra/high、resolved model/applied effortはunknown。
各condition 600秒/output 12000の固定枠。review側はreviewer→fresh makerと受渡しで共有した。

## 実測

時間はcondition開始から、提出・停止・保全を終えるまで。外部採点と事前準備は別計測。
inputはcacheを含む総inputであり、金額ではない。

| 初期実装 | 方式 | 外部動作 | 提出まで（秒） | input | cached input | output |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| 欠陥あり | solo | 4/4 | 96.055 | 102487 | 91904 | 2001 |
| 欠陥あり | review→maker | 4/4 | 176.978 | 191367 | 159104 | 3637 |
| 正しい実装 | solo | 4/4 | 63.777 | 82379 | 73088 | 1192 |
| 正しい実装 | review→maker | 4/4 | 184.508 | 208077 | 176640 | 3641 |

欠陥ありでは、review付きの時間84.2%増、input86.7%増、output81.8%増。
正しい実装では、時間189.3%増、input152.6%増、output205.5%増。
品質を満たした提出時間の比（review/solo）は、それぞれ1.842、2.893。
どちらも事前の改善候補条件（時間90%以下・input/output各110%以下）を満たさない。

欠陥ありの両成果は`queue_store.py`と`bin/queuectl`を変更し、`tests/test_repair.py`を追加した。
正しい初期実装では両成果とも変更pathは0で、4/4を維持した。変更を強制する比較にはしていない。
reviewを経由した方だけが到達した動作項目はなかった。reviewの指摘数や文章は採点していない。

初期状態も同じ外部評価で確認した。欠陥ありは不合格、正しい実装は4/4。
初期の引数再分割は全probeのCLI開始を妨げるため、失敗項目数を独立した欠陥数とは数えない。
提出後は通常の別process実行、引数境界、不正状態の保全、enqueue/ack更新の旧reader保全を確認した。

## 費用・停止・出典

各組の事前準備は15.752秒/23.441秒、組全体は312.469秒/294.470秒。
外部採点は各提出10.945〜11.518秒。上表の提出時間とは分けて保持する。
reviewとmakerの全usageを加算し、全6participantの停止・回収・container削除を確認した。
専用の評価containerも残留なし、private認証copy2件は削除済み。通常devcontainerは変更していない。

privateな出典は `/home/asakura/.local/state/development-harness/queue-review-pilot-v1-20260906-01/`。
`plan.json`に順序・全config・source commit・protocol/校正/検証/controllerのhashを事前保存し、
同じdirの再実行を拒否した。固定controllerはrepair→preserveの順に一度ずつ実行し、再試行しなかった。
`interpretation.json`は固定criteriaに基づく集計で、公開result.jsonはその同一bytesのcopy。
各組の`result.json`、`seal.json`、`queue-summary.json`、controllerのhash一致を確認した。
元artifact・advice・イベント列はprivateな証跡へ残す。意味上のreview採用はunknownとする。

実行前には正当な2実装と欠陥7実装の公開/外部判定を校正し、実Dockerを含む9テストを確認した。
校正・疑似providerの成功は、上表の実モデル結果と分ける。旧F04/F12のoracle・得点・atlasは更新していない。

## ハーネスへ戻す判断

この公開checkを自由に使える小課題では、常時reviewの品質上積みを確認できず、追加費用が生じた。
そのため、この条件で独立reviewを自動追加する既定は作らない。
「reviewが可能だから必ず呼ぶ」ことと、「残った不確実性を解くために呼ぶ」ことを区別する。

次の比較候補は、まず自分で公開検査・修正を進め、それでも残った具体的な不足を相談理由として
渡す方式。起動判断・自己検査にも費用を計上し、同じ協働能力と全予算で改良前後を比較する。
この条件付き起動の効果はまだ実測しておらず、推奨や改善率は付けない。
留保したconfirmationはlive未使用のまま、新しいprotocolでの確認へ残す。

各scenarioは1組だけで、固定された順序、同一family、provider cacheや時点の影響が残る。
今回の4項目は書込み中のkill、電源断、並行writer、一般設計品質、継続開発能力を測っていない。
この結果を複雑な実案件、途中相談、複数実装の選択、他providerへ一般化しない。
