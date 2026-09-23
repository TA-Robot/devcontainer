# 相談の受渡しから採点までの接続

更新: 2026-09-06。`flow_v1.py`を実装し、疑似providerと実Dockerで検証済み。
**live provider adapterは未実装。ここでの成功は協働効果の測定結果ではない。**

上記は`flow_v1.py`の境界。後続の[synthesis pilot接続](synthesis-runtime.md)では実Codex比較まで完了し、
[原結果と評価器の制限](synthesis-result.md)を記録した。二つの実行kindを混ぜない。

## 実行する関係

同じ公開診断課題で、soloのmaker一人と、advisorの助言を受けるmakerを比較する実行経路。
相談側はadvisor → 停止・保全 → 助言の受渡し → 新しいmaker sessionという直列の関係。
途中のprimaryからの相談、同一sessionの再開、双方向の対話、自動的な方式選択はまだ扱わない。
両条件でmakerは自由に公開tool・自己検証を使え、最終提出を所有する。

期待する作用は別contextからの証拠の補充だが、疑似providerは固定応答なので効果は測れない。
使う[診断課題v1](v1/README.md)も、主たる品質比較には不採用とした実行校正用の課題。
この接続は、今後の実モデル実験で測定漏れや受渡し失敗を起こさないために用意した。

## 再利用と新しい境界

旧`terminal/runner.py`・recorder・archive・clock・状態形式は変更せず、participantごとに
新しいterminal stateを作って実行する。過去runを再開せず、新しいflowは別のkindで記録する。

- 各participantは別のcheckout/container。同じ公開task/sourceから開始する。
- advisorへ渡すのは公開課題。makerの提出やhidden評価は渡さない。
- 助言はwriter停止後のhash付きarchiveから読み、`recommendation/evidence/uncertainty`の
  有限JSONだけを次のpromptへ渡す。助言は診断データとして扱い、指示として扱わない。
- 内容はprivate prompt/成果に残し、集計へはhash、byte数、受渡し状態を出す。
  「届いた」と「役立った」を区別し、意味上の採用は`unknown`を保持する。
- advisorとmakerの実行・待ち・初期化・停止・回収・受渡しを同じcondition期限へ含める。
  advisorの開始前にmakerの最低時間・outputを予約し、使用量不明なら後続を起動しない。
- solo makerはconditionの残り予算を使える。advisor一人の上限へsoloを制限しない。
- 全participantの停止確認後にだけ外部評価する。未確認なら、完了済みの他条件も採点を保留する。
- 無効な助言・期限・予算・実行異常で後続を停止し、未着手を残す。暗黙のsolo fallbackや再試行はしない。
- 一度開始した出力directoryは再利用しない。コードのsealも実行中と採点前後に確認する。

旧terminal promptは`DEVELOPMENT_HANDOFF.md`を要求するため、新flowの公開指示でこれを明示的に許可する。
元archiveに保存し、regular file・16 KiB以下を確認してhashを記録した後、課題用の評価入力からだけ除外する。
それ以外の余分なfileやsource変更は拒否する。既存の課題oracleへ一般的なignore規則を追加しない。

## 実行APIと有限上限

`flow_v1.run(config, unused_output_path, deterministic_transport_factory, evaluator)`が入口。
直接のlive CLIは提供しない。`execution=provider-free`、task variant、条件順を明示する。
transportには既存terminalと同じstart/stopped/stop_bounded/argv契約が必要。
`provider_free=True`は校正adapterの宣言であり、任意コードの通信を封じるsecurity boundaryではない。
検証で使うDockerはnetworkなし・read-only root・認証mountなしに設定する。

| config項目 | 意味 |
| --- | --- |
| `condition_seconds` | 初期化から全actor完了までの共通期限 |
| `actor_seconds` | advisorの開発上限。makerはconditionの残りを使う |
| `minimum_seconds`, `minimum_output_tokens` | 後続makerの予約と開始判定 |
| `output_tokens` | condition全体で観測するoutput上限 |
| `stop_seconds`, `capture_seconds`, `capture_window_seconds` | terminalの停止・回収・取得窓 |
| `snapshot_bytes`, `advice_bytes` | archiveと助言のbyte上限 |

全値はcallerが明示。実装は有限の正数と範囲を検査するが、live向けの既定値を生成しない。
現在の人数・直列順はこの校正関係のhard guard、上限はcost cap、最低予約はplanning prior。
範囲はこのflow、ownerはprimary/integrator。task/transportの変更や正常実行の上限超過で見直す。
この関係にadvisor一人を使うことを、一般的な相談人数の推奨にしない。

input/cache/outputは全actorの観測recordを合計し、欠測と完全性を併記する。
不完全な合計は実消費の見積りではない。in-turn output上限を厳密保証せず、総token同額とも呼ばない。
condition実行時間、外部評価時間、全体時間を分け、疑似runの速度比や料金は出さない。

## 検証

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest scripts/test-consultation-flow.py
```

`CONSULTATION_FLOW_IMAGE`に検証済みimage IDを指定すると、実Dockerで正常な両条件と
待ち続けるadvisorの停止を確認する。[検証記録](flow-validation.json)では9テスト合格、skipなし。
相談側でusageが2参加者分になること、助言の受渡し、全停止前の採点禁止、無効助言、
未知usage、予算超過、停止不明、評価器不正、source変更を確認した。

## 残る仕事

実モデル向けには、provider/version/権限・mountの同等性と能力probe、固定した全予算、
CLI接続、advisorとmakerの情報境界の実確認が必要。現在の疑似輸送の注入をlive対応済みと表示しない。
主比較の題材は[F12-L監査](../selection/f12-synthesis-audit.md)に基づいて測定範囲を限定し、
公開仕様、oracle、介入、採否を変える条件をまとめてからlive protocolを固定する。

この後続作業は別接続で実施済み。現在の次作業は、liveで再現した誤判定を別評価版の校正へ戻すこと。
