# 保存候補の受入判断adapter v1

provider-freeのprojection・公開probe・保存判定との照合を実装する。
根拠は[保存物の監査](../lifecycle-reuse-audit-2026-09-07.md)。live provider接続・協働比較は未実装。
過去のrunner・oracle・得点を変更せず、旧runを再開しない。

2026-09-07に専用imageで10テストと[標準・referenceの校正](calibration-2026-09-07.json)を完了。
標準は候補別の分類一致と採用保留、reference校正は分類一致と測定2群での選択を確認した。
[source・実行記録](validation.json)。初期の通常image試験後に独立reviewが完成版CLIの混入を指摘し、
専用imageへ変更して検証し直した。校正referenceをlive条件として使ったことにはしない。

## 公開するものと判定するもの

当時の3段階の公開要求と、候補の`manage-agent-project`本体だけを中立名でcopyする。
元の名前、README、test、Git履歴、評価、採用経緯は渡さない。
明示的なsource/targetを使う`matching-adoption`と`path-boundaries`だけを対象にする。
元repositoryを前提とするdefault source、配布image、他の要求、一般的な完成品質は対象外。

private sealへarchive tree・CLI・保存評価・評価source・公開要求・adapterのidentityを保持する。
標準はcontrol/improvedの2候補で、双方に既知のパス境界不合格がある。
integratedはcontrolからの統合修正なので、`--calibration`指定時だけ使う。独立した第三候補とは呼ばない。

stdoutのJSON分類を、hashの一致する保存評価の2群と照合する。
`matched / contradicted / incomplete / withhold`を返し、採用保留を強制選択へ変えない。
nullだけの提出は候補別・scope別の出力がないため無効。unknownは正答に数えない。
全分類が一致しても「根拠が正しい」「良い実装を選べた」「全要求合格」とは扱わない。
根拠fileの実在は構造検査であり、無関係なfileを参照して分類だけ当てる出力は識別できない。
`semantic_evidence_validity=unknown`を保持し、自由文をLLMで採点して穴埋めしない。

## 公開probeの実行境界

`probe`はcontrollerが呼ぶAPIであり、agentへhost Docker socketを渡すtoolではない。
任意のPython probeを別containerで実行する。候補codeをhostで実行しない。
imageは[専用Dockerfile](Probe.Dockerfile)から作ったPythonのみのimageで、[固定ID](probe-image.json)以外を拒否する。
通常devcontainerには完成版CLIと案内が同梱されているため、参照実装の漏洩を避けて使わない。
readonly rootfs、cap-drop ALL、no-new-privileges、networkなし、認証なし。
`/task`とprobeだけをread-only mountし、`/tmp`・`/work`は容量制限付きtmpfs。
hostへ書き込めるmountはなく、stdoutだけをbounded captureして終了後に保存する。
scratchの生成fileは回収しない。根拠には保存した`probe.py`か、公開taskのfileを参照できる。

終了・timeout・output超過後も所有containerを削除し、削除できなければ照合を保留する。
sourceや保存評価の変更、JSONの重複key/非有限数/不正参照、未提出、終了code不正も保留する。
実行時間とcleanup時間は別に記録し、過去の候補生成時間や不明のtoken費用を加えない。

## 実行

`prepare`には保存済みarchiveと評価が必要。既存pathへの出力は拒否する。
順序はcontrollerが明示し、IDから品質を推定させる運用をしない。

```bash
python3 experiments/development-harness/selection/lifecycle_v1/adapter.py prepare \
  --order improved control --output /tmp/new-selection-task
python3 experiments/development-harness/selection/lifecycle_v1/adapter.py probe \
  --task /tmp/new-selection-task --script /tmp/my-probe.py \
  --image sha256:IMAGE_ID --seconds 30 --output /tmp/new-selection-run
python3 experiments/development-harness/selection/lifecycle_v1/adapter.py assess \
  --task /tmp/new-selection-task --run /tmp/new-selection-run --output /tmp/new-assessment.json
```

schemaは[公開task](TASK.md)にある。`calibrate.py`は標準2候補とreferenceを含む3候補の経路を、
同じ[校正probe](calibration_probe.py)で確認して新しいpathへ保存する。
校正probeはprivate側に置き、一般のdeveloper入力へ正解や検査の着眼点として配らない。
このprobeで欠陥を露出できたことと、対象2群の全動作を新環境で再採点したことは区別する。

```bash
PYTHONDONTWRITEBYTECODE=1 LIFECYCLE_SELECTION_IMAGE=sha256:IMAGE_ID \
  python3 -m unittest scripts/test-lifecycle-selection.py
PYTHONDONTWRITEBYTECODE=1 python3 experiments/development-harness/selection/lifecycle_v1/calibrate.py \
  --image sha256:IMAGE_ID --output /tmp/new-selection-calibration
```

上限は今回のprovider-free能力確認のcost cap。probe最大120秒（校正は30秒）、stdout+stderr合計64KiB、
probe source64KiB、通常入力1MiB、archive照合file16MiB、各tmpfs16MiB、memory256MiB、PID64、CPU1、cleanup30秒。
根拠は小さいCLIと使い捨てのfile検証を有限にすること。ownerはprimary/integrator。
妥当なprobeが上限で止まる場合は新configで見直し、途中で上限を増やして成功扱いしない。
calibrationの候補数は保存物の役割から決めた構成で、協働の推奨人数ではない。
source不変・情報境界・削除確認・元得点保持はhard guard。

専用imageの追加依存はUbuntuのPython 3とそのOS依存だけで、既存CLIのstdlib実行に必要。
通常devcontainerへ依存を追加せず、providerや完成済みprojectを同梱する代替は情報境界のため不採用。
imageはbuild結果のdigestで固定する。再buildでdigestが変わる場合はpolicyと校正を新版として更新する。
廃止時はこのadapterと専用imageを削除すればよく、通常devcontainerや利用projectのruntimeへ影響しない。

次にlive接続を検討する場合は、agentが公開probeを呼ぶ窓口と全呼出し予算・停止を設計し、
モデルの選択・根拠の意味・協働効果を測る問いを別protocolに固定する。
probe側だけでなく、agent自身のtoolから見える実行環境にも完成実装・旧判定を含めない必要がある。
このadapterの成功から、live対応や協働の性能改善を主張しない。
