# Adaptive multi-agent collaboration model

Status: guidance accepted; effectiveness and runtime extensions remain evidence-gated
Updated: 2026-08-26

## Purpose

この文書は、native-first multi-agent基盤で**なぜ複数agentを使い、どう関係づけ、いつ止めるか**の設計境界を定義します。

read / write / isolated laneはworkspace、permission、resource boundaryを決めます。roleは責務を決めます。relationはagent同士の関係、lifecycleは時間上の起動形です。これらを分離し、人数、exchange数、candidate数、durationをglobal defaultとして固定しません。

探索catalogは[`temp/multi-agent-collaboration/`](../../temp/multi-agent-collaboration/)、Grok 4.6 / Claude Opus 5の独立reviewとprimary synthesisは[`04-cross-provider-synthesis.md`](../../temp/multi-agent-collaboration/04-cross-provider-synthesis.md)、target project向け手順は[`project/docs/agents/collaboration-playbook.md`](../../project/docs/agents/collaboration-playbook.md)にあります。

## Core principle

```text
required artifact / decision
  -> expected value mechanism
  -> binding constraint
  -> cheapest useful relationship
  -> lane / permission / workspace
  -> lifecycle / cost caps
  -> evidence-based continuation or stop
  -> primary-owned synthesis / integration
  -> project-local learning
```

multi-agentを使う理由が「agentを使いたい」しかない場合はsoloへ戻します。agent count、message count、exchange count、token totalを成功指標にしません。

## Orthogonal axes

| axis | question | examples |
|---|---|---|
| value mechanism | 複数agentにより何が改善するか | latency overlap、coverage、decorrelation |
| relation | agent同士をどう関係づけるか | delegate、consult、compete、verify |
| role | 誰が何へ責任を持つか | researcher、implementer、reviewer、primary |
| lane | どのworkspace / permissionで走るか | read、write、isolated |
| lifecycle | いつ、どんなtriggerで起動するか | one-shot、bounded exchange、event、schedule |
| authority | 誰が判断とside effectを所有するか | primary / single writer / human owner |

relation vocabularyは説明を短くするaliasであり、closed enumや成果指標ではありません。projectで別の関係が必要なら、その価値と境界を説明して拡張できます。

## Value mechanisms

複数agentを使う前に、得たいmechanismを少なくとも一つ説明します。

- **latency overlap**: 独立workを重ね、critical pathを短くする。
- **context partitioning**: contextを狭くし、制約とevidenceの密度を上げる。
- **coverage**: 異なるshard、観点、source、failure surfaceを探索する。
- **error decorrelation**: makerとfresh checkerの目的・情報・commitmentを分ける。
- **empirical selection**: candidate差をtestやmeasurementで識別する。
- **evidence-producing refinement**: critiqueにより新しいevidence、test、claim transitionを生む。
- **temporal sampling**: eventや時間をまたぐdriftを有限runで観測する。

同じpromptの複製、同じevidenceの読み直し、text上のagreementはmechanismの発火を保証しません。

## Binding constraints

modeを選ぶ前に、今回最初に尽きるものを確認します。

- briefを外へ渡すserialization cost
- primary / human review capacity
- wall-clockと待ち許容時間
- provider quota / rate window
- agentctl capacity / queue / shared resource
- integrationとrework cost
- context coupling
- evaluator availability
- late failure cost

たとえばhuman reviewが律速なら、reviewable artifactを増やすfan-outやcandidate比較より、consultやverifyの方が純価値を持つ可能性があります。capacity limitを推奨人数へ読み替えず、同時実行できない分がwaveになりwall-clockへ影響すると説明します。

## Current relation vocabulary

| relation | meaning | common value |
|---|---|---|
| `solo` | primaryが直接処理する | coordination costを払わない |
| `delegate` | bounded artifactをworkerへ渡す。fan-outとDAG handoffを含む | latency overlap、context partitioning、coverage |
| `consult` | option、assumption、critique、evidenceを集め、必要なら交換する | coverage、evidence-producing refinement |
| `compete` | 分岐したcandidateを同じ評価契約で比較する | empirical selection |
| `verify` | fixed artifactをneutralまたはadversarialに独立検査する | error decorrelation |

