# 開発ハーネスの現行計画

更新: 2026-09-06、Cycle 005の実比較・評価・統合完了を反映。
目的は、**実開発で使える成果の品質を上げ、そこへ到達する総時間と費用を減らすこと**。
小規模と大規模、速度と品質を別々に評価する。比較の実行・停止・検査・集計に人の採点を挟まない。

## 実施済みの題材・比較と現在地

**題材選定と実モデルによる比較は既に実施している。** 現在のP0〜P4はCycle 004後の
次サイクル準備であり、プロジェクト全体を未実施へ戻した番号ではない。

| 実施済みcycle | 題材 | 到達点 |
| --- | --- | --- |
| [001](agents/development-harness-cycle-001.md) | 共有JSON検証の非有限数拒否 | 両条件を実行・評価、成果を統合。33/33同士、379秒→235秒は1組の観測 |
| [002](agents/development-harness-cycle-002.md) | template導入・更新・復旧の3段階と、supervisor設定検証 | 両規模で比較・評価・統合まで実施。この比較では高速化を確認しなかった |
| [003](agents/development-harness-cycle-003.md) | JSONログの伏せ字と、独立acceptance実行・証拠保存・中断復旧の3段階 | 両規模で比較・評価・統合まで実施。予算超過・評価器の限界・統合修正を別記録 |
| [004](../experiments/development-harness/cycle-004/README.md) | 共有JSONローダーの重複キー拒否 | 比較を実施。改良側が途中中断し、保全成果を評価して修正を統合。最終速度比は未成立 |
| [005](../experiments/development-harness/cycle-005/result.md) | CLI同期の失敗保全・再試行 | 新方式のA/B、固定13項目、追加レビュー、統合・実image確認まで完了。互換性を根拠にBを採用し、自動feedbackの高速化は未確認 |

004の中断と計時不備を受け、P0で測定を修理し、P1で「同じ公開checkを使う自己検証と
自動feedback」の新しい比較方式を用意し、Cycle 005で最初のlive比較を完了した。
004後に用意した履歴表示の3段階案も存在するが、評価器・予算は未固定で保留中。
CLI同期は追加した次サイクルの題材であり、以前選定・比較した題材の代わりではない。

## 現在の採否と残る評価

**Cycle 005は完了。CLI同期の失敗保全を採用し、自動feedbackの通常既定化は見送る。**
[固定した要求・評価・予算](../experiments/development-harness/cycle-005/protocol.md)に従う。
両側が固定13/13・予算内で提出。Aは587.194秒、Bは780.894秒で、Bの追加修正は発動しなかった。
追加レビューでAのsymlink互換性の不足を再現し、Bのruntimeを採用した。過去の得点は変更しない。
外部projectのパスや追加要求の提出は開始条件にしない。改善候補の選定はこちらで進める。
[題材選定時の再現結果](../experiments/development-harness/selection/cli-sync-candidate.md)を参照。
第一候補のagentctl依存job経路は、[不足監査](../experiments/development-harness/selection/README.md)で
中核が既存CLIの合成で成立したため棄却した。次に再現したCLI同期を小規模の限定課題として先に評価した。
P2の両規模の固定は未完了で、新方式の大規模効果は未測定のまま保持する。
途中freezeを使わない[測定経路v2](../experiments/development-harness/terminal/README.md)は実装し、
実Dockerを含む新版27テストと旧ハーネス42テストで確認した。Cycle 005開始前には新課題・adapterを含む96テストが合格した。
[公開検証と修正の実行contract](../experiments/development-harness/feedback/README.md)も実装し、
同じ公開情報・実行環境と、検査・修正費を含む累積予算を疑似providerで確認した。
今回は実際に再現した起動時同期を先に扱った。段階数を増やして大規模と呼ばず、過去の大規模比較も保持する。

綿密な案比較、測定contract、課題候補、実行枠、自己批判は
[再計画の詳細](agents/development-harness-next-plan.md)。
評価上の共通ルールは[規模別評価方針](agents/development-harness-evaluation.md)。
P0の実装範囲と制約は上記の測定経路、検証記録は[validation.json](../experiments/development-harness/terminal/validation.json)。
P1の検証証跡は[feedback/validation.json](../experiments/development-harness/feedback/validation.json)。
P2でCycle 005の限定課題・13項目の評価・全開発上限・実行順を固定した。
新方式の大規模側の課題固定は未完了で、今回の結果をその代わりにはしない。

## 方針を変える根拠

- Cycle 004では、準備に計956.559秒、統合後の回帰と順次配布確認だけで計1,143.130秒を要した。
  並行した全作業の合計や、開発モデルの所要時間を意味しない。共通資産の再利用と総時間の計測を優先する。
