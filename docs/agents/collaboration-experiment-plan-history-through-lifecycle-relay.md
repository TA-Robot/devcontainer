# 協働実験計画: 比較から何を改善するか

更新: 2026-09-07。状態: **方式比較の実測を案内へ戻し、同じ相談能力を持つ両条件で初回の実比較を完了。情報介入は独立確認候補、一般既定への採用は保留。**
[プロジェクト計画](../project-plan.md)のM1〜M5を具体化する。
既存実験を未実施へ戻さず、以下の新しい方式比較を過去runへ遡及しない。

## 実験の単位と二つの比較

一単位は「公開要求 → 調査・相談・実装・選択 → 統合 → 独立した受入評価」の開発episode。
worker単体の回答だけで、開発episode全体の良さを採点しない。

1. **方式の効果を調べる比較:** 条件として使い方を固定し、何が起きたかを調べる。
   相談、review、案収集、候補実装のどれが、どの課題条件で成果や費用を変えるか。
2. **ハーネス改良の効果を調べる比較:** 同じ協働能力を持つAIへ、改良前後の指示・証拠を渡す。
   AI自身による使い分け・途中の切替・統合まで含め、別課題で開発結果を比べる。

後者に強いsolo対照も加える場合、「単体からの差」と「既存の協働ハーネスからの差」を分ける。
情報を渡しただけで能力が増えた、方式を指定しただけで実際に使われた、とは扱わない。

## 方式別の比較表

方式は探索範囲。人数やroundの標準値ではない。最初の実行で全表を総当たりしない。

| 方式・期待する作用 | 対照と介入 | 自動評価する成果 | 結果から改める場所 |
| --- | --- | --- | --- |
| 相談: 別の観点・別contextから原因や反例を得る | 同じmakerが調査を続ける / 別agentの証拠付き助言を受けてmakerが続ける | 最終診断の再現性、誤診、修正の退行、利用可能までの時間 | 相談のtrigger、contextの範囲、求める反証・実験、助言の採否 |
| 独立review: makerの見落としを検査する | 固定成果をmakerが自己review・修正 / 別agentがreviewしmakerが修正 | 欠陥の再現と解消、誤検出、修正が作った退行、統合費 | checkpoint、review時点、独立性、証拠の形式、再検査 |
| 多方面の案収集: 異なる有効案を探索する | 単体で複数案を作り選ぶ / 異なる観点から独立案を集め同じ責任者が選ぶ | 選択後の制約充足・実行結果、無効案の採用、選択・統合費 | 観点の分け方、重複の扱い、選択基準、追加相談の停止 |
| 複数実装: 別の実装経路を試して選ぶ | 単体の逐次試作と検証 / 同じbaseから独立実装し選択・統合 | 採用成果の品質、退行、全候補の消費、公開基準による選択の失敗 | 比較可能な差の作り方、実装境界、選択と最終検査 |
| 分担・証拠交換: context分割や独立作業の重なりを使う | 単体で同じ複合要求を進める / 担当を分け、依存境界で証拠を交換し統合 | 結合後の要求充足、再開・仕様変更の退行、待ち・重複作業・統合費 | 分担境界、handoff、対話継続条件、single-writer integration |

相談とreviewを全部入りの一条件へ束ねない。最初は違いを識別できる介入にし、
効果が重なる・打ち消す可能性は後の組合せ比較で扱う。
固定方式の探索でも、助言が不要・受渡し失敗・候補が無効という結果を記録する。

## 既存題材の一次監査と次の確認

以下は公開contract、validity台帳、評価実装/文書を読んだ一次判断。
既存の校正は下記の4課題で再実行済みだが、方式比較に適格と確定したことを意味しない。
既存atlasの`eligible`はeffort-quality用途の判定であり、新しい協働比較の合格証ではない。

