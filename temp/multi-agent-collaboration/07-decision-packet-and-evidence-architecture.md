# Orchestration decision packet and evidence architecture

検討日: 2026-08-28
Status: proposed architecture; schema and runtime not yet implemented

## 0. Outcome

別projectのorchestratorへ必要なのは「このtaskなら3 agent」のようなruleではない。必要なのは、現在taskの構造、runtime capability、利用可能な過去evidence、候補collaboration、選択理由、実行結果、次回更新を一つのprovenance chainとして扱う**decision packet**である。

```text
task-local facts + runtime doctor + project constraints
                         │
                         ▼
                 candidate relations
                         │
              exact evidence / missing cells
                         │
                         ▼
                  primary decision
                         │
                   finite execution
                         │
                         ▼
          outcome + integration + validity
                         │
                         ▼
             project-local planning prior
```

Packetはautomatic decision engineではない。primaryの判断を再現可能にし、観測不能を`unknown`にし、後で予測と結果を比較できるようにするcontractである。

## 1. Design principles

1. plan、observation、inferenceを分ける。
2. task contentを含むprivate recordとcontent-free aggregateを分ける。
3. relationをhook topologyから推測せずplan IDでcorrelateする。
4. exact evidenceがなければunmeasuredを返す。
5. hard guard、cost cap、planning prior、hypothesisを混ぜない。
6. causal claimにはmatched comparisonを要求する。
7. predictionを保存し、結果を見てから過去の予測を書き換えない。
8. human入力をrequiredにしない。
9. provider/model diversityをqualityの代理にしない。
10. primaryがdecision、continuation、synthesis、integrationを所有する。

## 2. Packet lifecycle

### P0: Task fingerprint

Primaryが通常planning中に構造化する。人間へformを要求しない。自動取得できる値はtoolから取り、semantic値はprimaryがtask planから生成し、分からなければ`unknown`にする。

### P1: Candidate set

Solo alternativeを必ず含める。multi-agent candidateは固有のmechanismを持つものだけ作る。relation名を変えただけのduplicate candidateを増やさない。

### P2: Evidence attachment

Duration Atlas、runtime doctor、project-local episodes、controlled collaboration studyを別sourceとして結合する。近傍cellを予測値へ変換しない。

### P3: Decision freeze

実行前に選択、理由、予測、budget、stop、fallback、比較基準を固定する。結果を見てからrubricを変更しない。

### P4: Execution correlation

Plan IDをprovider parent episode、agentctl job、attempt、collaboration runへ渡す。raw objectiveやpathをcontent-free ledgerへ複製しない。

### P5: Outcome and learning

Acceptance、timing、artifact、integration、failure、stop reasonを結合する。予測差とevidence gapを次回planning priorへ反映するが、別projectのglobal defaultにはしない。

## 3. Proposed packet sections

実装時は一つの巨大schemaへせず、private plan、sanitized decision、outcome、learning viewを分離してもよい。以下はlogical contractである。

### 3.1 Identity and provenance

```yaml
packet_schema_version: 1
plan_id: opaque-stable-id
project_id: opaque-project-id
base_sha: full-immutable-sha
created_at: utc
created_by: primary
sources:
  task_contract_digest: sha256:...
  capability_snapshot_digest: sha256:...
  evidence_snapshot_digests: []
```

Content-free aggregateにはraw objective、workspace path、prompt、session IDを入れない。

### 3.2 Task fingerprint

| Field group | Candidate fields | Meaning |
| --- | --- | --- |
| profile | family、structural size、stack、artifact type | duration corpusとの照合 |
| surface | expected files / modules / components、change kind | editとintegration範囲 |
| graph | independent units、dependency depth、shared nodes | latency overlap可能性 |
| context | context surface、partitionability、global invariants | serializationとcontext coupling |
| ambiguity | solution multiplicity、unknown type、external evidence | consult / dialogue候補 |
| evaluator | acceptance kind、oracle strength、latency、headroom | compete / verify可能性 |
| risk | reversibility、blast radius、late failure、security | verification価値 |
| temporal | one-shot、event、external drift | lifecycle候補 |

Structural sizeを予想時間で決めない。予想時間はevidence attachment後の別fieldである。

### 3.3 Runtime capability snapshot

| Dimension | Examples |
| --- | --- |
| provider surface | available CLI、auth freshness state、model alias |
| applied confidence | resolved model、requested / applied effort、confidence |
| interaction | native subagent、peer messaging、structured output |
| execution | read / write / isolated、worktree、container、network |
| control | cancel、timeout、hook、resume、validation |
| capacity | available slots、queue、resource class、competing load |
| governance | permission profile、external side-effect owner |

