# Cycle 003: 速度・品質を分けた比較

状態: 小規模02と継続開発02の両条件を実行し、外部検証・追加レビュー・実装の取り込みを完了。
速度、固定時点の品質、予算内完了、配布の検証を分けて報告する。
[小規模結果](../../experiments/development-harness/cycle-003/small-result.json)と
[継続開発結果](../../experiments/development-harness/cycle-003/large-02/result.json)が機械可読の正本。

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

## 校正の検証とlive比較の前提

品質評価の10テスト、readinessの12テストをhostと同梱Python 3.10で実行し成功。
Python compile、差分、文書リンクも確認済み。新しい依存関係は追加していない。
機械可読の観測は[校正結果](../../experiments/development-harness/quality/calibration-2026-09-05.json)、
詳細なlogと失敗履歴はworkspace外のcycle-003専用stateに保存する。

以下をlive比較の前提とした。小規模02では固定protocolと実行前確認へ反映した。
継続開発にも外部検証・予算・段階公開の固定を適用した。

1. 実需要のある新しい小規模課題と継続開発を確定する。既に解いた数値検証や
   今回修正したreadiness不備を、未知課題での有効性の根拠に使い回さない。
2. 通常開発と検証で必要な権限を明示し、介入以外は比較両側で揃える。Unix socketだけでなく、
   実際のDocker build・完成image検証まで完遂できる経路を確認する。
   無条件のnetwork許可やsandbox解除を、能力不足の既定の修正にしない。
3. 同時間の品質を測れる観測時点と公開要求、合格品質への到達条件、使用量と停止条件を
   固定する。利用性・保守性を評価する後続作業と、その追加費用も事前に定める。

## 新しい実開発比較

小規模02は[JSONログの伏せ字修正](../../experiments/development-harness/cycle-003/small-02.md)。
初期sourceでJSONの秘密値がそのまま残ることを、人工の文字列で再現した。
新評価器は19の観測を、秘密値の除去、構造保持、ログ文脈、従来形式の4項目へ分類する。
正しい独立test double、全ログを隠す変種、誤ったcountなど、5テストで校正した。

sourceは`0b1ad1e950a0c90edf8dc9fcc493bdd9de680792`、imageは上記校正と同じ固定版。
両条件の開始Git treeが元revisionと一致することを確認した。改良→対照の順で各1回、
GPT-6 Astra/high・CLI 0.153.0を指定し、1,200秒・観測output 20,000 tokensを上限とする。
120秒ごとと提出時にsnapshotを採取する。実行中の評価結果を開発側へ返さない。

差分はworkspace-write内のcommand network access。改良だけを有効にし、
filesystem sandbox・approval never・subagent無効・source・promptを揃える。
network権限の違いが介入であり、同じ権限での比較とは呼ばない。
Docker client設定は両条件とも一時directoryへ置く。これらは実験の明示設定で、
通常の利用者設定や既定policyを変更していない。

Dockerの実行前確認では、通信制限とは別にclient設定のread-only pathと、
検証用containerのoverlay上へ直接置いたDocker保存領域が問題になった。
一時client設定と専用volumeを使うと、workspace sandbox内でscratch imageの
buildと静的な確認programの起動が成功した。実評価用起動helperは既に専用volumeを使う。
失敗したprobeも専用stateに保存し、成功したrunだけの記録にしない。

campaignへ追加したbooleanの明示設定と既定動作の保持を、14テストのsuite
（Docker testは別実行）と実Dockerのfake-provider testで確認した。
実行結果は[機械可読記録](../../experiments/development-harness/cycle-003/small-result.json)へ保存した。

## 小規模02の速度と品質

| 観測 | 対照 | 改良 |
| --- | --- | --- |
| 提出までの開発時間 | 567.601秒 | 435.743秒 |
| 最初のsnapshot | 120.018秒、6/19 | 120.046秒、19/19 |
| 次のsnapshot | 240.069秒、19/19 | 240.160秒、19/19 |
| 提出時の固定観測 | 19/19、4項目合格 | 19/19、4項目合格 |
| 観測output tokens | 11,690 | 10,353 |
| 提出後に同じsourceで実行したcore回帰 | 64/64 | 64/64 |