| 候補 | 使える観点と根拠 | 不足・採否を変える確認 |
| --- | --- | --- |
| F03-L-PYBASH-001 revision 1 | 再起動時のbarrier付き再現・残存状態・cleanupを検査する。[oracle設計](../../temp/multi-agent-duration-atlas/case-designs/f03-l-pybash-001/04-oracle-and-quality-rubric.md)、[実装](../../scripts/agent_duration_cases/f03.py) | **原因発見の相談比較へ現版をそのまま採用しない。** [公開capsule](../../experiments/multi-agent-duration/capsules/f03-l-crash-restart-diagnosis.md)が原因のevent順序と保証を明示している。再現手順の構築は測れる。相談で原因を発見できるかには別版が必要 |
| F02-M-PY-001 revision 1 | 独立reviewの部品候補。可視のコードから隔離上の欠陥と根拠を提出する。[実装](../../scripts/agent_duration_cases/f02.py) | 現contractはreview.jsonのみでsource修正を禁止。review品質は測れても修正後の開発品質は測れない。修正まで扱う場合は別revision/adapterが必要 |
| F12-L-MDJSON-001 revision 3 | 複数観点の案と統合候補。公開の制約と複数の有効な設計を許す。[実装](../../scripts/agent_duration_cases/f12.py)、[validity](../../experiments/multi-agent-duration/validity/effort-quality.json) | 既存proposalと限定された選択肢からの制約充足・証拠統合に限る。新しい案を広く発明する能力や実装後の有用性は未測定。独立案と統合後のartifactを別々に保持する必要 |
| F04-L-PYBASH-001 revision 1 | 実装・review後の修正候補。別processでの正常再実行を検査する。[実装](../../scripts/agent_duration_fixtures.py) | [9実装監査](../../experiments/development-harness/selection/f04-lifecycle-audit.md)で2つの妥当な実装を受理したが、直接上書き・引数再分割も旧4/4を通る。旧版のまま採用しない。過去9/10満点を要求全体の天井へ広げず、別版で観測範囲を固定 |
| G1/G2/G3 | 実協働の失敗・復旧・観測の回帰材料がある | G2の自己申告採点/状態所有権、G3の天井などは[監査](../project-review-2026-09-05.md)参照。協働が勝つ方向への難化はしない |
| Cycle 002/003の複数段階開発 | 状態引継ぎ、要求追加、復旧、統合というM5の候補資産 | 既存完成物を学習済みのagentへ同じ正解として出さない。新しい要求系列と固定評価が必要。大規模という名前だけで再採用しない |

最初の候補集合はplanning prior。範囲はM1の準備順、根拠は既存oracleと作用の対応、
ownerはprimary/integrator。一次監査により「F03-L現版をそのまま相談比較へ使う」案を棄却した。
その資産を使った別版を実装・校正したが、下記の非agent解法により主比較には採用しなかった。
F03-Lを通せるまで他方式の検討を止めたり、一方式の実行完了で全比較を完了扱いしたりしない。

### 今回実施したprovider-free校正

[記録と実行条件](collaboration-experiment-calibration-2026-09-06.json)。4課題を上限として
`--continue-on-failure`で実行し、4/4合格、110.622秒。live providerは呼んでいない。
全課題で初期成果の不合格、known-goodの合格、snapshotの再現性、宣言済みmutantの拒否を確認した。

| Case | 宣言済みの有効な別解 | 拒否を確認したmutant |
| --- | --- | --- |
| F02-M | 0 | 3 |
| F03-L | 0 | 4 |
| F04-L | 0 | 2 |
| F12-L revision 3 | 1 | 8 |

別解0は「他の正解がない」ではなく、今回の校正に別解が登録されていないという意味。
評価器の現contractでの動作を確認した結果であり、相談・review・案収集・複数実装の改善効果や、
複数writerの実Docker停止を検証した結果ではない。F03-Lの公開情報の問題も校正合格とは両立する。

## M1で作る最初のprotocol

### 実モデル比較まで進めた現在地

