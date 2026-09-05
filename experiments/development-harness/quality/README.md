# 品質評価の実行と校正

`lifecycle.py`は、template lifecycleの品質を8つの要求単位で観測する。
cycle-002の35シナリオを再利用し、採用時の非実行permission保持、source/targetの
重複拒否、管理データのGit除外を追加する。総合点は付けず、要求ごとの
`passed / failed / unknown`と、その根拠になった各観測を返す。

これは新しい評価器の校正であり、cycle-002の固定得点を変更しない。
Git除外は今回明示した運用上の期待であり、旧課題へ遡って追加した合格条件ではない。
既知の不具合を識別できても、未知の品質差への感度が十分とはまだ言えない。

## 実行

認証情報とnetworkを渡さない一時評価containerで、停止済みのcandidate exportを
read-only mountして実行する。実作業中のcheckoutや未追跡実験を含むrepository全体を
candidateとして渡さない。outputはcandidateの外へ置く。

```bash
python3 /evaluator/quality/lifecycle.py \
  --candidate /candidate --output /results/quality.json
```

`/evaluator`には`experiments/development-harness/`全体をmountする。
共有する旧評価器のhashと、新評価器・candidateのhashを結果へ保存する。
終了コード0は**測定を完遂した**意味であり、候補の品質合格ではない。
評価器や環境の例外は`unknown`、観測できた要件違反は`failed`とする。
sourceが評価中に変わった場合は観測を`unknown`にする。
各CLI呼出しにはtimeoutがある。全体も呼出側で有限のjobにする。

要求に含まれる複数の検査を合算して品質点を増やさない。検査欠測は成功にしない。
hard guardはこの課題の変更保全・復旧に関する条件で、ownerはprimary/integrator。
将来の課題では利用目的・重大故障に合わせて再定義する。

## 測っていないこと

案内だけで初回利用できるか、人間の手間、後続開発の変更量・時間・退行、配布imageの
動作は、この評価器だけでは測らない。これらを明示的に`unmeasured`へ残す。
既存のmerge成功を、実装自体の保守しやすさの証明としない。
配布確認には既存のcontainer smoke、保守性には条件を揃えた後続開発が必要。

同時間の品質・同品質への到達時間は、この結果を時刻・公開要求・run identityと
結び付けて比較する。過去の最終成果だけを測って時間曲線を推定しない。
観測時刻の選定、課題・予算・反復は[評価方針](../../../docs/agents/development-harness-evaluation.md)
に従って新しいlive比較の前に固定する。

## 回帰と校正

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest scripts/test-lifecycle-quality.py
```

正しいCLI、permission全体の一致を誤って要求する変種、成功を返しながら権限を
緩める変種、Git除外の欠落、旧重複判定を使って検査の感度を確認する。
欠測、評価器例外、重複した観測による水増しも検査する。
以前の候補への同一評価と結果は[cycle-003準備報告](../../../docs/agents/development-harness-cycle-003.md)を参照。

## 検証能力の独立probe

`../probe_codex_sandbox.py`はモデルを呼ばず、固定版Codexの実際のsandboxで
Unix listener、既存Unix socketへの接続、loopback listener、workspace外の書き込みを
観測する。通常のユーザー設定は変更せず、一時的なCODEX_HOMEだけを使う。

```bash
docker run --rm --privileged --network none \
  -e PYTHONDONTWRITEBYTECODE=1 \
  -v "$PWD/experiments/development-harness/probe_codex_sandbox.py:/probe.py:ro" \
  -v /absolute/private/results:/results \
  --entrypoint python3 IMAGE /probe.py --output /results/sandbox.json
```

事前に専用results directoryを作り、image内の利用者が書けるようにする。
認証情報、host Docker socket、普段のCODEX_HOMEをmountしない。
30秒／commandはprobeのcost capで、固定版0.153.0の短いローカル確認に十分な
初期値としてprimaryが所有する。実測した遅延や別版への対応時に見直す。
全体を有限jobとして実行し、OS sandboxのためのprivileged containerを強い隔離と呼ばない。

`workspace-network`は比較用で、通常運用の既定設定として配布しない。
公式の[permissions仕様](https://learn.chatgpt.com/docs/permissions)では、network許可と
proxyによる接続先制限は別の設定である。ここでは外側の`--network none`の下で
ローカル能力だけを測るため、外向き通信や一般的な隔離の安全性は評価していない。
現行campaignのlegacy `--sandbox workspace-write`との完全な等価性も主張しない。
