# 05. Sampling、推定精度、analysis

## 1. 時間目安には二種類のばらつきがある

同じpromptを何度も投げるだけでは、次のprojectで別taskを頼んだときの時間帯を説明できません。

### Within-case variance

同じcase revision・構成でも変わる時間です。

- provider generation variance
- queue/rate window/network
- tool/cache状態
- nondeterministic agent path
- machine load

### Between-case variance

同じfamily/sizeでも題材を変えると生じる時間差です。

- 原因箇所を早く発見できるか
- repository layout
- test setup
- hidden coupling
- artifactの書きやすさ

atlasではこの二つをnested structureとして推定します。全runを平らに混ぜたmedianだけは表示しません。

## 2. Sampling unit

- `run`: 一回の実行attempt
- `case`: exact task capsule + snapshot + oracle revision
- `cell`: family + size/profile + configuration + environment class
- `series`: model identity confidence/resolved-or-alias key、applied setting、CLI/runtime surface、permission mode、観測期間を固定したcell群

case revision、resolved identity、applied setting、CLI/runtime surfaceが変わったら新seriesです。alias-only/default-unspecifiedは観測windowもseries keyに含めます。旧seriesは消さず`stale`またはhistoricalとして残します。

## 3. 固定反復回数をglobal defaultにしない

taskによってvarianceも一回の所要時間も違います。全cellを機械的に同じ回数だけ回すと、安定した短時間taskを過剰測定し、ばらつくL taskを過少測定します。

代わりにstudy manifestで次を宣言します。

- `planningResolution`: atlasで区別したい時間差。例: 2分、10分、30分
- `relativePrecisionTarget`: central estimateに対する許容不確実性
- `coverageTarget`: family内で覆うdescriptor/variant範囲
- `wallClockBatchCap`: 一batchの有限上限
- `rateWindowCap`: providerごとの有限上限
- `hardSampleCap`: runaway防止。統計上の推奨回数ではない

追加sampleは、推定幅を実際に狭めるcellへ割り当てます。hard capに達しても精度不足なら、無理に確定値を出さず`family-provisional`のままです。

## 4. Sequential sampling flow

### Step A: breadth observation

各candidate profileをまず一度観測し、clock coverage、task validity、桁、failure classを得ます。この段階の値は`single-observation`です。12×S/M/Lの見かけの枠を埋めても、未測定profileが残る限りcoverage完了とは呼びません。

### Step B: same-case repeat

同一caseをfresh sessionで再実行し、within-case varianceを見ます。追加run後にcentral estimateとspreadがどれだけ動いたかを記録します。

### Step C: case variants

同じfamily/size/profileへisomorphic variantを足し、between-case varianceを測ります。単一caseが安定していても、variant間差が大きければ継続します。

### Step D: uncertainty-directed sampling

次のいずれかなら追加sampleの情報価値があります。

- central intervalがplanning resolutionより広い
- slow/failure tailの存在は見えたが頻度が不明
- within-caseとbetween-caseのどちらが支配的か判別できない
- cold/warm、provider、構成差と時間帯効果が交絡している
- sampleが一つのcaseまたは一つの観測windowへ偏っている

次のいずれかならそのcellのsamplingを止められます。

- 宣言したprecision/descriptor coverageへ到達し、case偏りと観測window偏りがない
- 新sampleによるinterval更新がplanning resolution未満で、かつdistinct case多様性とwindow coverageを満たす
- hard batch/rate/time capに到達した
- case/evaluatorがinvalidと判明した
- model/CLI更新でseries継続が不適切になった

停止は「十分速い/遅いと判断した」からではなく、referenceの精度または安全capによります。

`family-provisional`には複数のisomorphic caseが必要です。`family-characterized`にはwithin-caseとbetween-caseの両方、複数観測block、valid identity/settings、必要landmark coverageが必要です。具体的なcase/run数はstudyのprecision/coverage設計で決め、universal defaultにしません。単一easy caseの反復だけではstateを昇格しません。

## 5. 具体的な表示統計

### Low sample

- 全durationを時系列で表示
- minimum / median / maximumは補助表示
- failure、timeoutを個別表示
- quantileやconfidenceを無理に作らない

### Characterized sample

- within-case medianとspread
- case別medianのdistribution
- family-level central estimate
- central prediction band
- estimate uncertainty interval
- failure/timeout empirical rateとuncertainty
- cold/warm、fresh/warmなどstratum別表

family-level推定はhierarchical bootstrapまたは同等のcase-aware手法を使い、run数が多い一caseに全体が支配されないようにします。採用method、seed、tool versionをaggregateへ記録します。

## 6. 「○分くらい」の作り方

人間が計画へ使える形として、machine dataのexact secondsと、evidence stateに応じて丸めたhumanized bandを分けます。

```text
quality-pass user-result typical:   10–20 min
censoring-aware user wait:           2/17 unfinished at the declared cap
first-valid-artifact typical:        5–10 min (progress-observed series only)
observed full range:                 raw samples linked separately
case/run/censor coverage:            6 / 17 / 2
identity/settings/surface:           alias-only / applied=<value> / agentctl
observation window:                  <start>..<end>
environment:                         fresh context, warm deps, no load
evidence state:                      family-provisional
```

