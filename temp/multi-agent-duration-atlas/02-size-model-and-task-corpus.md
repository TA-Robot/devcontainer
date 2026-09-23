# 02. S/M/L size modelとtask corpus

## 1. S/M/Lは時間ではなく構造で定義する

「5分ならS、30分ならM」と定義すると、測定前に答えを埋め込んでしまいます。LOCやfile数だけでも、1行のDocker変更が長いintegration testを必要とするようなcaseを表現できません。

sizeはtask family内の相対的な構造scaleとし、各caseに次のdescriptorを個別記録します。単純な合計scoreにはしません。

| Descriptor | 観測内容 |
| --- | --- |
| context surface | 理解が必要なcomponent、contract、language境界 |
| change/artifact surface | 作成・変更・比較するartifactの広がり |
| coupling | 複数箇所の整合、order、state transitionの結合 |
| validation depth | syntax、unit、integration、build、runtimeなどの層 |
| environment setup | install、build、container、service起動の必要性 |
| failure distance | 誤りが直ちに出るか、後段・並行・再起動後に出るか |
| statefulness | filesystem、DB、worktree、container、session stateへの依存 |

曖昧さ、risk、oracle strength、decomposabilityはsizeと直交する別axisです。大きいtaskが必ず曖昧とは限らず、小さいsecurity taskが低riskとも限りません。

### S: local

- 一つの局所的なreasoning/change unit
- context境界が狭く、直接oracleがある
- setupが軽く、failureが近い
- 結合変更や複数validation layerを原則含まない

### M: coupled

- 複数constraintまたはartifactの整合が必要
- component内または近接component間の結合がある
- unit以外のvalidation、または一定のsynthesisを含む
- 一部は分けられるが、最後に統合判断が必要

### L: cross-boundary

- language/process/container/contractなど複数境界をまたぐ
- 複数validation layerとfailure recoveryがある
- delayed failure、migration、concurrency、persistent stateのいずれかを含む
- 複数artifactを統合して初めてacceptanceを判定できる

size labelとdescriptorが食い違う場合はdescriptorを正本にし、case revisionでlabelを再校正します。観測時間が長かったという理由だけではlabelを変えません。

## 2. Caseを三層にする

時間目安が一つの偶然のtaskへ過適合しないよう、corpusを次の三層で管理します。

```text
family (例: bug diagnosis)
  -> size/profile cell (例: M, direct oracle, medium coupling)
    -> isomorphic case variants (異なるbug/fixture、同程度の構造)
      -> repeated runs (同じcaseの実行ぶれ)
```

- repeated runはprovider/network/cacheによるぶれを測ります。
- case variantは題材固有の当たり外れを測ります。
- family集計ではこの二つを混ぜず、両方を表示します。

`isomorphic variant`は「なんとなく似た問題」ではありません。少なくとも同じsize descriptor vector、oracle class、ambiguity class、artifact type、language/toolchain profile、同程度のchange/context surfaceを持ち、seedや対象箇所だけが異なるcaseです。条件が変わるvariantは別profileへ置きます。

## 3. Corpus source

### A. Seeded deterministic fixture

既知のdefect、acceptance test、gold findingを持つdisposable repositoryを生成します。goldはagent workspaceへ置きません。

- 長所: oracleが強く、同条件を再現しやすい
- 弱点: 実projectのmessinessを過小評価しやすい

### B. Historical replay

このrepositoryの過去snapshotから、当時の未修正状態とtask envelopeをbundle化します。未来のcommit、fix patch、review discussionをagentが参照できない隔離が必要です。

- 長所: 現実の結合やtoolchainを保てる
- 弱点: snapshot leakageと現在環境との差に注意が必要

leakage checkはfuture commitだけでなく、reachable tag/branch、`git blame`、修正後comment、release note、gold patch path、test名、fixture generator、provider memory/historyを対象にします。一つでも未来情報へ到達できたrunは`invalid: gold-leak`です。

### C. Natural live task

実際のbacklog作業を通常運用のまま観測します。

