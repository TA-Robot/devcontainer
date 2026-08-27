# Complete corpus duration-atlas release

実施日: 2026-08-27

Status: **current study release complete**。12 family × S/M/Lの全36 caseを各6文書で設計し、fixture/evaluatorを実装・校正したうえで、有限live batchを安全境界まで実行した。108件のimmutable terminal recordをatlas schema v2へ集約し、人間向けreport、bounded query skill、Dev Container同梱snapshotまで同一run-setから生成した。

ここでいうcompleteは、計画したcase corpus、実行可能だったprovider block、拒否・credential barrierを含む実験provenance、配布経路が閉じたという意味である。provider × model × effort × collaboration × environmentの無限に近い全組合せを測り切ったという意味ではない。未測定cellは値を補完せず`unmeasured`として残す。

## 1. Release artifacts

| Artifact | Contract |
| --- | --- |
| `generated/duration-atlas/current.json` | atlas schema v2、108 records、36 case IDs、104 primary strata |
| `docs/agents/duration-atlas/studies/current.md` | raw point、quality、censoring、identity、settingを省略しないcontent-free report |
| `project/.codex/skills/lookup-agent-duration/assets/current.json` | atlasとbyte-identicalなtarget-project skill snapshot |
| `/usr/local/share/mira-duration-atlas/current.json` | Dev Container imageへroot-owned / mode 0444で入るsnapshot |
| `final-release-disposition.json` | canonical input grouping、除外record、calibration-only、未測定blockの機械可読なrelease判断 |

Release identity:

- atlas schema: `2`
- canonical records: `108`
- unique catalog case IDs: `36`
- observation window: `2026-08-26T11:34:19.672Z` – `2026-08-27T06:07:15.461Z`
- run-set digest: `sha256:402b7a5bb5efa351bd31f768a0058f296a2902a5586d327347bf8fac86244b3f`
- atlas / skill snapshot SHA-256: `0713b2b9b3a1ce696ff5f3ec470e9265aa0e1f574f8ace231a7fd103132f7e62`
- human report SHA-256: `113a4b060ca94f3e6a5bea4d69d11593ebb917f50557e9d00dcf23dce59a8d1d`

## 2. Case design and implementation closure

全caseについてprimaryが次の6文書を先に完成させ、そのhandoff単位で独立実装を委譲し、返却後にprimaryがsource、oracle、negative mutants、contractをreviewした。

1. `01-profile-and-question.md`
2. `02-fixture-and-seed.md`
3. `03-task-and-artifact-contract.md`
4. `04-oracle-and-quality-rubric.md`
5. `05-execution-and-analysis.md`
6. `06-implementation-handoff.md`

Closure audit:

- 36 case × 6文書 = **216文書**
- INDEX status: **36 / 36 `observed`**
- family implementation: **F01–F12すべて実装済み**
- provider-free known-good: **36 / 36 pass**
- declared negative mutants: **153 / 153 reject**
- corpus audit wall time: **約1,278,850 ms**
- placeholder audit: case本文に未解決の`TBD` / `TODO` / `FIXME`なし

`observed`は「少なくとも一つのcontract-valid live terminal observationがある」というcase design statusであり、quality-passや全provider測定済みを意味しない。

## 3. Executed live matrix

今回の新規live blockはすべてC0 `primary-only`、fresh ephemeral session、isolated provider container、直列実行である。これはcalibration relationを固定しただけで、single-agent構成の推奨ではない。

| Provider / requested setting | Planned scope | Terminal observations | Result |
| --- | ---: | ---: | --- |
| Sol medium | all 36 + F09-S recovery + F06-L identity recovery | 38 | 36 breadth terminal、F09-S再試行もprovider result error、F06-Lをcurrent identityで再測定 |
| Sol high | family representative 12 | 12 | infrastructure success 12 |
| Sol xhigh | deep L 4 | 4 | infrastructure success 4 |
| Sol max | deep L 4 | 4 | infrastructure success 4 |
| Grok medium | family representative 12 | 12 | infrastructure success 12 |
| Grok high | family representative 12 | 12 | infrastructure success 12 |
| Grok xhigh | deep L 4 | 4 | infrastructure success 4 |
| Grok max | deep L 4 | 1 | first cellでprovider-wide setting rejection。残り3件は同じ拒否を消費して繰り返さず未測定 |
| Claude medium/high/xhigh/max | 12 / 12 / 4 / 4 | 0 new | CLIは存在するが`loggedIn:false`かつcredential freshness不明。generation前にfail closed |

