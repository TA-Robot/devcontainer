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

## 後順位

ForgeRoom、G3難化、全面的なtelemetry、atlas routing、定期agent、強いLane I、新しい汎用frameworkは、実際の開発に必要な不足が確認されてから再検討する。現在のtrust境界とunknownの扱いは維持する。既存の未追跡実験・raw証跡は削除・一括公開しない。

更新責任はprimary/integrator。ユーザーへ日報や形式的な再承認を要求せず、結果が次の優先順位を変えた時に説明する。
