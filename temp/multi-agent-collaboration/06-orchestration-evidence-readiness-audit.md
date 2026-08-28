# Orchestration decision evidence readiness audit

検討日: 2026-08-28

## 0. Outcome

現在のrepositoryは、multi-agentを安全かつ適応的に使うための**思想と実行境界**をかなりよく整備している。一方、orchestratorが別projectで`solo / delegate / consult / compete / verify`を実測に基づいて選ぶための**比較evidence**はまだ不足している。

成熟度は一枚岩ではない。

| Plane | Current state | Decision |
| --- | --- | --- |
| guidance | mechanism、binding constraint、relation、lane、lifecycle、stopを分離済み | 他projectへ配布できる |
| execution safety | finite job、worktree、permission、single-writer、structured resultを保有 | bounded write jobへ利用できる |
| solo duration evidence | 36 case ID、139 terminal samples、quality / censoring / artifact gateを保有 | exact条件のplanning priorに使える |
| collaboration topology evidence | current Atlasは全139 samplesが`primary-only / participants=1 / workers=0` | relation選択には使えない |
| automatic observation | hook / `agentctl`からcontent-free episodeを作れる | operational proxyとして利用可能 |
| semantic observation | mechanism、binding constraint、relation、outcome contributionは原則`unknown` | plan correlationなしに後付け分類しない |
| live collaboration study | finite DAGとfake adapterは実装済み | live provider / agentctl比較は未測定 |
| target-project delivery | playbook、plan template、duration lookup Skillあり | planning Skillとlocal evidence readerが不足 |

したがって現在地は、**solo baselineと安全なcollaboration design languageが完成し、multi-agentの相対効果を測る直前**である。task caseを無差別に増やすより、既存caseを同一identityのまま複数relationへ展開する方が次の情報価値は高い。

## 1. Audit scope and evidence

この監査では次を突き合わせた。

- authoritative guidance: `docs/agents/collaboration-model.md`
- target-project guidance: `project/docs/agents/collaboration-playbook.md`
- agent-owned plan: `project/docs/agents/tickets/collaboration-plan.template.md`
- zero-input observation: `docs/agents/collaboration-observation.md`
- execution contracts: `project/.agent/`、`scripts/agentctl*`
- collaboration DAG: `scripts/agent_duration_collaboration.py`
- controlled duration data: `generated/duration-atlas/current.json`
- compact delivery: `project/.codex/skills/lookup-agent-duration/`
- Wave 8 validity findings: `temp/multi-agent-duration-atlas/25-effort-inference-validity-review.md`と`26-wave8-identifiable-remeasurement.md`

Current Atlasの機械集計は次だった。

| Dimension | Observed population |
| --- | --- |
| samples | 139 |
| series / case strata | 113 / 118 |
| case IDs | 36 |
| relation | `primary-only`: 139 |
| configuration | `C0`: 139 |
| participants actual | `1`: 139 |
| workers actual / peak concurrent | `0 / 0`: 139 |
| provider observations | Codex 82、Grok 50、Claude 7 |
| generation-setting status | unknown 90、applied 47、rejected 2 |
| structural size | S 53、M 24、L 62 |

Provider countsはprovider rankingではない。case、study、quality population、setting confidenceが異なり、Claude recordsにはcalibration / infrastructure populationが含まれる。ここからprovider優劣を集計しない。

Current execution surfaceでは`/var/lib/mira-observations/collaboration-episodes.json`とfallback pathにledgerを確認できなかった。これは機能不良を証明せず、このaudit時点でproject-local natural episode populationを利用できなかったことだけを意味する。

## 2. What the current system can answer

### 2.1 Collaboration design

- multi-agentを使うcausal mechanismを説明できるか。
- 今回最初に尽きるbinding constraintは何か。
- relation、role、lane、lifecycle、authorityをどう分けるか。
- participantをartifact、perspective、approach、failure probeからどう導くか。
- continuationに必要なevidenceとstop conditionは何か。
- recurring workをfinite job、dedupe、quota、kill pathでどう囲うか。

### 2.2 Safe execution

- read / write / isolatedのどのlaneで動かすか。
- write jobをimmutable base SHAと専用worktreeへ置けるか。
- provider capabilityとpermission boundaryが満たされるか。
- result、changed paths、checks、risk、follow-upをstructured envelopeで回収できるか。
- capacity不足、orphan、validation failure、cleanup対象を検出できるか。

### 2.3 Exact solo duration evidence

- 同じcase revision、model identity、setting status、surface、environmentで何秒だったか。
- quality-pass / fail / unknown、censoring、criterion failureは何だったか。
- artifactがcomplete / partial / missingだったか。
- 一件のraw pointかsame-case repeatか。
- exact cellが未測定か。

## 3. What it cannot answer yet

### 3.1 Relative value of collaboration

Current Atlasにはmulti-agent topologyがないため、次を推定できない。

- delegateがsoloよりcritical pathを短縮したか。
- parallel shardのoverlapがserializationとsynthesisを上回ったか。
- consultが選択肢やevidence coverageを増やしたか。
- dialogueが言い換えでなくclaim transitionを生んだか。
- competeが追加実装・比較costに見合うwinnerを識別したか。
- verifyがmakerと相関しないfailureを発見したか。
- staged pipelineがcontext分割で得をしたか、handoff errorを増やしたか。

### 3.2 Contribution and counterfactual

Worker artifactがfinal outputへ存在しても、multi-agentが結果を改善したとは限らない。逆に、artifactを直接採用しなくても、反証やtestがprimary判断を変えた可能性がある。

必要なのは次の区別である。

