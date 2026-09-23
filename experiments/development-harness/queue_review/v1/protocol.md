# Queue review pilot v1 — fixed exploratory comparison

2026-09-06。対象は`queue-review-repair-v1`。旧F04/F12のoracle・得点・runnerを変更しない。
初回はrepair（直接上書き＋引数再分割）とpreserve（正しい初期実装）の2組。
confirmation（ackの非冪等性＋終了status隠蔽）は方式を改良した後の確認用に留保し、初回liveで使わない。
初期実装の状態名・期待得点・校正解をparticipantへ渡さず、同じ公開briefとtoolを与える。
preserveの正しい初期codeは意図した公開対照データであり、別の完成解や校正台帳のmountではない。

比較はsoloの点検・修正と、独立review→fresh makerの直列実行。内部aliasはconsult/advisorを継承する。
期待するmechanismはerror decorrelationと境界をまたぐ検査coverage。reviewも実行結果を根拠にできる。
makerの過去contextの継続、実装中の往復相談、複数candidateの競争ではない。
reviewerは実装を編集せず、3 fieldのadvice.jsonだけを提出。makerが検証・採否・統合を所有する。

## 固定条件

| 項目 | 値 |
| --- | --- |
| 要求provider | Codex 0.153.0、gpt-6-astra/high。resolved/appliedは確認できる範囲のみ記録 |
| image | sha256:c7f904a12d7e7c63a2c7e46bc6654c8304b497a2836ecb08fb5bea0118f679ea |
| 順序 | repair: solo→consult、preserve: consult→solo。repair組を先に実施 |
| 全condition | 600秒、output合計12000。soloは全枠、consultはreview＋受渡し＋makerで共有 |
| review/予約 | review最大120秒・開始最低15秒。maker最低180秒/1000 outputを予約 |
| 回収 | stop10秒、capture30秒、window10秒、snapshot16 MiB、advice16 KiB |
| 外部評価 | 初期と提出成果を各最大120秒のcommand開始枠。各CLI最大15秒、所有container削除最大30秒 |
| 実行環境 | task commandのnetworkなし、全participantの環境同等性・model-free probeを事前確認 |

2組は欠陥修正と不要な変更/費用を区別する最小の探索集合で、各条件1episode。一般効果の反復ではない。
600秒/12000 outputとreview上限は、この小さな3-file実装と過去pilotの作業量からのcost cap。
maker最低予約はplanning prior。初期状態、停止証拠、外部評価境界、同じ公開要求はhard guard。
scopeは初回探索、ownerはprimary/integrator。校正失敗、CLI/image/source変更で新たに固定し直す。
outputはturn終端で観測する上限であり、in-turnの厳密な総token/金額上限ではない。
全input/cache/output、欠測、準備・開発・受渡し・回収・採点を分ける。token同数だけを同費用と呼ばない。

## 採点と採否

原結果は4つの動作項目とsource contractを示す。初期状態も同じ外部評価で測り、participantには返さない。
不明・未完了・予算超過・source違反を除外しない。reviewの指摘件数や文章は品質にしない。
変更path数は記録するが、差分の存在だけで不要な変更・退行とは判定しない。

consultだけがrepairを全合格へ修正し、preserveで退行せず全員の停止・usageが確認できれば、
この方式を次の確認へ進める候補とする。両者合格なら、両組でconsultの提出時間がsolo比90%以下、
input/outputが各110%以下の場合だけ速度・消費の改善候補とする。これは探索上のhypothesisであり有意差ではない。
品質退行を速度で相殺しない。条件を満たさなければ常時reviewを既定化しない。
好結果でも留保したconfirmationと新protocolで改良前後を確認するまで、一般推奨や改善率を配布しない。

source hash一致の校正と、両条件・両初期状態の疑似provider/実Docker検証がliveの前提。
このprotocolと違う値、confirmationへのlive実行、出力dir再利用は拒否する。
初回の最大4conditionを勝つまで追加・再試行・fallbackしない。新たな実行には別protocolを要する。
