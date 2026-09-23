# Grok 4.6 / Claude Opus 5 cross-provider synthesis

Date: 2026-08-26

## 0. Outcome

二つの独立reviewは、現在のcollaboration guidanceが方向としては正しい一方、**観測前に人数、round、variant数、blindness、mode構成を典型値として固定しすぎた**という点で一致しました。

ゼロベースで残す核は次です。

```text
何を得たいか（value mechanism）
  -> 今回最初に尽きる制約は何か（binding constraint）
  -> 最も安い関係形を選ぶ（mode）
  -> workspace / permissionを選ぶ（lane）
  -> 時間上の起動形を選ぶ（lifecycle）
  -> evidence / acceptance / authority / budgetで止める
  -> primaryがsynthesisし、結果からproject-local priorを更新する
```

「通常何人」「通常何round」をglobal policyにしません。安全上のinvariant、runawayを止めるcost cap、計画用の暫定prior、未検証hypothesisを明示的に区別します。

> Zero-input correction: 当初の「manual episode記録が続いてからledgerを作る」という順序は、ユーザーが記録する前提を置いていたため棄却しました。客観的なepisode factsはhook / `agentctl` eventから自動生成し、semantic fieldはprimaryが通常作業中に生成するか、観測不能なら`unknown`にします。

## 1. Review method and limits

- Grok 4.6とClaude Opus 5へ同じbriefと同じbase commitを渡した。
- 別worktreeと別output directoryを使い、互いのreviewを見せなかった。
- web search、nested agent、source変更を許可しなかった。
- 各providerへ5文書を要求した。
- Grokはheadless file-write contractが安定せず、最終的にstructured outputをprimaryがprovider directoryへ保存した。
- Opus 5は一括5文書がwall-time capへ達したため、残成果を小さく分割し、最後の文書はstructured outputとして保存した。

この実行自体が一つの観測です。大きな複合成果物を一agent runへ固定すると、model能力よりtool contractとwall-timeが先に尽きる場合があります。ただしepisodeは一件だけで、一般的な最適分割数や時間は導けません。

## 2. Strong agreement

| topic | Grok 4.6 | Opus 5 | primary decision |
|---|---|---|---|
| 人数・round・variant数 | global optimumはない | priorとtermination mechanismを分離 | 固定defaultをauthoritative docsから外す |
| multi-agent value | 人数ではなくmechanismの発火 | M1–M7の成立条件として分解 | mechanism-firstを採用 |
| solo | 小さく明確なら標準 | serialization costがtask cost以上ならsolo | soloを失敗扱いしない |
| human review | first-class cost | binding constraintになりやすい中心cost | planへ明示fieldを追加 |
| blind advice | anchoring対策の一手法 | delegation可否と目的に依存 | independence policyを選択式にする |
| dialogue stop | evidence delta / acceptance / budget | claim変化、crux、authority、budget | round数でなく停止条件で制御 |
| variants | verifierと事前rubricなしでは浪費 | verifier能力を先に検証 | harnessは実証まで作らない |
| provider diversity | model数は品質指標でない | evaluator側で価値が出る仮説 | project実験までdefaultにしない |
| control plane | conversationを所有しない | structural stateだけ所有 | ADR-0001を維持 |
| recurring | permanent agentでなくfinite jobs | trigger + finite job + bounded carry-over | 維持。runtime未実装を明記 |
| scheduler timing | 手動点検の価値を先に確認 | non-agent CI / cronで足りないことを先に実証 | scheduler実装を延期 |
| observation | content-free episodeが必要 | episode + slot-seconds + human review | zero-input hook / agentctl factsから開始し、semantic欠測はunknown |

## 3. Where the reviews differ

### 3.1 Mode taxonomy

Grokは`solo / parallel / advice / review / variants / recurring`の6分類を提案しました。Opusは`solo / delegate / consult / compete / verify`の5 modeと、別軸のlifecycleを提案しました。

