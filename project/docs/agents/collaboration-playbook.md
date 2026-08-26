# Adaptive multi-agent collaboration playbook

このplaybookは、primary / managerが「複数agentを使うと何が改善し、どう関係づけ、いつ止めるか」を決めるための正本です。workspace、permission、process recoveryは`AGENTS.md`と`docs/agents/runbook.md`、individual write jobは`.agent/schemas/`を使います。

delegationやsubagent利用が上位instruction、tool、ユーザーによって許可されている場合だけ適用します。利用できない時は同じ分析枠組みをprimary一人のsequential reviewへ縮退し、独立性や並列性を得たとは主張しません。

## Start from the expected mechanism

人数や呼び出し回数より先に、soloに対して期待するmechanismを説明します。

- **latency overlap**: 独立workを重ね、critical pathを短くする。
- **context partitioning**: contextを狭く分け、制約とevidenceの密度を上げる。
- **coverage**: 異なるshard、観点、source、failure surfaceを探索する。
- **error decorrelation**: makerとfresh checkerの目的・情報・commitmentを分ける。
- **empirical selection**: candidate差をtestやmeasurementで識別する。
- **evidence-producing refinement**: critiqueにより新しいevidence、test、claim transitionを生む。
- **temporal sampling**: eventや時間をまたぐdriftを有限runで観測する。

「複数agentを使いたい」以外のmechanismを説明できない場合はsoloを選びます。同じpromptの複製、provider数、回答の多数一致はmechanismの成立を保証しません。

## Find the binding constraint

今回最初に尽きるものを確認します。

- briefを外へ渡すserialization cost
- primary / humanのreview・synthesis capacity
- wall-clockと待ち許容時間
- provider quota / rate window
- `agentctl` capacity、queue、shared resource
- integrationとrework cost
- context coupling
- evaluator availability
- late failure cost

たとえばreviewが律速なら、生成artifactを増やすより相談や独立検証の方が有益な場合があります。capacityは同時実行数とwaveの制約であり、価値ある参加者数の推奨値ではありません。

## Separate relation, lane, role, and lifecycle

| axis | question | examples |
|---|---|---|
| relation | agent同士をどう関係づけるか | `solo`、`delegate`、`consult`、`compete`、`verify` |
| role | 誰が何へ責任を持つか | researcher、implementer、reviewer、primary |
| lane | どのworkspace / permissionで走るか | read、write、isolated |
| lifecycle | いつ、どんなtriggerで起動するか | one-shot、bounded-exchange、event-triggered、scheduled |
| authority | 誰が判断とside effectを所有するか | primary、single writer、human owner |

relation名は説明を短くするaliasで、closed enumではありません。

- `solo`: primaryが直接処理し、coordination costを払わない。
- `delegate`: bounded artifactを渡す。fan-outやDAG handoffも含む。
- `consult`: option、assumption、critique、evidenceを集め、必要なら交換する。
- `compete`: 分岐したcandidateを同じ評価契約で比較する。
- `verify`: fixed artifactをneutralまたはadversarialに独立検査する。

旧来の`dispatch`、`panel`、`deliberation`、`variants`、`maker-checker`などはidea catalogや対応aliasとして使えます。pipelineはdependency graph、scheduled / event-triggeredはlifecycleであり、relationと同じ分類表へ混ぜません。

## Derive participants instead of choosing a count

- delegate: non-overlapping shard、stage、artifactから導く。
- consult: 固有のperspective、evidence source、failure modeから導く。
- compete: 実質的に異なるapproachと識別可能な評価から導く。
- verify: 独立させたいerror mode、probe、review surfaceから導く。

その後、capacity、quota、wall-clock、human review、integration costで実行可能な同時数とwaveを調整します。追加participantが固有の価値を説明できなければ増やしません。

## Prepare a collaboration brief

複数agentを開始する前に、`docs/agents/tickets/collaboration-plan.template.md`を埋めるか、同じ情報をtask planへ持ちます。