改良側の提出は131.858秒、約23.2%早かった。約120秒時点では、改良側だけが
秘密値の除去・構造保持・ログ文脈の要求を満たした。対照側も約240秒では満たした。
これは同じ品質条件への早期到達と、ほぼ同時間での到達品質を別に観測した結果である。
ただしsnapshot間の正確な到達時刻は分からず、「2倍速い」とは言えない。
1組・固定順序であり、network権限の違いも含む。一般的な速度・品質効果は未確定。

対照側では開発中のcore回帰64件のうち15件がsocket制限で失敗した。
改良側では途中の全63件と、その後の最終focused 11件が成功したが、最後の変更後に
全体を再実行してはいない。提出物を変更せず、外側の共通環境で検証すると両方64件成功。
これによって対照側の15件は環境の制約と切り分けた。内側の検証能力が上がったことと、
提出物の退行が減ったことを同じ意味には扱わない。

## 追加レビューと採否

固定観測の満点同士でも、提出後の[追加レビュー](../../experiments/development-harness/cycle-003/review_redaction.py)では差が残った。
5,000桁の整数と秘密値が隣接するJSONでは、対照側はJSON decoderの制限から
伏せ字を漏らした。改良側は数値表記を保ちつつ秘密値を除去した。
一方、escapeされた単独surrogateとtokenを含む文字列では、両方とも伏せ字後の
UTF-8出力に失敗した。これらは追加レビューとして別記録にし、固定19件へ後付けしない。

改良側の実装を採り、変更するJSON文字列をescapeして出力する修正と2件の回帰を追加した。
取り込み版は固定19件、追加レビュー2件、focused 16件、core回帰66件すべて成功した。
新しい依存はなく、既存の公開interfaceとraw logの扱いは維持した。
code commitは`464c6b6603c59d89e6877817d9505613e2d2fe18`。
測定後の修正・外部検証・統合作業を、モデルの提出時間へ混ぜない。

通常imageのbuildは成功し、sourceをmountしない同梱moduleでも追加レビュー2件が成功した。
Mira hookとnamed volume経由の観測保持も成功した。
固定依存imageのbuild、同梱CLI・native contract、lifecycleのmerge・中断復旧・rollback、
Docker-in-Dockerの起動とdoctorまで成功した。同梱moduleでも追加レビュー2件が成功し、
codeを検証用に持ち込まず確認できた。完成imageは
`sha256:1743b1bae47c7217095b4044c370e2512d98a4f4b3fb3275d91da77b7742d891`。
検証後のexportは、file bytes・mode・directory・symlinkを含めて元commitのarchiveと一致した。

このbuildでは、既存toolchainと通常build済みのsource層はcacheされたが、
その後段のDocker-in-Docker Featureのインストールが再実行された。
APT索引48.2 MBの取得に10分17秒を要し、HTTP取得の再試行も記録された。
依存環境の再構築がコード変更の配布待ちを延ばす箇所として、次の改善候補に残す。
この時間をliveの提出時間へ追加したり、単発の通信遅延からcache改善率を推定したりしない。
追加の一時containerではHTTPS経由の索引48.2 MBを53秒で取得できた
（外側の起動込み59.855秒、90秒の観測上限）。元buildとは実行contextと時刻が異なるため、
対照条件を揃えた速度比較ではない。通常設定は変更せず、通信経路も次の検証候補として残す。

採用するのは再現したログの不具合修正と、実験で権限差を明示して観測できる仕組み。
network許可を全利用者の既定値へ広げる判断はしていない。

## 継続開発02の課題と事前校正

