# Comparative experimentation and project-local learning roadmap

検討日: 2026-08-28
Status: proposed staged program; no live provider runs authorized by this document

## 0. Outcome

次の実証milestoneは、task corpusやmodel cellの単純な追加ではなく、同じtask identityとoracleでcollaboration relationだけを変える**matched topology study**である。

目的はglobal optimumを探すことではない。

- どのcausal mechanismが、どのtask structureで実際に発火したか。
- wall-clock短縮がworker、synthesis、integration costを上回ったか。
- quality改善がoracleで識別できたか。
- failure、variance、task-entry floor、ceilingを分離できたか。
- project-localな次回planを変更するだけのevidenceが得られたか。

## 1. Research questions

### Throughput

1. Non-overlapping shardをparallelにしたとき、critical pathはsolo / sequentialより短くなるか。
2. Queue、provision、serialization、fan-inがどのwidthでbinding constraintになるか。
3. Logical shard数とactual concurrencyを分離すると、同じcoverageを複数waveで行うcostはどう変わるか。

### Decision quality

4. Independent consultはsoloよりvalid option、risk、evidenceを増やすか。
5. Dialogueは新しいclaim transitionを生むか、それとも同じ主張を言い換えるか。
6. Provider diversityとperspective / source partitionのどちらがerror decorrelationへ寄与するか。

### Implementation and assurance

7. Maker-verifierは追加時間に見合う独立failureを発見するか。
8. Competeはcommon evaluatorで意味のあるcandidate差を識別できるか。
9. Parallel writeはconflict、integration edit、aggregate validationを増やし、生成時間の短縮を相殺するか。

### Reliability and operations

10. Relation別にprovider startup、artifact missing、timeout、cancel、orphan、cleanupはどう変わるか。
11. Higher concurrencyがinteractive work、rate window、shared Docker / build resourceをstarveさせるか。
12. Project-local predictionは時間とともにstaleになるか。

### Recurring work

13. Event / scheduled agentはactionable findingを生むか、duplicate / alert fatigueを増やすか。
14. Deterministic CI / script / normal cronよりagentを使うincremental valueがあるか。

Recurring workは後段であり、最初のlive topology studyへ混ぜない。

## 2. Evidence populations

異なるpopulationを一つの平均へpoolしない。

### P0: Controlled fixture study

- immutable fixture、task contract、known-good / valid alternatives、negative mutants
- same case revision、same base / bundle / capsule / evaluator
- provider / model / setting / environmentをexact strata化
- relationのcausal effectを識別する主population

### P1: Project-local natural episodes

- real taskのecological validity
- plan IDとtask fingerprintからrelation semanticsを取得
- operational timing、failure、integration proxyを自動収集
- selection biasがあるためcausal effectではなくlocal planning prior

### P2: Replay / shadow study

- 完了済みtaskをisolated baseで別planへ再実行
- production side effectなし
- task drift、leakage、known-answer contaminationを明示
- natural taskとcontrolled fixtureの中間population

### P3: Temporal / recurring observation

- external drift、event yield、duplicate、missed run、starvation
- finite jobとread-onlyから開始
- topology evidenceとscheduler governanceを分離

## 3. Experimental invariants

Matched comparisonには次を要求する。

1. same case revisionとfixture identity。
2. same visible task contractとacceptance。
3. same evaluator revisionとquality headroom。
4. same provider/model/runtime identity、または異なるdimensionとして分離。
5. same environment class、permission、cache/context policy。
6. relation以外の差をmanifestへ明示。
7. decision rubricを結果前に固定。
8. artifact retentionとunexpected-change audit。
9. automatic retryなし。再測定はnew run ID。
10. infrastructure、quality、censoring populationを分離。

Relation変更によりtask contract自体を変える必要がある場合、同一causal comparisonとは呼ばず新case revisionまたは別profileにする。

## 4. Participant and interaction derivation

