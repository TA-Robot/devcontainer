# 03. 実験dimensionと比較構成

## 1. 目的

時間atlasには「taskがMだった」だけでなく、どう実行したMなのかが必要です。ここでは時間を変え得るdimensionを列挙し、何を固定し、何を比較変数として動かすかを定義します。

最終的な出力はselection ruleではなく、次のような観測cellです。

```text
F03 diagnosis / M-coupled-deterministic-python
  × primary-only
  × Codex <resolved-or-alias identity> / applied <provider-specific setting>
  × agentctl execution surface / automatic permission
  × fresh context
  × warm repository cache
  × no competing load
  = observed duration distribution
```

## 2. Task envelopeとして固定するもの

同じcaseを構成間で比較するとき、次をimmutableにします。

- task capsule revisionとdigest
- base repository snapshot digest
- visible contextとreference docs
- allowed/forbidden path・tool・side effect
- acceptance commandとtimeout semantics
- expected artifact schema
- laneとisolation boundary
- gold/evaluator revision
- global safety capの役割

prompt wordingの変更はcase revisionです。途中で説明を足したrunを同じseriesへ混ぜません。

## 3. Collaboration configuration

構成名は価値判断ではなく、実行形を識別するためのlabelです。

### C0: primary-only

一つのprimary agentが調査、実装、validation、最終結果まで行います。multi-agent構成の比較元ですが、常に最良という意味ではありません。

### C1: bounded delegation

primaryが一つの明確なsubtaskをworkerへ渡し、そのartifactを統合します。dispatch、worker、synthesisを分離して測る最小delegation形です。

### CP: parallel shards

自然に独立なshardへ分けられるtaskを並行実行します。participant widthはpolicyとして固定せず、次を満たす範囲で観測curveを作ります。

- shard数以上のworkerを投入しない
- current runtimeが安全に提供するwidthを超えない
- widthごとにexact worker countとpeak concurrencyを記録する
- `solo -> 1 worker -> ... -> safe width`の未測定点を明示する

worker数は実験変数であり、「3 agentが良い」というdefaultではありません。同じtaskを幅別に測ることで、dispatch/queue/synthesisが増える様子そのものをreferenceにします。

### CC: independent candidates

同じ問題へ独立したanalysisまたはimplementation candidateを作ります。独立性を保つため、candidate作成中は互いのartifactを見せません。最後の比較・validation時間を別計測します。

### CV: maker + verifier

makerの結果を、別contextのverifierがtest、counterexample、contract checkで検証します。verifierへgoldは渡さず、検証方法だけを渡します。

### CD: bounded evidence dialogue

agent同士がclaim、critique、evidence、revisionを交換します。round数を事前defaultにせず、各exchangeを独立timing eventとして残します。

```text
proposal -> critique -> evidence request -> test/result -> revision -> unresolved crux
```

継続条件は「新規evidenceを取り得る未解決claimがある」、停止条件は「acceptance判定可能」「新規evidenceなし」「task-specific safety cap」のいずれかです。最終atlasは1回目、2回目、以後の**実際に発生したincremental time**を表示するため、project側は自分で必要なdepthを見積もれます。

### CS: staged pipeline

調査、実装、test、reviewなどを異なるroleへ順番に渡します。handoffの待ちとcontext再構築が見えるため、並列化できない協働の時間referenceになります。

## 4. Provider / model identity / generation settings

provider名やmodel aliasだけで束ねません。identity、generation setting、runtimeを分離します。

```text
modelIdentity:
  requestedAlias
  requestedSource: flag | config-file | runtime-default | unknown
  resolvedId
  identityConfidence: exact | alias-only | default-unspecified | unknown
  snapshotHint

generationSettings:
  requested[]
  applied[]
  unsupported[]
  ignoredOrUnknown[]
  capabilityStatus: supported | rejected | not-advertised | unknown

runtimeIdentity:
  provider / cliName / cliVersion / cliSource
  imageDigest / executionSurface / permissionMode / observedAt
```

`requested effort=high`は`applied effort=high`の証拠ではありません。CLIがrejectした設定はcapability結果、受理してもappliedを確認できない設定はdiagnostic-onlyです。requested値だけでduration stratumを作りません。

