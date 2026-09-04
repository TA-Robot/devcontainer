# 開発ハーネスの現行計画

更新: 2026-09-05。ユーザーが承認した目的は、このdevcontainer上で実開発を効率よく進められる環境を作り、定量評価と改良を繰り返すこと。Evidence Forge／ForgeRoom製品の完成は目的から外す。過去の[レビュー](project-review-2026-09-05.md)は履歴として保存する。

## 方針

実際に必要な保守・開発作業を進め、その過程の足止めを解消する。品質を落として時間だけを短縮しない。native agent、既存のGit・job管理、有限実行を活用し、独自の対話製品や総当たりbenchmarkを先に作らない。使わない評価器は修復を必須にしない。

## 最初のサイクル

計画・現状評価・改良候補の比較・実装・実際の開発試行・再評価・採否までを実施する。詳細と事前の測定条件は[cycle-001](../experiments/development-harness/cycle-001/protocol.md)。

1. 実際の標準imageで必須checkとcheckout側コードの検証経路を確認する。
2. 同じimmutable sourceと同じ開発taskを、初期環境で実際のCodexに実行させる。
3. 観測された環境起因の阻害要因を修正し、対象の回帰・plain/frozen imageを検証する。
4. 同じtask・model・effort・権限で改良後を実行する。candidateの自己申告に依存せず、外側で成果と実行記録を検証する。
5. 正しさ、必須check完遂、時間、usage、復旧作業、scope逸脱を報告し、採用・棄却・不確定を判断する。
6. 実用的なcandidate修正をprimaryがreview/integrateし、次の問いを残す。

## 現状評価で見つかった優先事項

- 標準imageはPython 3.10だが、必須template validatorがPython 3.11の`tomllib`を無条件importし起動できない。
- checkout側`scripts/agentctl`が、隣の編集対象libraryよりinstalled libraryを優先する。テスト対象が編集したコードと一致しない可能性がある。
- supervisorのlog縮小と保持metadataのpublicationに時間差があり、現行testは後者を待たず失敗する。

最初に予定していた「testの待合せ修正」より、環境と検証対象の一致を優先する。これは今回実測した問題に基づく計画変更である。

## 判断基準

意味的品質とユーザー変更の保持はhard guard。時間・usageは品質を満たしたrun同士で比較する。timeout、未実行、モデルによる自己申告、外側の実測を区別する。少数runの差を一般的な開発効率や全modelの推奨値に拡張しない。

source/import、依存の互換性、非同期publicationのような決定的な不具合は局所再現で採否を決められる。開発時間の差は探索的な観測であり、必要なら別taskの反復を次cycleにする。悪い結果が出た場合も計画を修正して進め、成功結果が出るまで無制限にrunを追加しない。

## Cycle 001で得た判断

計画・現状評価・改良・実試行・再評価・成果の取り込みを完了。取り込み後の固定依存コンテナで121/121 test、通常／固定依存buildと起動hookの確認が成功した。

実際の保守taskを同じmodel・CLI・権限で実行し、外部の意味的評価は改良前後とも33/33。所要時間は379.449秒から235.089秒へ短縮した。この1組の約38%差は探索的な観測値であり、一般的な速度改善や投資回収の証明にはしない。詳細・失敗履歴・最終検証は[結果報告](agents/development-harness-cycle-001.md)と[機械可読結果](../experiments/development-harness/cycle-001/result.json)を正本とする。

採用するのは、checkoutと実行コードの一致、同梱Pythonで動くvalidator、選択modelに対応するCLI、実際のmount元や非同期完了を確認するtest修正。実作業で生成した非有限JSON数値の拒否処理もreviewして取り込む。これらの決定的な不具合の再現・修復が採用根拠であり、速度差だけで採用しない。

次cycleは別の実際に必要な開発taskで、複数componentをまたぐ変更を扱う。今回の修正をbaselineとして固定し、探索・検証・統合のどこに無駄が残るかから次の介入を選ぶ。一般的な速度効果を問う段階では複数task・複数run・実行順の交替を事前に定める。既存testの起動・時間依存の不安定さは残件として追跡し、成功runだけで信頼性を判断しない。

## 後順位

ForgeRoom、G3難化、全面的なtelemetry、atlas routing、定期agent、強いLane I、新しい汎用frameworkは、実際の開発に必要な不足が確認されてから再検討する。現在のtrust境界とunknownの扱いは維持する。既存の未追跡実験・raw証跡は削除・一括公開しない。

更新責任はprimary/integrator。ユーザーへ日報や形式的な再承認を要求せず、結果が次の優先順位を変えた時に説明する。
