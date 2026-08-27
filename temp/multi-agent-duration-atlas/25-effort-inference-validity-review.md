# Effort inference validity review

実施日: 2026-08-27

## 結論

旧releaseのflatなcriterion scoreから、`mediumで十分`、`higher effortでも改善しない`、または`問題が飽和している`とは結論できない。現在の108 terminal recordsは時間、provider terminal state、criterion通過数を観測した有効な運用記録だが、effortとqualityの因果比較には次の3 gateが別々に必要である。

1. **Case design gate**: taskから採点基準を識別でき、evaluatorが未公開語彙や一つの好みを正解としていない。
2. **Observation gate**: 特にquality fail時、生成artifactを再読してsemantic false negativeと本当の不足を区別できる。
3. **Comparison gate**: 同一case revision / fixture identity、applied setting、repeatまたはsingleton制約、infrastructure populationを揃え、quality measureに設定差を識別するheadroomがある。

旧比較は3 gateを同時には満たさない。したがって飽和仮説もeffort不足仮説も現時点では未識別である。

## Case design audit

同一caseで複数effortを観測した14 case revisionを、capsule、公開validator、hidden evaluator、known-good/mutant校正から再監査した。

| Status | Case revisions | Interpretation |
| --- | --- | --- |
| eligible | F01-S r1, F02-M r1, F03-L r1, F04-S r1, F04-L r1, F05-M r1, F06-L r2, F07-S r1, F08-M r1, F08-L r1, F10-S r5, F11-M r1, F12-L r3 | visible contractとoracleは整合。ただし個々の旧fail observationはartifact未保持ならconditional |
| conditional | F06-L r1, F09-L r1, F10-S r3/r4 | fixture identityの非決定性、lexical proxy、またはscope failureの重複採点があり、causal effort比較へ直接使わない |
| ineligible | F10-S r1/r2 | hidden controlled vocabulary、または不完全な公開output contractでagent能力とcase constructionを識別できない |
| ineligible | F12-L r1/r2 | preferred architecture、invented identifier、または不完全な公開artifact shapeを要求 |

`known-good pass + mutants reject`は、少なくとも一つの受理artifactと既知の誤りを識別することだけを示す。初見agentが公開情報から正解を構成できること、複数の意味的に妥当な正解を受理することは示さない。

## Observation audit

旧108 recordsは全件`content-free-only`で、task artifactを保持していない。このためaudit済みeligible caseでも、quality failは`task-artifact-not-retained`としてconditionalに降格する。

Current run-level classification:

| Observation status | Runs | Meaning |
| --- | ---: | --- |
| eligible | 11 | case designがeligibleでquality pass。比較gateは未評価 |
| conditional | 53 | eligible designのquality failだがartifactなし |
| excluded | 21 | ineligible revision、またはquality unknown |
| not-audited | 23 | effort curve対象外でcase design audit未実施 |

この分類はterminal durationを無効にしない。conditional/excludedでも、providerが何秒でterminalになったか、infrastructure failureだったか、どのcriterion IDが落ちたかは観測事実として残る。無効になるのは、そこから`推論量を増やしても品質が伸びなかった`と解釈する部分である。

## Comparison audit

旧effort curveにはさらに次の制約がある。

- 多くのcellは各1回で、provider load、順序、cache、時刻変動を分離できない。
- Solはrequested effortを記録したが、runtimeからapplied値を独立確認できずstatus=`unknown`である。
- Grok medium/high/xhighはappliedを観測したが、maxはprovider surfaceでrejectされた。
- F06-Lのmedium/high差は大きいが、旧medium identity conflictを再測定した後も各cell singletonである。
- Claudeはcurrent credential barrierによりplanned matrixが未測定である。

よって、比較queryはcase/observation gateだけを表示し、comparison gateを`not-evaluated`のまま残す。`eligible-pending-comparison-gates`はwinnerやcausal resultではない。

## Observed-pattern reclassification

旧結果をcase / provider内のcriterion signatureまで戻して見ると、`flat`という一種類の現象ではなく、少なくとも次の異なる状態が混在している。

