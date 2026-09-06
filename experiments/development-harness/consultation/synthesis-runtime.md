# 証拠統合の実モデル比較接続

`synthesis_pilot.py`は[固定protocol](synthesis-protocol.md)の新しい実行入口。
旧`flow_v1.py`とterminal/feedback runnerは変更しない。
実比較は[結果と採否](synthesis-result.md)、事前確認は[synthesis-validation.json](synthesis-validation.json)を参照。
後続の`synthesis_report.py`が校正のvalidityを結合し、誤判定があると品質付き速度比を抑止する。

`synthesis_task.py`はF12-L revision 3の公開workspaceだけを各participantへ渡す。
advisorは`advice.json`、makerは既存の2成果物だけを提出する。余分なfile、symlink、入力変更を拒否し、
hash付き停止済みarchiveから助言を読む。hidden評価は全writerの停止を確認した後にだけ実行する。
評価器は別のnetworkなし・read-only containerで動かし、認証をmountしない。

`codex_transport.py`は既存のnamed workspace profileと固定CLIを使用する。
task commandのnetworkは無効。DockerのEnv順序は同一性に影響しないため、重複keyを拒否してからsortする。
値が違う場合は同等とは扱わない。全3containerの環境と、認証を使わないsandbox probeを確認する。
`prompt_relay.py`は旧terminalの汎用handoff要求が課題へ混入しないよう、入力hashを検証した後、
固定した実promptへ切り替える。terminal側とprovider側の両prompt hashを保存する。

```bash
SYNTHESIS_PILOT_IMAGE=sha256:<verified-image-id> PYTHONDONTWRITEBYTECODE=1 \
  python3 -m unittest scripts/test-synthesis-consultation-pilot.py

# configとprotocolを固定した新規実行だけ。過去の出力directoryを再利用しない。
PYTHONDONTWRITEBYTECODE=1 python3 experiments/development-harness/consultation/synthesis_pilot.py \
  --config <fixed-config.json> --output <new-private-run-directory> --auth <private-codex-auth.json>
```

校正では`execution=calibration`と`--fake-provider <directory>`を指定し、認証は渡さない。
疑似providerの固定応答による成功をモデル能力の証拠にしない。
期限・usage・提出不備で後続を止め、未着手と回収可能な成果を残す。自動retry/fallbackはしない。
終了時はこの実行が作ったcontainerだけを削除し、認証のprivate copyを削除する。

制約: requested model/effortは固定するが、resolved/appliedを確認できない場合はnull。
予約時間を実測時間へ読み替えず、全actorの観測usageと欠測を併記する。
外部評価の実行上限は90秒、作成と削除は各30秒。free textの対策の実効性は引き続き未測定。
host ownerのSIGKILLやDocker daemon喪失後の完全な自動復旧は、この接続で実装したことにはしない。