- 長所: ecological validityが高い
- 弱点: goldやcounterfactualがなく、構成間の因果比較には使いにくい

catalog annotationのない通常episodeからfamily、size、oracle、relationをevent列で推測しません。machine annotation surfaceができるまでは、natural seriesはopaque timing/outcomeとしてだけ保存し、family duration bandへ入りません。

三sourceは別seriesとして表示します。fixtureの時間を実taskの保証値へ昇格しません。

## 4. Candidate corpus: 12 family × S/M/L

以下の36項目は**candidate task pool**であり、36枠を埋めればcoverage完了という意味ではありません。公開cellはfamily × size-profileで分かれ、oracle、ambiguity、language/stackなどが異なる未測定profileは`unmeasured`のままです。各profileには複数のisomorphic variantを後から用意します。このrepositoryへsample appは追加せず、fixtureはtemporary workspaceまたはGit bundleから生成します。

### F01 Repository trace / explanation

| Size | Candidate |
| --- | --- |
| S | 一つのCLI flagの定義元とvalidation箇所を特定し、根拠pathを返す |
| M | hook eventがstate fileへ反映されるまでを複数module越しに追跡する |
| L | devcontainer lifecycleからhost wrapper、agentctl、companion表示までの境界をtraceする |

主な時間要因: context discovery、cross-language navigation。品質oracle: 必須node/edgeを持つgold trace。

### F02 Code review

| Size | Candidate |
| --- | --- |
| S | 小さなdiffへ一つのseeded validation defectを入れ、findingを求める |
| M | 複数fileへ相互作用するdefectを入れ、severityと根拠を求める |
| L | Python/Bash/JSまたはcontainer境界をまたぐ変更へ、lifecycle defectをseedする |

主な時間要因: diff surface、hidden interaction。品質oracle: seeded finding recall、false positive、severity。

### F03 Failing-test diagnosis

| Size | Candidate |
| --- | --- |
| S | 一つのunit test failureから局所root causeを特定する |
| M | 症状と原因が別moduleにあるfailureをdiagnoseし、regression test案を返す |
| L | race、restart、persistent stateなど遅延条件つきfailureを再現・特定する |

主な時間要因: reproduction cost、failure distance。品質oracle: root cause、再現command、regression test。

### F04 Bounded implementation

| Size | Candidate |
| --- | --- |
| S | 一つの純粋関数またはvalidatorへ明示的behaviorを追加する |
| M | CLI option、state処理、unit test、docsを整合させる |
| L | provider hookからledger、UI表示までcross-boundary featureを追加する |

主な時間要因: edit/test loop、integration。品質oracle: acceptance suiteとchanged-path contract。

### F05 Refactor / migration

| Size | Candidate |
| --- | --- |
| S | 局所helper抽出をbehavior-preserving test付きで行う |
| M | module内interfaceを移行し、全callerとtestを更新する |
| L | backend abstractionやschema migrationを互換性・rollback込みで行う |

主な時間要因: caller discovery、compatibility。品質oracle: old/new contract tests、behavior diff。

### F06 Test design and augmentation

| Size | Candidate |
| --- | --- |
| S | 明示behaviorに対するunit testを一つ追加する |
| M | failure mode群をcoverするtable/property testを設計する |
| L | concurrency、container、restartを含むintegration harnessを追加する |

主な時間要因: fixture setup、nondeterminism。品質oracle: mutation kills、known-bad implementation rejection。

### F07 Documentation / runbook

| Size | Candidate |
| --- | --- |
| S | 既存commandのusageと一つの制約を正確に追記する |
| M | failure path、diagnosis、recoveryを再現可能なrunbookへまとめる |
| L | architecture移行の現状、互換層、rollback、運用境界を複数文書へ反映する |

主な時間要因: source-of-truth照合、整合性。品質oracle: executable snippets、fact checklist、link validation。

### F08 Architecture / design analysis

| Size | Candidate |
| --- | --- |
| S | 二つの局所API案を既知constraintで比較する |
| M | 複数componentの責務分割案をfailure modes込みで比較する |
| L | execution fabricやpersistence方式をmigration、security、operations込みで設計する |