[固定protocol](../../experiments/development-harness/consultation/synthesis-protocol.md)で、
F12-L revision 3の事前相談→makerとsoloを一組実行した。
[原結果と採否](../../experiments/development-harness/consultation/synthesis-result.md):
元の固定得点は10/12同士。相談側の提出時間19.3%増、input44.8%増、output6.5%増。
ただし原失点に否定表現と関連unknownの個数制限による誤判定が作用しており、品質を揃えた速度比較は保留する。
校正用別表現の失敗を[集計gate](../../experiments/development-harness/consultation/synthesis_report.py)へ結び、得点を上書きせず改善率を抑止した。
[別評価版v2](../../experiments/development-harness/consultation/synthesis_v2/README.md)を実装し、
正当な別表現等10候補の受理、構造化scopeの一般化・根拠欠落等27候補の拒否を確認した。
自由文と無効な運用手順が依然通る2候補も残し、構造化assemblyという測定範囲を明示する。
実Dockerを含む14テストが合格。旧runは変換・再採点せず、品質解釈のguardも保持する。
F04-Lの動作監査では、原子的置換と引数保持の見逃しを再現し、別probeで識別できると確認した。
[queue別版](../../experiments/development-harness/queue_review/v1/README.md)でreview→修正を実装・校正し、
[固定2組の実比較](../../experiments/development-harness/queue_review/v1/result.md)を完了した。
欠陥ありと正しい初期実装の全条件が4/4。review付きの時間はそれぞれ1.842倍・2.893倍で、input/outputも増加。
正しい実装は両条件とも変更せず、品質の上積みは確認できなかった。常時reviewを不採用とし、
続いて[条件付き相談への情報介入](../../experiments/development-harness/queue_review/conditional_v1/result.md)を実装し、
両条件が同じsubmit/consult能力を持つ1組を、留保していたconfirmationで実行した。
情報ありは時間10.176%減/input13.615%減で事前基準を満たしたが、時間の余裕は約0.168秒で、両側とも相談せず4/4だった。
案内は独立確認候補に留め、相談起動の改善や一般的な優位性は主張しない。confirmationは今回でlive使用済み。
[3者の独立批判と採否](project-direction-review-2026-09-07.md)により、queueの順序反転確認は当面保留した。
統合判断への再批判で、複数実装を第一候補とする順位も取り下げた。
[通常配布入口への接続と利用確認](collaboration-evidence-delivery-2026-09-07.md)を完了した。性能改善の比較とは区別する。
[保存済みlifecycle成果の監査](../../experiments/development-harness/selection/lifecycle-reuse-audit-2026-09-07.md)では、
成果・評価の再利用可否と公開要求への誤読を確認し、同じ校正の再実行と新規の複数実装生成を保留した。
[保存候補の選択adapter](../../experiments/development-harness/selection/lifecycle_v1/README.md)のprovider-free経路を実装した。
採用条件とパス境界の2群について、候補別の分類・採用保留・校正referenceの選択と異常停止を専用imageで確認した。
10テスト合格。通常devcontainer内の完成実装の混入は独立reviewで発見し、固定したPythonのみのimageへ変更した。
integratedは校正専用で、独立候補として数えない。分類一致を根拠の意味や全品質へ読み替えない。
[固定relayの実比較](../../experiments/development-harness/selection/relay_v1/result.md)で、
agent側の情報境界・公開probe呼出し・全予算・停止を接続し、単独と事前助言の1組を完了した。
両条件4分類一致・採用保留。132.980秒対195.559秒で、相談側のinput/outputも約38%増えた。
固定事前相談を既定に追加しない。全7呼出しの消費・回収は確認済みで、このprotocolの追加runは行わない。
分類一致と自由文の根拠・全品質を区別し、配布案内の改良前後の再評価まで済んだとは扱わない。
以下の診断候補の準備履歴も保持し、既存資産や過去比較を未実施へ戻さない。

### 診断別版で実装・判断したこと

[consultation-crash-diagnosis-v1](../../experiments/development-harness/consultation/v1/README.md)で、
公開文からの原因開示を除き、再現計画を評価側が実行して状態を検査する方式を実装した。
旧atlasのF03-Lと過去の結果は維持。任意のregression.shの作成能力は新課題の測定範囲から外した。
正解・別表現・誤因果・虚偽状態・非再現計画など20校正候補の期待判定が一致し、実Dockerを含む11テストが合格。

