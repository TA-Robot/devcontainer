# 保存候補の受入点検を実モデルへ接続するrelay v1

[固定protocol](protocol.md)の1組だけを実行する有限controller。
公開仕様と候補を読んだmakerがPython検証を要求し、隔離probeのstdoutを受け、最終JSONを提出する。
consult条件は先に独立advisorのコード・仕様読解を加える。
[実比較結果](result.md): 両条件4分類一致・採用保留、相談側は時間47%増。固定1組は使用済み。
旧[adapter](../lifecycle_v1/README.md)、oracle、保存判定は変更しない。
分類の一致は自動判定するが、自由文の根拠の真偽はunknownのまま保持する。

## 情報境界

[actor image](actor-image.json)は既存のPython専用imageへ固定Codex native binaryとCA証明書だけを追加する。
通常devcontainerの完成CLI・templateを持ち込まない。actorへmountするのは固定policyと一時認証copyだけ。
公開候補はprompt中のデータとして渡し、候補codeは認証・networkなしの別probe imageだけで実行する。
既存認証はprivate出力配下へ0600でcopyし、終了時に削除する。prompt・生responseは公開せずprivate出力へ保持する。

`model-catalog.json`は当時のローカルモデルmetadataから対象モデルだけを固定したもの。
設定名の存在だけからtool無効を推測せず、実binaryのHTTP要求を[capability.py](capability.py)で捕捉する。
合格条件は要求1回・`tools=[]`・正常終了と既知usage。
code-mode host無効の既知startup通知だけを許容し、未知tool/error/usageは停止する。
設定項目の参考は[公式config reference](https://learn.chatgpt.com/docs/config-file/config-reference)。
この版の能力主張は固定binary・metadata・設定の実測に限定する。

## 検証と実行

```bash
PYTHONDONTWRITEBYTECODE=1 LIFECYCLE_RELAY_DOCKER=1 \
  python3 -m unittest scripts/test-lifecycle-relay.py
```

疑似providerだけで両条件のprobe受渡し・原文一致・未知usage・timeout・消費超過・回収失敗を確認する。
実CLIの能力確認もnetwork・認証なしのローカル疑似Responses serverで行う。
実比較にはsource hashが一致した`validation.json`が必要。fresh pathだけを受理し、旧runを再開しない。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 experiments/development-harness/selection/relay_v1/relay.py \
  --auth /path/to/existing/auth.json --output /path/to/new-private-run
```

これは自由な追加runの案内ではない。このprotocolのlive割当は1組のみで、使用後の再比較には新protocolが必要。
`result.json`へ全開始条件・全actorのinput/cache/output・時間・probe・最終自動照合を保存する。
最終原response、content、print-only probe、stdoutのhashを結び、採点入力の修復をしない。
時間は条件内の起動・相談受渡し・検証・提出・回収を含む。output上限は終了時の観測値で、in-turn強制上限ではない。
中断で最終usageが得られなければunknownとして停止する。

追加runtime依存は既存image由来のCodex binaryとCA証明書。CLI要求の実観測と既存認証方式を保つために必要。
通常imageの流用は完成版漏洩、独自API clientは別runtimeの検証費用があるため採用しない。
通常devcontainerの依存は変更しない。廃止時はこのrelayと専用actor image/tagを削除する。
親Python imageは旧adapterでも使うので、他の利用がなくなるまで残す。
