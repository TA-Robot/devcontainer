# Adaptive scheduling pair v1

[事前固定protocol](protocol.md)に従う、fresh soloとadaptive協働の探索比較。
[config](config.json)は各1開始、順序solo→adaptive、開発各2400秒、全参加者output各160000以下、
独立採点各900秒、全体7500秒。上限の種類と根拠、失敗時の扱いはprotocolが正本。

`run.py`は必要sourceをsnapshotし、そのtreeからfresh processで実行する。
開始記録をモデル呼出し前に排他的作成し、両成果物の封印後にだけqualificationを採点する。
終了・例外時の原結果とcleanupを保存し、未測定・費用欠落・失敗条件で品質効果を出さない。
全24ケース、12系列/負荷セル、3負荷帯の品質は`quality.json`へ残す。
`difference`はadaptive minus soloであり、旧reference方策との差ではない。

[source一致preflight](validation.json)を通過後、2026-09-09にliveの2開始を使用した。
[結果](result.md): 両developer正常終了、元比較は通知中断付近のusage不足でwithhold。
選択済み成果物だけの別診断48採点は完了し、最重要完了は単独564 / 協働550だった。
このcampaignは終了済みであり、再開・追加開始しない。
実行先: `/home/asakura/.local/state/devcontainer-evaluations/scheduling-adaptive-pair-20260909-01`。
このpathは一度だけ使用する。途中失敗を理由に削除して再開しない。
過去の保留soloは対照に使わず、既知qualificationを未使用confirmationと呼ばない。
結果の確定は`controller.json`と`result.json`、独立評価・cleanup証拠を照合して行う。

```bash
ADAPTIVE_PAIR_DOCKER=1 PYTHONDONTWRITEBYTECODE=1 python3 -m unittest scripts/test-adaptive-scheduling-pair.py
```

疑似providerの原記録保存は`ADAPTIVE_PAIR_EVIDENCE`へ未使用pathを指定する。
live追加開始は別protocolと別campaignが必要であり、この1組の勝敗による追加枠を設けない。