Atlasには今回のlive blockだけでなく、wave 1–3の13 + 9 canonical terminal recordsも含む。最終108 recordsのoutcome populationは次の通り。

| Population | Count |
| --- | ---: |
| infrastructure success / quality pass | 15 |
| infrastructure success / quality fail | 81 |
| infrastructure failure / quality unknown | 12 |
| complete terminal censoring | 108 |
| right-censored | 0 |
| administratively-censored | 0 |

`quality fail`は実験失敗ではない。providerはterminal artifactを返し、isolated evaluatorがどのcriterionを満たさなかったかを記録できた有効な観測である。逆にinfrastructure failureの短時間値をtask completion時間へ混ぜない。

## 4. Provider and setting boundary findings

### Claude

Current CLIは`2.1.220`だが、観測時は`loggedIn:false`、auth methodなしだった。runnerはcredential freshnessを観測できない状態でlive generationを開始しない。したがってwave 7の32 planned cellsは、失敗時間を捏造せず`unmeasured`のまま保持した。wave 2のClaude 7 recordsはinstrumentation calibrationのterminal operational evidenceであり、task-completion / effort-performance populationへpoolしない。

### Grok max

`run-001-b555a63a5f2dc998`は約1.57秒で`generation-setting-rejected`となり、requested=`max` / status=`rejected`を記録した。同じprovider surfaceに対する残り3 cellは、provider generationを開始せずmachine dispositionへ残した。旧`grok-f04-l-46-max-20260827-r01`はpre-run metadataをapplied settingと誤認したinstrumentation-invalid recordなのでcanonical setから除外した。

### Requested versus applied

- Grok medium/high/xhighはsession metadataにより`applied`を確認できた。
- Grok maxは`rejected`を確認できた。
- Solはrequested値を記録したが、applied値をruntimeから独立確認できないためstatus=`unknown`を維持した。
- model aliasからresolved modelを推測していない。

## 5. Identity correction

旧Sol medium F06-L `run-021-e0e435c0d3282153`は、後続high/Grok runとcase IDおよびinstruction digestは同じでも、base SHAとbundle digestが異なっていた。このままeffort/provider比較へ入れるとfixture差をsetting差として誤読する。

そこで同一identityで`run-001-758f6d400a39baad`を再測定し、旧recordを`calibration-obsolete / same-revision-fixture-identity-conflict`として最終setから除外した。current comparison identityは次で固定される。

- base SHA: `a41685e60ec9e83713a0682e1209e09c7085e200`
- bundle digest: `sha256:4663cb59494a727556365cfe615251121817906daa9b0f98de76e7ccc062caac`
- instruction digest: `sha256:e95b2a3cd9c10ed97a6785a56b0e8e4ba88cc1271dc86d221b6d5576fec710c0`

Builderへdirectoryを広く渡さず、明示allowlistから108 recordsを生成した。Atlas sourceには全run IDとrun digestが入り、release dispositionとrun-set digestで再監査できる。

## 6. Representative raw observations

以下は、同一case identityで得た**各一回のraw point**である。傾向、typical値、provider順位、routing ruleではない。

| Case | Provider | Requested effort | Terminal wall | Criterion score |
| --- | --- | --- | ---: | ---: |
| F12-L | Sol | medium / high / xhigh / max | 236.9s / 364.1s / 488.5s / 722.1s | 5/12 / 5/12 / 5/12 / 5/12 |
| F03-L | Sol | medium / high / xhigh / max | 110.0s / 103.2s / 140.1s / 217.9s | 7/9 / 5/9 / 7/9 / 7/9 |
| F08-L | Sol | medium / xhigh / max | 249.1s / 342.0s / 372.6s | 9/11 / 8/11 / 8/11 |
| F09-L | Sol | medium / high / xhigh / max | 347.1s / 360.1s / 400.6s / 657.6s | 3/11 / 3/11 / 4/11 / 3/11 |
| F06-L | Sol | medium / high | 678.3s / 424.0s | 3/11 / 11/11 |
| F06-L | Grok | medium / high | 28.4s / 28.9s | 5/11 / 5/11 |
| F09-L | Grok | medium / high / xhigh | 219.8s / 288.5s / 278.0s | 5/11 / 5/11 / 5/11 |
| F12-L | Grok | medium / high / xhigh | 335.1s / 278.9s / 387.5s | 6/12 / 5/12 / 5/12 |
| F03-L | Grok | medium / high / xhigh | 35.6s / 66.0s / 48.4s | 0/9 / 0/9 / 0/9 |