継続開発は[独立したacceptance実行](../../experiments/development-harness/cycle-003/large-02/README.md)
を選定した。fake providerに「`exit 17`が成功した」と報告させた実際のjobで、
現状の`job validate`は成功するが、そのcommandの実際の終了値は17だった。
既存機能はproviderの報告とGitを照合するもので、commandの独立実行は提供していない。
モデルを追加で呼ぶことなく、この差を実CLIで再現した。
段階要求は実行・証拠の鮮度・中断と配布へ分けた。実jobを作るfixtureは、
成功を偽った報告、結果だけに含まれるcommand、commandのないmanual要求を使って検証した。
この2テストは問題の再現とfixtureの校正であり、未実装のcheckerの合格実績ではない。
さらに実行の証跡、失敗後の停止、元taskの権限、manual要求を扱う4観測のprobeを実装した。
実際にshell commandを実行する独立referenceと、成功の捏造・失敗の上書き・結果だけに
書かれたcommandの実行を使った校正を加え、計6テストが成功した。
その後、timeout・source同一性・鮮度・旧版からの移行・並行実行・中断を含む
全41観測へ拡張し、参照実装と誤実装を区別する8テストが成功した。
配布image内では13観測を実行し、ソースのmountがなくても動くことを別に確認する。
[継続開発protocol](../../experiments/development-harness/cycle-003/large-02/protocol.md)に
3段階の予算、後続要求の公開条件、共通要求での時点比較、未完了の扱いを固定した。
校正と共通ビルドの結果は、開発候補が要求を満たした実績とは区別する。

共通環境はAPT取得先を同じ署名付きarchiveのHTTPSへ変更した。
通常／固定依存build、起動とMira確認が成功し、導入package一覧は変更前と一致した。
両条件へ同じOCIキャッシュを渡し、ソースだけを変更したビルドで実際の層再利用を確認した。
コンテナ再起動で消える一時領域は各段階の起動時に準備し、Dockerとcache双方の準備完了を
待ってからモデル時間を測る。これらは共通の実験条件であり、条件間の変更は通信権限のまま。
キャッシュ読込の失敗、network指定によるcache key変化、起動待ちの不足も準備記録に残した。

## 継続開発02の速度と品質

両条件とも同じソース・イメージ・キャッシュで3段階を実行した。改良A→対照Bの固定順、
各1組、各3セッション。指定はGPT-6 Astra/high、CLI 0.153.0で、実際に適用された
model/effortは観測できずunknown。改良側だけcommand network accessを許可し、
filesystemはworkspace-write、approval never、subagent無効を共通にした。
通信権限が介入であり、同じ権限の比較ではない。

| 観測 | 対照B | 改良A |
| --- | --- | --- |
| 第1段階の提出 | 1,308.931秒 | 1,018.320秒 |
| 第2段階の追加開発 | 980.382秒 | 875.598秒 |
| 第3段階の追加開発 | 1,612.120秒 | 1,047.066秒 |
| 最終成果までの累積開発 | 3,901.433秒（65.0分） | 2,940.984秒（49.0分） |
| 観測output tokens | 92,945、上限超過 | 74,343、上限内 |
| 提出時の固定source観測 | 24/24 → 37/37 → 40/41 | 24/24 → 37/37 → 41/41 |
| 外側の実配布イメージの固定観測 | 12/13 | 13/13 |
| 成功確定のSQL更新直前にSIGTERMを送る追加レビュー | incompleteとして拒否 | passedとして受理する不具合 |
| 検証中の作業領域をGC候補から除外する追加レビュー | 不具合あり | 不具合あり |
| 内容を変えないGit stat-cache更新の確定再現 | 誤ってsource-changedとして拒否 | 合格 |

80,000 output tokensは観測と次セッションの開始を制御するcost capであり、
providerが使用量を通知するのはturn終了時だけだった。Bの最後のCLIは正常終了して
成果を残したが、そこで累積超過を検出した。予算内完了ではなく、同予算の成功成果同士の
短縮率にも換算しない。超過後の追加セッションや代替runは実行していない。
課金額と人間のレビュー時間はunknown。準備・外部評価・修正・配布buildの時間を
モデル開発時間へ足し込まず、各実行記録を別に残した。

同じ累積300秒付近では、Bが第1段階24件を満たし、Aはcheck interfaceが未実装だった。
Aは600秒付近で24件を満たした。両側へ第2段階が公開済みの1,500秒付近では、
Aは37件合格、Bは途中のfixture作成失敗で1件不合格・36件未確認。1,800秒付近では
両方37件合格だった。2,400秒付近の第3段階ではAが41件、Bが38件合格だった。
比較する公開要求は各時点で共通の範囲に限定し、完成済み成果を後の時点へ持ち越しても
開発時間を加算しない。初期機能の到達と最終提出では順位が異なる。
300秒間隔のsnapshotから正確な到達時刻や倍率は求めない。