| Pattern | Concrete observations | What can be said | What cannot be said |
| --- | --- | --- | --- |
| evaluator ceiling | F04-LはCodexのmedium/high/xhigh/max/ultraが全て4/4 pass。Grokもapplied medium/high/xhighが4/4 pass | このexact task/oracleでは測定scoreに上方向の余地がない | model reasoning自体が飽和した、または他taskでもmediumで十分とは言えない |
| candidate effort signal | F06-L Codexはrequested mediumが3/11 fail、requested highが11/11 pass | 再測定する価値がある最大の差 | 各cell singletonかつapplied effort未確認なので、差をeffortへ帰属できない |
| within-cell variance | F04-S Grokのapplied mediumは5/5 passと4/5 failがあり、別runはstartup failure | nominally同じcellにも実行間変動がある | mediumとhighの一点差をeffort効果として読むことはできない |
| artifact/task floor | F03-L Grokはmedium/high/xhighの全てでworkspace 3 checksを含む0/9 | 高い推論量でも採点対象artifactへ到達しなかった観測 | reasoning不足、tool-use failure、task misunderstandingのどれかはartifactなしに分離できない |
| invariant criterion bottleneck | F01、F07、F08-M、F11はprovider内でmedium/highのfailed criterion setが同一。F12-L r1 Codexもmedium/high/xhigh/maxで5/12と同一set | 同じboundaryで繰り返し止まった | 問題飽和、固定strategy、prompt解釈、semantic false negativeのどれかは決められない |
| non-monotonic singleton | F03-L Codexはmedium/xhigh/maxが7/9だがhighは5/9。F05-M Codexはmedium 5/7、high 4/7。F08-L Codexはmedium 9/11、xhigh/max 8/11 | 少なくとも旧一点観測は単調なeffort curveではない | higher effortが害であるとも、mediumが最適とも言えない |
| invalid or unavailable cell | F04-S Claudeはquality未観測のstartup/configuration/sandbox failure。Grok maxはF04-L/F12-Lでsetting rejection | provider surfaceまたはinfrastructure populationとして別扱いにする | quality failや高速完了としてeffort curveへ混ぜられない |
| oracle mismatch risk | F10-S r1とF12-L r1は非公開語彙またはpreferred architectureを要求。F09-L r1はlexical proxyを含む | 旧scoreはそのevaluatorへの一致度 | open-endedな問題解決能力やeffort効果を直接表さない |

したがって、ユーザーの「問題側が飽和していたのでは」という仮説はF04-Lの**測定上限**には当てはまる。一方、all-failまたは同じcriterionで止まったcaseを「難しさが飽和した」と呼ぶ根拠はない。そこでは測定の床、固定strategy、oracle mismatch、artifact未生成を分離できていない。必要なのは一律に難しくすることではなく、patternごとに異なる再測定である。

1. Ceiling caseでは、同じrubricのrepeatを増やすより、追加のchallenge criterionまたはより高いcase revisionを用意する。
2. Candidate signalでは、同一fixture、applied setting、複数repeatで差の再現性を確認する。
3. Floor / invariant bottleneckでは、task artifactを保持し、どこまで実装・記述したかを人手入力なしで再評価する。
4. Infrastructure / rejected settingはquality populationから分離し、provider capability観測として扱う。

## Implemented repair

### F10-S revisions 2–4 audit and revision 5 repair

- Revision 2はcandidate、relation、counter、strategy、preservation vocabularyを公開したが、完全なoutput shapeとsole editable pathを公開し切れていなかった。
- Grok medium/high各2回のlive floorで、全4回がinfrastructure success / quality failになった。medium 2回はsemantic root causeへ到達したがcontractと異なるnesting/field shapeで、high 2回は許可対象外pathを編集して`performance.json`を残さなかった。これはeffort差ではなくcase construction failureとして除外する。
- Revision 3はtemplateとmappingを公開したが、sole editable pathをpublic validatorで検査せず、hidden 5 criteriaそれぞれのsetupでscope違反を再検査していた。最初のlive 2件ではmedium artifactが全semantic obligationsを満たした一方、2つの契約外scratch pathだけでhidden 5/5がまとめてfailしたため、scoreをeffort evidenceに使えない。
- Revision 4はpublic edit-surface checkを追加したが、hidden setupの旧scope checkを除去し忘れ、最初のlive medium 1件で同じ5重計上が残っていることを確認した。
- Revision 5はbenchmark出力をpipeで渡し、public validatorだけが`git status`とcontractのeditable pathsを照合する。hidden criteriaはprotected input integrityと個別semantic obligationだけを検査する。どのcandidateがprimaryかだけはcounterとsourceから導出させる。