旧`dispatch / fanout / panel / critique / deliberation / variants / maker-checker / red-team / pipeline`はidea catalogと対応aliasとして残せます。relationから参加者数やinteraction回数を暗黙導出しません。

## Lifecycle

| lifecycle | meaning |
|---|---|
| `one-shot` | 一回のrequest / resultでterminal |
| `bounded-exchange` | useful evidenceやartifactが増える間だけ継続 |
| `event-triggered` | relevant eventを評価しfinite jobを起動 |
| `scheduled` | external driftや履歴集計を有限intervalで評価 |

pipelineはdependency graph、scheduled / event-triggeredはlifecycleです。interaction relationと同じ分類表へ混ぜません。

## Participant derivation

参加者数を先に置きません。

- delegate: non-overlapping shard、stage、artifactから導く。
- consult: 固有のperspective、evidence source、failure modeから導く。
- compete: 実質的に異なるapproachと識別可能な評価から導く。
- verify: 独立させたいerror mode、probe、review surfaceから導く。

その後、capacity、quota、wall-clock、human review、integration costで実行可能な同時数とwaveを調整します。追加participantが固有の価値を説明できなければ増やしません。

## Parameter roles

数値やbooleanを使う場合、意味を次のいずれかとして明示します。

| role | meaning | update |
|---|---|---|
| `hard guard` | safety / authority上、違反を機械的に拒否する | 明示的な設計変更だけ |
| `cost cap` | runawayやresource starvationを止める上限 | project / taskのcapacityとriskから設定 |
| `planning prior` | 過去の観測からbudgetを見積もる参考値 | project-local evidenceで更新 |
| `hypothesis` | まだ検証されていないstarting assumption | experimentで採用・修正・棄却 |

各parameterへscope、rationale、invalidation evidence、update ownerを付けます。cost capを品質最適値、planning priorをtermination rule、provider defaultをcollaboration defaultとして扱いません。

## Continuation and termination

interaction後にprimaryが次を判断します。

- acceptanceまたはdecisive evidenceを得たか。
- new evidence、test、claim transition、useful artifactが増えたか。
- disagreementはmeasurementで解けるか。解けるなら会話より測定を優先する。
- disagreementがuser preference / authorityへ到達したか。
- scope、safety、cost capへ到達したか。
- 残る期待利益がcoordination / synthesis / review costを上回るか。

継続回数は結果として観測します。contentが変わらない言い換えを深い議論とみなしません。budget到達時はfalse successにせず、partial result、open question、追加evidenceの必要条件を返します。

## Independence policy

blindnessを無条件defaultにしません。目的と利用可能なexecution surfaceから選びます。

| purpose / constraint | useful policy |
|---|---|
| option enumerationでanchoringを避けたい、独立agentが使える | isolated-blind候補 |
| coverageを広げたい | context / source / failure surfaceをpartition |
| fixed proposalやdiffをreviewする | artifactを共有し、makerの試行軌跡やprimaryの選好を隠す |
| interfaceやfixtureの事実確認 | shared contextまたはbounded direct exchange候補 |
| delegationが使えない | blind independenceやcontext partitioningを得たと主張しない |

provider diversityは補助であり、品質の代理指標ではありません。generatorとevaluatorのどちらへ割り当てると価値があるかもproject実験で判断します。

## Dialogue ownership

primary-mediatedかprovider-native peer messagingかは、利用可能なsurface、fact共有の必要性、serialization cost、観測した有効性からprojectごとに選びます。どちらでもprimaryがbudget、authority、continuation、synthesisを所有します。

provider-native peer messagingを使う場合も、topic、authority、cost cap、interrupt owner、result contractを固定します。peer exchangeは検証可能なfactやinterface調整に向く場合がありますが、winner、risk acceptance、permission escalationをpeer agreementへ委ねません。

