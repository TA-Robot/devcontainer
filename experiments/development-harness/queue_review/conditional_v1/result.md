# 条件付き相談への情報提供: 初回の結果

2026-09-07。[固定protocol](protocol.md)の1組を完了。
**情報あり条件は事前の改善候補基準を満たしたが、一般既定には採用せず独立確認候補に留める。**
両条件とも相談せずに提出したため、相談起動の選択が改善したとは確認できない。

## 観測

同じ初期実装、公開check、相談能力、全予算を使い、drafterへ渡す案内だけを変えた。
control→informedの固定順序。各600秒/output合計12000、drafterは両条件とも最大300秒。
要求modelはgpt-6-astra/high、Codex 0.153.0、resolved/appliedはunknown。

| 条件 | 選択 | 最終動作 | 条件時間（秒） | input | cached input | output |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| 共通の能力案内だけ | submit | 4/4 | 95.209 | 128293 | 112256 | 2104 |
| 前回の範囲付き観測と起動案内も提供 | submit | 4/4 | 85.520 | 110826 | 98560 | 1901 |

情報あり条件は時間10.176%減、input13.615%減、output9.648%減。
品質を満たした条件時間の比は0.898240（informed/control）。
事前基準の0.9以内を**約0.168秒だけ**満たした。1組の変動や順序/cacheの影響に対する頑健性は未確認。
inputはcacheを含む総inputで、金額ではない。

初期状態は4項目中2項目に失敗（ackの冪等性、未知ID/不正状態の保全）。
両成果は`queue_store.py`・`bin/queuectl`を修正し、`tests/test_repair.py`を追加した。
最終的に通常再実行、引数境界、不正状態保全、enqueue/ackの旧reader保全を満たした。
requestの参照先・構造も有効だった。理由や自己検証の自己申告を品質判定には使っていない。

## 経路と費用

両側でdrafterがsubmitを選び、reviewer/final-makerのprovider呼出しもcontainer作成も発生しなかった。
全2participantの停止・回収・削除、認証copy削除を確認。環境fingerprintと最終artifact hashも一致を確認した。
条件時間はstage準備・probe・自己調査・選択・提出・停止回収を含む。
共通の事前準備は8.866秒、初期/最終評価等を含む実行全体は200.855秒。

相談の発動が両側とも0なので、今回の時間差を相談の省略による改善とは解釈しない。
質問の意味上の必要性、guideの意味上の採用、未検査の品質、今回未発動のreview経路の実モデル効果はunknown。
consult経路は実Dockerと疑似providerで引継ぎ・修正・停止を検証済みだが、その結果をliveの効果へ混ぜない。

## 採否と次の確認

事前の判定は「独立確認候補」のまま保持する。閾値や得点を結果を見て変更しない。
一方、1組で案内を一般既定にせず、条件付き相談が品質・速度を改善するという一般推奨は出さない。
queue v1の常時review/soloとの時間比較は、能力・stage・時計範囲が異なるため今回の対照にはしない。

次の候補は、今回の発見用1組を採否集計から外し、両方の条件順序を扱う**2組の固定確認**。
同じ入力を使う場合は反復と明示し、未使用課題とは呼ばない。
2組は順序の偏りを点検する最小のcoverageというplanning priorで、精度や有意差の保証ではない。
scopeはこの情報介入の再現性確認、ownerはprimary/integrator。
新protocolで全予算・採否・停止を先に固定し、未完了・差なし・逆転も全て含める。
結果が再現しなければ改善未確認へ戻し、より広い用途には別familyでの確認が必要。

今回のconfirmationは、この1組でlive使用済みになった。未使用へ戻さず、成功まで追加実行しない。
実測→判断材料の提供→未使用条件での実比較→採否までの限定した一循環は実施できた。
一般的な協働の優位性、継続開発への適用、案内の既定化は未達のまま区別する。

## 出典と検証

[機械集計と出典hash](result.json)、[実装](conditional_review.py)、[集計器](conditional_report.py)、
[preflight](validation.json)。source commitは`0e81c05`。
6テストでsubmit/consultの両情報条件と、未知usage・不正request/advice時の停止を確認した。
v1の動作評価sourceが校正時から不変であることも確認した。

private証跡は `/home/asakura/.local/state/development-harness/queue-conditional-review-v1-20260907-01/`。
`plan.json`を実行前に保存し、`run/seal.json`にconfig・全source・preflightのhashを保持した。
`interpretation.json`は固定集計器の出力。公開result.jsonはその判定を保持し、plan・provider・
初期状態・停止・環境のprovenanceだけを追加した。原結果と元artifactは変更していない。
旧F04/F12/queue v1のoracle・得点・atlasも変更していない。