しかし公開CLIだけで中断点を列挙する非agent解法が両variantで全項目に合格したため、
**相談で品質を上げる主課題には不採用**。実行・評価の校正、および不要な相談を評価する対照候補として残す。
校正結果は[記録](../../experiments/development-harness/consultation/v1/calibration.json)。live効果は未測定。

この小課題をM2の疑似providerによる受渡し・採点確認へ使い、実Dockerの正常系とadvisor停止を検証した。
F12-L revision 3の[反例監査](../../experiments/development-harness/selection/f12-synthesis-audit.md)も実施。
数値の誤りは検出したが、実効性のない対策・rollbackでも12/12となったため、数値・参照・明示制約の
組立てという限定された問いの候補にする。これはplanning priorで、ownerはprimary/integrator。
その範囲で相談の起動・context分割・根拠引継ぎの採否を変えられないなら採用しない。
単に難しい、課題が大きい、モデルが失敗した、という理由だけで選ばない。

### 診断候補で具体化したprotocol項目

以下は診断別版の準備に使った比較設計であり、現在のlive予約ではない。
主課題を変えるときは問い・成果・評価をその課題へ結び直して固定する。

- **問い:** 再起動障害の診断に別agentの独立調査を加えると、単体の追加調査より最終診断を改善できるか。
- **成果:** 同じ公開要求に対する最終診断と再現手順。提案された手順を外部で実行し、
  seeded failure、event順序、再起動後状態、安定性、所有範囲内のcleanupを確認する。
- **対照:** 自己調査・検証を自由に続けられるsolo。介入は証拠付き相談とmakerによる採否・最終化。
  makerを止めて相談するか並行するかも先に固定し、その待ち/重なりを計測する。
- **境界:** 同一source/task/公開情報。相談先にhidden oracleや模範解答を渡さない。
  makerの暫定説を渡すかは検査する独立性に応じて固定する。最終提出の責任はmaker。
- **事前校正:** known-good、妥当な別表現、誤因果、偶然に頼る再現、虚偽の成功、広域cleanupを識別する。
  協働ありの模範解答を良く作って比較優位の証拠にしない。
- **固定項目:** source/fixture/evaluator/harness版、model/effort/CLI、公開tool・権限、実行順、
  run数、参加者、各dispatchと全体の時間・usage方針、停止許容幅、評価費、保存上限、欠測・中断時の扱い。
- **確認へ進む条件:** 方式が実行でき、評価が成果差を識別し、全参加者の費用・停止を回収できる。
  予備比較の分散・費用を基に、検出したい最小改善と確認の精度・本数を事前固定する。

診断候補の人数・repeat・分数は未sealのまま主比較への採用を見送った。
今後再採用する場合は、必要な観点・実測した準備費・全体資源から実装側が固定する。

## M2の実装境界

[実装と検証記録](../../experiments/development-harness/consultation/README.md):
`flow_v1.py`でsoloと「advisor停止・保全→助言→新しいmaker→全停止→採点」を接続した。
直列の事前助言が対象で、primaryの途中相談・同一session再開・双方向対話は未対応。
この`flow_v1.py`自体は疑似provider用。別の[synthesis pilot接続](../../experiments/development-harness/consultation/synthesis-runtime.md)で
実Codex・model-free probe・環境比較・実promptのhash付きrelayを実装し、liveで確認した。元のterminalコードは変更していない。

[terminal](../../experiments/development-harness/terminal/README.md)の時計・停止・保全、
[feedback](../../experiments/development-harness/feedback/README.md)の共通公開check・累積予算、
既存のtask/result・agentctl所有権を再利用する。旧sealed runnerは変更して再開しない。
新方式は別versionのadapter/manifestから接続し、既存比較の意味を保つ。

