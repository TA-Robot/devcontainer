# Native development actor integration, v1

単独とadaptive協働に、同じCLI起動・期限停止・終了後のusage回収を接続した。
`entry.py`は固定Codex 0.153.0を起動するcontainer内bridgeであり、疑似providerとlive引数で共用する。
**実モデルの新しい比較はまだ開始していない。** このdirectoryだけでは比較protocol・開始台帳・全体集計は提供しない。

## 実装と検証済みの結果

- `actor.py`: fresh workspace、共通公開入力、条件別native tool設定、source/input seal、credential copy除去、container回収。
- `entry.py`: 永続native記録を有効にした1回のexec、CLI出力上限、開発期限、CLI process group停止、usage/inventory回収。
- collectorは[前段で検証したもの](../native_probe_v1/accounting.py)をsnapshotして使用する。
- `fake_solo.py`と`fake_adaptive.py`も同じbridgeを通す。前者の疑似response IDは応答ごとに一意。

[検証記録](validation.json)の2テストには、実Dockerのactor 5実行と外部policy採点2実行を含む。

| actor条件 | 結果 | 確認した内容 |
| --- | --- | --- |
| solo正常 | completed | 4応答のinput 80 / output 20を回収。公開修正checkと独立採点が一致 |
| adaptive正常 | completed | 親6・子3応答、子への再相談を含むinput 180 / output 45を回収。公開checkと独立採点が一致 |
| 子の再相談usage欠落 | withhold | 正式usageはnull。欠落前のinput 160は部分観測として保存 |
| 子がshell実行中に開発期限到達 | withhold | 実行開始の印、deadline理由、部分usageを保存してcontainerを削除 |
| 全参加者のoutput上限40に対し45を観測 | withhold | 親の30だけでは超過を見逃す例を、子も含めて検出 |

7 containerは全て削除済み。child shellの疑似providerへのsocket接続と、`/observation`への書込みは拒否された。
SQLiteはinventoryの4列だけを保存し、`auth.json`やCodex home全体をhostへコピーしない。
session原記録とCLI出力はrun内のprivate evidenceへ残す。通常の集計は本文を含まない。
credentialのcopy/removeを実行するlive分岐は、この認証なし検査の測定範囲外。

## 公開能力と時計

両条件へ同じ9ファイルを配布する。TASKは協働を禁止する旧solo文から共通contractへ改め、
条件固有の協働可否と予算はrun promptで指定する。公開generator・hidden課題・強い参照実装は渡さない。
物理runtimeは旧動的課題と同一。transportは別時間診断の90秒版を使い、RUNTIMEの記述も90秒へ合わせる。
5秒の各応答上限は同じ。公開checkの1 CPU / 2 GiB共有と外部policyの1 CPU / 256 MiBは区別する。
今回の外部一致検査は公開smoke 1例ずつであり、難しい24例の品質比較ではない。

## 予算の意味と未完了の境界

以下はこのadapterのcost capで、scopeは1 actor、ownerはprimary/integrator。
2400秒・80000 output tokensの関数defaultは旧solo予算を踏襲した候補値であり、新しいlive protocolの固定を代替しない。
CLI出力16 MiB、native homeとtmp各64 MiB、CPU1・memory2 GiB・PIDs256は既存actor境界を踏襲する。
不足が観測されたら理由と新しいsourceを固定して更新する。参加者数の推奨値ではない。

開発期限はbridge起動からCLI終端・停止まで。container準備と証拠回収・削除を含む外側時間も別に残す。
外側は開発予算+20秒で待受けを打ち切り、container削除へ15秒を確保する。
output token上限は**終了後の全参加者観測**であり、token単位の逐次打切りではない。
タイムアウトやusage欠落で全費用が取れなければ正式usageはnullのまま、観測できた部分を保存する。
強制killやhost障害でbridge結果が出ない場合も、削除結果を残してwithholdにする。

live比較前に残っている作業は、有限な開始台帳・条件別prompt・全予算・source一致preflightの固定と、
許す同時子/孫/compactionの観測検査。actorのauth引数が存在するだけでlive比較へ進めない。
旧保留soloを新条件の対照に流用せず、fresh soloとadaptiveを新しいprotocolで開始する。
協働の効果、安定性、費用効率はまだ未測定。

```bash
NATIVE_ACTOR_DOCKER=1 PYTHONDONTWRITEBYTECODE=1 python3 -m unittest scripts/test-native-development-actor.py
```

検証原記録を保持する場合は`NATIVE_ACTOR_EVIDENCE`へ未使用のdirectory pathを指定する。