### F12-L revision 2 audit and revision 3 repair

- Revision 2はclaim / option / constraint / refresh vocabularyとbounded decision spaceを公開したが、全entity field、required dependency、editable surfaceのshapeを公開し切れていなかったためlive比較前にineligibleへ戻した。
- Revision 3は`decision-record.template.json`と`DECISION-RECORD.template.md`を追加し、required control evidence、decision dependencies、phase/gate/rollback/unknown/refresh shapesを公開する。
- D migration bridge後のtargetとして、evidence/controlを満たすAまたはBを受理する。D→B known-goodに加え、異なるcontrol IDsとD→A targetを使う独立valid alternativeをfull-pass校正する。

### Future observation retention

- 新しいbatch plannerは`task-artifacts` retentionをdefaultにする。
- 保存対象はfixture recipeが宣言したtask outputだけで、最大16 files、1 file 256 KiB、合計1 MiB、UTF-8に限定する。
- provider credentialの実値を検出したartifactは本文を保存せずdigestだけ残し、snapshotを`partial`にする。
- unexpected path、non-UTF-8、non-regular、size capも`partial`として推論gateを通さない。
- unexpected pathは内容やpathを保存せず、tracked / untracked / deletedの件数だけを残して、自動failure adjudicationの材料にする。
- raw provider transcript、prompt、private reasoning、stderrは引き続き保存しない。
- Snapshot処理がcompleteでもallowlisted task artifactが実在しなければ、quality failは`task-artifact-missing`としてconditionalにする。

## Machine-readable delivery

- Validity source: `experiments/multi-agent-duration/validity/effort-quality.json`
- Schema: `experiments/multi-agent-duration/schemas/validity.schema.json`
- Validator: `scripts/validate-agent-duration-validity`
- Atlas companion: `generated/duration-atlas/current-validity.json`
- Skill companion: `project/.codex/skills/lookup-agent-duration/assets/current-validity.json`
- Dev Container companion: `/usr/local/share/mira-duration-atlas/current-validity.json`

Atlas queryとhuman reportはvalidity companionを結合し、case design、observation artifact auditability、未評価のcomparison gatesを別々に出す。旧raw recordは変更せず、current Atlasへの採否はrelease dispositionで明示する。F10-S r1 / F12-L r1の時間観測も保持する。

## Finite remeasurement design（subsequently executed）

次のlive remeasurementはF10 revision 5 / F12 revision 3 caseに対して、少なくとも次を固定してから行う。

1. 同一fixture identity。
2. task-artifact snapshot `complete`。
3. provider runtimeでapplied effortを観測できる系列、またはrequested-onlyであることを明示した別population。
4. medium/high/xhigh/maxを目的に応じて含め、max拒否はquality cellへ混ぜない。
5. 各cellのrepeat数をmanifestで明示し、singletonならcausal curveとして扱わない。
6. 全cellが満点ならceiling-limitedと明示し、effort効果なしではなく、より識別力のあるcase revisionへ送る。

この再測定が終わるまで、もっとも強い安全な結論は「旧データでは問題飽和とeffort効果なしを識別できない」である。

## 2026-08-28 remeasurement amendment

34-run finite waveの結果は`26-wave8-identifiable-remeasurement.md`へ固定した。結論は単一の
`medium sufficient`や`higher effort useless`ではなく、case/providerごとに異なる。

- F10-S r5はSol requested medium/highとも4/4 total full-pass、Grok applied medium/highも
  semantic criterion 20/20 passで、測定上限に達した。
- F12-L r3 Solはmedium/high/xhighの各1件がfull-passした一方、各2件目とmax 2件は一つの
  bounded-evidence criterionを落とした。単調なdepth curveではない。
- F06-L r1はrepeat内varianceが大きく、さらにhash-seed由来のfixture identity分岐が判明した。
  Revision 2へ修復するまでr1をcausal effort evidenceへ使わない。
- Grok F06/F12はrequired artifact missingが支配し、problem saturationではなくtask-entry floor。

したがって、現時点で提供できるのはexact conditionの時間・criterion・artifact auditabilityで
あり、project-independentなmodel/effort選定規則ではない。
