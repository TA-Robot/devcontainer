# 人の採点を挟まない開発比較

比較するのは同じ課題を同じ初期コードから実行した対照／改良の成果。
小規模修正と、前の実装に追加要求を重ねる複数段階の開発を別々に扱う。
暦の週数、常駐agent、人による採点を比較の成立条件にしない。

```mermaid
flowchart LR
  A[課題・コード・予算・テストを固定] --> B[対照を自動実行]
  B --> C[改良を自動実行]
  C --> D[各時点の成果を自動テスト]
  D --> E[品質・時間・消費・未完了をJSON出力]
```

`compare.py run` は事前に固定した順で両条件の全段階を実行する。
各段階の公開、次段階の開始判定、停止、成果の展開、独立containerでの検証、集計まで
コードで決める。人や別のAIが結果を見て合格へ変更する処理はない。
追加のagentを使わず、開発側へ評価器や途中の評価結果を渡さない。

## 出力する判断

- **品質**: 事前に固定した要求テストごとの合格・不合格・未確認。
- **時間**: 累積開発時間と同じ観測時点の品質。公開済み要求が違う場合は共通部分だけ比較。
- **消費と完了**: output tokens、使用量の欠測、予算内提出、品質と予算の両方を満たしたか。
- **速度比**: 両条件が全段階の品質と観測予算を満たした場合だけ提出時間の比を計算。

終了値0やモデルの完成宣言だけで合格にしない。検査結果の欠落・重複・改変・評価器の
異常終了・timeoutは未確認にする。前の段階が合格でも、未完成の全課題を合格にしない。
後続要求の未確認を、以前の共通要求へ混ぜない。完成成果を後の時点へ持ち越しても
待機時間を足さない。checkpointが欠けた途中経過は推測しない。

自動判定の対象は列挙した実行可能な要求。配布build、実利用、あらゆる品質まで合格した
ことにはせず、`release_accepted`はunknownのまま。必要な追加性質は**次の比較の前に**
自動テストとして校正・固定する。既に観測した結果の基準を後から変更しない。

## 一度の比較を実行する

まず専用container、同じ初期sourceのclean checkout、候補に見せないevidence directoryを
両条件について準備し、[開始判定入口](../continuation/README.md)で初期化する。
実モデル用環境は開始前にbuild/testが実行できることを確認し、必要な起動処理を
containerに備える。この比較コマンドは新しい環境や権限を自動作成するものではない。

設定JSONは次を持つ:

| field | 内容 |
| --- | --- |
| `schema_version` | `1` |
| `mode` | 新しい比較は `prospective`。既存成果の校正は `retrospective` |
| `task` | `redaction-v2` または `acceptance-v2` |
| `conditions` | 実行順の配列。`id: control/improved` と各初期化済み `state` directory |
| `image` | 外部評価containerの固定 `sha256:…` image ID |
| `legacy` | acceptanceの旧jobを作る固定source。redactionではnull |
| `include_checkpoints` | 全checkpointを評価するかを開始前に固定 |
| `observer_seconds` | 観測1回の秒数cost cap |
| `observer_slots` | 外部観測の同時実行数。ローカルresource cost capとして1または2 |
| `intervention_fields` | 異なってよいmanifest項目。通常は `command_network_access` のみ |

予算のscope・rationale・owner・update_whenも設定に記録する。数値を成果点にしない。
source bytes/mode、初期image、課題、上限が介入以外で異なる設定は拒否する。
新規比較では初期Git HEADも一致させる。retrospectiveでは旧runの異なる初期commitを
記録しつつ、source bytes/modeの一致を必須にする。新規比較の証拠とは扱わない。

```bash
python3 experiments/development-harness/automatic/compare.py seal \
  --config /private/pair.json --output /private/new-comparison
python3 experiments/development-harness/automatic/compare.py run \
  --output /private/new-comparison
```

この2操作の間で評価器やrunnerを変えると拒否する。seal時にコードhash、manifest hash、
初期source、テスト一覧を保存する。runは一度だけで、失敗した開発stageを再試行しない。
予算不足や不明usageでも停止して、得られた成果を評価する。状態の再初期化や
成功するまでのrun追加はしない。開発両条件を停止してから外部評価を始める。

結果は `comparison.json`、個別の生の観測は `observations/`、候補とは分離した復元sourceは
`artifacts/` に置く。元のarchiveはhashを検証して保持し、外部exportのPython bytecodeだけ
除去し、同じ固定imageのPythonでruntimeの検証付きbytecodeを作り直してからsourceを実行する。
元の成果や過去のexportは変更しない。archiveのpath escapeや特殊permissionを拒否する。
評価containerはnetworkなし・root filesystem読み取り専用で、認証情報を渡さない。
外部観測は開発の時間へ足さず、各 `observer_seconds` を別に記録する。

既存成果の再評価は `retrospective` でsealし、`evaluate` を使う。
このmodeは開発者を起動できず、元のstateと固定評価結果も変更しない。

## 今回の校正

`redaction-v2` は従来の19件に巨大整数とUTF-8出力の2件を追加した21件。
`acceptance-v2` は従来の41件を基に、Gitの内容を変えない更新、検証中GC、
SQL確定時の中断の3件を加えた44件。強制終了後の復旧手順は、CLIが公開する
`--recover-incomplete` の有無から事前固定した規則で選ぶ。失敗後に成功する方を試さない。

これらは前回の発見から作った**新版の校正**で、未見課題の品質改善の証明ではない。
旧版の19/41件の結果はそのまま残す。
[自動再評価と検証結果](validation.json)に、両規模の成果・checkpointの自動判定、
故障を入れた成果の検出、実Dockerでの実行から採点までの確認を記録する。
読みやすい結果表は[小規模](small-comparison.md)と[複数段階](staged-comparison.md)。
保存済み36点を自動で再評価し、既知の不具合を検出した。修正済みの参照成果は
複数段階の44項目を満たした。

初回の校正では、archive由来のbytecodeを除いた反復CLI検査が120秒上限に達した。
未確認の記録と停止履歴を保存し、同じimageでsourceからcacheを作り直す手順と
300秒の観測上限を新たに固定して校正を完了した。新しいモデルrunは実行していない。
校正後の統合では移行用sourceのmountを第3段階だけに限定し、usageの各成分と
指定／観測model情報を出力へ追加した。元の観測や採点は変更していない。

```bash
AUTOMATIC_COMPARISON_IMAGE=sha256:検証済みimageのID \
  PYTHONDONTWRITEBYTECODE=1 python3 -m unittest scripts/test-automatic-development-comparison.py
```

この試験の開発者は疑似providerで、認証情報やモデル呼び出しを使わない。
image指定がなければDocker試験はskipとして明示する。
追加の依存はない。host Pythonには安全なartifact展開用の `tarfile.data_filter` が必要。
この入口を戻す場合はdirectoryと専用testを除去し、旧runnerが段階公開・外部評価・比較を
一括実行しないことを記録する。

採点済みJSONを読みやすい表にする場合は次を使う。判定の上書き機能はない。

```bash
python3 experiments/development-harness/automatic/report.py \
  --comparison /private/new-comparison/comparison.json --output /private/new-comparison/comparison.md
```