primary判断はOpus寄りです。`recurring`はagent同士の関係ではなく時間上の起動形だからです。ただし5という数を正解にしません。これらは現在の概念を重複なく説明するaliasであり、projectが新しい関係形を必要とすれば拡張できます。

### 3.2 Detailed termination rules

Opusは10 termination ruleを列挙しました。catalogとして価値がありますが、すべてを毎回checklist化するとbrief serialization costが増えます。canonical guidanceでは次へ縮約します。

- acceptance / decisive evidenceを得た。
- new evidence、claim status、artifact valueが増えない。
- disagreementがuser preference / authorityへ到達した。
- scope / safety / hard cost capへ到達した。
- 残る期待利益よりcoordination costが高い。

必要なprojectだけ詳細ruleを採用します。

### 3.3 New fixed values inside the reviews

reviewer自身も、`一phaseでmodeは二つまで`、`claimを二回再提示したら停止`、特定期間やepisode数などの値を提案しています。これらは有用なpilot hypothesisになり得ますが、global invariantではありません。

採用する場合は必ず次を付けます。

```text
parameter role: hard guard | cost cap | planning prior | hypothesis
scope
rationale
invalidation evidence
update owner
```

### 3.4 Held-out verification

Opusはvariantへ非開示のheld-out checkとrubric weightを提案しました。過適合検出には有力ですが、hidden requirementや評価の後出しにもなり得ます。現時点では採用しません。

- まず既存の明示acceptanceだけでvariant比較が本当に有益かを測る。
- held-outを使うなら、明示acceptanceと同じ性質のcheckだけにする。
- task/result schema v1を変えずsidecarにする。
- verifierが過去結果を識別できることを先に確認する。

### 3.5 Capacity as participant count

Opusはcurrent capacity limitから参加者数を制約する案を出しました。capacityは同時実行可能数とwall-clock予測には使えますが、価値ある観点数そのものではありません。queueで複数waveに分けてもcoverageが必要な場合があります。

canonical ruleは「capacityを超えた分は並列ではなくwaveになると明示し、time / quota / human-review costへ算入する」です。capacity値を推奨人数へ変換しません。

## 4. Adaptive model

### 4.1 Value mechanisms

複数agentを使う理由は、少なくとも次のどれかとして説明します。IDや数は固定schemaではなく、説明語彙です。

- independent workのwall-clock overlap
- contextを狭く分けることによる制約保持
- search / option / evidence coverage
- makerとcheckerのerror decorrelation
- test / measurementによるcandidate selection
- critiqueにより新しいevidenceや反証を生むこと
- time / eventをまたぐdrift sampling

`why_multi_agent`が「agentを使いたい」しか書けない場合はsoloへ戻します。

### 4.2 Binding constraints

modeより先に、今回最初に尽きるものを確認します。

- primary / human review capacity
- wall-clock and waiting tolerance
- provider quota / rate window
- agentctl resource capacity and queue
- brief serialization cost
- integration / rework cost
- context coupling
- evaluator availability
- late failure cost

たとえばhuman reviewが律速なら、生成artifactを増やすfan-outやcompeteより、consultやverifyを優先する可能性があります。

### 4.3 Relationship modes and lifecycle

| relation | meaning |
|---|---|
| `solo` | primaryが直接行う |
| `delegate` | bounded artifactを一つ以上のworkerへ割り当てる。fan-outとpipelineを含む |
| `consult` | option、assumption、critique、evidenceを集め、必要なら交換する |
| `compete` | 分岐したcandidateを同じ評価契約で比較する |
| `verify` | fixed artifactをneutralまたはadversarialに独立検査する |

| lifecycle | meaning |
|---|---|
| `one-shot` | 一回でterminal |
| `bounded-exchange` | evidenceが増える間だけinteractionを継続 |
| `event-triggered` | local / external eventごとにfinite jobを評価 |
| `scheduled` | external driftや履歴集計を有限intervalで評価 |

mode数をKPIや制限値にしません。既存の12 mode名と60 patternはidea catalogとして残し、上のrelation / lifecycleへ対応づけます。

