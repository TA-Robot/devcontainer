# Grok review統合結果

統合日: 2026-08-26

## Review execution

- reviewer: Grok CLI 1.0.5
- requested model: `grok-4.6`
- local model inventory: `grok-4.6` default、`grok-4.5` available
- requested reasoning effort: `high`
- applied reasoning effort: CLI/eventから独立確認できず`unknown`
- mode: single session、`GROK_MEMORY=0`、no subagents、web disabled、plan/read-only
- source: `09-grok-independent-review.md`

「highを指定したがappliedを確認できない」というreview実行自体が、requested effortをそのままduration stratumへ使えない問題の具体例になりました。

## 結論

Grokの判定は「重大な基盤不足」でした。指摘されたMust項目を計画へ統合し、live duration runより前にidentity/settings、online/offline clock、progress coverageを検証する構成へ変更しました。

## 採用した主要変更

### 1. Modelとeffortを第一級のseries keyにした

旧案:

```text
provider / model string / reasoning string / CLI
```

統合後:

```text
modelIdentity:
  requested alias/source
  resolved ID or alias-only confidence
  snapshot hint when observable

generationSettings:
  requested
  applied
  rejected/unsupported
  accepted-but-unknown

runtimeIdentity:
  provider / CLI version+source / image
  direct-or-agentctl surface
  permission mode / observation window
```

model差とeffort差は明確に測定対象です。ただし次を守ります。

- implicit default、explicit alias、resolved identityを別seriesにする
- appliedを確認できたeffortだけをeffort名つきduration cellにする
- provider固有settingを共通の`high/medium/low`へ正規化しない
- model比較ではapplied settingなどを固定し、effort比較ではmodel identityなどを固定する
- aliasやserver-side backendが変わった疑いがあれば旧seriesをstale候補にする
- unsupported/silent setting probeはcapability結果で、task duration sampleではない

### 2. First usefulを自動で捏造しない

schema-valid artifactが人間にとってusefulとは限りません。T2を`first contract-valid artifact`へ変更しました。progress envelopeを出せないprovider/surfaceではT2をfinal時刻で補完せず、指標そのものを非掲載にします。

### 3. 利用者待ちとstudy採点を分けた

- T0–T6: online/user-visible path。online validationは独立したV0–V1区間
- S0–S1: gold/evaluatorによるoffline study score

offline scoring runtimeをuser waitへ足しません。quality-conditioned referenceは、offline passしたrunの元のT6−T0を抽出して作ります。

### 4. 36枠をcoverage完成条件にしない

12 family × S/M/Lはtask候補の目録です。実際の公開cellはfamily × size-profileで、oracle、ambiguity、coupling、validation、language/stack、artifactが異なれば未測定profileとして残します。

各candidateへambiguity、oracle、decomposability、language/stack、artifactのstarting profileを追加しました。

### 5. 実行面の交絡を追加した

追加した条件:

- direct provider vs `agentctl`
- automatic vs approval-gated permission
- auto-injected instruction set digest
- context compaction
- provider prompt cache
- pre-T0 worktree/image/cache provisioning
- nested worker detection

controlled studyはautomatic permission、初期はnested delegation disabledです。人間のapproval待ちをagent durationへ混ぜません。

### 6. Natural observationを無理に分類しない

通常episodeにはcatalog annotationがありません。hook eventからfamily、size、oracle、relationを推測する案を撤回しました。annotation surfaceができるまでnatural dataはopaque timing/outcomeのshadow seriesで、family duration bandへ入りません。

### 7. Sampling promotionを厳しくした

intervalが動かなくなっただけでは`family-characterized`へ上げません。

- multiple isomorphic cases
- within-caseとbetween-case variance
- multiple observation blocks/windows
- valid model/settings series
- required landmark coverage

を満たす必要があります。具体的run数はprecision/coverage設計で決め、universal defaultにしません。

### 8. Censored waitを別面で出す

時間referenceは常に次を分けます。

1. accepted/quality-pass runに条件づけたuser-result time
2. timeout/cancel/rate-limitを含むcensoring-aware user wait

これで「成功したときは15分」だけを出して、一定割合が1時間capまで終わらない事実を隠すことを防ぎます。

## Dimensionの役割

| Role | 主なdimension |
| --- | --- |
| primary stratum | task family + size profile、collaboration relation、model identity、applied settings、execution surface、session class、source series、progress resolution |
| blocking/covariate | language、ambiguity、decomposability、artifact/lane、cache、time window、machine/load、permission、repository scale |
| diagnostic-only | token/tool count、compaction、instruction digest、prompt-cache unknown signal、approval wait、nested worker、clock anomaly、residual resource |

worker widthとdialogue depthは全dimensionへ掛け算せず、該当configuration card内の実測curveにします。

## Model / effort測定の具体像

### Capability phase

provider × CLI buildについて、default、explicit alias、advertised setting、unsupported settingをprobeします。ここでは時間bandを作りません。

### Duration phase

applied settingを識別できた組だけ、同じcase/profile、surface、session、permission、cacheでpaired blockを作ります。

```text
same model identity:
  applied effort A -> observed user time / worker time / quality
  applied effort B -> observed user time / worker time / quality

same applied setting:
  model identity A -> observed distribution
  model identity B -> observed distribution
```

cross-providerではsetting意味が一致する保証がないため、「同一effort比較」ではなくprovider/model/settings構成の並置として提供します。

## 統合後も意図的にunknownなもの

- aliasしか返らないserver側snapshot
- silent ignoreされたeffort
- schema-valid artifactが人間にとってusefulか
- worker成果が最終判断を変えたか
- 人間のreview/注視時間
- progressがないsurfaceのfirst artifact
- annotationがないnatural taskのsemantic profile
- providerが返さないthinking/tool/queue内訳
- untracked nested workerを含む真のaggregate
- 未測定configurationの反実仮想時間

## 実装前gate

次の順に通します。

1. fake clockとmissing-data contract
2. model/effort capability and identity probe
3. online waitとoffline scoreの分離
4. progressなしでT2を非掲載にする確認
5. same-case / between-caseの非混合
6. instruction/gold leakage検知
7. direct / agentctl surfaceの非混合

これが通るまで、36候補やmulti-providerの大量計測へ進みません。