主な時間要因: ambiguity、constraint discovery、synthesis。品質oracle: constraint coverage、counterexample、unresolved unknowns。

### F09 Security / isolation review

| Size | Candidate |
| --- | --- |
| S | name/path validationのbypass候補を調べる |
| M | workspace boundary、symlink、environment overrideの組合せをreviewする |
| L | worktree、Docker、credential、cleanup ownershipを含むthreat modelを作る |

主な時間要因: adversarial search、environment assumptions。品質oracle: seeded exploit、negative tests、threat checklist。

### F10 Performance / resource diagnosis

| Size | Candidate |
| --- | --- |
| S | 一つのlocal hot pathをbenchmarkで特定する |
| M | serialization/cache/I/Oの候補をinstrumentして比較する |
| L | concurrency、queue、container startup、provider waitを分解してbottleneckを特定する |

主な時間要因: measurement runs、noise。品質oracle: reproducible benchmarkとbefore/after distribution。

### F11 Devcontainer / operations / recovery

| Size | Candidate |
| --- | --- |
| S | shell/config syntax defectを修正し、static checkを通す |
| M | post-start hookやversion syncのfailureを再現・修正する |
| L | rebuild、persistent volume、host/container境界をまたぐrecoveryを設計・検証する |

主な時間要因: image build、startup、external state。品質oracle: lifecycle smoke test、residual resource inventory。

### F12 Evidence synthesis / decision support

| Size | Candidate |
| --- | --- |
| S | 二つの短いanalysisから一致点・相違点・根拠を抽出する |
| M | 独立reviewの矛盾をsource/testで裁定し、unknownを残す |
| L | 複数proposal、実測、failure evidenceを統合したdesign recordを作る |

主な時間要因: number of claims、conflict resolution。品質oracle: source entailment、unsupported claim、decisive evidence coverage。

F07/F08/F12のようにdeterministicなonline oracleを作れないcaseでは、`time-to-user-result`は出せても`online accepted`は`unknown`になり得ます。calibrated offline scoreで後からquality-conditioned distributionを作ることはできますが、score runtimeをuser waitへ足しません。弱いjudgeしかないcaseへaccepted labelを捏造しません。

## 5. Candidate profile registry

以下はcorpus作成時のstarting hypothesisです。`stack`に複数値がある行は一つへpoolする指示ではなく、language別variantを用意して差がplanning resolutionを超えたら別profileへ分ける指示です。

