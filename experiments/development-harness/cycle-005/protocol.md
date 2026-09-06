# Cycle 005: CLI同期の失敗保全

Cycle 001〜004の比較・統合を引き継ぐ、新しい限定課題。題材はこのdevcontainer自身の起動時CLI同期。
外部projectは不要。公開要求は`brief.md`、公開fixtureは`sync_fixture.py`、固定評価は`evaluate_sync.py`。
前サイクルの評価器・得点・中断記録は変更しない。

## 比較するもの

Aは同じ公開検査を使える強いsoloの自己検証。Bは同じ情報と権限で開発し、提出後の公開検査失敗を
自動返却して残予算内で修正する。両条件とも自主検証・修正を禁止しない。初期source、model/effort、
CLI、image、公開要求、累積予算を揃える。P1の親時計へ検査・起動・停止・回収・修正を全て計上する。

本課題は単一の起動時更新経路を対象とする**小規模の比較**。失敗・中断・所有権の結合はあるが、
後続の追加要求を受けて発展させる大規模の継続開発ではない。3段階へ分けて規模を作らない。
当初の大規模先行案から、再現済みのこの限定課題を先に進める。既存の大規模比較結果は保持し、
新しいfeedback方式の大規模への効果は未測定として残す。小規模結果で代用しない。

## 評価の固定と校正

13項目で、正常更新・no-op・stable・無効化・不正入力・未指定CLI保持・取得失敗・SIGTERM・同時更新・
npm部分失敗・誤った版・実行ファイル欠損・SIGKILLを検査する。最後の4故障は独立評価で追加する。
公開fixtureの入力版は2.3.4、独立評価は8.6.5。要求は全て公開し、隠された追加要求を採点しない。
評価器がtemp prefixとinstaller stubを所有し、実file bytes/mode/link、CLI実行結果、process結果を確認する。
candidateの「成功」申告やcandidateが変更できるテスト件数から得点を計算しない。

正しい校正用実装、現行の部分更新、常時成功／常時失敗、所有権欠落、実行ファイル検証欠落で識別能力を確認する。
校正用の実装・hidden driverはdeveloper checkout/imageに入れない。評価は両条件終了後、networkなし・
read-only candidateの別containerで行う。source不変・完全な観測・元の提出／予算条件を要求する。

## この1組の上限

scopeはCycle 005の1組、ownerはprimary/integrator。数値は次の理由で開始前に固定し、結果を見て延長しない。
CLI/image/sourceや校正所要時間が変われば、開始前に新しいsealとして更新する。

| 項目 | 値 | 分類・根拠 |
| --- | --- | --- |
| 条件数・同時開発数 | A/B各1、直列 | cost cap。新方式の限定した探索で、資源競合を増やさない |
| 全開発時間 | 1,200秒／条件 | cost cap。以前の小規模枠を用い、今回から公開検査・修正・停止回収も含む |
| 観測output | 25,000／条件 | cost cap。完了turn通知で観測し、厳密なin-turn上限とは呼ばない |
| session・追加修正 | 最大3 session、追加2回 | cost cap。1回の初期提出と有限の修正。失敗するたび無制限に再起動しない |
| 開始／修正の最小予約 | 120秒、2,000 output | planning prior。検査・修正・回収の余地を残す |
| 公開検査 | 120秒／登録entrypoint | cost cap。校正の通常所要時間を上回り、停止不能な検査を有限に切る |
| 能力確認・独立評価 | 30秒／条件、180秒／成果 | cost cap。model要求なし。能力確認は両開発より先、独立評価は両開発終了後 |
| 停止・capture・取得窓 | 10秒・60秒・10秒 | cost cap、取得窓はhard guard。取得窓超過を同予算の成果にしない |
| 保存量 | source/archive最大512 MiB、公開出力64 KiB／entrypoint | cost cap。temp実験・oracleを除いたcheckoutとbounded feedback |
| source・停止・欠測・品質 | 全条件に適用 | hard guard。欠測をゼロ費用や合格にしない |

要求するmodel/effortは過去比較と同じ`gpt-6-astra/high`、Codexは`0.153.0`。
適用model値をproviderが示さなければunknownを維持する。通常の利用者設定は変更しない。
実行順は固定seed `cycle-005-cli-sync-v1`からSHA-256の先頭byteの偶奇で決め、manifestへ保存する。
1組では順序効果や一般的な速度改善を証明できない。runを成功するまで差し替えない。

source・image・順序・public sourceの実際のhashと準備確認は実行前のprivate sealへ保存する。
この文書だけをlive開始済みの記録にしない。準備と最終評価・統合費は開発時間と分離して報告する。
両元成果が品質・予算・取得窓を満たした場合だけ条件全体の速度比を計算する。
この比較は配布までの全面的な速度や金額を測るものではない。統合修正で元の得点を上書きしない。
