# Native collaboration accounting capability, v1

固定CLI 0.153.0・既存actor imageを使い、**親だけのusageを協働全体の費用にしない**ための有限な実動作検査。
実provider、認証、外部network、課題のhidden評価は使わない。
これは協働の品質効果やlive比較の完了を示す実験ではない。
[検証記録](validation.json): 実Dockerを含む11試験成功、skipなし。

## 確認する境界

疑似Responses providerが親のshell実行 → native spawn → 子の公開check → 完了 → 同じ子へのfollowup → 完了を指示する。
親6応答・子3応答、子は2turn。`fork_none`と`fork_all`を検査する。
親の`codex exec --json`はinput 120 / output 30しか返さないが、全参加者ではinput 180 / output 45になる。
cached input 63はinput 180の内数であり、加算しない。

`accounting.py`は、各sessionの`token_usage_record`をthread / turn / responseへ対応付けて集計する。
累積値の足し算、コピーされた親履歴の足し算はしない。応答合計をthread累積値へ照合し、
SQLiteのthread inventoryとrollout集合、固定model / effort / CLI、全turnの終端も照合する。
集計結果にprompt、モデル本文、command、private reasoning、認証を保存しない。

`missing_usage`では子の再相談応答からusageだけを除く。
直前までの累積値が残っていても新しい応答記録がなければ`withhold`、正式usageはnull。
`observed_usage`は回収できた部分だけであり、欠けた費用をゼロと見なさない。
失敗threadは最初の不整合で読むのを止めるため、その後の既知費用まで含むと保証しない。

子のshellでも公開probeを採点でき、疑似providerのlocal socketへ接続できないことを実行して確認する。
`child_timeout`は子がshellを開始した印を保存してから長い処理を続ける故障注入。
外側の期限でcontainerを削除し、計測を保留する。停止中の費用回収を正常計測と呼ばない。

## 実行

```bash
NATIVE_ACCOUNTING_DOCKER=1 PYTHONDONTWRITEBYTECODE=1 python3 -m unittest scripts/test-native-collaboration-accounting.py
python3 experiments/development-harness/scheduling/native_probe_v1/run.py \
  --mode fork_all --output /tmp/new-native-accounting-probe
```

`--output`は未使用path。modeは`fork_none / fork_all / missing_usage / child_timeout`。
`child_timeout`は意図した故障でもstatus `withhold`・exit 1を残す。テストが実行開始と削除を別に判定する。
source snapshot、生成した公開入力とpolicyのhash、疑似provider台帳、照合結果、container名と削除結果を保存する。
過去のsolo runner / evaluator / protocolは変更しない。

## 上限と適用範囲

全数値のownerは本課題のprimary/integrator。scopeはこのprovider-free能力検査のみ。

| 値 | 種類 | 根拠 / 更新条件 |
| --- | --- | --- |
| 子1体・子2turn・全9応答 | hypothesis / test fixture | 親子計上と再相談の最小識別例。推奨人数やlive予算ではない |
| 内側60秒・外側75秒・cleanup15秒 | cost cap | 正常検査は数秒。遅延で不足なら原因を保存して別検証版へ |
| 子稼働中の外側10秒 | cost cap / fault injection | shell開始後の打切りを確認。起動前に切れた検査は成功にしない |
| CPU1・memory2GiB・PIDs256 | cost cap | 既存actorの資源境界を再使用。実作業の最適値ではない |
| 外部networkなし・認証なし・read-only source | hard guard | 実モデルを使わずnative配線を検査する境界 |

現時点で検査したのは子1体の新規起動、全履歴fork、再相談、shell、usage欠落、container停止。
compaction、複数の同時子、孫、provider切断・retryの課金、途中停止時の全費用回収は未検証。
未知の記録形式では保留する。SQLiteとrolloutの照合もproviderの請求台帳の証明ではない。

次の作業はこの観測をlive actorの終了処理へ接続し、実際に許す協働範囲だけを追加検査すること。
その後、同じ公開check・新しい時間方針・全参加者予算を持つ新しい有限protocolで、fresh soloとadaptive協働を比較する。
元の保留soloを対照へ流用しない。汎用的な会話基盤や全方式の試験一式の完成を開始条件にしない。
