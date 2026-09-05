# Cycle 003: 速度・品質の比較に向けた準備

状態: 品質評価器の校正、検証能力の切り分け、起動待ちの修正と回帰確認まで終了。
新しいモデル開発の対照比較はまだ開始していない。今回の確認はすべてprovider-freeで、
開発用モデルの追加呼出しは0件。課題と運用条件を未確定のままliveを増やさない。

## 品質の差を検出できる評価器

[評価器と手順](../../experiments/development-harness/quality/README.md)を実装した。
要求単位の観測を8項目に整理し、38の動作確認へ対応づける。件数を品質点として
足さず、合格・不合格・未確認を根拠付きで返す。旧35シナリオのsourceとcycle-002の
記録は変更していない。新しい検査は、既知の不足を使った校正として区別する。

前回の同じ停止済みsourceを、認証情報なし・networkなし・read-only mountの
共通imageで評価した。3つのsource hashが前回の記録と一致し、検証中も不変だった。

| 要求 | 対照成果 | 改良成果 | 統合成果 |
| --- | --- | --- | --- |
| 導入、読み取り・再実行、更新、計画の前提、復旧・取り消し | 合格 | 合格 | 合格 |
| 配置元と配置先の境界 | 不合格 | 不合格 | 合格 |
| 内容・実行bitが一致した既存fileの採用 | 合格 | 不合格 | 合格 |
| Gitでの作業に管理データを混入させない | 不合格 | 不合格 | 合格 |

従来の満点同士でも、今回測った性質には差がある。統合によって改善した箇所も
識別できた。ただし、既知の不具合に対する校正であり、改良環境が未知の開発taskで
より良い成果を生むという実験結果ではない。案内だけで使えるか、人間の負担、
実装の保守性は未確認のまま。これらを静的な見た目や成功テスト数で埋めない。

## 検証できない原因の切り分け

固定imageのCodex 0.153.0で、ローカルのsocketとfilesystemだけを比較した。
一時CODEX_HOMEを使い、認証情報とhost socketは渡していない。
外側containerはnetworkなしで、sandbox実行のためprivilegedとしている。
そのcontainer自体を強い隔離と主張するものではない。

| 実行条件 | Unix listener | 既存Unix接続 | loopback listener | workspace外への書込 |
| --- | --- | --- | --- | --- |
| 比較用の直接実行 | 可 | 可 | 可 | 可 |
| workspace、通信無効 | 拒否 | 拒否 | 拒否 | 拒否 |
| workspace、通信許可 | 可 | 可 | 可 | 拒否 |
| 通信許可＋proxy・local binding・指定Unix socket許可 | 拒否 | 拒否 | 可 | 拒否 |

通信許可が必要な局面を確認できたが、Unix socketのallowlist設定だけで
必要な検証が成立するとは確認できなかった。通信許可と接続先制限の違いは
[公式permissions仕様](https://learn.chatgpt.com/docs/permissions)を参照。
これらは比較用のprofileで、通常運用の設定やlegacy campaignの権限を変更していない。
legacy `--sandbox workspace-write`とprofileの完全な等価性や外向き通信は未検証。

同じソースで既存のsupervisorテスト2件も実行した。
通常workspace設定では2件とも失敗、通信許可profileでは2件とも成功した。
対象はdispatch client終了後の継続とheartbeat、およびprocess groupのキャンセル。
22.603秒の失敗と5.860秒の成功はテスト実行の観測であり、モデル開発の速度改善ではない。

最初にread-only exportをworkspaceとして直接mountした確認は、sandboxの
`.git` mountpoint作成で止まった。これをテスト不合格に数えず、外部exportを
一時container内へcopyし、書き込めるworkspaceを用意してから比較した。
元exportと対象scriptのbytesは変更していない。準備失敗のlogも保存した。

## 起動待ちの正しさを改善

cycle-002で一度発生したDocker readiness timeoutを追うと、全体の待機予算が
残っていても、1回の5秒probeがtimeoutすると待機全体を終了していた。
逆に全体の残り時間が短くても5秒のprobeを開始できた。

`benchmark-devcontainer.py`でcommand timeoutを識別し、同じcontainerの
probeを全体期限内で再試行するよう修正した。1回のprobeと待機sleepも残り時間に
制限する。Docker executable不在など、timeout以外の失敗は再試行しない。
containerやモデルrunを新しく起動する処理は追加していない。

実際に遅延する疑似Docker executableとの比較では、7秒予算で初回probeが
timeoutする場合、修正前は5.008秒で失敗、修正後は2回目で5.649秒に準備完了。
0.15秒予算では、修正前は1.170秒後の応答を成功として受け入れ、修正後は
0.153秒で未準備として終了した。わずかな期限超過はOSの実行・停止のoverheadを含む。
これはハーネス自身の待機・停止の正しさの改善で、開発品質の向上の代理指標にはしない。

## 検証と次の実施条件

品質評価の10テスト、readinessの12テストをhostと同梱Python 3.10で実行し成功。
Python compile、差分、文書リンクも確認済み。新しい依存関係は追加していない。
機械可読の観測は[校正結果](../../experiments/development-harness/quality/calibration-2026-09-05.json)、
詳細なlogと失敗履歴はworkspace外のcycle-003専用stateに保存する。

次のlive比較の前に、以下を満たす必要がある。

1. 実需要のある新しい小規模課題と継続開発を確定する。既に解いた数値検証や
   今回修正したreadiness不備を、未知課題での有効性の根拠に使い回さない。
2. 通常開発と検証で必要な権限を明示し、比較両側で揃える。Unix socketだけでなく、
   実際のDocker build・完成image検証まで完遂できる経路を確認する。
   無条件のnetwork許可やsandbox解除を、能力不足の既定の修正にしない。
3. 同時間の品質を測れる観測時点と公開要求、合格品質への到達条件、使用量と停止条件を
   固定する。利用性・保守性を評価する後続作業と、その追加費用も事前に定める。

ここまでで成立したのは、新しい比較に必要な測定と局所修正である。
速度・品質双方の一般的な向上や、新しいcycle全体の完了はまだ主張しない。
