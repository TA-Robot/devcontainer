# 保存済みlifecycle成果から次の比較を選ぶ

2026-09-07。[3者の再批判](../../../docs/agents/project-direction-review-2026-09-07.md)を受けた限定監査。
**保存済み成果と評価は再利用できる。既存校正の再実行と複数実装の新規生成は、次の必須作業にしない。**
[hash照合記録](lifecycle-reuse-audit-2026-09-07.json)。candidate codeは実行せず、過去の評価・得点を変更していない。

## 確認した資産

保存先は `/home/asakura/.local/state/devcontainer-evaluations/`。
Cycle 002のcontrol/improved最終sourceとintegrated-sourceのtree hash、および
Cycle 003の3つの保存評価のhashは[既存校正](../quality/calibration-2026-09-05.json)と一致した。
[要求別評価](../quality/lifecycle.py)と[共有評価](../multi-scale/large-01/evaluate.py)も校正時から不変。
3段階の公開要求は[phase 1](../multi-scale/large-01/phase-1.md)、[phase 2](../multi-scale/large-01/phase-2.md)、
[phase 3](../multi-scale/large-01/phase-3.md)。対象の題材はCycle 002のtemplate lifecycle。
Cycle 003の独立acceptance機能の開発とは別で、その全実装を再利用する話ではない。

| 確認した不足 | 公開根拠・source差 | 保存済みの外部判定 |
| --- | --- | --- |
| 既存file採用時に、内容・実行bitが同じでも非実行permissionの違いを拒否する | phase 2はsame bytes and executable modeを条件にする。controlはmodeの`0o111`を比較、improvedは通常permission全体を比較 | `private-mode-adoption`でcontrol/integrated合格、improved不合格。採用時の無変更、再採用no-op、更新後の0600保持も検査 |
| 両開発成果に共通するsource/target重複の見逃し | 別rootという要求と、root・二重slashを含むpathの照合 | control/improved不合格、integrated合格。単一項目で良かったcontrolも全要求の完成品とは限らない |

Gitへの管理data混入も既存校正で識別済みだが、これは後から明示した運用上の期待。
旧公開要求へ遡って追加した合格条件として使わない。
35/35という旧得点と、この別評価での要求別判定は併存する。

## 今回答えられた問いと採否

- **保存物を探し直したり評価器を直したりする必要があるか:** この範囲では不要。source・評価・校正は揃っている。
- **複数実装の生成比較を始める根拠があるか:** 保留。確認できた失敗は要求の解釈と受入検証の不足で、
  有効な実装案が足りなかったことは確認していない。integratedはcontrolから後で修正した成果であり、
  独立生成された第三候補ではない。3成果があることを3つの独立試行とは呼ばない。
- **新しく調べる対象があるか:** 公開の仕様・code・検証から、候補の要求違反を見つけて受入判断へ反映できるか。
  既存の判定結果はこの能力を測っていない。一方、同じ保存物を固定評価で再採点するだけでは新しい証拠は増えない。

## 限定実装に進める範囲

次の準備対象は、**保存済み候補の受入判断を記録するtask adapter**に限定する。
これは選択経路の校正であり、協働の効果比較や複数実装方式の採用ではない。
今回の監査はここで終了する。新しい候補生成・全方式runner・3段階全再演はこのadapterの前提にしない。

| 境界 | 具体化するもの |
| --- | --- |
| 入力 | 当時の公開要求と中立名へ写した候補source。元のcontrol/improved等の名前、得点、レビュー、Git履歴、統合経緯は開発側へ渡さない。integratedは校正専用に保持 |
| 公開検証 | CLIの実行・コード調査・独自checkを使える。採用判断に必要なpermission等の確認を禁止しない。固定外部評価と過去の判定は渡さない |
| 出力 | 候補ごとの受入可能/要修正/未確認、根拠の公開fileとcheck、選ぶ候補または採用保留。正しい候補がない時にも選択を強制しない |
| 外部判定 | 全員停止後、保存済みの候補identityと要求別判定に照合する。正しいcheck結果を引用しただけで全要求合格とはしない。最終選択をhidden結果でやり直さない |
| 時間・費用 | 候補の探索・公開検証・選択・受渡し・停止を含む全体を有限にする。値はadapterの実行能力を確認してからprotocolで固定し、過去の生成時間を今回の開発時間へ足さない |

[terminal runner](../terminal/runner.py)のmanifest・停止・snapshotと
[Codex transport](../consultation/codex_transport.py)はstage実行の再利用候補。
[queue binding](../queue_review/v1/pilot.py)はtask-specificなprobe・prompt・source制限・評価接続が必要なことを示す実装例であり、
そのまま新課題を実行できるとは扱わない。新adapterでは中立projection、公開checkの隔離実行、出力検証、
保存評価へのidentity照合を追加対象とする。旧runnerや既存runのmanifestは変更しない。

候補内のREADMEやtestに旧レビューや正解に相当する情報が含まれるか、受入判断に必要な公開情報が足りるかは、
projectionを実物として作る時に確認する。候補を安全に分離できない、公開情報では差を観測できない、
狭いadapterでは接続できない場合は保留に戻す。生成比較へ自動的に進まない。

## ハーネスへ戻す判断との関係

選択経路を動かせたこと自体には、協働の改善率を付けない。
その後に方式を比べる場合は、単体の受入点検を続ける条件と、別の観点の点検を受けて同じ責任者が判断する条件など、
実際に不足へ対応する介入を固定する。方式・本数・順序・全予算を今回の監査で固定したわけではない。

もし誤採用が減れば、その課題条件で要求と検証の対応を点検する手順が確認候補になる。
判断が同じで費用だけ増えれば自動追加を既定にしない。差が判定できなければ推奨を保留する。
いずれも強いsoloの自己検証を許し、同時間比較から独立性だけの効果を推定しない。
案内を変えた後は、結果を見た保存済み課題とは分けた系列で改良前後を実行して採否を決める。
配布・利用確認と、性能の再評価を同じ完了扱いにしない。
