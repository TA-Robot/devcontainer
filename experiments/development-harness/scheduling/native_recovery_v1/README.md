# 提出物・品質・費用を分ける native actor

`native_actor_v1` の container 条件と CLI bridge を引き継ぐ新しい版。
過去の source、run、得点、withhold を変更しない。
[指示比較](../failure_refinement_v1/README.md)を成立させる回収経路に範囲を限定する。
live campaign・開始台帳は別の[refinement cohort](../refinement_cohort_v1/result.md)に置き、実行済み。
新しい実行は別 protocol と source 一致 preflight 前に開始しない。

## 順序と判定

1. bridge が native process を止め、session と必要な inventory 列だけをコピーする。
   使用量の完全性はここで開発の終了状態へ混ぜない。
2. host が container を削除し、認証 copy の削除と source 不変を確認する。
3. 提出物が存在すれば regular file / 64 KiB を確認して別の read-only file へ封印する。
   期限停止時の途中ファイルも保全できるが、正常な最終選択とは認定しない。
4. 封印の後で、全参加者の tree・model/effort・CLI・開始/終端を inventory と照合する。
   使用量不足があっても、その後の token_usage_record を回収する。
5. 品質は正常終了した選択済み成果物に限り、別の認証/networkなし Docker で採点する。
   新 campaign では全条件の開発終了・封印を barrier にしてからこれを呼ぶ。

| 軸 | 意味 |
| --- | --- |
| artifact | 封印済み source。正常選択かどうかは別軸 |
| lifecycle | 全参加者が正常終了し、構成と inventory が一致したか |
| usage | complete は検証した応答台帳の完全性。partial の known_usage は記録済み部分のみ。請求の完全性は常に unknown |
| budget | 開発 wall-clock と全参加者の観測 output を別判定。既知分だけで上限超過なら exceeded、不足があり上限以下なら unknown |
| cleanup | container と認証 copy の除去を確認したか |
| quality | eligible は独立採点前。別評価で measured / invalid-policy / withhold を記録 |
| admission | 品質対象が適格で、応答台帳が完全かつ観測output・開発時計が上限内の場合だけ admitted |

usage 不明・output 上限超過でも正常終了した成果物の品質は測定できるが、予算適合した比較へ昇格しない。
期限停止・子の中断・構成不明・回収不明・source 不一致は品質の適格性を保留する。
root stdout は全消費へ読み替えない。parent history を再加算せず、compaction 応答も応答記録から扱う。
actor の `status=recovered` は提出物の保全だけを示す。品質測定完了や予算適合の成功状態ではない。

## 検証

```bash
NATIVE_RECOVERY_DOCKER=1 PYTHONDONTWRITEBYTECODE=1 python3 -m unittest scripts/test-native-recovery.py
```

実 CLI 0.153.0、固定 actor image、疑似providerのみ。外部モデル呼出し・host認証は不要。
`NATIVE_RECOVERY_EVIDENCE` は未使用 directory。正常solo/adaptive、子のusage欠落、期限、
観測費用超過、通知と遅延usage、通知と意図的usage省略、通知なし対照を有限試験で確認する。
通知自体が実providerの欠測原因であるとは推定しない。

64 KiB / 1 CPU / 2 GiB / PID 256 / CLI出力16 MiB は旧開発環境から継承する hard guard。
60秒・output 80000 は通常fixtureの cost cap、期限試験だけ短い cap とする。
notice fixture は最大12応答、CLI25秒、actor30秒の cost cap。全て当該校正だけの値で、
人数・本番予算の推奨ではない。owner は primary、正常fixtureが収まらない場合は開始前に見直す。

新しい依存は追加しない。旧 container/public projection、固定評価器、厳密collectorを再利用する。
独立採点の値を model に返さず、未確認の回収を成功扱いしない。

## 2026-09-09 の確認結果

[validation.json](validation.json)の source と一致する7試験が通過、skipなし、86.799秒。
疑似providerによる12 actor（上記8経路とtree/local compaction/remote compaction/圧縮usage欠落）と、
封印済みFIFOの独立採点7回を実行し、計19 containerを全て削除した。

- 子のusage欠落・通知と意図的usage省略でも、正常終了を照合して封印・独立採点できた。
  usage はpartial、output上限適合はunknown、admissionはwithholdのまま。
- 観測output上限超過は品質を測定してもbudgetをexceededとし、期限停止は品質適格性を保留した。
- 通知と遅延usage、通知なし対照は完全な応答記録を回収した。通知だけの因果は主張しない。
- fork履歴・4ノードtree・再相談・local/remote compactionを確認した。
  remote compactionをroot stdoutが除く例でも応答記録から加算し、欠落があればpartialとした。
- 封印後のcollector故障、回収不明、source変更、symlink、異常な評価器終了は、
  保存消失や正常品質・予算適合へ変換しない回帰試験で確認した。

これは回収経路の校正であり、指示改良の効果検証とは別の証拠である。
その後の[実比較](../refinement_cohort_v1/result.md)でもusage不足を残しながら全3提出物・72採点を回収できた。
品質回収は成立したが、協働の全費用・output上限適合は不明のままである。
最初の校正も別pathへ保持した。その後に評価器異常終了と不正policyの分類を修正したため、
現sourceの根拠には `native-recovery-preflight-20260909-02` とその `-extended` を使う。
