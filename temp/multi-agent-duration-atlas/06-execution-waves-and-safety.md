# 06. Execution wavesとsafety

## 1. 原則

実験は常駐schedulerではなく、明示的に開始する有限batchとして進めます。subscription利用のためper-call課金は前提にしませんが、provider rate window、concurrency slot、wall-clock、host/container資源、通常開発への干渉は有限です。

各waveは次を持ちます。

- manifestで確定したrun候補
- wall-clock/rate/concurrency safety cap
- manual pause/kill
- expected disk/Docker scope
- promotion gate
- content-free result inventory

## 2. Wave 0: instrumentation calibration

目的: agent品質を測る前に、時計とcorrelationが正しいことを証明する。

- fake provider / deterministic workerでP0/P1、T0–T6、V0/V1、S0/S1を発生
- parallel workerのaggregate time、active union、tracked spanをdeterministic fixtureで検証
- failure、timeout、cancel、harness restartを模擬
- episode ID、agentctl job/attempt ID、run IDの重複・二重計上を確認
- raw contentがanalytic recordへ漏れないことをtest
- measurement overheadをbaseline化

Gate:

- clock landmark coverageが期待どおり
- derived durationがmonotonic
- fail/timeoutをsuccessへ変換しない
- rebuild後もintended persistent recordが残る
- cleanupがowned resourceだけを対象とする

## 3. Wave 0.5: capability / identity probe

目的: durationを層別するmodel identityとgeneration settingが、本当に観測できるかを先に確定する。

- provider × CLI buildごとにimplicit defaultとexplicit aliasをprobe
- resolved ID / snapshot hintの有無とidentity confidenceを記録
- reasoning/effort/thinking settingをrequested / applied / rejected / silent-unknownに分ける
- progress artifact、synthesis envelope、permission modeの観測可否を確認
- direct providerと`agentctl` surfaceを別seriesへ置けることを確認
- approval-gated runをautomatic user-wait sampleへ混ぜないことを確認

これはcapability coverageであり、task duration sampleではありません。Grokの`--reasoning-effort`のようにflagが存在しても、appliedを確認できなければそのeffort名のduration cellを作りません。

Gate:

- alias/defaultとresolved identityを区別できる
- requestedとapplied settingを区別できる
- unsupported/silent settingをduration stratumから除外できる
- progressのないsurfaceでT2を非掲載にできる
- execution surfaceとpermission contaminationを識別できる

## 4. Wave 1: case/oracle calibration

目的: S/M/Lとquality oracleが実際に機能することを確認する。

- seeded fixtureをprimary-only/fresh contextで実行
- gold leakage、task ambiguity、acceptance commandを確認
- known-good / known-bad artifactへevaluatorを適用
- setup timeがsize descriptorから漏れていないか確認
- case revision ruleを実地確認

最初から全providerを混ぜません。一つのexecution surfaceでcaseの欠陥を先に除きます。

Gate:

- task capsuleだけで開始可能
- oracleがknown-good/badを区別
- artifact validityとacceptanceを自動判定
- online validationとoffline score runtimeを分離
- S/M/Lがdurationではなく構造で説明可能

## 5. Wave 2: broad size-profile map

目的: 12 family内のS/M/L **profile**について、桁と欠測を一つのmodel identity/applied setting/execution surfaceのprimary-onlyで広く観測する。

- candidate poolからprofileを明示したvalid caseを観測する
- batchはfamilyまたはlane単位に有限分割する
- S/M/Lを混ぜた実行順でtime-window biasを減らす
- read-onlyから始め、write、Docker/isolatedを後段へ送る
- single observationはあくまでraw referenceとして公開する

成果:

- profile付きC0 coverage map。未測定language/oracle/ambiguity profileは`unmeasured`
- first-valid-artifact（観測可能なsurfaceのみ）/ user-result / quality-conditioned durationの初期実測
- failed/invalid fixture inventory
- 次にwithin-case/between-case samplingが必要なcell

36 candidate taskを実行したという事実をcoverage完了と呼びません。

## 6. Wave 3: repeatabilityとfamily range

目的: 「一回は14分」から「この種なら概ね何分」へ進める。

- same-case repeatでrun varianceを測る
- isomorphic variantでcase varianceを測る
- precision gapの大きいcellへsampleを配分
- short/long/failure tailを消さない
- seriesのevidence stateを逐次更新

固定回数を全cellへ課しません。計測精度、coverage、batch capで次sampleを決めます。

## 7. Wave 4: collaboration timing profiles

目的: collaboration形ごとの時間構造を測る。

- bounded delegationはsubtask boundaryが明確なcase
- parallel shardsは独立shardが実在するcase
- independent candidatesは複数解が成立するcase
- maker/verifierは強いoracleまたはseeded defectがあるcase
- evidence dialogueは反証・testでclaim状態を変えられるcase
- staged pipelineはhandoff costが観測できるcase

入場条件は、対象execution surfaceでT2 progress artifactとT4 synthesis envelopeを明示観測できることです。取れないsurfaceでは総時間を観測できても、collaboration breakdown atlasへ昇格しません。

各構成についてdispatch、worker completion、synthesis、online validationを分けます。初期controlled runはnested delegationを無効化します。自然にserialなtaskへ無理にworkerを増やして「multi-agentは遅い」という結論を作らず、その構成を測るなら`mismatched-decomposition` stratumとして明示します。

