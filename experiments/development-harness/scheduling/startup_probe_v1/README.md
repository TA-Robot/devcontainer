# 起動待ちと応答時間の切分け

固定された非agent fixtureの6観測で、旧時計では起動待ちも最初の5秒応答上限へ
入ることを確認した。[結果](result.md)と[事前計画](PLAN.md)を参照する。
以前のホスト遅延の根本原因や、候補の品質を特定する診断ではない。

```bash
STARTUP_PROBE_DOCKER=1 PYTHONDONTWRITEBYTECODE=1 python3 -m unittest scripts/test-scheduling-startup-probe.py
```

原記録を保存する場合は`STARTUP_PROBE_EVIDENCE`へ未使用directoryを指定する。
6観測を1回ずつ行い、予想外の結果・回収不明で停止する。実モデル・旧提出物は使わない。
固定fixtureのmarkerを、任意の候補が自己申告する準備完了へ一般化しない。
候補の自己申告に依存しない実装は[別版](../ready_runtime_v1/README.md)に置く。