人数、round、candidate数をglobal defaultにしない。

| Relation | Derivation basis |
| --- | --- |
| delegate | bounded artifact / stageの所有単位 |
| parallel shards | dependency graph上で同時実行可能なnon-overlap units |
| consult | distinct perspective、source、risk、unknown |
| compete | evaluatorが識別できるmeaningfully different approach |
| verify | decorrelateしたいfailure modeとindependent check |
| dialogue | unresolved claimと新しいevidenceを供給できるparticipant |

Pilotでtask-entry、artifact contract、evaluatorを確認する。Continuationはrepeat回数ではなく次で決める。

- within-cell varianceがdecision boundaryを覆っているか。
- quality ceiling / floorでrelation差を識別できないか。
- new repeatが比較の解釈を変える可能性があるか。
- budget、quota、deadline、review capacityへ達したか。
- negative evidenceによりcandidateを停止すべきか。

Singletonはraw pointとして保持できるが、causal relation ruleにはしない。

## 5. Relation-specific study designs

### 5.1 Solo vs bounded delegation

Mechanism hypothesis: context partitionまたはprimaryのcritical-path解放。

Control:

- solo primaryが同じartifactを完成。
- delegated planはworker artifactとprimary synthesisを分離。

Observe:

- brief / dispatchからworker terminalまで
- primary blocking / overlapping work
- synthesis / integration tail
- artifact validity、primary correction、acceptance

Disconfirming evidence:

- serialization + synthesisがsolo wallを超える。
- worker outputをprimaryが実質的に再実装する。
- scope / context不足によるquality低下。

### 5.2 Sequential vs parallel shards

Mechanism hypothesis: independent work intervalのoverlap。

必要条件:

- dependency graphでparallel-ready。
- edit surfaceまたはartifactが衝突しない。
- fan-in contractがある。

Observe:

- critical path、aggregate worker、active union、queue wave
- shard skew、straggler、duplicate investigation
- merge / integration conflict、aggregate validation

Logical shard数とmax concurrencyを別dimensionにする。Width-1でも同じshard planをsequential controlとして観測できる。

### 5.3 Solo advice vs independent consult

Mechanism hypothesis: option / evidence / risk coverageとanchoring低減。

Evaluator候補:

- versioned claim / evidence obligations
- valid alternativeを複数受理するplural-gold
- hidden vocabularyではなくsemantic criteria

Observe:

- unique valid claims、evidence source coverage、unknown honesty
- primary decision changeとdecisive evidence
- duplicate / unsupported claims
- synthesis wallとcontext size

### 5.4 Independent consult vs evidence dialogue

Mechanism hypothesis: disagreement交換によりnew evidenceまたはclaim transitionが生まれる。

Dialogue inputは全文回答でなくopen claim / evidence pointer / cruxだけにする。

Observe:

- claim status transitions
- new evidence / test count
- resolved unknownとintroduced unsupported claim
- exchange wall、context growth、no-useful-delta stop

固定roundを置かない。新しいevidenceが増えない言い換えで停止する。

### 5.5 Maker-only vs maker-verifier

Mechanism hypothesis: makerと相関しないfailure discovery。

Observe:

- verifier-only finding / test / criterion
- true finding、false positive、already-covered finding
- maker repair wall、retest、remaining defect
- verifier costとlate-failure avoided proxy

Verifierが同じprompt、同じattempt trail、同じassumptionを共有する場合、独立性を主張しない。

### 5.6 Single candidate vs compete

Mechanism hypothesis: empirical selectionが初期commitmentより良いartifactを選ぶ。

必要条件:

- meaningfully different approach。
- common immutable base、scope、acceptance、resource cap。
- correctness / safety first、performance / maintainability second。
- evaluator capability pilot。

Observe:

- time to first acceptable candidate
- discarded worker time、comparison / synthesis wall
- winner stability、hybrid rework
- candidate diversityとduplicate implementation

