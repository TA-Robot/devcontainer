# 07. Implementation roadmap

Implementation update: 2026-08-26にMilestone Aのschema/clock/fake runner、Wave 0.5の非生成provider capability probe、Milestone Bのinitial S/M/L isolated fixtureを完了。詳細は`15`、`16`、`17-milestone-b-case-fixtures.md`。以下はroadmap全体として残します。

## 1. 現在地

既にあるもの:

- `agentctl` job/attempt lifecycleとvalidation evidence
- provider hookからのcontent-free collaboration episode
- persistent observation volume
- deterministic wrapper/control-plane benchmark
- native task/result contract、read/write/isolated lane
- duration studyのstudy / run schema v1、case/capability schema v2
- deterministic monotonic fake clock、derived duration validator、immutable run write
- Codex / Claude / Grokのpassive version/help/catalog adapter
- bounded implementation S/M/L case catalog、capsule、disposable one-commit Git builder
- harness-only hidden evaluatorとknown-bad/good calibration

不足しているもの:

- 12 familyへ広げたversioned task case catalog contents（initial F04 S/M/Lだけ実装）
- study/run/config correlation
- live providerからのT2/T4/V0/V1/T6/TX capture
- task実行時のresolved model identity confidenceとrequested/applied generation setting capture
- execution surface、permission mode、instruction/compaction diagnostic
- case-specific quality oracle
- adaptive sampling state
- duration atlas generator
- safe finite batch controller

このため、いきなりlive agentを大量実行すると、終端時間しか分からない低価値dataが溜まります。先に薄いstudy control layerを作ります。

## 2. Proposed repository shape

実装時の候補です。正本化前に命名・scopeを再確認します。

```text
experiments/multi-agent-duration/
  schemas/
    study.schema.json
    case.schema.json
    run.schema.json
    capability.schema.json
  catalog/
    cases.json
    configurations.json
  evaluators/
    <family-specific metadata>

scripts/
  agent-duration-study
  agent_duration_study.py
  report-agent-duration-atlas.py
  test-agent-duration-study.py

/var/lib/mira-observations/duration-atlas/
  studies/<study-id>/manifest.json
  runs/<study-id>/<run-id>.json
  artifacts/<study-id>/<run-id>/...   # separate retention and permissions
```

このrepositoryへsample appを追加しません。fixture sourceはgenerator、small Git bundle、またはtemporary repo recipeとして管理し、実行物はdisposable pathへ展開します。

## 3. Storage decision candidate

raw timing recordは一run一JSONをtemporary fileからatomic renameする方式が単純でrecoverableです。

- append中断で全ledgerを壊しにくい
- run単位のschema validationが容易
- artifactとrecordをseparate permissionにできる
- aggregateをいつでも再生成できる

検索性能が必要になった場合だけderived SQLite indexを追加します。SQLiteを最初からsource of truthにして既存`agentctl` DBへ実験schemaを混ぜません。

## 4. Milestone A: schema and deterministic clock — implemented

追加:

- study/case/run JSON schema
- ID、enum、timestamp、provenance validation
- model identity / generation settings / runtime identity schema
- online user-waitとoffline scoringを分離したlandmark schema
- monotonic clock collector
- fake runnerでP0/P1、T0–T6、V0/V1、TX、S0/S1、worker、dialogue exchangeを再生
- duration derivationとmissing landmark handling

Tests:

- `not_observed`を0にしない
- `not_applicable` / `not_observed` / `unknown`を区別
- requested effortをapplied effortへ昇格しない
- offline scoring runtimeをuser waitへ加えない
- T3/T4がnot-applicableなC0でもV0–V1 online validationを算出する
- online fail / offline pass-fail / online unavailableのcanonical quality-passを検証する
- negative durationをreject
- parent/childを二重計上しない
- timeout/cancel/failureをsuccessにしない
- atomic writeとrestart recovery
- content allowlist外fieldをreject

Deliverable:

- actual providerを使わないsample run records
- measurement overhead report

## 5. Milestone B: case catalog and fixture isolation

Status: initial F04 bounded-implementation S/M/L、capsule digest、deterministic snapshot、hidden oracle calibrationまで実装。historical replayとbroad 12-family corpusは未実装。

追加:

- 12 family、S/M/L size-profile descriptor catalog
- case revision/digest generation
- disposable repository/worktree builder
- gold/evaluatorをagent workspace外へ置くboundary
- task capsule exporter
- auto-injected instruction set digest capture

Tests:

- future commit/tag/blame/comment/gold patch/generatorがworkspaceから読めない
- host instruction digest差とgold leakageを検出できる
- immutable base digestが一致する
- write caseがprimary checkoutを変更しない
- duplicate case ID/revision mismatchをreject
- cleanupがrun ownership外へ触れない

Deliverable:

- Wave 1用の小さなcalibration case set

## 6. Milestone C: provider and agentctl adapters

Status: passive CLI advertisement probeまで実装。generationを伴うidentity/settings/progress canaryとagentctl correlationは未実装。

追加:

- Codex / Claude / Grok command adapterからrun correlationを渡す
- capability probe: implicit/explicit model、resolved/alias confidence、supported/rejected/silent setting
- provider model identity、requested/applied setting、CLI/runtime surface capture
- `agentctl` job/attempt ID correlation
- provider-native resultを共通artifact envelopeへ変換
- progress envelopeがある場合だけのT2。無い場合は非掲載
- primary synthesis T4、online validation V0/V1、user result T6のboundary
- offline evaluator S0/S1の別boundary

安全設計:

