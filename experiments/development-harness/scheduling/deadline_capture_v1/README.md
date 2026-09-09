# 期限停止後の成果物を評価する別契約

[継続開発pair](../continuation_pair_v1/result.md)は、提出物と公開検証を保存していたが、
単独のCLIターンが40分以内に完了せず、協働の開始・独立採点を止めた。
その原判定を保持し、次の測定用に[別契約](CONTRACT.md)を疑似providerだけで検証する。

`capture.py`は既存native actorを変更せず使い、元のquality / lifecycle / usage / budgetを残したまま、
新しい`capture.json`で固定できた成果物の評価可否を表す。期限停止を正常終了へ変更しない。
`submission.py`以外の候補を後から選ばず、container・認証コピーの回収とsource確認後に封印したbytesを使う。

評価対象は**観測した停止・回収後の成果物**。要求した締切ちょうどの品質とは異なる。
bridgeの開発時計と、準備・回収も含むactor時計によるcapture windowの上界を保持する。
校正では要求時間+20秒を回収のhard guardとした。20秒の追加開発を与える意味ではなく、
この上界や時刻が不明なら保留する。新しい実比較の時間条件は、その前に別途固定する。

## 実際に確認したこと

[validation.json](validation.json)の39 sourceと一致する4試験が通過（skipなし、52.683秒）。
実CLIと疑似providerの6 actor、4つの独立採点containerを全て回収した。

| 条件 | 新しいcapture判定 | 独立採点 | 元の判定 |
| --- | --- | --- | --- |
| 正常終了・有効提出 | evaluable | measured | eligibleを維持 |
| 有効提出後の期限停止 | evaluable | measured | quality withhold / 時計exceededを維持 |
| 不正な割当を返す提出後の期限停止 | evaluable | invalid-policy | 同上。不正を品質成功にしない |
| 未提出で期限停止 | withhold | 実行しない | withholdを維持 |
| 子が書込み中に期限停止 | evaluable | measured | withholdを維持。採点中のhash不変を確認 |
| 外側から中断 | withhold | 実行しない | withholdを維持 |

回収不明、model bindingの不一致、source・manifest・公開入力・提出物の改変でも採点を保留する。
子の試験は、作業コピーへcommentを書き続けている途中で停止する。
旧actorの報告もhashで照合し、独立採点で上書きしない。

## 不正提出の分類修正

実Docker試験で、固定された`timing_diagnostic_v1/evaluate.py`は不正な割当をcase結果へ記録する一方、
その場合もprocess終了コード0を返すと確認した。旧adapterは不正の終了コードを1と想定し、
その結果をwithholdへまとめていた。新版の`assessment.py`では、実際の終了契約と、全caseの状態・
coverage・回収を併せて検査する。異常終了やunmeasuredは保留し、確認済みの不正をinvalid-policyに分ける。
旧評価器・adapter・保存済みの原判定は変更しない。

## 再現と範囲

```bash
DEADLINE_CAPTURE_DOCKER=1 PYTHONDONTWRITEBYTECODE=1 python3 -m unittest scripts/test-deadline-capture.py
```

`DEADLINE_CAPTURE_EVIDENCE`は未使用path。検証原記録は
`~/.local/state/devcontainer-evaluations/deadline-capture-preflight-20260909-03/`と`-03-interrupted/`。
初回の分類不一致、2回目の疑似writerのread-onlyコピーによる試験失敗も別pathに保持する。
writerの作業コピーだけをwritableにする修正後の`-03`を開始根拠とし、公開元のread-onlyは維持する。

この接続は疑似provider専用で、live入口・認証引数はない。
現runの成果物や非公開入力をこの契約で再採点しておらず、新しい実モデルも開始していない。
次は、この契約を両条件の回収・全提出封印・独立採点へ接続する有限な別比較を固定する。
会話完了と成果物品質の区別を検証できたことを、協働の品質効果へ読み替えない。
