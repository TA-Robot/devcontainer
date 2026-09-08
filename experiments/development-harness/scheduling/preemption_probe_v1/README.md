# Native notification and partial-stream diagnosis

実CLI 0.153.0と固定actor imageを疑似providerで動かす有限な切り分け。
親の応答を途中までstreamし、usageを含むresponse.completedを送る前に、
子からnative send_messageで通知する。
初回は終端usageを送らず、親子とも正常終了してもcollectorがwithholdになる状態を作れた。
ただしこれは、通知だけを原因として分離した試験ではなかった。

追加のfixtureは通知後に遅延した終端usageを送り、通知なしcontrolも実行する。
両方でusageを回収できた。**このfixtureでは通知だけによる欠落は再現していない。**
`notification_hypothesis_reproduced=false`は有効な診断結果であり、失敗を勝ちまで繰り返さない。
`--control`は通知なしで遅延終端を送る。通常モードは通知ありで同じ終端を送る。

これは「途中応答の費用をゼロにしてよい」という根拠ではない。
実runの38箇所では未計上出力の直後にnative通知が入っているが、原因や実providerでの
終端処理・課金まではこの疑似providerで判定できない。隣接する事実と因果を区別する。

`run.py`は元pairのsourceを新しいpathへコピーし、fake fixtureだけ差し替える。
元runや元の固定コードを変更しない。実モデル・認証・外部networkは使わない。
1 parent + 1 childは通知中断を識別するfixture、25秒のCLI期限・30秒のactor期限・
12応答上限はこのprobeのcost capであり、ownerはprimary/integrator。
原記録・source hash・削除結果を保存し、実行完了と仮説の再現を別フィールドへ残す。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 experiments/development-harness/scheduling/preemption_probe_v1/run.py \
  --original /path/to/original-pair --output /tmp/new-native-preemption-probe
```