| Claim | Required evidence |
| --- | --- |
| artifact contributed | commit ancestry、adopted patch、evidence pointer等の観測 |
| decision changed | primary-owned synthesisでbefore / after claimを記録 |
| collaboration caused improvement | matched solo / collaboration comparisonと識別可能なoracle |
| human review was cheap | 直接観測がなければ断定不能。post-worker tailはproxyのみ |

Natural logだけからcounterfactualを捏造しない。

### 3.3 Project-local routing prior

Task familyだけではrelationを選べない。同じ`bounded-implementation`でも、独立fileへ分けられる変更と、一つのstate machineを全員が触る変更ではdecomposabilityが異なる。次のproject-local informationがまだaggregateされていない。

- repository topologyとchange coupling
- test / build feedback latency
- evaluator strengthとheadroom
- primary synthesis / integration capacity
- conflictとreworkの履歴
- provider task-entry / tool-use reliability
- project固有risk、release cadence、late failure cost
- natural taskでのprediction error

### 3.4 Live collaboration runtime

`run-agent-duration-collaboration`はrelation別DAG、dependency、concurrency、failure、cancel、content-free analyticsを検証できる。しかしcurrent boundaryは`provider_execution=not-implemented`、`agentctl_mapping=adapter-owned-not-implemented`である。fake clock / fake adapterのcontrol-plane timingをlive agent performanceとしてAtlasへ入れない。

## 4. Decision-material taxonomy

Orchestratorへ渡す情報は、少なくとも次の七群へ分ける。異なる意味を一つのrouting scoreへ潰さない。

### A. Task structure

- family / structural size / stack
- expected artifactとdefinition of done
- change surface、dependency graph、shared state
- decomposability、context coupling、serialization cost
- ambiguity、novelty、unknownの種類
- oracle strength、validation latency、measurement headroom

### B. Project and risk

- reversibleか、migration / release / security boundaryか
- failure detection distanceとrollback可能性
- late failure cost、blast radius、external side effect
- deadline、interactive latency、review / integration capacity

### C. Runtime capability

- provider / model / CLI identityとsetting confidence
- native subagent、peer messaging、tool、write、cancel、hook availability
- lane / permission / workspace / image
- quota、rate window、capacity、queue、competing load

### D. Collaboration candidate

- expected mechanismとdisconfirming signal
- relation、lifecycle、participant derivation
- independence policy、artifact flow、authority
- predicted wall、worker、synthesis、integration budget
- stop / fallback / partial-result behavior

### E. Execution evidence

- queue、provision、dispatch、worker interval、synthesis、validation、terminal
- peak concurrencyとworker-active union
- failure、cancel、timeout、unfinished work
- artifact completeness、unexpected change、result contract validity

### F. Outcome evidence

- acceptanceとcriterion-level quality
- contribution、adoption、conflict、rework、rollback
- open claim、disagreement、unknown、stop reason
- project-local prediction error

### G. Evidence validity

- controlled / natural / replay population
- exact case / family-adjacent / unmeasured
- identity、setting、environment、freshness
- repeat / singleton、within-cell variance
- ceiling / floor / oracle mismatch / infrastructure population

## 5. Multi-perspective readiness review

| Perspective | Strength | Missing evidence |
| --- | --- | --- |
| throughput | worker timing primitivesはある | solo対parallelのmatched critical-path比較 |
| epistemic quality | consult / dialogueの思想はある | claim transition、novel evidence、decision change |
| implementation quality | resultとvalidation contractあり | maker-verifierのdefect escape / rework比較 |
| empirical selection | compete条件とoracle原則あり | live candidate cost、winner stability、discard cost |
| reliability | failure / cancel / capacity / cleanupあり | topology別failure率、recovery time、tail risk |
| human factors | review capacityをfirst-classにしている | human timeはzero-inputでは直接取得不能。proxy校正が必要 |
| security | lane / permission / single writerが明確 | relationごとのcredential / untrusted artifact exposure実測 |
| economics | wall / worker timeを保持 | subscription環境でもquota、latency、context、review costが不足 |
| temporal work | finite recurring guardの思想あり | actionable yield、duplicate、alert fatigue、starvation実測 |
| portability | templateとSkill配布面あり | project-local evidence bootstrapとplanning Skill |

## 6. Readiness decision

### Use now

- collaboration guidanceとplan template
- provider-native read consultation / bounded delegation
- `agentctl` write / isolated jobs
- exact solo duration lookup
- zero-input content-free operational observation

### Do not claim yet

- relationのglobal ranking
- task familyからのautomatic topology selection
- provider / model / effortのproject-independent default
- recommended participant / exchange / candidate count
- worker countからのproductivity score
- reviewProxyをhuman review timeとすること
- natural episodeだけからのcausal improvement

### Highest-value next work

1. plan semanticsとexecution episodeを結ぶmachine decision envelope。
2. live collaboration adapterとagentctl correlation。
3. 同一caseでsoloとrelationを比較するcontrolled study。
4. outcome / integration proxyを持つproject-local aggregate。
5. duration、capability、local evidenceを統合するplanning Skill。

## 7. What not to expand first

- 36 case corpusを目的なく増やさない。
- model / effort cellだけをさらに埋めてmulti-agent判断ができたとみなさない。
- episode event列からsemantic relationを推測しない。
- transcript、private reasoning、raw promptを学習loopへ保存しない。
- routing scoreやbandit optimizerをcomparison evidenceより先に作らない。
- schedulerをnatural routing evidenceより先にenableしない。

次のmilestoneはtask corpus expansionではなく、**Multi-agent Decision & Outcome Evidence**である。