同じlabelでも時間とqualityの関係はcaseごとに異なり、単調でもない。これが「high固定」「3 agents固定」のようなglobal defaultをatlasから生成しない理由である。repeatがないcellはばらつきを表さず、時刻、provider load、cache、順序効果も交絡している。

## 7. Query and skill delivery

`lookup-agent-duration` skillは巨大なreportを会話へ読み込まず、bounded queryで必要なcellだけ返す。

Discovery order:

1. explicit `--atlas`
2. `AGENT_DURATION_ATLAS_PATH`
3. nearest project `generated/duration-atlas/current.json`
4. skill `assets/current.json`
5. Dev Container `/usr/local/share/mira-duration-atlas/current.json`

Forward testでは、fresh agentが次を確認した。

- exact measured cellはraw point、quality score、requested/applied status、identity confidenceを落とさず読める。
- exact cellが無いClaude条件は`unmeasured`を返し、別providerや近傍effortで補完しない。
- `--print-atlas-path`は選択sourceを表示して終了する。
- helpにdiscovery order、environment override、context capを表示する。
- query responseはboundedで、atlasのraw `samples` bodyを漏らさない。

Requested effortは現在の`compare-by`軸ではないため、forward testではmedium/highをそれぞれexact summaryとして取得した。これは異なるstudyやquality populationを一つのpaired curveへ誤結合しない安全側の制約であり、利用者は各rowのstudy、identity、qualityを並べて読まなければならない。

Skill本文は判断原則だけに絞り、1.1 MiBの詳細snapshotはassetとして分離した。これにより通常promptのcontextを圧迫せず、必要なときだけ最大row/byte cap付きで参照できる。

## 8. Collaboration coverage boundary

Repositoryにはprimary-only、parallel decomposition、independent advice、iterative dialogue、independent alternatives、periodic bounded maintenanceの6 relationを表現できる有限manifest/control-planeがある。しかし現時点のcollaboration runnerはfake adapterだけで、actual provider / `agentctl` workerへ接続していない。

したがって今回の108 recordsはC0 primary-only calibration evidenceであり、multi-agent relation間の速度・品質比較値ではない。collaboration timing cellを測ったことにせず、queryもrecommendationを返さない。この境界は未実装を隠すためではなく、単独task atlasとmulti-agent topology効果を混同しないためのものだ。

## 9. Reproduction and integrity rules

- raw recordはimmutable。retryやrecoveryは新run IDで記録する。
- broad globでaudit JSON、manifest、derived atlas、invalid recordをbuilderへ渡さない。
- wave 3は`wave-3-disposition.json`のcanonical IDsだけを使う。
- final releaseは`final-release-disposition.json`の除外を適用する。
- atlasとskill snapshotはbyte-identicalにする。
- report内run-set digestはatlas sourceと一致させる。
- Dev Container snapshotはroot-owned / 0444、query runtimeはcaller `PYTHONPATH`を継承しない。
- exact cellが無ければ`unmeasured`。補間、ランキング、default routingをしない。

Historical wave 1–3 recordsは旧catalog digestを含むため、current reportはdigest mismatchを明示する。case revision / identity差がないことは別に検査済みであり、mismatchを隠してcurrent digestへ書き換えない。

## 10. Closure decision

このmilestoneは次を同時に満たしたため完了とする。

1. 全36 caseを各6文書で設計した。
2. 全family fixture/evaluatorを実装・provider-free校正した。
3. 実行可能なSol/Grok blockを有限実行し、Claude/Grok max boundaryをgeneration前または最初の拒否で確定した。
4. 失敗、quality、setting、identity、censoringを落とさず108 recordsへ集約した。
5. exact-match query、human report、target skill、Dev Container snapshotへ配布した。
6. 除外と未測定をmachine-readable dispositionへ固定した。

今後、新しいprojectでprovider/model/effort/relationを選ぶ際は、このreleaseを唯一の正解として扱わない。exact条件の観測事実と欠測を取り出し、そのproject固有の期限、risk、review cost、quality oracleを加えて次の有限studyを設計する。
