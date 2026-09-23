# Fixed-artifact diagnosis after accounting withholding

元のpairはwithholdのまま保存する。両developerのCLIは正常終了しcontainerを削除済みだが、
native通知直前の出力にusageがなく、全費用を確認できなかった。
この別診断はモデルを呼ばず、終了済みの選択済み2ファイルだけを採点する。
適切な費用上限下での協働効果・費用効率を認定する比較には読み替えない。

`run.py`はsoloの既存封印とadaptiveの終了前SELECTION.md記載SHA256を照合し、
固定された元sourceの評価器・元qualificationを新pathへコピーする。
単独成果物→協働成果物の2採点、各900秒、総scenario 90秒/response 5秒。
最初の失敗で止め、再試行・候補交換・採点器変更は行わない。
これらのcost capはこの診断だけに適用し、ownerはprimary/integrator。
結果・cleanup・source hash・原結果hashを保存する。原case生成も元の封印済みgeneratorと一致確認する。

`audit_usage.py`は最初の不整合で打ち切られた元collectorを上書きせず、
全threadの記録済み応答だけを後から合算する。通知前の観測欠落は残し、
その後に記録された消費も回収する。累積値との一致は請求の完全性を保証しない。
`known_usage`は下限であり、欠けた応答をゼロ費用と見なさない。本文は集計へ保存しない。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest scripts/test-pair-recovery-diagnostics.py
```

実Docker採点結果は未使用pathへ保存する。原runの状態・得点・費用を更新しない。