これはprimaryが通常のplanning中に生成・更新するagent-owned artifactです。ユーザーへformの記入やepisode logの保守を求めません。自動観測できないfieldは捏造せず`unknown`とします。

- required decision / artifactとdefinition of done
- expected mechanismとbinding constraint
- relation、lifecycle、参加者を導いた理由
- shared facts、perspective、independence policyとその理由
- artifact flow
- lane、permission、base SHA、workspace
- acceptance、comparison criteria、disconfirming evidence
- human review budget、capacity / quota / integrationへの影響
- parameterのrole、scope、rationale、invalidation evidence、update owner
- continuation / stop condition
- synthesis、integration、external side effect owner

各workerへtask全体を丸投げせず、担当scope、expected output、evidence requirement、stop conditionを渡します。

## Classify every parameter

数値やbooleanは次のどれかとして扱います。

| parameter role | purpose | treatment |
|---|---|---|
| `hard guard` | safety / authority invariant | 違反を拒否し、明示的な設計変更だけで更新 |
| `cost cap` | runawayやresource starvationの防止 | task / projectのcapacityとriskから設定 |
| `planning prior` | 過去の観測に基づく見積り | project-local evidenceで更新 |
| `hypothesis` | 未検証のstarting assumption | experimentで採用・修正・棄却 |

cost capを品質最適値、planning priorをtermination rule、provider既定値をcollaboration既定値として扱いません。各parameterへscope、rationale、無効化するevidence、更新ownerを付けます。

## Choose independence for the purpose

independenceやblindnessを無条件に適用しません。

| purpose / constraint | candidate policy |
|---|---|
| option enumerationでanchoringを避けたい、独立agentが使える | isolated-blind candidates |
| coverageを広げたい | context / source / failure surfaceをpartition |
| fixed proposalやdiffをreviewする | artifactを共有し、makerの試行軌跡やprimaryの選好を隠す |
| interfaceやfixtureの事実確認 | shared contextまたはbounded direct exchange |
| delegationが使えない | sequential reviewへ縮退し、独立性を主張しない |

provider diversityは品質の代理指標ではありません。generatorとevaluatorのどちらへ割り当てると価値があるかもprojectごとに観測します。

## Continue only while value changes

各interaction後、primaryは次を判断します。

- acceptanceまたはdecisive evidenceを得たか。
- new evidence、test、claim transition、useful artifactが増えたか。
- disagreementはmeasurementで解けるか。解けるなら会話より測定を優先する。
- disagreementがuser preference / authorityへ到達したか。
- scope、safety、cost capへ到達したか。
- 残る期待利益がcoordination、synthesis、review costを上回るか。

継続回数は結果として観測します。全文transcriptやprivate reasoningを連鎖させず、必要ならopen claim、evidence pointer、未解決questionだけを渡します。budget到達時はfalse successにせず、partial resultと次に必要なevidenceを返します。

primaryがbudget、authority、synthesisを所有します。provider-native peer messagingを使う場合も、topic、authority、cost cap、interrupt owner、result contractを先に固定します。winner、risk acceptance、permission escalationをpeer agreementへ委ねません。

## Keep exchange artifacts small

全文transcriptの代わりに、目的に応じた小さいartifactを渡します。必要なfieldだけを使い、形式自体を成果にしません。

相談・reviewの例:

```text
recommendation
evidence pointers
assumptions
alternatives considered
risks / unknowns
confidence and why
disconfirming test
```

継続するclaimの例:

```text
claim_id
status: proposed | supported | refuted | unresolved
new evidence or test result
what changed since the previous interaction
next measurement, authority decision, or stop reason
```

candidateは既存task / result contractを使い、approach差、acceptance evidence、既知risk、未完了事項を補足します。private reasoning、人格的debate、単なるagreement countは次へ渡しません。