`quality-pass`は`04` §2のcanonical規則（online failは除外、offline pass/failを優先、offline不在のstrong online oracleだけonline passを使用）に固定します。onlineが`unavailable`でもoffline passは対象にできます。両方で判定不能ならquality bandへ入りません。

`typical`のquantile範囲は各studyのreport schemaで明記します。provisional/characterizedの表示桁は`planningResolution`へ丸め、central secondsはmachine JSONにだけ置きます。`single-observation`にはbandを出しません。display roundingは元dataを変えません。観測のないtaskを「たぶん同じ」と補完しません。

## 7. p95とtail

p95はplanningで魅力的ですが、少数runではほぼ最大値の言い換えになります。

- methodが要求するsample adequacyを満たすまでp95を出さない
- 出す場合もconfidence intervalを併記する
- それ以前はobserved maximum、timeout count、slow-run一覧を使う
- provider incidentやrate limitは通常varianceと別tagでも表示する
- long-running taskのtimeoutはsurvival/censoring-aware summaryで扱う

legacy benchmarkの「5回でp95」を今回のlive seriesへ適用しません。

## 8. Paired comparisonの表示

同じcase blockで構成A/Bを測った場合、absolute timeに加えてpaired deltaを出せます。

```text
case          A user-time  B user-time  B-A wall clock   B-A worker time   quality/outcome
F03-M-004       ...          ...             ...              ...
```

ただし`faster`, `winner`, `recommended`を自動付与しません。quality/outcomeが異なる場合は時間差を単独で解釈できないため、必ず隣に表示します。

## 9. Dialogueのincremental analysis

対話は最終durationだけでなく、exchange curveを出します。

| Exchange | Incremental wall time | Contract-valid evidence | Claim state changes | Cumulative time |
| --- | ---: | --- | ---: | ---: |
| proposal | observed | n/a | observed | observed |
| critique | observed | yes/no | observed | observed |
| evidence/test | observed | yes/no | observed | observed |
| revision | observed | yes/no | observed | observed |

これによりprojectは「2往復が正解」というruleではなく、過去の類似taskで各追加exchangeが何分かかり、versioned family contract上で何が増えたかを見られます。人間にとってdecisive/usefulだったかは自動推測しません。

## 10. Quality-conditioned duration

最低でも次を分けます。

- canonical `qualityPass=true` runのuser-result wall time（offline scoring runtimeは除外）
- failed runのtime-to-terminal
- retryを含むend-to-end recovery time
- progressを観測できたrunのtime-to-first-valid-artifact

attempt-level durationと複数attemptを含むrecovery durationを同じtypicalへpoolしません。fast failureをfast completionへ数えず、高品質構成と低品質構成の時間を一つに混ぜません。

## 11. Biasとthreats to validity

### Case selection bias

測りやすいunit taskだけを選ばないよう、12 familyとsource type coverageを公開します。

### Survivor bias

accepted runだけの時間表と全outcome表を併記します。

### Prompt tuning leakage

結果を見てpromptを直したらcase revisionを上げ、旧runを残します。

### Gold/future leakage

historical future commit、gold patch、seed scriptをagent workspaceから隔離します。

### Cache/order bias

paired blockの順序をrotateし、cache/contextをstratifyします。

### Provider non-stationarity

resolved model IDがあればそれを使い、alias-onlyならalias + CLI/runtime +観測windowでseriesを区切ります。requested effortとapplied effortを混ぜません。同一control cellのdistribution shiftがplanning resolutionを超えた場合は`stale candidate` diagnosticを出し、旧seriesと自動poolしません。

### Instrumentation bias

harnessだけのdeterministic no-op/fixtureでclock overheadを先に測ります。

### Evaluator bias

known-good、known-bad、ambiguousを区別できないjudgeを使いません。

### Natural-task confounding

catalog annotationのないlive backlog観測はfamily/size reference rangeへ含めません。opaque timing/outcome seriesとして外的妥当性の候補を探し、machine annotationが導入された後でも構成差の因果結論はpaired controlled seriesからだけ出します。

### Execution-surface double counting

harness outer runをuser-waitの正本にし、相関したdirect provider episodeや`agentctl` outer/jobを別sampleとして足しません。directと`agentctl`は別seriesです。component episodeはworker/queue breakdownにだけ使います。

### Instruction/permission contamination

auto-injected instruction set digest、permission mode、compaction detectionを残します。approval待ちを含むrunはautomatic-permission seriesへ混ぜず、観測不能なら`unknown`です。

## 12. Aggregate禁止事項

- languageもartifactも違う全taskの総平均
- agent event数をproductivityへ変換
- worker数で割った「一人当たり速度」
- failureを除外したprovider ranking
- requested effortをapplied effortとみなした比較
- offline evaluator runtimeをuser-waitへ加えた比較
- progressのないfinal時刻をfirst artifactへ補完すること
- uncertaintyを隠した単一分数score
- subscriptionに金銭課金がないことを、rate/time/capacity costがゼロという意味にすること