provider固有settingを一つの共通`low/medium/high`へ畳みません。Codex reasoning effort、Claude thinking、Grok reasoning effortはnamespace付きで保持し、同じprovider/model/setting内だけを直接比較します。cross-providerでは各構成を並置しますが「同一effort」とは呼びません。

### Capability/identity probe

duration runの前にprovider × CLI buildごとに次をprobeします。

- implicit defaultとexplicit model alias
- CLI/eventがresolved IDやsnapshot hintを返すか
- advertised generation settingとaccepted value
- reject、silent/unknown、applied-confirmedの区別
- progress envelope、permission mode、execution surface

probe失敗時間はtask duration cellへ入れません。2026-08-26時点のlocal Grok CLI 1.0.5は`grok-4.6`（default）と`grok-4.5`を列挙し、`--reasoning-effort` surfaceを持ちますが、それだけでは実際に適用されたeffortを証明しません。

### Series boundary

同一seriesには少なくとも次を要求します。

```text
provider
+ exact resolvedId、または alias/default + observation window
+ canonical applied settings
+ CLI version/source
+ execution surface
+ permission mode
```

exact identityとalias-onlyをpoolしません。CLI versionだけではserver-side driftを識別できないため、resolved identity変化、CLI変化、または同一cellのdistribution shiftを`stale candidate`として新seriesを開始します。旧seriesは削除しません。

観測候補は次です。

- same-provider primary/worker
- Codex、Claude、Grokそれぞれのprimary-only
- cross-provider delegation
- cross-provider independent candidates
- cross-provider verifier

全provider × 全model × 全setting × 全case × 全構成を総当たりしません。未測定cellはそのまま残し、provider間の総合順位を出しません。

## 5. Context dimension

### Fresh context

新しいsessionでtask capsuleだけを渡します。構成間のcontrolled comparisonの基本です。

### Warm task context

同じprojectで直前の作業historyを持つsessionへ依頼します。現実の継続開発に近い一方、history内容が条件になります。

### Warm repository familiarity

同じagent/sessionが別taskでrepositoryを既に探索しています。task historyとrepository familiarityを区別して記録します。

warm条件をfreshの再試行として混ぜません。引き継いだcontextのdigestまたはsession relationを残し、prompt本文はanalytic ledgerへ保存しません。

auto compaction/summarizationの発生とcontext-window occupancyが安全に観測できる場合はdiagnosticとして残します。観測できなければ`unknown`です。初期controlled comparisonはfresh contextだけを因果比較に使い、warm replayはhistory digestの再現方法を作ってから別seriesにします。

## 6. Environment/cache dimension

- container fresh build / restarted / long-lived
- dependency cache cold / warm / unknown
- repository index/cache cold / warm / unknown
- Docker image cold / warm / not-used
- provider prompt cache hit / miss / unknown（repository cacheと分離）
- network required / not-required
- machine CPU/memory class
- concurrent interactive workload
- provider queue/rate-limit signal
- time window and timezone
- pre-T0 provisioning: worktree/image/cache restoreの開始・ready
- auto-injected instruction set digest: AGENTS/CLAUDE/persona/skills/MCPなど本文を保存しないdigest

cacheを完全に消す操作は破壊的になり得るため、専用temporary cacheまたはfresh disposable environmentで行います。shared host cacheの全削除はしません。

## 7. Task property dimension

S/M/Lとは別に、以下の代表点を取ります。

| Axis | Values |
| --- | --- |
| ambiguity | exact / bounded-open / open |
| oracle | deterministic / structured / calibrated / weak |
| decomposability | serial / partial / independent |
| risk | low / medium / high |
| artifact | answer / findings / patch / test / design / runbook |
| lane | read / write / isolated |
| source | fixture / historical replay / natural live |
| knowledge | repo-only / provided-docs / current external info |
| language/toolchain | Python / Bash / JavaScript / Markdown / Docker / cross-stack |
| execution surface | direct provider / agentctl job / legacy comparator |
| permission | automatic / approval-gated / unknown |