Capabilityはperformanceではない。`peer messaging available`からdialogue品質を推測しない。

### 3.4 Candidate collaboration plans

各candidateは次を持つ。

```yaml
candidate_id: stable-local-id
relation: solo | delegate | consult | compete | verify | project-specific
lifecycle: one-shot | bounded-exchange | event-triggered | scheduled
expected_mechanisms: []
why_mechanism_should_fire: bounded explanation
disconfirming_signal: observable condition
participant_basis: artifacts | perspectives | approaches | failure-probes
participant_plan_ref: digest-or-local-ref
independence_policy: ...
artifact_flow: ...
lane_permission_workspace: ...
authority: primary
limits: []
continuation_evidence: []
stop_conditions: []
fallback_candidate_id: solo-or-cheaper-plan
```

Participant countはplan resultでありinput defaultではない。Capacity不足時は価値あるworkを削るかwaveへ分けるかを明示し、capacityを理想人数に読み替えない。

### 3.5 Evidence matches

Evidenceはcandidateを支持するscoreではなく、観測事実と適用限界である。

```yaml
evidence_id: digest
source_kind: controlled-atlas | project-episode | replay | capability
match:
  task_identity: exact | structural-adjacent | unmatched
  relation_identity: exact | absent | unmatched
  runtime_identity: exact | partial | unknown
  environment_identity: exact | partial | unknown
observation_state: singleton | same-case-repeat | provisional
quality_gate: eligible | conditional | excluded | not-audited
freshness: current | stale | unknown
usable_for:
  - terminal-time-prior
not_usable_for:
  - causal-relation-effect
```

`structural-adjacent`はidentifier hintでありduration estimateではない。

### 3.6 Prediction and budget

予測は過去evidenceと仮説を区別する。

| Prediction | Representation |
| --- | --- |
| wall time | raw exact point、same-case range、またはunavailable |
| aggregate worker | exact evidenceまたはunavailable |
| queue / provision | capability / local operational prior |
| synthesis / integration | local proxy、またはunknown |
| quality effect | hypothesis。causal evidenceがある場合だけobserved effect |
| failure / censoring | populationを分離 |
| usage / quota | provider観測。billing costと分離 |

Subscription環境でもusageは無意味ではない。実課金ではなく、rate window、context、compaction、concurrency、interactive work starvationのconstraintとして扱う。

### 3.7 Decision freeze

```yaml
selected_candidate_id: ...
rejected_candidates:
  - candidate_id: ...
    reason: ...
decisive_constraints: []
decisive_evidence_ids: []
open_unknowns: []
decision_confidence: exact-evidence | bounded-hypothesis | exploratory
external_side_effect_owner: primary-or-human
```

`confidence`を数値確率にしない。Calibrationされていない0–100 scoreは精密さを装うだけである。

### 3.8 Execution outcome

| Group | Required observations |
| --- | --- |
| timing | queue、provision、dispatch、worker、synthesis、validation、terminal |
| topology | planned / dispatched participant、peak、wave、unfinished |
| quality | acceptance、criterion、artifact validity、censoring |
| coordination | duplicate work、dependency wait、handoff failure、conflict |
| integration | adopted artifacts、primary edits、aggregate tests、rollback |
| termination | completed、decisive evidence、no useful delta、authority、cap、failure |
| validity | coverage、missing events、identity、setting confidence |

### 3.9 Learning delta

```yaml
prediction_comparison:
  wall_time: within-observed-range | under | over | unavailable
  quality: supported | refuted | unresolved
mechanism_observation:
  status: supported | contradicted | not-identifiable
  evidence: []
routing_prior_change:
  scope: this-project-and-comparable-fingerprint
  change: ...
  invalidation_condition: ...
next_measurement: ...
```

一episodeでrouteを確定しない。Negative evidenceは`soloへ戻す`、candidateを削る、measurementを停止する根拠になり得る。

## 4. Automatic proxies without human forms

Human inputをrequiredにしないため、次を自動観測候補とする。

| Question | Safe proxy | Limitation |
| --- | --- | --- |
| workerは動いたか | start / stop、active union、artifact terminal | usefulnessではない |
| primary synthesis cost | last worker stopからterminalまでのactivity / elapsed | human review、provider wait、editを混ぜる |
| reworkは発生したか | failed test後のedit、red-to-green、worker後の追加validation | reasoning difficultyではない |
| artifactは採用されたか | exact commit ancestry、patch / path provenance | semantic contribution全体ではない |
| integrationは重かったか | conflict、additional changed paths、aggregate test duration | maintainabilityではない |
| verifierは価値を出したか | new failed criterion / test / evidence pointer | findingの重要性にはoracleが必要 |
| dialogueは進んだか | new evidence、claim status transition、resolved unknown | 文章差分やmessage数では代用しない |

