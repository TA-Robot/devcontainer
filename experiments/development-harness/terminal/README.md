# 終端回収と測定時計 v2

P0の実装。途中でcontainerをpauseせず、提出・打ち切り・中断の後に停止を確認し、
成果を回収して固定評価器へ渡す。新しい依存や常駐service、agentの追加はない。
実装は新しいschema 2専用で、Cycle 004以前のmanifest・時計・得点を変更しない。

## 実行と停止の所有権

`runner.py`が有限のstageを管理し、`recorder.py`を別processで起動する。
recorderはCLIのイベントとusageだけを記録する。親のrunnerが期限を監視し、
recorderのSIGKILL、pipe切断、usage欠測があってもcontainerの停止と成果保全を実行する。
SIGINT/SIGTERMは親が受け取り、停止・回収・中断記録を閉じる。提出観測は停止処理前に保存する。

回収は停止証拠の間で行う。固定container ID/imageと、専用benchmark label・workspace mountを
検証する。停止APIが失敗しても、独立したinspectが停止を確認できた場合だけ回収する。
停止を確認できない場合は`stop_unconfirmed`で閉じ、採点と後続起動を行わない。
partial archive、評価器異常、記録process喪失も成功へ変換せず、未開始条件を残す。

`pair.py`は比較全体と両条件のstate lockを採点終了まで保持する。同じ入口の再実行、
別CLIによる割込み起動、初期sourceや固定コードの変更を拒否する。
隠された評価結果は開発sessionへ返さない。候補の品質不合格と評価基盤の異常を分ける。

SIGKILLで停止所有者そのものを失った場合やホスト・Docker daemon自体の喪失は、
通常のSIGTERMやrecorder子process喪失とは異なる。stateをreadyへ書き換えて再開しない。
provider側のtimeoutだけでcontainer全体の停止を証明せず、外側で所有者と実際の停止を確認する。
この版は新しい常駐watchdogや、所有者死亡後の無人再起動を提供しない。

## 時計と結果

各stageのelapsed timeは親processのmonotonic clockだけで測る。

| field | 意味 |
| --- | --- |
| `preparation_seconds` | containerの起動・準備にかかった時間 |
| `development_seconds` | recorder起動から親が提出・打ち切りを観測するまで。記録処理の時間も含む |
| `stop_requested_seconds` / `stop_confirmed_seconds` | 同じstageの起点からの停止要求／実際の停止確認。未確認の確認時刻はnull |
| `shutdown_seconds` | 要求から確認まで。提出時間へ加算しない |
| `capture_started_seconds` / `capture_completed_seconds` | 停止後のarchive取得区間 |
| `controller_seconds` | stageの準備から停止・回収までの全経過時間 |
| `known_development_seconds` / `reserved_unknown_seconds` | 計測済みの累積時間と、recorder喪失などの予約計上を分離 |
| `comparison_elapsed_seconds` | 一括実行開始から最後の採点までの実経過時間。事前のimage準備・sealは含まない |

`terminal-event.json`は停止前の原観測、`observation.json`は停止・回収を含む結果。
取得済みusageは打ち切り時も残すが、欠測のあるsessionを完全な使用量やゼロ費用とは扱わない。
未提出の成果がテストに合格しても、提出済み・予算内完了へ昇格させない。

`capture_window_seconds`を超えて停止が遅れた場合、同予算の品質比較と速度比の採用条件を
満たさない。複数段階では過去のstageの超過も引き継ぐ。許容窓内でも、予算時刻ちょうどの
sourceを得た証明にはせず、固定した停止方針の下で得た成果として報告する。
細かな品質到達曲線、model内部の計算時間、未観測の金額・model適用値、release品質は推定しない。

archive、展開、停止判定、固定評価器と採点は既存の`campaign.py` / `automatic/compare.py`を再利用する。
`automatic/finalize_interrupted.py`の旧時計向け予約投影へv2 stateを流さず、同じ
「停止確認→保全→固定検査」の境界をv2で接続する。旧finalizerは旧実験用にそのまま残す。

## 入力と起動

manifestは従来のstudy・condition・scale・model・effort・CLI指定、phases、全体の時間・session・
output・snapshot上限、phaseごとのadmission予約を持つ。変更点は以下。

- `schema_version: 2`と`clock: "terminal-v2"`を必須にする。
- `checkpoint_seconds`は指定できない。
- `stop_seconds`、`capture_seconds`、`capture_window_seconds`を正の有限値で明示する。
- `admission`には既存形式のscope・rationale・owner・update_whenと全phaseの予約を必須にする。

停止・archive時間とbyte/session/outputの上限はその比較のcost cap。
停止確認・source identity・state lockはhard guard。取得窓は同予算比較のhard guardで、
許容値はprovider-free校正から事前に決める。phase予約はplanning prior。
適用scopeはsealした比較だけ、更新ownerはprimary/integrator。校正条件やtaskが変われば
次のseal前に根拠付きで見直す。テストfixtureの数値を運用defaultへ転用しない。

```bash
python3 experiments/development-harness/terminal/runner.py init \
  --manifest /private/control-manifest.json --workspace /candidate/control \
  --container DEDICATED_CONTAINER --state /private/control-state

python3 experiments/development-harness/terminal/pair.py seal \
  --config /private/pair-v2.json --output /private/new-pair
python3 experiments/development-harness/terminal/pair.py run --output /private/new-pair
```

もう一方のconditionも独立したclean checkoutと専用containerで初期化する。
pair configは`schema_version: 2`、`clock: "terminal-v2"`、既存の固定`task`、
control/improvedの`conditions: [{id, state}, ...]`、digest固定`image`、
`observer_seconds`、`observer_slots: 1`、`intervention_fields`、必要時の`legacy`を指定する。
状態・workspace・比較出力の各directoryは互いに包含しない。
一括結果は`comparison.json`、途中の確定結果は`progress.json`、各観測は`observations/`へ置く。

このP0で使った課題は既存の校正fixture。P1の公開check/feedback contractとP2の未見課題・
全予算の固定は別のゲートであり、この実装だけで次のlive比較を開始しない。

## 確認

```bash
TERMINAL_DEVELOPMENT_IMAGE=sha256:検証済みimageのID \
  PYTHONDONTWRITEBYTECODE=1 python3 -m unittest scripts/test-terminal-development.py
```

実Dockerでも疑似providerだけを使い、host認証を渡さない。image未指定時はDocker確認をskipする。
正常提出後の遅い停止、閉じたpipe、期限超過、停止前の追加書込み、usage欠測・部分usage、
recorder SIGKILL、親のSIGTERM、停止API異常・停止未確認、archive上限、評価器異常、
3段階の継続、両条件の実行から21項目の自動採点までを確認する。