全candidateをproduction品質へ仕上げない。明らかな不合格はpredeclared gateで止める。

### 5.7 Primary monolith vs staged pipeline

Mechanism hypothesis: context specializationとcontracted handoff。

Observe:

- stage latencyとdependency wait
- handoff artifact validity
- error propagationとrollback point
- total wall、aggregate worker、primary integration

前段failureを後段agent能力のfailとして数えない。

## 6. Case selection from the existing corpus

新caseを先に増やさず、既存36 caseからmechanismを識別できる候補を選ぶ。

| Relation question | Candidate families | Required adaptation |
| --- | --- | --- |
| delegate / partition | repository-trace、documentation-runbook | non-overlap evidence shardとfan-in artifact |
| parallel write / pipeline | refactor-migration、devcontainer-operations | dependency graph、exclusive paths、aggregate check |
| consult / dialogue | architecture-design、security-isolation、evidence-synthesis | plural valid answers、claim ledger |
| compete | bounded-implementation、performance-resource | common evaluator、approach difference、early reject |
| maker-verifier | test-design、security-isolation、devcontainer-operations | verifier-only mutants / checks |
| blocker hypotheses | failing-test-diagnosis | independent hypothesis probesとsame failure evidence |

既存caseのoracleにheadroomがない場合、relation差を測れない。Ceiling caseをrepeatして`同等`と結論せず、challenge criterionまたは新revisionへ送る。

## 7. Metrics

### Time decomposition

- T0 decision / plan freeze
- T1 dispatch request
- T2 worker start
- T3 first contract-valid artifact
- T4 worker terminal
- T5 synthesis complete
- T6 integration / aggregate validation complete
- T7 user-visible terminal

Derived observations:

- queue / provision
- worker terminal wall
- aggregate worker
- worker active union
- critical path
- synthesis tail
- integration / validation tail
- censored wait at cap

### Quality and artifact

- infrastructure success / failure
- acceptance pass / fail / unavailable
- criterion scoreとfailed IDs
- artifact missing / complete / partial
- unexpected tracked / untracked / deleted counts
- verifier-only evidence
- unknown honestyとclaim provenance

### Coordination and integration

- participants planned / dispatched
- peak concurrency、waves、straggler
- dependency wait / skipped descendants
- duplicate artifact / claim
- merge conflict、additional primary edit、retest
- adopted / rejected artifact refs
- cleanup / orphan / residual resource

### Resource and operational pressure

- provider setting statusとidentity confidence
- quota / rate rejection
- context / compaction state when observable
- CPU / memory / Docker / build contention class
- queue capacityとinteractive starvation

Tokenやevent数を成果KPIにしない。Constraintとdiagnosticとしてのみ使う。

## 8. Analysis rules

1. Case間平均でrelation winnerを作らない。
2. Same-case repeatとbetween-case varianceを分ける。
3. Requested settingとapplied settingを混ぜない。
4. Fast failureをfast completionへ入れない。
5. Ceiling、floor、oracle mismatch、task-entry、infrastructureを別分類する。
6. Natural episodeのselection biasを明示する。
7. Multiple testingをprovider leaderboardへ変えない。
8. Median / p95をsample countに関係なく自動表示しない。
9. Causal effectはmatched eligible strataだけで論じる。
10. Negative / ambiguous resultを機能追加の失敗でなくstop evidenceとして扱う。

## 9. Staged roadmap

### R0: Decision semantics contract

Deliver:

- decision packet schema / validator
- plan ID、candidate、prediction、stop、fallback
- sanitized outcome / learning delta

Exit evidence:

- primary workflowから過剰なhuman formなしに生成できる。
- unknownとprovenanceが保たれる。
- raw task contentがcontent-free ledgerへ漏れない。

### R1: Correlation and read-only reporting

Deliver:

- plan IDをprovider hook、agentctl job / attemptへcorrelate
- current episodeとbroker timingのjoin
- project-local bounded report