Human review minutes、user satisfaction、maintainabilityは直接観測できない場合`unknown`にする。Proxyを真値へrenameしない。

## 5. Claim and evidence ledger

Dialogue、consult、verifyでは全文transcriptを保存せず、小さいledgerを使う。

```yaml
claim_id: stable-id
status_before: proposed | supported | refuted | unresolved
status_after: proposed | supported | refuted | resolved
new_evidence_refs: []
new_test_refs: []
decision_effect: changed | unchanged | unknown
next_action: measure | authority | revise | stop
```

Continuationはclaim数やround数でなく、validなtransition、新しいevidence、useful artifactが増えたかで決める。Message count、文章量、agreement countをprogressにしない。

## 6. Storage and privacy layers

| Layer | Content | Location candidate | Retention |
| --- | --- | --- | --- |
| L0 private task plan | objective、paths、task-local details | project-local private state / bounded ticket | task / project policy |
| L1 immutable outcome | structured result、checks、commit refs | `agentctl` attempt evidence | bounded existing retention |
| L2 content-free decision episode | opaque IDs、categories、timing、validity | Mira observations volume | bounded cap |
| L3 controlled aggregate | exact strata、quality、censoring | generated Atlas | versioned release |
| L4 compact Skill result | selected evidence and unknowns | invocation output | ephemeral |

保存しないもの:

- prompt、response、private reasoning、full transcript
- credential、environment dump、raw workspace / session IDs
- arbitrary tool input / output
- unbounded artifact content
- human identityやbehavior surveillanceに使える詳細event stream

## 7. Skill delivery design

新しい`plan-agent-collaboration` Skillをtarget-project copy sourceとして追加する案が有力である。

### Inputs

- current task fingerprint
- project collaboration constraints
- `agentctl doctor` / capacity snapshot
- `lookup-agent-duration`のexact query result
- project-local sanitized evidence
- explicit user constraints / authority

### Outputs

1. solo alternative。
2. mechanismが異なるbounded candidateだけ。
3. 各candidateのknown evidence、unknown、cost、risk。
4. selected planと理由。
5. plan ID、budget、stop、fallback。
6. 実行後のlearning delta。

### Modes

- `profile`: task fingerprintとmissing factsだけ。
- `plan`: candidateとfinite planを作る。
- `compare`: user / primaryが指定したcandidateだけ比較。
- `audit`: 過去decisionのevidenceとpredictionを確認。
- `learn`: project-local priorの差分候補を返す。

Skillはprovider/model/relationをglobal rankingしない。Exact dataが無ければ、exploratory planとmeasurement needを返す。

## 8. Cross-project portability

Base imageへ持たせるもの:

- schema、validator、planner/query runtime
- controlled Atlasとvalidity companion
- collaboration guidanceとSkill

Projectへ持たせるもの:

- AGENTS contract、role、lane、permission
- project-local task fingerprint mapping
- acceptance profiles
- local priorsとdecision historyのsanitized aggregate

Project間で共有しないもの:

- raw task content
- local absolute path、session、credential
- project-specific routing conclusion
- human behavior proxy

## 9. Failure modes and safeguards

| Failure | Safeguard |
| --- | --- |
| plan serializationがtaskより重い | short inline packetを許容し、同じdecision fieldsだけ維持 |
| fieldを埋めるための捏造 | provenanceと`unknown`を必須化 |
| routing scoreへの過度な集約 | dimension別evidenceとhard gateを分離 |
| stale model data | identity、observed window、freshnessを表示 |
| post-hoc rationalization | decision freezeとprediction digest |
| proxy gaming | event / token / worker countをsuccess KPIにしない |
| privacy expansion | allowlist field、opaque ID、content-free aggregate |
| feedback loopの自己強化 | explorationとcausal claimを分け、project-local scopeを付ける |
| plannerの過信 | fallback solo、unmeasured、human / authority boundary |

## 10. Recommended implementation boundary

最初からautomatic routerを作らない。最小の価値あるsliceは次である。

1. decision packet schemaとvalidator。
2. collaboration plan templateからpacketを生成するprimary workflow。
3. plan IDをepisode / agentctl jobへ渡すcorrelation。
4. read-only decision / outcome report。
5. planning Skillがcandidate、evidence、unknown、stopを返す。

このsliceだけでも、現在`unknown`のsemantic fieldを正しく埋め、次のcontrolled comparisonを設計できる。
