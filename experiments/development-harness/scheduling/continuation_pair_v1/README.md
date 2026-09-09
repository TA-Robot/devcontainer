# 強い初期実装からの継続開発比較

[protocol.md](protocol.md)と[config.json](config.json)が今回の実行条件。
単独→標準native協働を各1開始・追加開発各40分で比較する。
[前回の判断](../refinement_cohort_v1/result.md)を受け、同じ強い初期sourceを両条件へ渡す。
前回未達だったrefinement指示の採用・再試行とは分ける。

2026-09-09、単独が40分の期限で停止し、[比較は保留](result.md)になった。
1開始のみ使用し、協働は開始せず、独立採点も行っていない。未使用枠を含めこのpairは閉じる。
以下のsingle-use pathを追加開始・再開に使わない。

`initial-policy.txt`は前回単独の選択済みsourceのbyte-identicalな保存物。
SHA256は`24c82c7e2fbc98edb73a384170074da8bf0240eb5203179aa253cbe9a5055424`。
原記録は`~/.local/state/devcontainer-evaluations/scheduling-refinement-cohort-20260909-01/actors/solo/submission.py`。
テキストassetとして保存し、hostでimport・実行しない。actorへは`/public/initial.py`としてコピーする。
初期sourceの前回作成費は共通の既払い準備費で、今回の追加開発費と分ける。全project費用は未計測。

## 実行と採点

既存native recovery actorを変更せず、公開11ファイルを同じbytesで両条件へ渡す。
初期sourceを含む公開説明のほか、前developerの会話・評価得点・非公開traceを渡さない。
単独も全面置換・複数案・自己検証を使え、協働も初期実装の保持を選べる。

`adapter.py`は固定actorを読み込む薄い接続。疑似providerの検証時だけ、独立したmodule instanceと
専用directoryでfixtureを差し替える。entry・accounting・sandbox・回収は元のbytesを維持し、
liveでfixtureを差し替えない。両条件の初期読込み→壊れた編集→公開失敗→修正→提出を確認する。

両developerの正常終了と提出物・公開bytes・初期source・actor結果の封印後に、固定した同じ評価24例を使う。
初期source、単独、協働の順に各24例を独立Dockerで採点する。初期sourceは非agent基準であり、advisorではない。
主比較は新しい協働対新しい単独。両者の初期sourceからの変化も同じ入力上で報告する。

品質・usage・予算適合・回収を分ける。usage不足でも正常提出の品質は測定し、費用とoutput適合を保留する。
期限・異常終了・未提出・source不一致・回収不明では後続を止める。追加開始や候補交換は行わない。

## 検証

```bash
SCHEDULING_CONTINUATION_DOCKER=1 PYTHONDONTWRITEBYTECODE=1 python3 -m unittest scripts/test-scheduling-continuation.py
PYTHONDONTWRITEBYTECODE=1 python3 experiments/development-harness/scheduling/continuation_pair_v1/calibrate.py --output /tmp/NEW-continuation-calibration
```

`SCHEDULING_CONTINUATION_EVIDENCE`は未使用directory。通常・使用量欠落・output超過・期限・外側中断と、
両提出・共通初期sourceのbarrierを確認する。校正では固定FIFO/初期sourceを公開24例で実行し、
公開checkと独立Dockerの全結果・traceを照合する。評価用入力は合法性確認と封印だけで採点しない。
初期sourceの公開校正は接続と時間枠の証拠であり、協働効果や単独の改善不可能性ではない。

実行前にsourceと一致する検証・全公開校正を`validation.json`へ固定した。
認証内容を保存・表示せず、必要な有効期間だけを確認する。固定live pathはsingle-use。
以下は実施済みの入口記録。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 experiments/development-harness/scheduling/continuation_pair_v1/run.py \
  --output "$HOME/.local/state/devcontainer-evaluations/scheduling-continuation-pair-20260909-01" \
  --auth "${CODEX_HOME:-$HOME/.codex}/auth.json"
```

新しい依存は追加しない。旧runner・protocol・提出物・得点は変更しない。
新seedを未使用の課題系列やconfirmationと呼ばず、1組で安定した能力拡張を認定しない。

## 開始前の根拠

[validation.json](validation.json)の49 sourceと一致する実Dockerの5試験が通過（skipなし、80.411秒）。
疑似providerの8 actorと9独立採点、公開校正の48独立採点と2つの公開check container、計67個を全て回収した。
FIFO/初期sourceとも、公開24例の全指標・trace・completion mapが独立採点と一致した。
採点用24例は合法性確認と封印だけで、policyの得点を見て入力を選んでいない。
最初の疑似provider fixtureにあった故障注入コマンドの引用符誤りは修正した。
失敗した`continuation-pair-preflight-20260909-01`は保持し、開始根拠には修正後の`-02`を使う。