| ID | Ambiguity | Oracle | Decomposability | Language / stack | Artifact |
| --- | --- | --- | --- | --- | --- |
| F01-S | exact | gold-trace | serial | Python / Bash / JS variants | answer + evidence paths |
| F01-M | bounded-open | gold-trace | partial | Python + JS or Python + Bash | trace graph |
| F01-L | bounded-open | structured-gold | partial | devcontainer + Bash + Python + JS | cross-boundary trace |
| F02-S | exact | seeded-defect | serial | Python / Bash / JS variants | findings |
| F02-M | bounded-open | seeded-defect | partial | multi-file single/cross stack | ranked findings |
| F02-L | bounded-open | seeded lifecycle defects | independent/partial | Python + Bash + JS + container | findings + lifecycle evidence |
| F03-S | exact | failing/passing test | serial | Python / JS / Bash variants | diagnosis |
| F03-M | bounded-open | reproducer + regression | partial | multi-module | root cause + test |
| F03-L | bounded-open | repeatable lifecycle harness | partial | concurrency/container/state | diagnosis + reproducer |
| F04-S | exact | unit acceptance | serial | Python / JS / Bash variants | patch + test |
| F04-M | exact | unit + contract | partial | CLI/state/docs | patch + tests + docs |
| F04-L | bounded-open | layered acceptance | independent/partial | provider hook + Python + JS | integrated patch |
| F05-S | exact | behavior equivalence | serial | Python / JS variants | refactor patch |
| F05-M | exact | caller + compatibility tests | partial | module/interface | migration patch |
| F05-L | bounded-open | old/new contract + rollback | independent/partial | schema/backend boundary | migration set |
| F06-S | exact | known-bad rejection | serial | Python / JS / Bash variants | unit test |
| F06-M | bounded-open | mutation/known-bad set | partial | table/property harness | test suite |
| F06-L | bounded-open | repeatable integration harness | independent/partial | concurrency + Docker | integration suite |
| F07-S | exact | executable fact check | serial | Markdown + one CLI | doc patch |
| F07-M | bounded-open | command replay + checklist | partial | Markdown + runtime | runbook |
| F07-L | bounded-open | structured/calibrated | partial | multi-doc + architecture | document set |
| F08-S | bounded-open | constraint checklist | serial | design text | comparison note |
| F08-M | open | calibrated evaluator | independent/partial | component architecture | proposal |
| F08-L | open | calibrated/weak | independent/partial | execution/persistence/security | design record |
| F09-S | bounded-open | seeded bypass | serial | path/name validation | findings + negative test |
| F09-M | bounded-open | seeded exploit set | partial | filesystem/env/symlink | review + tests |
| F09-L | open | threat checklist + exploits | independent | Git + Docker + credentials | threat model |
| F10-S | exact | benchmark | serial | Python / JS variants | diagnosis + measurement |
| F10-M | bounded-open | benchmark distribution | partial | I/O/cache/serialization | experiment report |
| F10-L | bounded-open | multi-stage instrumentation | independent/partial | queue + container + provider | bottleneck model |
| F11-S | exact | static/smoke check | serial | Bash / config | patch |
| F11-M | bounded-open | lifecycle smoke | partial | host + container hook | patch + recovery evidence |
| F11-L | bounded-open | rebuild/persistence harness | independent/partial | devcontainer + volume + host | recovery design/patch |
| F12-S | exact | source entailment | serial | Markdown/JSON evidence | synthesis |
| F12-M | bounded-open | calibrated entailment | independent/partial | reviews + test evidence | adjudication |
| F12-L | open | calibrated/weak | independent | proposals + metrics + failures | decision record |

## 6. Sizeとは別に必ず振るaxis

各caseへ次を明示し、S/M/Lへ埋め込みません。

- ambiguity: exact / bounded-open / open
- oracle strength: deterministic / structured-review / calibrated-evaluator / weak
- risk: low / medium / high impact
- decomposability: serial / partially shardable / independently shardable
- lane: read / write / isolated
- expected artifact: answer / findings / patch / tests / design / runbook
- environment dependence: none / local-tool / Docker / network/provider
- knowledge locality: repository-contained / docs-needed / external-current-info
- expected failure modes: compile / behavioral / concurrency / lifecycle / semantic
- language/toolchain: Python / Bash / JavaScript / Markdown / Docker / cross-stack
- repository scale/index state: fixture-small / historical-observed / unknown

これにより、たとえば「Mだからmulti-agent」のような短絡ではなく、「M、partially shardable、strong oracle、Docker cold-startあり」の実測値を検索できます。

## 7. Generalization boundary

初期corpusはこのrepositoryのPython、Bash、JavaScript、Markdown、Docker、agentctl/devcontainer contractへ偏ります。したがって得られる時間帯はこのstackとrepository scaleに対するreferenceです。Java、Rust、大規模monorepo、mobile buildなどへそのまま移植しません。別stackは別profile/corpusで追加し、このrepositoryにはsample appを置かない原則を維持します。

## 8. Calibration

最初のsolo runは時間baselineを作ると同時に、case designの校正にも使います。

- acceptanceが即時passするcaseはfixture defectを疑う
- 全providerがtask解釈で失敗するcaseはtask envelopeを修正し、revisionを上げる
- S/M/L descriptorに未記載のsetupが支配したらdescriptorを追加する
- gold leakageが見つかったcaseは全runをinvalid扱いにする
- case revisionを跨いだ時間は同一seriesに混ぜない

校正による修正は不都合な遅いsampleの削除ではありません。invalid reasonと元sampleを保持します。
