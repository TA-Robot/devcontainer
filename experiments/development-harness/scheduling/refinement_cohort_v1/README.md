# 旧協働指示・失敗から改良する指示・強い単独の比較

[protocol.md](protocol.md) と [config.json](config.json) が今回の正本。
3条件各1開始、順序standard→refined→solo、各40分、観測output上限各16万。
新しい公開24例と採点24例を同じ生成器の固定seedから作り、全条件へ同じ公開bytesを渡す。
新しい課題系列・未使用confirmationの検証とは呼ばない。

主比較は同じ協働能力を持つ旧指示対新版。strong soloにも自己検証・複数案・逐次改善を許す。
指示は既存の原文をsource snapshotへ含め、実験中に書き換えない。
原pairの結果・開始枠・候補は再利用しない。

## 実行経路

`run.py` が依存sourceを凍結し、別processから実行する。
開始台帳はactorの呼出し前に排他的に作る。`native_recovery_v1` がcontainerを削除して
各提出物を封印し、全参加者の終了とusageを別々に照合する。
全条件のsource・actor結果・公開入力を再確認してbarrierを作り、各採点前にも照合する。
採点は固定された別Docker評価器が行う。候補codeをhostで実行しない。

正常提出のusage不足・観測output超過では品質測定を継続し、output予算適合をwithholdとする。
参加者の異常終了・未提出・回収不明・source不一致は次の開始や採点を止める。
外側からの中断も稼働actorを停止・回収し、次の条件を開始しない。再試行枠はない。

`quality.json` は旧reporterの算術を使い、refined対standardを主比較として、両者対soloも残す。
case別の応答tail・未完了量、全セル・全負荷帯を保持する。
`triage_promising` は事前固定した限定的な採否材料で、安定した協働効果や単独不可能性ではない。
費用不明なら、共通の開発時計での品質と、未認定のoutput上限・費用効率を明確に分ける。

## 検証と開始

```bash
REFINEMENT_COHORT_DOCKER=1 PYTHONDONTWRITEBYTECODE=1 python3 -m unittest scripts/test-refinement-cohort.py
PYTHONDONTWRITEBYTECODE=1 python3 experiments/development-harness/scheduling/refinement_cohort_v1/calibrate.py --output /tmp/NEW-public-calibration
```

`REFINEMENT_COHORT_EVIDENCE` は未使用directory。通常・usage欠落・output超過・期限停止・外側中断を
疑似providerで検証する。公開校正は新しい全24例を固定FIFOで実行し、採点用24例は合法性確認と封印だけを行う。
sourceと一致する native recovery / cohort / 公開校正を `validation.json` へ固定するまでliveへ進めない。

固定campaignの入口:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 experiments/development-harness/scheduling/refinement_cohort_v1/run.py \
  --output "$HOME/.local/state/devcontainer-evaluations/scheduling-refinement-cohort-20260909-01" \
  --auth "${CODEX_HOME:-$HOME/.codex}/auth.json"
```

出力はsingle-use。認証の有効期間も開始前に確認する。認証内容は記録やレポートへ出さない。
新しい依存は追加しない。今回の実行で有効性が分からなければ、未達・不明としてそのまま保存する。

## 開始前の根拠

[validation.json](validation.json)のsourceと一致する6試験が通過（skipなし、122.648秒）。
疑似providerの13 actor、probeの独立採点9回、新しい公開全24例のFIFO採点を行い、
計46 containerを全て削除した。usage不足・output超過では品質を測定しつつ予算を保留し、
期限停止・外側中断では次条件を開始せず回収した。資格用24例を採点する校正はしていない。
この校正は難題適格性や指示の有効性の証拠ではない。
