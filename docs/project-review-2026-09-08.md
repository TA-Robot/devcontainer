# 開発・評価・計画のレビューと修正

2026-09-08。対象は直近の静的scheduling H1/H2、動的課題の初回校正、主計画と利用案内。
全リポジトリの全機能を再認証したレビューではない。実モデルの追加実行は行っていない。

## 維持する結論

静的H2はgpt-6-astra/highの独立した単独開発2回が全参照水準へ到達している。
これを失敗へ変更したり、成功runを除外したりしない。単独の自己検証・複数案を許した点は適切だった。
動的課題も、評価側が状態・時計・資源・得点を持つ境界と、4方式の品質差は維持する。
いずれも協働の効果を測った結果ではない。今回のモデル切替を、過去runのmodel変更として記録しない。

## 修正した問題

### 1. 校正失敗が終端にならず、空の記録から回収成功を出す

旧`calibrate.py`の`Popen`を起動失敗に置換すると、保存結果は`status=running`、`modes={}`、
`all_recorded_containers_removed=true`になった。実行が終了していることと、何を確認したかを表せていなかった。
子processを強制停止した場合も、その停止自体をpolicy container回収の証拠にはできない。

[別版controller](../experiments/development-harness/scheduling/dynamic_v1/calibrate_v2.py)で、開始試行を起動前に記録し、
起動失敗・timeout・欠測・不正なcoverageを`withhold`で終端保存する。
回収不明を`unknown`のまま残し、空集合から成功を推定しない。CLIも未完了で非zero終了する。
旧controllerは過去のsource identity用に保持し、新しい実行入口から外した。

強制停止後のcontainer回収を完全に自動保証する仕組みは追加していない。
その場合は成功を保留し、独立した回収が必要。今回確認した正常実行の回収とは区別する。

### 2. 計画hashと実行sourceの結合が不十分

旧controllerは計画時にhashを保存した後も、各方式ごとにcheckoutのreferenceを読み直し、
checkoutの評価器を起動した。計画後の編集で異なるsourceが混ざり得た。

別版では実行開始時に評価器・runtime・transport・生成器・参照・契約を一つの専用snapshotへコピーする。
入力もその生成器から作り、全方式が同じsnapshotを使う。各方式の前後にhashを確認し、
提出物・入力・評価器seal、全24件のID・測定・回収を照合する。
途中で元checkoutのreferenceを書き換える回帰試験でも、全方式が元のsnapshotを使うことを確認した。

### 3. 資源不足を、AIが回復できる品質差と混同する余地

新しい[必要条件の監査](../experiments/development-harness/scheduling/dynamic_v1/audit_bounds.py)は、
実処理時間を使い、最速の互換worker、setupなし等の楽観条件で処理時間の下限を求める。
依存する共通仕事は一度だけ数え、worker停止分を除いた供給と共有memoryの供給に照合する。
個別jobの最早完了がdeadlineを超える場合も検出する。candidate codeは実行しない。

全24例で、個別の最早完了だけから期限内完了が不可能な仕事はなかった。
しかし重い負荷の8例中4例（scarce/mixedの各2例）は、全仕事を終える最低限の資源すら足りなかった。
したがって「100%からの差」全体を能力拡張の余地にはできない。
最重要classだけでは今回の必要条件に違反しなかったが、共同での実行可能性・online達成可能性は未証明。
将来情報を使うこの診断を、actorへの情報や新しい必達得点にしない。旧得点も変更しない。

### 4. 強い参照づくりが、次の準備の終点になりかけていた

課題を動的に広げた方向は妥当だが、次に「より強い非agent参照の完成」を必須化すると、
また準備だけを続ける経路へ戻る。4方式の差は課題を解くAIの限界ではない。

主計画を、現在の動的課題を実際の開発へ接続し、有限なstrong-soloの品質プロファイルを測る順へ修正した。
既存4方式と必要条件の診断は基準として維持する。高い絶対SLAを裏付けられない段階では、
事前固定した品質vectorの探索として扱い、恣意的な満点を導入しない。
参照追加は、観測した不足を解釈するために必要な場合へ限定する。
難題で協働が単独を越え、ハーネス改善へ戻すという主目的は変更していない。

### 5. CLI同期のトラブルシュートがchannel条件を省略

READMEの手順はinitialize→再起動を案内する一方、stableや同期無効時にも同期するように読めた。
実装はその場合host probe/syncを行わない。stableのversion差は正常であり、手順はedgeで同期が有効な場合だと明記した。
コンテナ定義・同期実装・認証設定は変更していない。

## 検証の範囲

新規回帰試験は起動失敗、timeout、強制停止、元sourceの変更、欠けた/重複したcase、seal不一致、
必要条件の反例、共有依存と停止容量を扱う。動的runtimeの既存10試験も実Dockerを含め、計18試験・skip 0が成功した（4.079秒）。
新controllerの全96実行を新しいpathで検証した（404.373秒）。旧校正と全caseの得点・完了時刻・traceが一致し、
96個の所有containerが実状態でも残っていないことを確認した。旧静的H2と旧動的校正のsource hashも一致した。
実測記録は[レビュー検証結果](../experiments/development-harness/scheduling/dynamic_v1/review-validation.json)、
必要条件の診断は[全24例の監査](../experiments/development-harness/scheduling/dynamic_v1/bounds-audit.json)へ保存した。

残る主作業は、動的課題の公開開発tool・情報境界を実CLIへ接続し、品質vectorと全予算を固定して行うsolo探索。
今回の修正・再校正を、難題での協働効果やプロジェクト目的の達成とは呼ばない。
