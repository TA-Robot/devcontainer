# 規模別の実開発評価

[評価方針](../../../docs/agents/development-harness-evaluation.md)に従い、小規模と大規模を別に評価する。現在は[大規模01](large-01/protocol.md)の課題・外部検証・有限段階実行を準備している。live結果はまだない。

## 有限の段階実行

`../campaign.py`は専用の評価containerで一度に一段階だけを実行する。後続stageの公開はprimaryが行う。自動scheduler、品質判定、自動採用、native session resumeは含まない。

外部のimmutable checkoutと専用containerを用意し、`scripts/benchmark-devcontainer.py start`で初期readinessを検証した後に停止する。manifestは`schema_version: 1`、study/condition/scale、model/effort/CLI、累積秒数・session・観測output tokenの上限、snapshot間隔・容量、各phaseのid・秒上限・prompt・prompt_sha256を持つJSON。大規模01の値はprotocolに固定する。manifestとstateはcandidateにmountしない。

```bash
python3 experiments/development-harness/campaign.py init \
  --manifest /private/control-manifest.json \
  --state /private/control-evidence \
  --workspace /private/control-workspace --container CONTROL_CONTAINER
python3 experiments/development-harness/campaign.py run --state /private/control-evidence
python3 experiments/development-harness/campaign.py status --state /private/control-evidence
```

`run`の終了はそのstageの提出であり、機能の合格ではない。次の`run`は既存sourceと公開済み要求を引き継ぐ新sessionで、元のbudgetから続ける。各stage後に専用containerを停止する。workspaceのtracked/dirty/untracked/ignored file・空directory・symlink自体をtarへ、Git履歴をbundleへ、差分とindexを別fileへ保存する。symlink先、workspace外の一時file、Docker volumeやメモリ状態はsnapshot対象外。sourceの復元はbundleとtarを別の一時directoryで行い、実作業中のcheckoutへ上書きしない。

実行中のstatusは、Dockerの実状態と進捗を読む。state fileや古い時刻だけでは停止と判定しない。recorderを失った場合は同じcontainerとprocess状態を確認し、必要なら**その専用containerだけ**を停止してから`recover --state ...`を使う。実行中containerからのrecoverは拒否する。復旧は予約したstage秒数を保守的に消費扱いにし、usageをunknown、状態をneeds_reviewとする。これは再実行の許可ではなく、primaryが次の条件を判断するための証跡回収。

usageは`turn.completed`で取得できた範囲のみ。output上限はイベント到着時・次のsession開始時に検査し、未報告のturn内での厳密な課金上限ではない。usage欠測なら次stageを自動的に許可しない。候補の自己申告が成功でも`task_accepted`はnullのまま。

監視の実装上のcost capとして、1イベント行は8 MiB、private event記録は64 MiB／stage、stderrは末尾64 KiB。記録打切りは明示し、集計は続ける。これらは初期source規模と通常CLI出力に基づく保存量の制限で、ownerはprimary。実際の不足が観測されたら比較条件と共に変更する。reasoning itemは保存しない。Docker管理commandは期限付きで、providerにはcontainer内の`timeout`も適用する。recorder障害時も無期限のモデル実行を前提にしない。

## 外部の意味的検証

停止・保存したcandidate sourceをread-only mountし、認証情報・networkを渡さない別の評価containerで実行する。

```bash
python3 /evaluator/evaluate.py --candidate /candidate --phase 3 --output /results/semantics.json
```

phase 2/3にはそれ以前の検証も含まれる。CLIのJSONに加え、実際のfile bytes・mode・利用者変更・障害後の状態を検査する。`semantic_checks_accepted`は列挙したシナリオの合格で、配布imageでの動作・build・全回帰・reviewまでを表す`release_accepted`は別途確認する。

## 検証

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  scripts/test-development-campaign.py scripts/test-project-lifecycle-evaluator.py
DEVELOPMENT_CAMPAIGN_IMAGE=devcontainer-frozen-smoke:latest \
  PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  scripts.test-development-campaign.DockerCampaignTests
```

実Dockerのtestもfake providerのみを使い、networkなしで実行する。copyだけの不完全な実装を用いて、正しい初回copyは検査を通る一方、既存fileの上書き・独自設定の消失・成功の自己申告だけを受け入れないことを検証する。これは全仕様のreference実装やlive成功を意味しない。