### Width curve

parallel taskでは、runtimeのsafe width内を段階的に測ります。exact participant countを記録し、width増加ごとのwall-clock、queue、aggregate worker time、synthesis tailを曲線として残します。現在のslot数を将来のdefaultへ固定しません。

### Dialogue curve

各exchangeを一sampleとして累積時間とfamily contract上のevidence state changeを残します。あらかじめ「2往復」「3往復」を品質defaultにせず、task-specific capだけを安全境界にします。

## 8. Wave 5A: model / effort strata

目的: 同じproviderでもmodel identityとapplied generation settingで何分変わるかを測る。

- implicit default、explicit alias、resolved identityを別seriesにする
- capability probeでappliedを確認できたsettingだけを比較する
- collaboration、case、surface、session、permission、cacheを固定したpaired block
- model alias/CLI/server driftでseriesを切り、旧値をstale候補にする
- provider固有effortを共通尺度へ正規化しない

effort比較は「highが良いか」を決める実験ではなく、同じtaskで各applied settingのuser wait・worker time・qualityがどう分布したかを提供します。

## 9. Wave 5B: provider / context / cache strata

目的: 同じtaskでも運用条件で何分変わるかを測る。

- Codex / Claude / Grokのidentity/settings/runtime別series
- same-providerとcross-provider collaboration
- fresh sessionとwarm task context
- cold/warm dependency・Docker cache
- rebuilt containerとlong-lived container
- quiet loadとmeasured competing load

一軸ずつpaired blockで動かします。provider prompt cacheはrepository/dependency cacheと分離し、観測不能なら`unknown`です。alias、resolved identity、applied setting、CLI/surfaceが変化したら新seriesへ切ります。

## 10. Wave 6: natural live observation

目的: fixture/historical replayの時間帯が実作業でも妥当かを確認する。

- 人間のrating/formを要求しない
- transcriptではなくcontent-free timing/outcomeを蓄積
- controlled corpusと別seriesにする
- catalog annotationがないepisodeはfamily/size/oracle/relationを`unknown`のままにする
- opaque timing/outcomeをfamily duration bandへpoolしない

natural taskを用いて「この構成が原因で速い」と断定しません。annotation surfaceが将来追加されるまでは、atlasの欠落条件と運用異常を見つけるshadow dataです。

## 11. Batch safety

### Provider

- providerごとにconcurrency upper boundをmanifestへ宣言
- rate-limit/retry-afterを観測したら同provider batchをpause
- interactive user taskをbenchmarkより優先
- credentialやsubscription detailをrecordへ保存しない
- no-progress loopをterminalにする有限capを持つ
- controlled studyはautomatic permissionを使い、人間のapproval waitを混ぜない
- initial studyはnested subagentを無効化し、検出時はrunを汚染扱いにする

### Filesystem/Git

- read-only caseはwrite不可のdisposable copy
- write caseはimmutable baseから専用worktreeまたはtemporary repo
- primary checkoutへworkerが書かない
- merge、push、releaseを実験runnerへ許可しない
- failed artifactはretention policyに従い隔離し、global cleanupしない
- auto-injected instruction setのdigestを記録し、gold/future instruction leakageをinvalidにする

### Docker/container

- project/job labelとunique namespaceを必須化
- shared fixed port/project nameを使わない
- `docker system prune`やbroad volume deletionを禁止
- image/cache cold testは専用scopeで行う
- residual resource inventoryをrun outcomeに含める

### Network/current-info task

- network利用をcase manifestへ明示
- source retrieval timeをagent reasoning timeと分離
- mutable external pageはsnapshot/digestを残す
- credential、cookie、private sourceをfixtureへ含めない

## 12. Pause/abort condition

- interactive developmentへ目立つlatencyを与えた
- providerがrate-limit/retry loopへ入った
- run correlationまたはclock monotonicityが壊れた
- primary checkoutや他jobへのwriteを検知した
- owned resourceだけをcleanupできない
- content/privacy leakageを検知した
- invalid fixtureが同じbatchで繰り返した
- batchのwall-clock/disk/concurrency capへ到達した
- requested/applied setting、model identity、permission modeを識別できないまま別seriesへpoolしようとした

abortしたsampleも`cancelled`または`invalid`として残します。再開時は新attempt IDを使います。

## 13. Promotion gate

次waveへ進む条件はrun数ではなく、次の能力です。

- 今のwaveの時間を正しく分解できる
- quality/acceptanceを自動判定できる
- online user waitとoffline scoringを分離できる
- model identity confidenceとapplied settingを正しく層別できる
- missing dataをmissingのまま扱える
- fixtureとnatural taskを区別できる
- safety capとkillが実際に働く
- atlasへ具体的な時間帯と観測条件を出せる

満たせない場合、live runを追加するよりinstrumentation/caseを直します。

## 14. 実行順序の現実案

```text
instrumentation fake
  -> identity / setting / progress capability probe
  -> S read-only fixture
  -> M/L read-only fixture
  -> S/M write fixture
  -> Docker/isolated fixture
  -> broad primary-only map
  -> adaptive repeats/variants
  -> collaboration profiles
  -> model/effort strata
  -> provider/context/cache strata
  -> natural live shadow data
```

これなら初期の測定バグで高時間・高riskなL/Docker/provider runsを浪費しにくく、途中段階でもsingle-observation atlasを提供できます。
