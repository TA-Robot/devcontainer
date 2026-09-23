# Fresh solo/adaptive pair: withheld accounting, separate artifact diagnosis

2026-09-09。[事前固定protocol](protocol.md)の2開始を使用した。
**両developerは正常終了したが、通知中断付近のusage不足により元比較はwithhold。**
元runnerはその時点で止まり、qualification採点は始めていない。原結果は変更していない。
提出済み2ファイルの[別診断](../pair_diagnostic_v1/README.md)では全48採点が完了し、
全48 containerを削除した。モデルの再実行・候補の選び直し・confirmationは行っていない。

## 得られた成果物の品質

同じ元qualification 24例、同じ封印済み物理runtime・評価器、90秒/5秒での**診断結果**。
元protocolの全費用上限を満たすことを認定した比較には読み替えない。

| 負荷帯 | 単独: 期限内価値 | 協働: 期限内価値 | 単独: 最重要完了 | 協働: 最重要完了 |
| --- | ---: | ---: | ---: | ---: |
| ordinary | 1314/1459 (90.06%) | 1288/1459 (88.28%) | 61/65 | 59/65 |
| contended | 3080/3945 (78.07%) | 3011/3945 (76.32%) | 144/163 | 137/163 |
| severe | 7070/9908 (71.36%) | 7123/9908 (71.89%) | 359/403 | 354/403 |
| 全24例 | 11464/15312 | 11422/15312 | 564/631 | 550/631 |

協働成果物の期限内価値は5例で増加、5例同数、14例減少。
最重要完了は3例増加、11例同数、10例減少。全3負荷帯で最重要完了が減った。
severe/scarceでは価値+110・最重要+3、severe/mixedでは価値+46・最重要同数の改善がある。
一方、severe/burstでは価値−59・最重要−8。平均や局所改善で退行を隠さない。
この2成果物から全般的な能力拡張は確認できず、方式の安定した有効性も単独不可能性も示していない。

全12セル・全24ケースの指標は[result.json](result.json)。大きいtraceとcompletion mapはhash付き原記録に残す。

## 実行と費用の範囲

| 項目 | 単独 | adaptive |
| --- | ---: | ---: |
| CLI終了コード | 0 | 0 |
| 参加者 | 1 | 4（主担当+3子） |
| 開発時計 | 2073.829秒 | 2053.682秒 |
| 記録済み応答 | 59 | 298 |
| 記録済みinput | 3,309,622 | **少なくとも**13,584,834 |
| 上記に含むcached input | 3,117,184 | 13,210,496 |
| 記録済みoutput | 49,534 | **少なくとも**97,664 |
| 未計上出力を伴う観測箇所 | 0 | 38 |
| 元runnerのactor状態 | completed | withhold |

開発時計の差は約20秒。これを速度改善の安定した推定にしない。
協働側は既知のoutputだけでも約1.97倍だが、未記録分の費用・全output上限適合は確定できない。
cached inputはinputの内数。reasoning outputもoutputの内数で、重複加算しない。
準備・外側orchestrator・診断設計のモデル消費とhuman review costは未計測であり、この表に含まない。

元collectorは最初の不整合で各threadを読むのを止めたため、後続の記録済み消費も元の部分集計から抜けた。
別のread-only監査で全298応答を合算し、各threadの累積値と照合した。これは請求の完全性の証明ではない。
38箇所はいずれも直後にagent間通知があった。[疑似provider診断](../preemption_probe_v1/README.md)では、
通知と終端usage未送信を組み合わせると、正常終了してもusageがない状態になった。
しかし終端usageを遅れて送る追加試験では、通知あり/なしの両方で回収できた。
通知だけが原因とは確認できていない。実providerの終端処理・課金は不明であり、
欠落をゼロ扱いして元比較をcompletedへ変更しない。

## 開発上の観察と次の判断

単独は46設定のsweepに加え複数方式を作り、7ケースで独自simulatorと公開実装のtrace一致を確認した。
独自training・再標本化・validationを各24例で比較し、予約計画とcache-aware dispatchを統合した。
候補数は成果の代理ではなく、単独に十分な探索と自己検証を許したことの診断材料。

協働は優先度方策・先読み方策・独立検証を分担し、主担当も別方式を試作した。
推定締切で有望な重要仕事を捨てる問題、重要後続仕事のmemory予約、性能修正の挙動一致を検査した。
検証担当は実験中のsource変更によるprovenanceの問題を見つけ、候補を凍結するよう修正した。
その活動は有用なartifactを生んだが、選択された成果物の全般的な品質向上にはつながらなかった。
両者とも予約とdispatchの組合せへ到達しており、人数だけで解法の多様性が得られたとは言えない。

次のmilestoneは、**成果物の回収・品質測定と、費用記録の完全性を分離すること**。

1. 正常終了と選択済みsourceを確認したら、usage照合の前に提出物を封印する。
2. 新protocolではquality / usage / cleanup / budget適合を別状態にし、費用不明を品質不明へ変換しない。
   不明な費用効率・token上限適合を主張せず、wall-clock条件と観測範囲を明示する。
3. 最初のusage gap後も既知の応答記録を回収し、途中通知を含む疑似provider試験を必須にする。
4. 次の品質改善仮説は、共通の再現可能な実験結果から、案の違い・反例・退行を選択へ反映させる支援。
   source固定と採否の支援をprovider-freeで校正し、新しいlive開始は別protocolで固定する。

本数追加で今回を勝ちに変えること、新しい題材・汎用studioへ移ることは次の作業にしない。

原pair: `/home/asakura/.local/state/devcontainer-evaluations/scheduling-adaptive-pair-20260909-01/`。
別診断: `/home/asakura/.local/state/devcontainer-evaluations/scheduling-pair-artifact-diagnostic-20260909-01/`。
提出SHA256は単独`230a990f284d42552d0e8369bd5c4c6d7a0c62281c553fb6146290c429430614`、
adaptive`9fe8963be17f7e683437be16769b83e6563ef5d72a9aceb6a65c84f1d4be18a1`。
adaptiveは終了前のSELECTION.md記載hashとも一致する。