## 評価器の不足と追加レビュー

Bの固定source/installed各1件の不合格は、強制終了後の再検証に評価器が通常の
`job check`しか使わなかったことによる。公開要求は文書化した明示復旧を認めている。
Bは旧実行の停止確認後に`--recover-incomplete`を要求しており、独立probeで
所有process groupの停止を確認してこの手順を適用すると、sourceと実配布版で合格した。
生の40/41・12/13は保持し、追加観測で要求への適合を説明する。flagの違いを
製品不具合として数えず、固定評価器を後から書き換えて満点にもしていない。

追加のSIGTERM観測は、実際のSQLite完了UPDATE直前にsignalを注入し、その後の
queryとstrict validationを実CLIで確認した。Aの固定41件合格では検出できなかった
誤った成功確定を再現し、Bでは拒否された。GCは本当にvalidate・cherry-pick・collectを
済ませたjobで再検証を開始し、両候補が作業領域の削除候補を返すことを確認した。
実際の削除は行っていない。

最初のGit refresh probeではBも合格したが、最終統合検証では拒否された。
単なる`touch`が同じ時刻になりindex bytesを変えない場合があるため、過去の時刻を
明示して更新を確定させるとBの不足を再現できた。初回の合格記録も残し、確定再現を
採否に使う。キャッシュされたPython bytecodeは別に監査し、使用された68件は
sourceと一致、古い7件は無視、6件は不在で、不一致はなかった。

## 継続開発成果の採用と配布確認

Bの独立command実行、永続証拠、鮮度を要求するvalidate、並行実行の排他、
明示的な中断復旧を取り込んだ。理由は中断時の成功確定を防ぐ実動作と旧clientの
互換性であり、速度の優劣ではない。モデルの自己申告だけを受理する従来のvalidateは
`provider-reported`と明示し、独立証拠が必要な利用では`--require-checks`を使える。

統合時に、実行中・未完了の検証を持つjobと、所有lockを安全に読めないjobを
GC候補から除外した。通常完了と明示復旧の後は再び候補になる。
Gitの内容・mode・index flagsは検査しながら、stat-cacheだけの更新は許容する。
旧証拠は旧来のraw index判定のまま保存し、新しい証拠から版付きのsemantic判定を使う。
現在のcheckerはsubmodule、欠落したsparse checkout、filterで変換されたworktreeを
未対応として拒否する。独立commandは呼び出し元権限で動く信頼済みtaskのコードであり、
新しいsandboxや自律的なpermission拡張を実装したものではない。

固定の元66回帰はBが全件合格。AはDB schemaの期待値2に対する実装値4のassertだけが
不合格で、その期待値だけを適応した別実行は66件合格。候補自身の追加suiteは
Aが102件、Bが106件合格だった。最終統合版はcore 108件、通常／固定依存イメージで
それぞれ同梱checker 42件が合格し、両buildとMira起動確認も成功した。
build事前確認・一時領域の5回帰、contractの26回帰も合格した。
コードrevisionは`8764401efea84fc8cb9fd314da0901c4f5e36b58`で、詳細は機械可読結果の
`integration`へ記録した。配布版の検査では
candidate checkoutをmountせず、同梱CLI/libraryのhash一致を確認する。

外側で二つの公式CLI buildを同時に開始した際には、millisecond由来の一時パスが衝突し、
生成Dockerfileが壊れた。候補の失敗と区別して元logを残し、専用TMPDIRで順次再実行すると
両方成功した。共通build helperも呼び出しごとに一時領域を分け、失敗時のcleanupと
終了値保持を並行回帰で検証した。最初の統合イメージ検証では、移行用テストが存在しない
checkout CLIを参照して失敗したため、同梱CLIを使うよう修正した。両方とも観測側の
不備として記録し、完成イメージの成功を推測で補わない。

小規模と継続開発の測定・レビュー・統合を実施できたが、今回は数十分〜約1時間の
結合した機能開発であり、週単位の大規模projectを代表しない。次は既存の実projectで
継続利用・変更・引き継ぎを追うことを優先し、今回の1組やテスト件数から一般的な
速度・品質の向上を断言しない。新しい比較の前に、予算の観測遅延と公開された復旧手順を
評価contractへ反映する。
