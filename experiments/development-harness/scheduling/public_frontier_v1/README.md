# 保存済み公開実験から次の介入を選ぶ

2026-09-09。adaptive pair の費用回収改修を主 milestone とする前に、
候補生成と選択のどちらに不足の手掛かりがあるか調べる有限の診断。

## 固定する範囲

- 対象は `scheduling-adaptive-pair-20260909-01` の保存済み公開 development 24 ケース。
  adaptive の work 直下の JSON のうち、同じ全ケースの結果を持つものを全て inventory にする。
  点数を見て候補を追加・除外しない。元の単独・協働の最終公開結果も保持する。
- 新しいモデル呼出し・候補実行・qualification/confirmation 読込みはゼロ。
  この禁止は今回の診断の hard guard。旧 run・評価器・得点・選択を変更しない。
- 入力 hash と保存 source hash が一致し、開始時 source 固定を記録した集合、
  source は一致するが入力 hash がない集合、それらも不足する全記録の集合を分ける。
  hash 一致は記録の追跡性であり、developer が作った記録の独立認証ではない。
- 各目的のケース別最大値を合計する。これは未来を知る選択の算術上限であって、
  実装可能な方策、実際の成果、online 必達目標、二目的を同時達成する一つの選択ではない。
  単一候補の非劣集合と負荷帯・family 別結果も残す。
- 上限が単独以下なら、この記録集合・目的では候補を選ぶだけでは差を埋められない。
  上限が単独を超えても、公開情報で選べたことや未使用条件への一般化を意味しない。
  新たな統合は別実装なので、この上限で制約しない。
- JSON の不正、重複、測定失敗、母数不一致は成功値へ変換しない。
  記録の不足を候補が存在しなかった証拠にしない。
- scope と guard の owner は primary/integrator。入力不一致・記録破損なら分析を止める。
  診断の完了を能力拡張の完了へ読み替えない。

## 実行

```bash
PYTHONDONTWRITEBYTECODE=1 python3 experiments/development-harness/scheduling/public_frontier_v1/audit.py \
  --original /home/asakura/.local/state/devcontainer-evaluations/scheduling-adaptive-pair-20260909-01 \
  --output /tmp/NEW-public-frontier
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest scripts/test-public-candidate-frontier.py
```

出力先は未使用 directory。plan に診断 source、全入力、採用・除外理由を固定してから
集計し、result に元記録を変更していないことを残す。candidate code は読み込んで hash を
計算するだけで、import/exec しない。新しい依存は追加しない。