Exit evidence:

- duplicate outer / inner observationを識別できる。
- missing eventを欠測として表示する。
- relationをtopologyから推測しない。

### R2: Live collaboration adapter

Deliver:

- finite collaboration DAGからprovider-native / agentctl dispatchするadapter
- cancel、deadline、dependency skip、owned cleanup
- prompt / transcript非永続のstructured terminal result

Exit evidence:

- fake adapterと同じcontrol invariantsがliveでも成立。
- timeout / cancel / partial artifactでfalse successにならない。
- automatic retry、recurring、merge / pushを含まない。

### R3: Matched topology pilot

Deliver:

- mechanismが異なるrelation comparison
- exact fixture / evaluator identity
- artifact-retained run records
- validity dispositionとhuman report

Exit evidence:

- relation差を識別できるheadroom、または識別不能の明確な理由がある。
- within-cell variance、synthesis、integrationを観測できる。
- global defaultを生成しない。

### R4: Project-local natural learning

Deliver:

- task fingerprintとdecision packetをnormal workへ比例的に導入
- project-local prediction / outcome comparison
- stale / unmeasured / negative evidence表示

Exit evidence:

- 次回planを実際に変更したevidenceがある。
- plan serializationがtask costを支配しない。
- human入力なしで維持できる。

### R5: Planning Skill

Deliver:

- `plan-agent-collaboration`
- capability、duration、controlled topology、local evidenceのbounded query
- candidate、unknown、selected finite plan、stop / fallback

Exit evidence:

- exact evidenceを短く返す。
- missing cellを補間しない。
- router / rankingを装わない。
- Skillなしのplaybook workflowよりdecision consistencyまたはplanning costが改善する。

### R6: Recurring read-only pilot

Prerequisite:

- natural episodeから繰り返す価値が確認された。
- deterministic CI / script / normal cronでは不足する。

Observe:

- actionable yield、duplicate、missed trigger、false positive
- budget、backoff、circuit、expiry
- interactive capacity impact

Recurring write、auto merge、auto pushは別のauthority milestoneとする。

## 10. Go / stop decisions

### Continue when

- new evidenceがcandidate choiceまたはbudgetを変える。
- evaluatorがrelation差を識別できる。
- natural taskでsame fingerprintが再発する。
- operational failureが修復可能なinstrumentation gapである。

### Stop or shrink when

- soloがserialization前に完了する。
- all candidateが同じceilingへ達しrelation差を測れない。
- worker artifactが繰り返しmissingでtask-entryがbinding constraint。
- synthesis / integrationがcritical pathを支配し改善しない。
- review / validation capacityを超えるartifact fan-outになる。
- new exchangeがevidenceやclaimを変えない。
- privacy、authority、quota、resource guardへ達する。

## 11. Governance and rollback

- Live runはexplicit finite manifestとconfirm boundaryを持つ。
- Credential valueとpathをrecordへ残さない。
- Derived Atlas / reportだけをreplaceし、raw runを上書きしない。
- Schema変更はversioned migrationまたはparallel readerで行う。
- Planning Skillは削除してもagentctl execution fabricが動く構成にする。
- Local priorが壊れた場合、controlled Atlas + playbookへfallbackする。
- Scheduler、router、auto integrationを同一milestoneへ抱き合わせない。

## 12. Recommended immediate milestone

次に実装するなら、R0とR1を一つのbounded milestoneにする。

```text
Goal:
  primaryが作ったcollaboration planの意味を、content-free episodeとagentctl outcomeへ
  安全にcorrelateし、予測と結果をread-only reportで比較できるようにする。

Definition of Done:
  - decision packet schema / validator
  - plan ID correlation
  - sanitized outcome / learning delta
  - bounded local report
  - no live provider adapter、no scheduler、no automatic routing
```

このmilestoneが完了して初めて、R2のlive topology experimentが「何を測ったか」を失わず実行できる。
