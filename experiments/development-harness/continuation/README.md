# 継続利用の開始判定と復旧観測

Cycle 003で実際に発生した「turn終了時の使用量超過」と「文書化した復旧手順を
評価器が使わない問題」に対する、次の利用のための修正。
過去の `campaign.py`、段階要求、評価器、manifest、結果のbytesは保持する。
[検証結果](validation.json)はprovider-freeの校正であり、新しいモデル比較ではない。

`admission.py` は既存runnerの開始前にmanifestと累積記録を検証し、同じ
`campaign.lock`の下で開始可否を判定する。残予算が正でも、未提出段階の最低予算を
確保できない場合は開始しない。実行・snapshot・停止には既存runnerを使う。
既存の入口を直接呼ぶ利用には追加判定は効かないため、次のcampaignの起動はこの入口へ
統一する。通常のCodexやagentctlの設定は変更しない。

```bash
# 読み取りのみ。Dockerやモデルを起動しない。旧runも変更せず診断できる。
python3 experiments/development-harness/continuation/admission.py inspect --state /path/to/evidence

# 次の試行では、新しいmanifestを実行前に固定する。
python3 experiments/development-harness/continuation/admission.py init \
  --manifest /path/to/manifest.json --state /path/to/new-evidence \
  --workspace /path/to/clean-candidate --container dedicated-container
python3 experiments/development-harness/continuation/admission.py run --state /path/to/new-evidence
```

新しいmanifestには既存の必須fieldsに加えて `admission` を指定する。
`schema_version: 1`、`kind: "planning_prior"`、`scope`、`rationale`、`owner`、
`update_when`、`stages` が必須。`stages` は全phase IDをkeyとし、各値に
`minimum_seconds` と整数の `minimum_output_tokens` を持つ。
値は課題の段階要求に応じて開始前に決め、global defaultを置かない。
時間の最低値はそのphase上限以下、全段階の最低値の合計はcampaign上限以下とする。
公開後のmanifest変更、usageの累積値の書換え、unknown usage、活動中session、
session数不足も新しい開始を許可しない。判定は `admission.json` に実行前stateのhashと
ともに保存する。旧manifestにpolicyを後付けして既存runを再開しない。

最低値は**次の開始を止めるplanning prior**であり、段階内の消費上限や完了保証ではない。
観測outputの上限は引き続きcost cap。turn途中の未通知使用量を止める保証はない。
`within_turn_output_enforcement` はfalseで、金額の上限とも呼ばない。
`submitted_within_observed_budget` は提出・観測予算の判定だけであり、
`quality_accepted` と `container_stopped` はunknown。実際の停止はtransport、
品質は独立した成果評価で別に確認する。`run` の終了値2は追加開始不可またはエラーを示し、
同時に返すJSONで今回の実行後なのか開始前の拒否なのかを判断する。
`stage_started` が今回の呼び出しで段階を実行したかを示す。
この入口だけではproject固有のDocker/cache readinessは確認しない。
実モデル試行では事前に実行環境を確認し、必要なら `run(output, transport_factory)` に
検証済みのstartup transportを渡す。準備時間とモデル時間を分ける手順も固定する。

[前回結果](../cycle-003/large-02/result.json)のAは予算内提出、Bは12,945 output tokensの
超過として読める。policyを追加して再実行せず、旧記録のhash一致も確認した。
この診断で失った費用が戻った、または開発速度が改善したとは主張しない。

## 公開された復旧手順を使う

```bash
python3 experiments/development-harness/continuation/recovery.py \
  --candidate /path/to/source --template /path/to/source/project \
  --procedure explicit --output /path/to/recovery.json
```

`--procedure automatic|explicit` は対象の公開手順から評価開始前に選ぶ。
CLIが失敗した後で成功する方へ自動切替はしない。`explicit` は
`--recover-incomplete` を使う既存agentctlの手順で、任意のshell文字列を受け取らない。
この観測は元のconcurrency witness、SIGKILL、query、strict validationを使い、
所有していた旧process groupの停止を確認してから再検証する。
停止の確認失敗・所有情報の読み取り不可は合格にせず、復旧コマンドも呼ばない。
新しいprovider sessionが増えていないことを確認する。

`--installed` では候補source/templateの指定を禁止し、同梱CLIとtemplateを使う。
呼び出し元が実image内で実行し、候補checkoutをmountしないことをDocker inspectで
確認する必要がある。observer自身はmountの安全性を推測しない。
自動復旧する参照実装と、明示復旧する配布実装の双方を校正する。
この追加観測で過去の40/41・12/13を書き換えない。

## 確認

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  scripts/test-development-admission.py scripts/test-development-campaign.py \
  scripts/test-development-recovery.py
```

実Dockerも確認する場合は既存の検証済みimage IDを
`DEVELOPMENT_CAMPAIGN_IMAGE` に指定する。試験は偽のprovider実行ファイルを使い、
ネットワークなしの専用containerを作成・停止・削除する。モデルや認証情報は使わない。
追加依存はない。戻す場合は新しいentrypointの利用をやめてこのdirectoryと専用testsを
除去できるが、旧runnerには後続段階の最低予算の判定がないことを記録する。