### 4.4 Participant derivation

人数を先に決めません。

- delegate: 独立shard / stage / artifactの数から導く。
- consult: 固有の観点、evidence source、失敗様式から導く。
- compete: 実質的に異なるapproachと安価なevaluatorから導く。
- verify: 独立させたいerror modeやprobe面から導く。

その後、capacity、quota、wall-clock、human reviewで実行可能数とwaveを調整します。追加participantが固有の価値を説明できなければ増やしません。

### 4.5 Interaction continuation

各interaction後、primaryは次を判断します。

```text
new evidence / test / claim transition / useful artifact が増えたか
  yes -> 残budgetと期待利益があるなら継続候補
  no  -> 停止

disagreementはtestで解けるか
  yes -> dialogueよりtestを優先
  no  -> user preference / authorityなら返す
```

round数は観測結果です。hard cost capは必須ですが、その値はproject / task / provider / milestoneごとに理由を持たせます。

### 4.6 Independence policy

blindを無条件defaultにしません。

- anchoringを避けたいoption enumerationで独立agentが使える: isolated-blind候補。
- coverageが目的: context / evidence sourceをpartitionする。
- fixed artifactのreview: artifactは共有し、makerの試行軌跡やprimaryの選好は共有しない。
- interfaceの事実確認: shared context / direct peerを許せる場合がある。
- delegation不可: blind independenceやcontext分割の価値を得たとは主張しない。

## 5. Recurring work

### 5.1 Start with the trigger question

- repository commitが原因ならevent-triggeredを先に検討する。
- external driftや履歴累積ならscheduled候補。
- CI、deterministic script、通常cronで足りるならagent schedulerを作らない。

### 5.2 Hard invariants vs adaptive parameters

hard invariant候補:

- finite jobだけを発行する。
- schedule creationとenableを分離する。
- enable / circuit / budget stateをjob worktree外へ置く。
- safe permission以外をrecurring emitterから暗黙選択しない。
- same input / active runを重複発行しない。
- every trigger evaluationをcontent-free auditへ残す。
- agent自身がschedule、quota、permission、circuitを変更しない。
- control planeからmerge、push、releaseを提供しない。
- expiry / owner / kill pathを持たないscheduleをenableしない。

adaptive parameter候補:

- interval / event filter
- expiry duration
- wall time / attempt / usage cap
- backoff / circuit threshold
- retention / notification threshold
- recurring capacity share
- carry-over staleness

parameter値はproject-localにし、rationale、scope、invalidation、ownerを付けます。

### 5.3 Missing mechanisms worth preserving

- input digest gating: base / template / lock / feed cursor等が同じならjobを発行しない。
- `run_status`と`findings`を分け、finding検出をfailureとしてcircuitへ入れない。
- finding stateのnew / changed / resolvedだけ通知し、unchangedはauditだけにする。
- missed runはsnapshot checkとcursor/event checkで扱いを分ける。
- recurring workはinteractive workをstarveさせないadmission policyを持つ。

これらはschedulerを実装する場合のrequirementであり、現時点の実装claimではありません。

## 6. What to build now

### Adopt now

1. authoritative docsから未検証のglobal fixed countを除去する。
2. modeとlifecycleを分離し、relation vocabularyを簡素化する。
3. collaboration planへvalue mechanism、binding constraint、independence policy、human review budget、parameter role、invalidation、stop reasonを追加する。
4. first-round blindnessをcontext-dependent choiceへ変更する。
5. claim / advice / variantの軽いMarkdown contractを用意する。
6. validatorで上記のauthoritative guidanceが欠落・regressしないことを確認する。

### Observe automatically before adding analysis machinery

- content-free episode record
- solo / collaborationのtime-to-accepted-result
- human review bucket
- decisive evidence kind
- rework / conflict
- actual participants / exchanges / stop reason

