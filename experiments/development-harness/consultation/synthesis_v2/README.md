# 証拠統合の別評価版: synthesis scope v2

2026-09-06。`consultation-synthesis-scope-v2`を実装し、provider-free校正39候補と
実Dockerを含む14テストを確認した（新規11＋旧pilot解釈の回帰3）。
**構造化された証拠統合を測る版として校正済み。一般的な設計品質を比較する主課題には未採用。**

旧F12-L revision 3の[live pilot](../synthesis-result.md)では、適切な否定表現と関連する
複数のunknownをhidden oracleが不当に拒んだ。その[再現](../../selection/audit_synthesis_false_negatives.py)を
踏まえ、旧oracleや得点を修正せず、新しい公開contractと評価器を作った。
旧pilotの10/12対10/12、品質判断の保留、常時事前相談を既定化しない判断は維持する。

## 変更と測定範囲

| 対象 | v2の判定 |
| --- | --- |
| 主張の適用範囲 | claimの`scope.population/workloads`を公開ルールで検査。文章中の禁止単語で判定しない |
| 未確認事項 | `topics`のrecovery/providerを網羅。各topicは複数件・重複可。recoveryの各項目には事故根拠が必要 |
| 根拠と出典 | 全evidence IDの実在、claimごとの最低限の根拠と出典、重複ID・欠落を検査 |
| 数値 | 元の系列から中央値、標本数、censored数、混合集計の除外を再計算 |
| 制約と参照 | bridge→target、意思決定の依存、対策・反証の根拠、matrixのgate参照を検査 |
| JSONとMarkdown | 公開rendererが全JSONをMarkdownへ展開し、scope/topicsを含めて一致を検査 |
| 境界 | 停止済みsnapshotの入力不変性・余分なpath・ファイル種類・サイズを検査。candidateのcodeやGit設定を実行しない |

必須fieldとルールは[公開課題](brief.md)・生成される`decision-contract.json`に開示する。
公開checkerと外部評価は同じ意味判定を使用し、外部評価だけがtrusted sourceとの照合も行う。
模範解答・校正候補・外部評価adapterは開発用bundleへ配布しない。
sourceの独立性は保つが、意味判定が別実装の独立oracleであるとは主張しない。

**自由文の真偽・topic名と文章の意味の一致・gate/rollbackの実効性は測らない。**
正しい構造の横に誤った文章を書いた場合や、形だけの対策も通り得る。
この限界を示す候補を意図的に校正へ残した。8項目の合格を旧版の12点と換算・合算しない。
公開contractからの機械的な組立てが可能な範囲を越えた能力や、相談の有用性は実証していない。

## 校正結果と採否

[calibration.json](calibration.json)は候補ごとの期待判定、実判定、失敗項目、source SHA-256を保持する。
[validation.json](validation.json)は検証command、実Docker image IDと旧結果の不変性を保持する。

| 校正集合 | 件数 | 確認 |
| --- | ---: | --- |
| 正解・別target・否定・日本語・追加/重複topic・並び替え・別ID | 10 | 全件受理 |
| 構造化した過剰一般化、根拠/出典/topic欠落、未知の根拠、虚偽の既知化、数値/型/制約/版の誤り | 27 | 全件を所定の検査で拒否 |
| 文章だけの過剰一般化、無効な運用手順 | 2 | 受理される限界を確認。改善成功には数えない |

新規11テストには、全39候補の公開/外部判定一致、旧artifact拒否、Markdownへの全field反映、
不正JSON・非有限数・symlink/FIFO・入力改変・評価中の変更、実Docker校正を含む。
Dockerはnetworkなし、read-only rootfs/repository、tmpfsと一時結果dirのみ書込み可、認証mountなし。
固有名の所有containerを`finally`で削除し、終了を確認する。live provider呼出しは0。

校正成功が許可するのは、同じ版の構造化assemblyを検査すること。
`general_quality_comparison_eligible: false`は維持し、旧集計guardも解除しない。
v2で実モデルを再比較していない。旧task adapter/runner/protocolの差替えや既存runの再開もしていない。

## 再現

repository rootから実行する。出力先は未作成のpathを使う。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 experiments/development-harness/consultation/synthesis_v2/synthesis_case.py \
  create --workspace /tmp/new-synthesis-v2-workspace
PYTHONDONTWRITEBYTECODE=1 python3 experiments/development-harness/consultation/synthesis_v2/calibrate_synthesis.py \
  --output /tmp/new-synthesis-v2-calibration.json
PYTHONDONTWRITEBYTECODE=1 SYNTHESIS_SCOPE_IMAGE=sha256:c7f904a12d7e7c63a2c7e46bc6654c8304b497a2836ecb08fb5bea0118f679ea \
  python3 -m unittest scripts/test-synthesis-scope-v2.py scripts/test-synthesis-pilot-report.py
```

新しい実験のtask identityはcase IDと校正対象の全source SHAの組。
継承元`f12.py`も含む。変更時は新しい校正とrun sealが必要で、旧artifactにscope/topicsを
推測して補完する移行は提供しない。privateな別target校正解では、新たに必須にしたgate参照を
明示的に整えた。これは旧runの変換ではない。

## 上限と次の到達条件

| 設定 | 分類・scope・根拠・見直し条件 |
| --- | --- |
| file 262144 bytes、collection 128項目 | このfixtureのcost cap。提示資料と必要な複数unknownを収容し、不正な巨大入力を制限。正当な成果が収まらなければ次版で再校正 |
| phases/unknowns各2件以上 | この公開課題のhard guard。段階移行と複数の未確認事項を要求する。運用defaultではない |
| scope、unknown状態、版・入力不変性 | この評価のhard guard。根拠を越えた構造化主張と異なる課題の混入を拒否。測定対象が変われば別版 |
| Docker create/start/cleanup 30/60/30秒、public tool test 10秒 | provider-free検証のcost cap。有限の静的検査と回収の上限。環境由来の不足が再現した場合に再設定 |
| 校正39候補 | 今回のcoverage集合。人数・本数の運用defaultではない。未検出の欠陥や正当な別解を発見したら追加し再校正 |
| 一般品質比較への採用false | admissionのhard guard。文章・運用効果が未測定のため。実動作による別の確認課題で識別力が成立するまで解除しない |

ownerは全てprimary/integrator。
次は既存候補F04-Lの再起動を含む実装評価について、正当な別実装と欠陥を区別できるか、
既知の天井がどの問いを制限するかを監査する（M1のplanning prior）。
そこから相談・review・複数実装比較の確認課題と固定予算を選ぶ。
同じF12の文章評価を拡張し続けることや、v2校正から自動的にlive本数を増やすことは次の条件にしない。
