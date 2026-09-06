# Queue review→修正の比較入口

別task `queue-review-repair-v1`と、新しい`queue-review-pilot-v1`を提供する。
[F04監査](../../selection/f04-lifecycle-audit.md)で見つけた要求違反を実動作で検査し、
同じ初期実装へのsolo点検・修正と、独立review→fresh makerを比較する。
[公開課題](brief.md)と[固定protocol](protocol.md)が今回の範囲を定める。

## 測るもの

- 各commandを別processで実行したときの状態とackの冪等性。
- path/ID/payloadの引数境界、未知IDの終了status、不正JSONの保全。
- 既存storeへのenqueue/ack更新で、旧readerが完全な旧bytesを保持し、pathには新状態が現れること。
- 修正前後の到達項目、退行、変更path、提出時間、reviewを含む全usage、欠測・未完了。

repairは直接上書きと引数再分割、preserveは正しい初期実装。初回比較はこの2組。
confirmationはack countと終了statusの別の欠陥を持ち、初回liveでは使用を拒否する。
同じbrief・検査手段を与え、シナリオ名や期待得点は参加者に知らせない。
preserveでは変更なしが有効な成果。変更pathがあるだけで不要な変更や品質退行とは判定しない。

## 実行・評価の境界

`pilot.py`は既存の固定pilotを独立したmodule instanceへ読み込み、task/KIND/transportを束縛する。
旧moduleのglobals、旧runnerのsource、古いrunは変更しない。
既存のprompt relay、環境照合、model-free sandbox probe、全停止・archive・usage回収を再利用する。
review受渡しは3-fieldのadvice.jsonで、makerが採否を決める。意味上の採用は自動判定できずunknown。

外部評価では評価側が状態を読み、CLI呼出しごとに専用containerを作成・終了・削除する。
mountは投影した実装3fileのread-only directoryと、そのprobeの一時stateのみ。
network・認証・Docker socket・oracle・校正解をcandidateへ渡さず、capabilityを全て落とす。
評価側のfile読み込みはsymlink/FIFOを拒否し、サイズを制限する。
評価側はcandidateのPythonをimportせず、提出testや公開checkerも実行しない。
全候補containerの停止を確認してから状態を観測する。

公開checkerは同じ意味の動作probeをlocal processへ実行する。外部評価は同じprobeをisolated runnerへ接続する。
判定にLLMや人の点数上書きは使わないが、意味判定が別実装の独立oracleであるとは主張しない。
sourceの変化、評価timeout、container起動/削除失敗は成功へ変換しない。

各CLI15秒、全評価のcommand開始枠120秒、削除30秒、CPU 1・memory256 MiB・PID64、
状態512 KiB・source1 MiB・stdout/stderr合計64 KiBはこの小課題のcost cap。
公開local checkのCLI上限は5秒。環境起動込みの外部上限と区別する。
scopeはこの版、ownerはprimary/integrator。正当な実装が収まらない、環境・sourceが変わった場合に再校正する。

## 検証とliveへの条件

```bash
PYTHONDONTWRITEBYTECODE=1 QUEUE_REVIEW_IMAGE=sha256:c7f904a12d7e7c63a2c7e46bc6654c8304b497a2836ecb08fb5bea0118f679ea \
  python3 -m unittest scripts/test-queue-review.py
PYTHONDONTWRITEBYTECODE=1 python3 experiments/development-harness/queue_review/v1/queue_calibration.py \
  --image sha256:c7f904a12d7e7c63a2c7e46bc6654c8304b497a2836ecb08fb5bea0118f679ea \
  --output /tmp/new-queue-review-calibration.json
```

校正は正当な2実装と欠陥を持つ7実装を使い、公開/外部判定を照合する。
testは両初期状態の両条件を疑似providerで実行し、正しい初期実装のno-op、全usage、
review受渡し、未知usage時の後続停止、元module不変性も確認する。
疑似providerへの正解mountはこの検証だけで使い、liveではauthだけを許す排他的な入口を継承する。

liveは`calibration.json`と`validation.json`の成功、image、source SHA、校正結果SHA、
両シナリオ検証の一致が必要。実行sealにもこの2記録を含める。
固定config以外、留保したconfirmation、既存出力dirへの再実行を拒否する。
別出力dirをまたぐ全体の実行回数台帳は未実装なので、初回2組という上限はprotocolに従いcontrollerが守る。

## 限界

これは通常完了時の動作とfile置換を測る小さな課題。
書込み途中のkill、電源断、並行writer、一般的な設計品質、継続開発能力は未測定。
同一family内の留保scenarioを、未使用の実プロジェクト全般に置き換えて呼ばない。
協働の品質・速度改善は校正や疑似providerでは実証できない。
実比較の結果と未使用条件での確認がそろうまで、常時reviewは既定化しない。

2026-09-06のpreflight: [校正9候補](calibration.json)と[実Dockerを含む9テスト](validation.json)が合格。
[repair config](repair-live.json)・[preserve config](preserve-live.json)を固定した。