同じdimensionを可能な限り一度に一つ動かします。ただしlive taskでは完全固定できないため、controlled seriesとnatural seriesを分離します。approval待ちは人間の反応時間を混ぜるため、controlled user-wait sampleはautomatic permissionだけを採用し、検出したapproval-gated runは`contaminated`またはinvalidとして別表示します。

## 8. Dimension role classification

full factorialを避けつつ、重要な交絡を潰すために役割を分けます。

### Primary stratum

- task family + size profile（oracle/coupling/validationを含む）
- collaboration relation class
- model identity series + applied generation settings
- execution surface
- session class
- fixture / historical / natural source series
- progress artifact resolution

### Blocking factor / covariate

- language/toolchain、ambiguity、decomposability、artifact/lane
- knowledge locality、expected failure mode、repository scale/index state
- dependency/repository/Docker cache、time window、machine/load
- provider CLI/image identity、permission mode

比較blockでは固定し、spreadがplanning resolutionを超えたときだけ別profileへのsplitを検討します。

### Diagnostic-only

- token/output/tool-call count
- providerが出す場合だけのthinking/tool/queue breakdown
- compaction/context occupancy
- auto-injected instruction digest
- provider prompt cacheが未確認の場合のsignal
- approval wait interval、clock anomaly、harness overhead
- nested worker detection、residual Docker/disk

diagnosticをproductivity KPIや意味推定へ使いません。

## 9. Comparison block

構成差を見るunitは同じcase revisionのpaired blockです。

```text
block ID
  - same task capsule and base snapshot
  - configuration A
  - configuration B
  - execution order rotated/randomized
  - fresh isolated session per run unless warm is the treatment
  - same model identity series and applied generation settings unless that is the treatment
  - same execution surface, permission mode, and instruction digest
```

順序を固定すると、cache warm-up、provider混雑、rate window、machine loadが後の構成へ偏ります。block内の順番をrotateし、開始時のenvironment stateを記録します。

## 10. Full factorialにしない

36 candidate task × size profile × provider/model/setting × collaboration × width × context × cache × load ×反復を総当たりすると、時間もrate windowも無制限に消費します。代わりに次の順でcoverageを増やします。

1. task family/size-profileごとのprimary-only時間を広く薄く観測
2. run varianceとcase varianceが大きいcellを追加観測
3. collaboration構成は、その形を実際に成立させるdecomposability/ambiguityのcaseへ割り当てる
4. provider差はtask familyを代表するblockへ追加する
5. context/cache/loadは基準cellで一軸ずつ測る
6. 未測定cellを補間せず、価値の高い穴だけ次waveで埋める

ここでいう「価値」はrouting recommendationではなく、atlas利用者が見積り時に遭遇しやすい条件をどれだけ覆えるかです。

worker widthとdialogue exchange depthはprimary stratumを無限に増やさず、同一configuration card内のcurveとして表現します。

## 11. Fairな時間比較の二つのview

### User-wait view

requestからuser-visible resultまでのwall-clockをそのまま比べます。後段のoffline score runtimeは足しません。quality-conditioned viewではoffline passしたrunの同じuser-wait durationを抽出します。並列workerが多くても、利用者が待つ時間という意味では公平です。

### Resource-time view

aggregate worker time、primary active tail、container/runtime占有時間を比べます。wall-clockが短い代わりに大量のworker時間を使ったことを隠しません。

どちらかへscore化せず、両方を併記します。subscriptionでper-call課金がなくても、rate window、concurrency slot、対話可能時間は有限です。

## 12. Nested delegation、retryとfailure

初期controlled studyではworkerのnested delegationを無効化します。検出したrunは`nested-worker-untracked`としてduration breakdownの信頼度を落とし、flat構成とpoolしません。nested topology自体を測る段階では、全descendant eventを相関できるsurfaceだけを使います。

- 自動retryは別attemptとして記録する
- provider failureを同じrunから消さない
- harness retry、provider internal retry、tool再実行、agent自己再試行を区別し、観測できないinternal retryは`unknown`にする
- retry込みのuser-waitと、successful attemptだけのactive timeを両方出す
- global timeout到達は`right-censored`または`timeout`であり、成功sampleではない
- task説明不足、fixture破損、gold leakageは`invalid`として理由を残す
- 「遅かったのでやり直す」は許可せず、protocolで定めた条件だけretryする
