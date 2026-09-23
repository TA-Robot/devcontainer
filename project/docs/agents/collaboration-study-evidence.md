# 協働の比較から得た判断材料

2026-09-07の配布snapshot。devcontainer基盤の限定した実験結果であり、このprojectの実測ではありません。
方式を選ぶ時に、似た条件の観測と限界を参照します。今回の未達要求へ適用できるかはprimaryが判断します。
使い方は[playbook](collaboration-playbook.md)、このprojectの実行観測は`$review-collaboration-evidence`から確認できます。

## 何を使い分けるか

相談、独立review、多方面の案収集、複数実装の選択、分担・統合は、異なる不足に対応する選択肢です。
次に変えたい判断と、別agentが追加できる証拠・実装・検査を結び付けて選びます。
以下は一部の方式だけの観測です。ここで未測定の方式も選択肢に残り、優位とも無効とも確定していません。
ユーザーの明示的な相談・review依頼や、projectで必要なreviewを、この観測を理由に省略しません。

## 小さいqueue実装を点検・修正する場合

同じ初期コードと公開checkで、soloの点検・修正と、reviewerの点検→新しいmakerによる修正を比較しました。
各初期条件1組。実装したmaker自身のcheckpointへの独立reviewとは情報履歴が異なります。
最終成果の外部動作検査は通常の再実行、引数保持、不正状態の保全、更新時の旧reader保全です。

| 初期条件 | solo / review付きの品質 | solo / review付きの条件時間 | input増加 | output増加 |
| --- | --- | --- | --- | --- |
| 欠陥あり | 両方4/4 | 96.055 / 176.978秒 | 86.7% | 81.8% |
| 正しい実装 | 両方4/4、変更なし | 63.777 / 184.508秒 | 152.6% | 205.5% |

この条件では常時reviewを足す品質上積みを確認できず、費用が増えました。
公開checkと自己修正で対応できる似た小課題で、reviewを自動追加する根拠にはなりません。
具体的な見落としや別の検査能力がある状況でreviewが有効かは、この結果だけでは決まりません。
書込み中のkill・電源断・並行writer・一般設計品質・継続開発は測っていません。

出典: [queue review v1の固定集計](collaboration-studies/queue-review-v1.json)。各条件600秒/output合計12000の枠。
時間は条件開始から提出・停止・保全までで、事前準備と外部採点は別です。

## 同じ相談能力へ過去の観測を追加した場合

同じqueue familyの別初期状態で、両条件に自己調査後のsubmit/consultを許し、一方だけへ上記の観測と起動案内を追加しました。
1組、共通案内→観測付き案内の固定順序。各条件600秒/output合計12000、最初の自己調査は最大300秒です。
相談を選んだ場合だけreviewer→新しいmakerへ進む能力は両条件で共通でした。

| 観測 | 共通案内 | 過去の観測付き案内 |
| --- | --- | --- |
| 選択・最終品質 | 相談なし・4/4 | 相談なし・4/4 |
| 条件時間 | 95.209秒 | 85.520秒 |
| input / cached input / output | 128293 / 112256 / 2104 | 110826 / 98560 / 1901 |

事前の探索基準を満たした「独立確認候補」ですが、時間基準の余裕は約0.168秒だけで、一般既定には未採用です。
両条件の相談選択は同じなので、相談判断の改善や相談省略による高速化は観測していません。
順序・cache・モデル変動への頑健性、案内の意味上の採用、相談経路の実モデル効果は未確認です。
「情報を足せば10%速くなる」という予測には使いません。
出典: [条件付き相談の固定集計](collaboration-studies/conditional-review-v1.json)。
初期化・必要なstage準備・引継ぎ・提出・停止回収を条件時間に含み、外部評価は別計測です。
この初期状態は今回でlive使用済みです。前節の古い集計内の留保状態を現在の未使用状態とは読みません。

## 証拠をまとめる前に相談する場合

公開の数値・根拠ID・移行制約をまとめるF12-L revision 3で、soloとadvisor→新しいmakerを1組比較しました。
元の固定得点は両方10/12。相談側は282.256→336.729秒、input44.8%増、output6.5%増でした。
ただし評価器が正しい否定表現と複数の関連unknownを不当に拒否したため、**品質改善と品質を揃えた速度比較は保留**です。
元の得点を12/12に直したり、同等品質と見なしたりしません。常時事前相談の一般既定を支持する根拠にはなりません。
出典: [証拠統合pilotの固定集計とvalidity](collaboration-studies/synthesis-pilot-v1.json)。
助言の受渡しと全員の停止を確認したことは、助言の品質効果と区別します。

## この情報の扱いと出典

全実験はCodex CLI 0.153.0、gpt-6-astra/highを要求しました。resolved model/applied effortはunknownです。
inputはcacheを含む総inputで金額ではありません。全参加者の消費を数えていますが、同じoutput枠だけで同費用とは言えません。
少数例の固定順序の探索であり、典型時間や他provider・他課題での改善率ではありません。
案収集・独立複数実装・分担の比較結果を、これらの数値で代用しません。

同梱JSONは公開済み集計のbyte-identicalなcopyで、評価器・開発用の模範解答・認証情報は含めていません。
JSON中のprivate pathは出典の識別情報であり、このprojectから読めることは前提にしません。
原記録を変更せず、測定範囲や採否が変わる場合は新しい観測として更新します。
配布snapshotの更新ownerはdevcontainer基盤のprimary/integrator。このprojectの独自観測とは分けて保持します。
copy sourceは`TA-Robot/devcontainer`のcommit `f4c5c96`にある以下のfileです。実行時のsource commitは各JSONに別途あります。

| 同梱file | repository内のcopy source |
| --- | --- |
| `queue-review-v1.json` | `experiments/development-harness/queue_review/v1/result.json` |
| `conditional-review-v1.json` | `experiments/development-harness/queue_review/conditional_v1/result.json` |
| `synthesis-pilot-v1.json` | `experiments/development-harness/consultation/synthesis-result.json` |

SHA-256は同じdirectoryの[copy元との照合記録](collaboration-studies/source-sha256.json)にあります。
新しい案内を配布して利用できても、開発性能が改善した証拠にはなりません。
採否を変えるには、適合する課題と比較条件で最終成果・時間・全消費を改めて確認します。