- arbitrary annotationをhookへ注入させず、catalog IDとopaque run IDだけallowlist
- credential/env dumpをcaptureしない
- adapter failureはrun failureとして残し、provider CLI自体をwrap-loopしない
- experiment flagがない通常運用へbehavior changeを与えない
- controlled studyはautomatic permissionかつnested subagent disabled

Deliverable:

- 各providerのexplicit live canaryでresolved/alias、applied/requested、progress、surfaceを確認
- correlation coverage report

取れないfieldを「たぶんdefault」と埋めません。そのprovider/surfaceでは該当指標またはeffort stratumを非掲載にします。

## 7. Milestone D: finite batch runner

追加:

- manifestから有限run queueを生成
- order rotation/random seed記録
- provider/concurrency/rate-window cap
- pause/resume/cancel
- safe retry policyとattempt linkage
- owned worktree/container inventory
- crash後のunfinished run recovery

runnerは常駐cronではありません。userが明示起動したstudyだけを処理し、manifestにないtaskを生成し続けません。

Deliverable:

- Wave 2 profile mapを分割batchで実行可能

## 8. Milestone E: evaluators

familyごとに強いoracleから追加します。

1. test/command/schema based
2. seeded defect/finding based
3. mutation/known-bad based
4. constraint/source entailment based
5. calibrated model evaluator where unavoidable

各evaluatorはID/revision、input digest、result、runtimeを返します。online test/buildだけをV0–V1へ含め、study専用evaluatorはS0–S1へ置いてuser waitから除外します。

Deliverable:

- fast-but-wrongをaccepted durationから除外できる

## 9. Milestone F: sampler and atlas generator

追加:

- within-case / between-caseを分けたsummary
- evidence state判定
- precision/coverage gap report
- next-sample candidate list
- raw samples、range、central/prediction interval
- accepted-onlyとcensoring-aware user-waitの二面表示
- p95 adequacy guard
- model/CLI/runtime/applied-setting series boundaryとdistribution-shift stale diagnostic
- execution surface / first-artifact resolutionの非混合
- Markdown/JSON/CSV generation

`next-sample candidate`は「この構成をprojectで選べ」ではなく、「このreference cellの不確実性を減らすなら次にどこを測るか」です。

Deliverable:

- concrete duration atlas
- machine-readable dataset
- missing/stale coverage map

## 10. Atlas output candidate

```text
docs/agents/duration-atlas/
  README.md                    # methodology and environment
  current-summary.md           # human-readable time ranges
  by-family/<family>.md
  by-configuration/<config>.md
  coverage.md                  # unmeasured/provisional/characterized/stale
  studies/<study-id>.md        # immutable observation report

generated/duration-atlas/current.json   # machine-readable aggregate
generated/duration-atlas/manifest.json  # schema/source/freshness manifest
```

generated outputはsource run digestを持ち、手編集しません。raw prompts/artifactsはdocsへcommitしません。

### Skill delivery boundary

詳細dataをskill本文へ埋め込みません。`generated/duration-atlas/current.json`をdeterministic query scriptで絞り、`project/.codex/skills/lookup-agent-duration/`候補のcompact skillから呼びます。skill、aggregate schema、data snapshotを別versionにし、未知schemaはfail closedします。詳細は`11-skill-delivery-and-context-budget.md`を参照します。

## 11. Minimum useful release

最小releaseは「すべて測った」状態ではなく、次を満たす状態です。

- S/M/Lが構造descriptorで検索できる
- 少なくとも一つのstrong-oracle caseで、条件を明示した`single-observation`を正しく表示できる
- progressを観測できる場合だけfirst-valid-artifactを出せる
- user-result、online validation、offline scoreを分けられる
- model identity confidence、requested/applied setting、surfaceを表示できる
- sample/case count、range、failure、environmentが見える
- 未測定cellを明示できる
- projectへのselection ruleを生成しない
- 人間の入力なしでrun recordが完成する

## 12. 最初の実装slice

次turn以降に実装へ進める場合のcritical pathは次です。

1. schema + fake clock harness
2. identity/settingsのpassive capability probe — implemented; applied/progress canary remains
3. case catalogのprofile descriptor部分 — initial F04 S/M/L implemented
4. deterministic isolated S/M/L case + online oracle separation — implemented
5. primary-only provider canary
6. atlasのraw-sample表示
7. same-case repeat + variant summary
8. collaboration timingとdialogue sub-event
9. bounded query CLI + compact skill + fresh-agent forward test

初期sliceで統計modelや全36 candidateを先に作り込みません。実測一件が正しいidentity/setting/event境界でatlasへ出るend-to-end pathを通してから、corpusを増やします。

## 13. Falsification pilot

pilotの目的は時間帯を確定することではなく、壊れた測定設計を早く落とすことです。

- P0: fake clockでmissing landmark、timeout、parent/child非二重計上
- P1: implicit/explicit alias、supported/unsupported setting、approval contamination
- P2: strong-oracle S caseでonline waitとoffline scoreを分離
- P3: progressあり/なしsurfaceでT2掲載規則を検証
- P4: same-case repeatとisomorphic variantがflat medianへ潰れないことを検証
- P5: isolated fixtureとhost instructionが残るworkspaceのdigest/leakage検出
- P6: directと`agentctl`が別seriesになることを検証

collaboration clockはP3を通過したsurfaceでC0/C1の一paired blockだけを使って破壊検査します。これはagent数の推奨ではなくdelegation clock coverageです。gateが落ちたらlive runを増やさずschema/adapterを直します。

## 14. この計画turnでは行わないこと

- live Codex / Claude / Grok taskの連続実行
- automatic schedulerの追加
- project routing policyの実装
- model/provider winnerの判定
- authoritative docsへの未検証数値の掲載

計画承認後、Milestone Aからsmall commitに分けて進めます。
