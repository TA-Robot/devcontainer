# 起動完了を確認してから方策を実行する評価時計

[固定診断](../startup_probe_v1/result.md)に基づく別評価版。
Pythonの起動待ちを候補の初回応答と分け、候補自身の初期化は応答上限に含める。
旧版・旧得点は保持する。現在の範囲は非agent校正であり、実モデル比較は未接続。
[最終4試験と全公開校正](result.md)は通過した。source・原記録は[validation.json](validation.json)。

`launcher.py`は準備完了を通知して実行許可の1 byteを待つ。`transport.py`は応答時計を
開始してから実行許可と元のJSONL要求を送る。通知待ちの間には候補が実行されない。
元source・パス・argvを維持し、raw stdinでも最初の要求を失わない。
候補が準備完了を偽装しても時計は延長されない。

公開checkと独立Docker評価は共通のlauncher・受渡しを使う。起動待ち20秒、応答5秒、
起動を含む総scenario 90秒の範囲は[READY.md](READY.md)に固定する。
物理simulation・採点計算・非公開情報境界は旧版と同じ。時間はwall timeでありCPU時間ではない。

```bash
READY_RUNTIME_DOCKER=1 PYTHONDONTWRITEBYTECODE=1 python3 -m unittest scripts/test-ready-scheduling-runtime.py
PYTHONDONTWRITEBYTECODE=1 python3 experiments/development-harness/scheduling/ready_runtime_v1/calibrate.py --output NEW_PATH
```

試験の保存には`READY_RUNTIME_EVIDENCE`へ未使用prefixを指定する。`-activation`、`-parity`、
`-bounds`の3directoryを作る。校正はFIFOと同じ強い初期sourceについて、公開24例だけを
公開actorと独立評価で照合する。固定sourceを保存して実行し、未測定・不一致で停止する。
候補codeはhostで実行せず、qualification・旧live成果物・認証・モデル要求を使わない。

依存は既存のPython標準libraryとDockerのみ。`support.py`に実際に使用する旧sourceを列挙し、
それらを変更せず再利用する。`runtime.py`と`recovery.py`の旧版とのbyte一致も試験する。
通常配布への変更はない。撤去時はこの新directoryと対応試験・案内だけを対象にし、原記録は保持する。