## Compare candidates only when comparison can decide

`compete`を使う前に次を満たします。

- candidate間に意味のあるapproach差がある。
- common base、scope、acceptance、resource boundaryがある。
- correctness / safetyを先に判定できる。
- evaluatorが差を識別できる根拠またはpilotがある。
- human reviewを含むcomparison costが失敗 / rework costに見合う。

明らかな不合格は早く止め、全candidateをproduction品質まで仕上げることを目的にしません。rubricを結果確認後に変更せず、hybridは新しいartifactとして再検証します。held-out check、blinded evaluator、cross-provider evaluatorは有力な仮説ですが、global requirementではありません。

## Bound recurring work

定期・event駆動workは常駐agentではなく、毎回terminalになるfinite jobとして設計します。repository eventならevent-triggered、external driftや履歴集計ならscheduledを検討します。CI、deterministic script、通常cronで足りるならagent schedulerを作りません。

runtimeを実装する場合のhard guard候補:

- finite jobだけを発行する。
- creationとenableを分離する。
- enablement、budget、circuit stateをjob worktree外へ置く。
- safe permission以外を暗黙選択しない。
- same inputまたはactive runを重複発行しない。
- trigger evaluationをcontent-free auditへ残す。
- agent自身がschedule、quota、permission、circuitを変更しない。
- merge、push、PR、releaseへ直結しない。
- owner、expiry、kill pathを持たないscheduleをenableしない。

interval、expiry、wall time、attempt、usage、backoff、circuit threshold、retention、notification、capacity shareはproject-localなadaptive parameterです。scheduler runtimeが実装・有効化されていると確認できるまで、scheduleが存在すると仮定しません。

## Synthesize and learn locally

primaryは多数決で決めず、evidenceとproject constraintを比較します。最終報告には次を残します。

- 決めた / 作ったもの
- decisive evidence
- 重要なdisagreementと扱い
- 採らなかった案と理由
- 残るrisk、validation、次のowner
- multi-agentが結果を変えたか、review / integration costに見合ったか
- 次回変えるparameterまたはsoloへ戻す条件

agent数、message数、token量を成果として報告しません。観測をproject-localなplanning priorへ更新し、他projectの標準値にはしません。

このdevcontainer基盤を使う場合、客観的なepisode factsは`$MIRA_COMPANION_EPISODE_DIR/collaboration-episodes.json`へ自動保存されます。基盤既定はrebuild後も残る`/var/lib/mira-observations`です。primaryは比較やretrospectiveが必要な時に自分で読み、ユーザーへ転記を頼みません。sourceとcoverageを確認し、terminal successをartifact品質、post-worker-tailを実human review時間、topologyをsemantic relationへ読み替えません。ledgerが欠けている場合も数値を推測せず`unknown`とします。

## Current tooling boundary

- provider-native layer: interactive consultation、delegation、peer UX。
- `agentctl`: finite job / attempt、worktree、process、resource、structured result。
- primary / integrator: relation選択、continuation、synthesis、winner、integration。
- future trigger layer: trigger、dedupe、budget、audit、finite job emission。

`agentctl`へconversation graph、transcript、private reasoning、consensus stateを入れません。provider hook / `agentctl` lifecycleからcontent-free episode factsを自動記録し、human inputを要求しません。semantic relationや期待mechanismをhook topologyから推測せず、reliableなmachine annotationがなければ`unknown`にします。comparison harness、resource-aware recommender、schedulerはautomatic observationが必要性を示してから実装します。

## Anti-patterns

- agent count theater
- unsupported fixed participant / exchange / candidate defaults
- 同一prompt複製を多様性と呼ぶこと
- evidenceの増えないdebate
- recursive delegation explosion
- shared-checkout parallel writes
- candidate確認後の評価基準変更
- reportだけ集めてsynthesis ownerがいない状態
- unbounded recurring agent
- recurring writeからauto merge / pushへの直結