`agentctl`へconversation graph、transcript、private reasoning、consensus stateを入れません。interaction間で必要ならopen claimとevidence pointerだけを渡します。

## Candidate comparison

`compete`を使う前に次を満たします。

- candidate間に意味のあるapproach差がある。
- common base、scope、acceptance、resource boundaryがある。
- correctness / safetyを先に判定できる。
- evaluatorが差を識別できる根拠またはpilotがある。
- human reviewを含むcomparison costが失敗 / rework costに見合う。

candidateをすべてproduction品質まで完成させることを目的にせず、明らかな不合格は早く止めます。evaluationを見てからrubricを変更しません。hybridは新しいartifactとして再検証します。

held-out verification、blinded evaluator、cross-provider evaluatorは有力な仮説ですが、global requirementではありません。採用するprojectはfairness、fixture maintenance、hidden-requirement riskを含めて検証します。

## Recurring work boundary

定期・event駆動workは常駐agentではありません。

```text
trigger evaluation
  -> input / overlap / budget / authority checks
  -> immutable finite job
  -> existing lane / permission / result validation
  -> bounded report or candidate commit
  -> primary / human gate
```

repository commitが原因ならevent-triggeredを先に検討します。external driftや履歴の累積ならscheduled候補です。CI、deterministic script、通常cronで足りる場合はagent schedulerを作りません。

runtimeを実装する場合のhard guard候補:

- finite jobだけを発行する。
- creationとenableを分離する。
- enablement、budget、circuit stateをjob worktree外へ置く。
- safe permission以外を暗黙選択しない。
- same inputまたはactive runを重複発行しない。
- trigger evaluationをcontent-free auditへ残す。
- agent自身がschedule、quota、permission、circuitを変更しない。
- control planeからmerge、push、releaseを提供しない。
- owner、expiry、kill pathを持たないscheduleをenableしない。

interval、expiry duration、attempt、wall time、usage、backoff、circuit threshold、retention、notification、capacity shareはadaptive parameterです。値をglobal policyとして固定しません。

入力digest gating、`run_status`と`findings`の分離、finding state transition通知、snapshotとcursor checkのmissed-run分離、interactive workをstarveさせないadmission controlは、将来schedulerを実装する場合のrequirement候補です。現在のruntime claimではありません。

## Ownership

| owner | responsibility |
|---|---|
| primary / native orchestrator | mechanism、relation、participant、continuation、synthesis、winner、stop |
| provider-native layer | interactive agent UX、prompting、session、peer messaging、provider permission |
| `agentctl` | finite job / attempt、worktree、process、resource、structured result |
| future trigger layer | trigger、dedupe、budget、audit、finite job emission |
| primary / integrator / human owner | merge、push、PR、release、enable、permission escalation |
| Mira Companion | sanitized activity visualization only |

## Evidence-gated delivery

### Now: correct guidance and prepare observation

- remove unsupported global counts and unconditional blindness.
- simplify relation / lifecycle vocabulary without deleting the idea catalog.
- add mechanism、binding constraint、parameter role、human review、independence、stop reason to the collaboration brief.
- validate that the authoritative copy source preserves this guidance.
- begin manual, content-free observation on real project tasks.

### Later: automate only fields that survive use

- optional episode ledger helper after manual recording proves sustainable.
- resource occupancy report if it changes routing decisions.
- comparison harness only after evaluator capability and maintenance cost are demonstrated.
- read-only trigger pilot only after manual/non-agent alternatives prove insufficient.
- recurring write only after read-only findings are repeatedly triaged.

Negative evidence is a valid outcome: do not build a capability whose expected value was not demonstrated.

## Non-goals

- universal conversation orchestrator or message bus
- transcript / private reasoning store
- automatic consensus、winner、hybrid、merge、push、release
- agent-count or exchange-count optimizer before observation exists
- untrusted recurring execution before a real Lane I exists
- claiming same-container worktrees are a security boundary