必要な接続は、participantごとの有限dispatch、情報境界付きのartifact受渡し、
makerの継続、全writerの停止、全usage集計、最終artifactの外部評価。
content-free集計にはID・hash・時刻・状態を渡し、相談本文・sourceは既存のprivate artifact側で扱う。
採用したとagentが書いた情報と、自動検査で確認した成果変化を分け、分からない関係はunknownにする。

疑似providerでは、未発動、遅い助言、無効な候補、受渡し失敗、部分usage、worker残留、
統合失敗、評価器異常で成功を偽らないことを確認する。実Dockerで停止/保全境界も確認する。
現在の協働DAGのfake結果をlive atlas観測へ投入しない。汎用schedulerや全文対話基盤は前提にしない。

## 比較の公平性と読める範囲

同じ時間上限で何に届くかと、同じ総消費方針で何に届くかを分ける。
全参加者のinput/cache/output、待ち、公開検査、候補選択、統合、最終評価を記録する。
同じoutput capだけでは同費用にならない。in-turnの厳密上限が取れないなら超過区間を明示し、
同資源の主張を保留する。単体へ追加調査の機会を与えず、人数だけ増やした優位を方式固有の効果にしない。

最初はmodel/effort/tool条件を揃え、異種modelの価値は別の問いとして扱う。
順序は事前割付し、case・revision・環境を対応付ける。反復数はpilotの分散と判断の精度から決める。
成功runだけを集めず、未発動・失敗・中断・未着手を含めて報告する。

候補選択は開発側に見える基準だけで行う。hidden evaluatorで一番良かった候補を後から
採用したことにしない。選択済み成果と全候補の事後評価を分け、良い候補があったのに
選べなかった場合は選択手順の不足として記録する。混合実装は新しいartifactとして検証する。

## 結果を改善へ戻す記録

各比較の結論に次を結び付ける。新たな汎用schemaを作る前に既存result/protocolとsidecarで満たす。

| 記録 | 内容 |
| --- | --- |
| 問い・介入 | 方式、期待する作用、対象課題の条件、比較相手、変えた要因 |
| 根拠 | task/evaluator/harnessの版、run集合、全開始数、発動/欠測、品質・時間・全費用 |
| 言えること | その課題での観測、正/負/不明、適用できない条件、確認が必要な点 |
| ハーネス判断 | 採用/条件限定/棄却/保留、変更対象のfile/contract、理由、戻す条件 |
| 次の検証 | 未使用の確認課題、改良前後の比較、重大退行・許容費用・精度の基準 |

例として「reviewが増えたが欠陥解消が増えず、到着も遅かった」なら、
効果なしの観測を残し、早い時点への移動・対象限定・停止を次の比較候補にする。
原因が時点にあると確定したわけではないので、その変更の比較を省略しない。

AIへの提供情報は、方式の説明、起動候補となる状況、渡す/返すartifact、停止条件、
測定済みの効果と不確実性、失敗条件、出典を一緒にする。未測定にも使用例は提供できるが、
改善率は付けない。観測用atlasと、条件付きの使用判断を支えるplaybook/skillの役割を分ける。

## この計画の自己点検

- **実験設備を作り続けてしまう:** 最初の適格方式で一つの循環を閉じる。全方式対応engineの完成を待たない。
- **既存課題を捨てて再出発してしまう:** 上の候補と過去の失敗を再利用し、不足のある境界だけ版を分ける。
- **reviewだけへ縮む:** 相談・案収集・実装比較にも明示の問いと候補を置き、未実施を残す。
- **協働が勝つ課題を作る:** oracle校正と方式の勝敗を分離する。満点や費用増も有効な観測。
- **一般的な能力と呼びすぎる:** 自動検査が測れる性質に結論を限定し、別課題と継続開発で確認する。
- **配布しただけで終わる:** 改良後の情報をAIが使った開発結果まで確認し、効果がなければ既定化しない。

当面の完了は「実験が一回動いた」ではなく、結果に基づくハーネス判断と、その判断を確かめる
改良前後の比較まで。必要な追加実行が予算に見合わない場合は、未確認として保留する。