人間へ入力を求めません。provider hook / `agentctl` eventから取得できるfieldは自動保存し、hookだけでは分からないsemantic fieldを推測しません。fieldの有用性は自動ledgerを後から分析して判断します。

### Build only behind evidence gates

- semantic annotation / episode analysis helper: reliableなsession correlationと、routing判断を変えるuse caseを確認した後。
- slot-seconds report: resource costがroutingに必要と確認した後。
- compete harness: evaluatorが過去candidateの優劣を識別できた後。
- held-out sidecar:fixture維持可能性を確認した後。
- scheduler: manual recurringまたはnon-agent automationでは足りないuse caseを示した後。
- recurring Lane W: read-only recurringのfindingが実際にtriageされた後。

### Do not build

- conversation graph / universal message bus in `agentctl`
- transcript / private reasoning store
- automatic consensus / winner / hybrid generation
- agent-count or round-count optimizer before observations exist
- auto merge / push / release from recurring work
- untrusted recurring execution before Lane I exists

## 7. Roadmap

### R0: correction and lightweight contracts

- canonical docsとtemplateをadaptive modelへ更新する。
- raw provider reviewsとcross-provider synthesisをtempへ保存する。
- validatorを更新する。

### R1: zero-input observation

- 実project taskのcontent-free episode factsをprovider hook / `agentctl` eventから自動記録する。
- projectごとのtask classとbinding constraintを学ぶ。
- no global sample countを設定せず、decisionを変えるだけのcoverageが得られるまで試す。

### R2: smallest reusable helper

- automatic observationでrouting判断に使われたfieldだけをoptional analysis helperへ昇格する。
- helperはcontent-free、project-local、削除可能にする。
- task/result schema v1を変えない。

### R3: conditional experiment tooling

- reviewer decorrelation、evaluator strength、compete costなど、対応toolのgateとなる実験だけ行う。
- negative resultを「作らない」判断として受け入れる。

### R4: conditional recurring runtime

- non-agent alternative、manual value、owner、digest、budget、audit、fault injectionが揃った場合だけread-only pilotを作る。
- Lane WやMira UIはさらに後段。

## 8. First episode lesson

今回のGrok / Opus reviewは次を示しました。

- 参加者数2は最適値ではなく、ユーザーが指定した独立providerの集合から導かれた。
- five-doc bundleは両providerで一run完了しなかった。成果物を小さく分割すると回収できた。
- Grokのfilesystem tool contractとOpusのwall-timeが異なるbinding constraintになった。
- structured resultとprimary persistenceはprovider差を吸収した。
- 人間のsynthesisは依然critical pathである。

この一件から人数や時間のpriorを作りません。再現するproject taskで観測を続けます。

## 9. Primary decision

実装を急ぐ対象はschedulerやdebate engineではありません。まず誤った固定値を外し、projectが自分の有効なcollaboration形を学べるcontractを渡します。

事前toolingの役目は最適値を決めることではなく、次を可能にすることです。

- safe boundaryを越えない。
- parameterの意味と根拠を忘れない。
- costとoutcomeをcontent-freeに振り返れる。
- negative evidenceにより機能を作らない判断ができる。
- projectが学んだpriorをglobal truthへ誤昇格させない。

## 10. Zero-input implementation correction

人間はcollaboration telemetryを入力・保守しない前提へ変更しました。

- solo / delegated / managed-job episodeを同じcontent-free schemaで自動保存する。
- duration、worker start / stop、peak concurrency、worker slot time、structured test outcome、rework、post-worker-tail、hook coverageを記録する。
- prompt、response、command、path、raw ID、private reasoningは保存しない。
- relation、mechanism、binding constraint、quality、actual human-review timeはhook topologyから推測しない。
- primaryのplan / synthesisはagent-owned artifactであり、ユーザーへform入力を求めない。
- automatic ledgerのretention値はstorage cost capであり、必要なepisode数や品質最適値ではない。

これにより「manual recordingが続くこと」はtooling gateから外れました。次のgateは、automatic dataのどのfieldが実際にrouting判断を変えたかです。