- 定期checkpointが実行中のcontainer全体を止め、その再開で比較が中断した。
  timeout延長を主策にせず、正常提出・上限停止・段階境界で回収する方式へ移る。
- 必要な検証が起動しない条件は既に再現済み。次の比較ではA/B両方が検証できる土台を用意する。
  通常利用者の権限を自動で広げることとは分ける。
- 履歴表示の段階追加だけでは大規模側を代表できない。実際の状態・依存・復旧をまたぐ変更を先に選ぶ。

原結果と検証証跡は[Cycle 004](../experiments/development-harness/cycle-004/README.md)。
既存のclock、得点、budget超過、中断・欠測の記録は書き換えない。

## 実装・比較の順序

| 順位 | 成果物 | そこまでで止める条件 |
| --- | --- | --- |
| P0（完了） | 新しい時計、終端での回収、一括入口から中断後の停止・保全・採点までの接続 | 正常終了・遅い停止・打ち切り・recorder喪失・停止未確認・archive/評価器異常の機械試験と実Dockerの疑似実行が合格 |
| P1（完了） | 同じ公開checkを使う強いsolo Aと、自動feedback Bの実行contract | 同一環境・段階公開・有限修正・未知usage時の停止・実Codex sandboxを疑似providerで確認。課題別の最終check表はP2でseal |
| P2（小規模完了） | CLI同期の公開要求・13項目の評価・上限・順序を固定。大規模側は未固定 | 実需要・依存・退行・評価器の識別能力から規模を決める。外部project指定待ちにはしない |
| P3（小規模完了） | Cycle 005のA/Bと全条件の自動報告を完了。新方式の大規模側は未実施 | 小規模の結果を大規模効果へ代用しない。判断を変えない追加runを行わない |
| P4（Cycle 005完了） | 同期runtimeは互換性を根拠にBを採用。feedback既定化は見送り | 追加修正が発動していない1組から、自動feedbackの因果効果や一般推奨を導かない |

P0で高頻度snapshot、filesystemサービス、新しい常駐schedulerを作らない。
既存のarchive、observer、`finalize_interrupted.py`、所有権の確認を再利用する。
停止を確認できないときは構造化した未確認結果で閉じ、評価や後続起動へ進まない。

大規模側の第一候補だった、依存jobの独立検証・中断復旧・収集経路は新しい11項目の監査で再現した。
中核のCLI合成、旧状態の読込、明示的復旧は既存機能で成立する。
検証確定後の再検査失敗が後続dispatchを阻止しない不足も再現したが、それだけで大規模変更とはしない。
この基盤のホストCLI同期で再現した部分更新は、失敗保全・再試行・既存環境との互換を確認して修正した。
大規模に該当するかは結合した実要求から判定し、未成立なら大規模効果は未測定とする。
規模を作るための機能追加や、外部案件の提出待ちを設けない。
自動merge/push・破壊的GCは対象に含めず、single-writerの引継ぎを保つ。

## 測る結果

- **速度:** 同じ品質条件を満たした提出の時間と到達率。停止・回収の遅延を分離する。
- **品質:** 同じ上限と公開要求で得た成果の要求別の成績、退行、データ保全、互換性。
  停止が遅れた成果を予算時刻ちょうどの成果に見せない。
- **総費用:** 準備、開発中の検証・修正、外部評価、配布までの実経過時間とusage。
  検査を外へ移しただけの見かけの高速化を避ける。
- **不確実性:** 規模ごとの少数例、取得時刻のずれ、中断、usage欠測、未測定の品質を明記する。

当初の探索案は、両規模A/Bの計4開発run。仮置きは小規模20分・大規模累積120分／条件で、
開発だけの最大枠が計4時間40分。**全作業の完了予測でも、現在の実行予約でもない。**
分類はこの系列のcost cap、根拠は既存の開発・検証量、ownerはprimary/integrator。
Cycle 005では小規模1組の上限を固定して実施した。未実施の大規模側の予約・評価器・全上限は未固定。
課題や能力に合わなければ開始前に理由付きで変更し、結果を見た後の延長・成功runへの差し替えはしない。

## 維持するものと履歴

native-first、既存のGit/job所有権、有限実行、独立した受入検査、unknown保持を維持する。
既存の正常なtoolchain/image/cacheと検証済みの修正を共通土台にする。
ForgeRoom製品化、atlas routing、汎用telemetry、多人数・複数modelの総当たりは今回の経路から外す。

[Cycle 004までの計画履歴](project-plan-history-through-cycle-004.md)、
[最初のproject review](project-review-2026-09-05.md)、各cycleの固定protocol・原記録を保持する。
現行の優先順位はこのfile、選択理由と停止規則は[詳細](agents/development-harness-next-plan.md)が正本。
更新責任はprimary/integrator。ユーザーへ採点、日報、形式的な再承認を要求しない。
