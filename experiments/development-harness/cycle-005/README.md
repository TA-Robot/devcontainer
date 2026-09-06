# Cycle 005: CLI同期の失敗保全

Cycle 001〜004の実績を引き継ぎ、このdevcontainer自身の起動時更新を改善する次サイクル。
公開要求は[brief.md](brief.md)、比較方式・範囲・上限は[protocol.md](protocol.md)。

現行sourceでは、後段のGrok取得失敗で先に更新したnpm CLIが残る。故障注入で確認した。
空白を含むprefixで一時Grok binaryを起動する際の引用不足も、新しい正常経路の検査で顕在化した。
旧版へ結果を良く見せる補正を入れず、両候補は同じ未修正sourceから開始する。

`sync_fixture.py`は公開の9ケース。`evaluate_sync.py`は別入力と追加の4故障で合計13項目を確認する。
`reference_sync.py`は評価器の校正専用で、製品へ統合せず、開発者にも渡さない。
現行source、常時成功／失敗、所有権欠落、実行ファイル検証欠落、source変更を使って評価器を検査する。
評価器の合格は開発方式の改善効果ではない。

この題材は一つの起動時同期を扱う小規模比較で、大規模の継続開発へ一般化しない。
P0の時計・P1の同じ公開検査を使う自己検証／自動feedbackを適用する。
同じsource・image・公開情報・権限・予算のA/Bを登録順で各1回、途中結果によるやり直しなしで実行する。
既存の大規模比較を未実施へ戻さず、新方式の大規模効果だけを未測定として残す。

実行前のsource/image/order/public sourceはprivate sealへ保存する。実行後に、元の結果、
中断・欠測・予算超過、独立評価、統合判断をこのdirectoryへ記録する。
この準備文書だけでlive実行・改善・採用が完了したとは扱わない。

```bash
TERMINAL_DEVELOPMENT_IMAGE=sha256:検証済みimageのID \
  PYTHONDONTWRITEBYTECODE=1 python3 -m unittest scripts/test-cli-sync-evaluator.py
```

新taskは`feedback/task_evaluation.py`で接続する。旧`automatic/observer.py`と旧protocolは変更しない。
