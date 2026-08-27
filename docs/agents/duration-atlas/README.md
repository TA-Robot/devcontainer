# Agent Duration Atlas operator guide

この文書は、このrepositoryに含まれるduration atlas toolchainのoperator向け正本です。目的は、agent taskに要した時間を、task構造、model/runtime、collaboration構成、environment、quality、censoringと結び付けた観測事実として残し、必要なcellだけを安全に参照できるようにすることです。

Atlasはrouterではありません。provider、model、effort、agent数、relationを順位付けせず、projectへ既定構成を与えません。どの条件を試すか、どの観測をprojectの判断材料にするかは、そのprojectの目的、risk、期間、review costに基づいて別途決めます。

## 1. 変えてはいけない原則

- 36 caseはtask corpusのcoverageです。provider × model × effort × relation × environmentの全組合せを測定済みという意味ではありません。
- `S` / `M` / `L`は構造的な大きさです。短時間・中時間・長時間という所要時間ラベルではありません。
- 単一観測はraw pointです。typical valueやbandには昇格しません。
- 同一case・同一primary stratumのrepeatだけが、同一case内のobserved rangeを作れます。異なるcaseを平坦化しません。
- requested model/settingと、runtimeで確認できたresolved/applied valueを分離します。requested valueをapplied valueとして補完しません。
- quality-pass、quality-fail、quality-unknownを混ぜません。timeoutやcancelledを速い完了として扱いません。
- exact cellが無ければ`unmeasured`です。近隣caseや別modelの時間を代入しません。
- credentialが存在しない、期限を確認できない、または安全window内に失効する場合、live runは開始前に拒否されます。そのcellは`unmeasured`のままであり、別providerへ自動fallbackしません。
- raw prompt、transcript、private reasoning、credentialはatlas、query、study reportへ保存しません。
- 数値capはresource/context safety guardです。統計精度、model quality、agent数の推奨値ではありません。

## 2. Corpusと設計正本

Versioned aggregate catalogは[`experiments/multi-agent-duration/catalog/cases.json`](../../../experiments/multi-agent-duration/catalog/cases.json)です。12 familyのそれぞれに`S`、`M`、`L`が一件ずつあり、合計36 caseです。

| Code | Family | Sizes |
| --- | --- | --- |
| F01 | `repository-trace` | S / M / L |
| F02 | `code-review` | S / M / L |
| F03 | `failing-test-diagnosis` | S / M / L |
| F04 | `bounded-implementation` | S / M / L |
| F05 | `refactor-migration` | S / M / L |
| F06 | `test-design` | S / M / L |
| F07 | `documentation-runbook` | S / M / L |
| F08 | `architecture-design` | S / M / L |
| F09 | `security-isolation` | S / M / L |
| F10 | `performance-resource` | S / M / L |
| F11 | `devcontainer-operations` | S / M / L |
| F12 | `evidence-synthesis` | S / M / L |

各caseの測定意図は、[`temp/multi-agent-duration-atlas/case-designs/`](../../../temp/multi-agent-duration-atlas/case-designs/README.md)内の次のpatternにある6文書が所有します。

```text
temp/multi-agent-duration-atlas/case-designs/<lowercase-case-id>/
  01-profile-and-question.md
  02-fixture-and-seed.md
  03-task-and-artifact-contract.md
  04-oracle-and-quality-rubric.md
  05-execution-and-analysis.md
  06-implementation-handoff.md
```

それぞれ、profileと測定質問、disposable fixture、agentへ見せるcontract、public/hidden oracle、実行・解析条件、実装handoffを定義します。[Case design index](../../../temp/multi-agent-duration-atlas/case-designs/INDEX.md)から全36 caseへ辿れます。case ID、rubric、capsule wording、sizeを変更するときは、実装だけを先に変えず、この6文書との整合をreviewします。

Runtimeのversioned入力は次です。

- family別のexclusive edit surface: [`experiments/multi-agent-duration/catalog/families/`](../../../experiments/multi-agent-duration/catalog/families/README.md)
- agentへ渡すcontent capsule: [`experiments/multi-agent-duration/capsules/`](../../../experiments/multi-agent-duration/capsules/)
- case、run、batch、atlasのcontract: [`experiments/multi-agent-duration/schemas/`](../../../experiments/multi-agent-duration/schemas/)
- deterministic fixture/evaluator実装: [`scripts/agent_duration_cases/`](../../../scripts/agent_duration_cases/)

## 3. Data flow

```text
six-document case design
        │
        ▼
family fragments + capsules + deterministic evaluators
        │
        ├── build catalog ──► versioned 36-case aggregate
        │                         │
        └── provider-free audit ◄─┘
                                  │
                                  ▼
                    explicit finite batch manifest
                                  │
                      dry-run ────┴──── live confirm
                                             │
                                             ▼
                              immutable validated run records
                                             │
                                             ▼
                              deterministic aggregate atlas
                                      │              │
                                      ▼              ▼
                                bounded query   Markdown study report
                                      │
                                      ▼
                             lookup-agent-duration skill
```

Provider-free calibrationがtaskとoracleを検証し、その後にだけ明示的なfinite manifestを作ります。manifest作成はproviderを呼びません。live generationは[`run-agent-duration-batch`](../../../scripts/run-agent-duration-batch)へ`--execute`と`--confirm-live-provider`の両方を渡した場合だけ開始されます。

## 4. Artifactの役割と保存場所

| Surface | 役割 | 更新規則 |
| --- | --- | --- |
| `experiments/multi-agent-duration/` | versioned catalog、capsule、schema | source reviewとcalibrationを通して更新 |
| `temp/multi-agent-duration-atlas/` | 設計、実験計画、review、implementation provenance | operator commandや現在値のruntime sourceにはしない |
| `<private-run-dir>/<study-id>/*.json` | live runのimmutable raw evidence | private directoryへatomic create。credentialは含めない。既存run IDを上書きしない |
| `generated/duration-atlas/current.json` | query/skillが読むmachine aggregate | validated raw run setからprovider-freeで再生成し、derived fileとしてatomic replace |
| `docs/agents/duration-atlas/studies/<study-id>.md` | 人間がauditするcontent-free study report | run-set digestを固定。releaseを残す場合はstudyごとに一意なpathを使う |
| `docs/agents/duration-atlas/README.md` | operator contract | この文書 |
| `project/.codex/skills/lookup-agent-duration/` | target projectへ配るbounded lookup skill | project templateからcopyし、詳細datasetをskill本文へ埋め込まない |
| `/usr/local/share/mira-duration-atlas/current.json` | Dev Container image同梱のversioned reference snapshot | image build時に固定。更新にはDev Container rebuildが必要 |

Raw run recordを`generated/`、`docs/`、skillへ複製しません。`temp/`には設計provenanceを残しますが、そこに書かれた検討中の数値をatlas観測値として返してはいけません。

## 5. Command inventoryと安全境界

| Command | Provider call | 必須boundary |
| --- | --- | --- |
| [`build-agent-duration-catalog`](../../../scripts/build-agent-duration-catalog) | なし | `--revision`、`--published-at`; mutationには`--write` |
| [`audit-agent-duration-corpus`](../../../scripts/audit-agent-duration-corpus) | なし | `--max-cases`と、`--fail-fast` / `--continue-on-failure`のどちらか |
| [`plan-agent-duration-batch`](../../../scripts/plan-agent-duration-batch) | なし | 明示filter、series row、ID、repeat、rotation、run/deadline/output cap |
| [`run-agent-duration-batch`](../../../scripts/run-agent-duration-batch) | defaultはdry-run | `--output-dir`、`--image`; liveには`--execute --confirm-live-provider`の両方 |
| [`build-agent-duration-atlas`](../../../scripts/build-agent-duration-atlas) | なし | `--output`、`--max-records` |
| [`query-agent-duration-atlas`](../../../scripts/query-agent-duration-atlas) | なし | `--max-rows`、`--max-output-bytes` |
| [`report-agent-duration-study`](../../../scripts/report-agent-duration-study) | なし | `--output`、`--max-series`、`--max-cases`、`--max-output-bytes` |
| [`lookup-agent-duration`](../../../project/.codex/skills/lookup-agent-duration/SKILL.md) | なし | queryへcontext capとfilterを渡す |

### Cap contract

| Surface | Contract |
| --- | --- |
| corpus audit | `max-cases`: 1..512。filter後、fixture生成前に検査 |
| batch planner | `max-runs`: 1..36、`repeat`: positive、`rotation-seed`: non-negative、deadline: `> 0`かつ`<= 604800`秒、provider timeout: `> 0`かつ`<= 3600`秒、evaluator timeout: `> 0`かつ`<= 300`秒、per-run output: 1024..67108864 bytes。deadlineは少なくとも一件のprovider + evaluator budgetを収容すること |
| batch runner | manifest内の`max_runs`、deadline、per-run timeout、evaluator timeout、output capを使用。automatic retryなし |
| atlas builder | `max-records`: 1..5000が必須。`max-input-bytes`と`max-output-bytes`のhard ceilingは512 MiB。CLI defaultはそれぞれ64 MiB / 32 MiB |
| atlas query | `max-rows`: 1..1000、`max-output-bytes`: 1..32 MiB。両方必須 |
| study report | `max-series`: 1..5000、`max-cases`: 1..5000、`max-output-bytes`: 1..512 MiB。すべて必須 |

Batch plannerは、選択case数 × 明示series row数 × repeat数をpreflightし、`--max-runs`またはhard cap 36を超えるmanifestを作りません。Queryはcap到達時にwhole row単位で縮小し、`truncation`と理由を返します。Study reportはsilent truncationせず、全series/caseをcap内で表示できなければ失敗します。

## 6. End-to-end operation

以下はcommand templateです。`<...>`はoperatorが観測目的と利用可能なruntimeから明示的に置き換えます。記載したmodel、effort、repeat、agent count、timeoutのplaceholderは推奨defaultではありません。

### 6.1 Catalogをcomposeして確認する

Family fragmentsからaggregateを再composeし、checked-in catalogとの差分を確認します。

```bash
scripts/build-agent-duration-catalog \
  --revision <positive-catalog-revision> \
  --published-at <UTC-timestamp>
```

意図的にcatalog revisionを進めるときだけ`--write`を追加します。

```bash
scripts/build-agent-duration-catalog \
  --revision <new-positive-catalog-revision> \
  --published-at <UTC-timestamp> \
  --write
```

Commandは12個のfamily fragment、各fragmentのS/M/L、case ID prefix、capsule digest、schemaを検査します。Family実装者はaggregateを直接編集せず、fragmentを変更してからcomposeします。

### 6.2 Provider-free corpus auditを行う

Auditはdisposable fixtureをbuildし、initial failure、private known-good、snapshot reproducibility、declared negative mutantとfailed criterionをdeterministic evaluatorで検査します。AI providerやcredentialは使用しません。

```bash
scripts/audit-agent-duration-corpus \
  --catalog experiments/multi-agent-duration/catalog/cases.json \
  --family <family> \
  --max-cases <filtered-case-cap> \
  --continue-on-failure \
  --isolated-image <network-disabled-evaluator-image> \
  --evaluator-timeout-seconds <evaluator-timeout> \
  --output <private-audit-record.json>
```

`--family`と`--case-id`はrepeat可能で、両方を指定するとintersectionです。未指定なら全catalogが対象になります。綴り間違いとempty selectionは失敗します。最初のfailureで止める場合は`--continue-on-failure`の代わりに`--fail-fast`を選びます。`--isolated-image`を省略したtrusted calibrationはlocal evaluatorを使用します。

### 6.3 Explicit finite manifestを作る

現在のbatch plannerはC0 primary-only calibration用です。これは一つの測定relationであり、通常projectへ一人構成を推奨する意味ではありません。Multi-agent relationの観測は別のversioned manifest/configuration contractで明示し、query時にはactual participant/worker countをprimary stratumとして扱います。

```bash
scripts/plan-agent-duration-batch \
  --catalog experiments/multi-agent-duration/catalog/cases.json \
  --output <private-batch-manifest.json> \
  --batch-id <batch-id> \
  --study-id <study-id> \
  --block-id <observation-block-id> \
  --provider <codex-or-claude-or-grok> \
  --model <explicit-model-id> \
  --effort <explicit-provider-supported-effort> \
  --family <family> \
  --size <S-or-M-or-L> \
  --rotation-seed <non-negative-seed> \
  --repeat <explicit-repeat-count> \
  --max-runs <explicit-run-cap-up-to-36> \
  --deadline-seconds <batch-deadline> \
  --timeout-seconds <per-run-timeout> \
  --evaluator-timeout-seconds <evaluator-timeout> \
  --output-bytes-cap <per-run-output-byte-cap>
```

少なくとも一つの`--case-id`、`--family`、`--size`が必要です。複数seriesを測る場合は`--provider`、`--model`、`--effort`を同数だけrepeatします。同じ位置の三値が一行になり、暗黙のCartesian productにはなりません。

Provider surfaceが現在受理するeffort labelは次です。これはCLI compatibility listであり、qualityの順位や推奨ではありません。

- Codex: `low`, `medium`, `high`, `xhigh`, `max`, `ultra`
- Claude: `low`, `medium`, `high`, `xhigh`, `max`
- Grok: `medium`, `high`, `xhigh`, `max`

PlannerはS/M/Lをseed付きでinterleaveし、catalog digest、repeat、run ID、全budgetをmanifestへ固定します。modelやeffortを推測せず、`terra`、`low`、その他の値を暗黙選択しません。Manifestはimmutable createであり、同じpathを上書きしません。

### 6.4 必ずdry-runしてからlive実行する

`--execute`を付けない実行はprovider-freeです。Manifest/case/digest/order/effort surfaceを検査し、planned/existing statusだけを返します。

```bash
scripts/run-agent-duration-batch \
  <private-batch-manifest.json> \
  --output-dir <private-run-dir>/<study-id> \
  --image <frozen-evaluator-and-provider-image>
```

Live generationには二つのflagを同時に指定します。

```bash
scripts/run-agent-duration-batch \
  <private-batch-manifest.json> \
  --output-dir <private-run-dir>/<study-id> \
  --image <frozen-evaluator-and-provider-image> \
  --codex-auth <private-codex-auth.json> \
  --claude-auth <private-claude-auth.json> \
  --grok-auth <private-grok-auth.json> \
  --execute \
  --confirm-live-provider
```

Manifestに無いproviderのauth flagは省略できます。省略時は各providerの標準user pathを使います。Credential sourceはregular/private/owner-owned JSONであることと、run timeout + refresh marginの間有効であることをprovider呼び出し前に検査します。Unavailableまたはfreshness unknownならrecordを作らず停止するため、その条件は`unmeasured`です。Credential内容やpathはrun recordへ永続化しません。

Runnerはmanifest orderで一件ずつ実行し、自動retryしません。Infrastructure failureでbatchを停止し、残りdeadlineが一件分のprovider + evaluator budget未満なら次を開始しません。Quality failは観測結果なので、infrastructureが成功していれば次の明示entryへ進みます。

### 6.5 Exact-match resume

同じmanifestと同じ`--output-dir`でもう一度実行すると、`<run-id>.json`が存在するentryを再生成せず検査します。再利用には、少なくとも次がmanifestと一致する必要があります。

- run ID、case ID、study ID、block ID
- catalog digest
- C0 primary-only relation、participant actual = 1、worker actual = 0
- provider
- requested model alias
- requested effort

一致したrecordは`existing`になります。一つでも違えばfail closedし、上書きも自動retryもしません。Infrastructure failureを再測定したい場合も、既存runを削除せず、新しい明示run IDを持つmanifestを作ります。Applied settingとresolved modelは後段のatlas primary stratumでrequested値から分離されます。

### 6.6 Validated runsからatlasをbuildする

```bash
scripts/build-agent-duration-atlas \
  <private-run-dir>/<study-id> \
  --output generated/duration-atlas/current.json \
  --max-records <explicit-record-cap> \
  --max-input-bytes <explicit-input-byte-cap> \
  --max-output-bytes <explicit-atlas-byte-cap>
```

Builderはschema-v2 runだけを受理し、duplicate run ID、conflicting case identity、invalid requested/applied stateを拒否します。Seriesはstudy、profile、configuration、全participant、model identity、generation setting、CLI/surface、environmentのexact combinationです。Caseはseries内にnestされ、repeatとbetween-case variationを分離します。

Atlasは次を保持します。

- source run-set digestとobservation window
- raw duration point、および同一case repeatが二件以上あるときだけobserved range
- quality-pass / quality-fail / quality-unknown counts
- evaluator status、criterionまたはaggregate-check score、存在するfailed criterion IDs
- complete / right-censored / administratively-censored countsとsafety cap
- first-artifactの`progress-envelope` / `not-observed` / `not-applicable` / `unknown`

Aggregate生成はprovider-freeで、derived outputをatomic replaceします。

### 6.7 Exact queryを行う

まずcoverageで利用可能なdimension valueを調べます。

```bash
scripts/query-agent-duration-atlas \
  generated/duration-atlas/current.json \
  --mode coverage \
  --format markdown \
  --max-rows <context-row-cap> \
  --max-output-bytes <context-byte-cap> \
  --family <family> \
  --size <S-or-M-or-L>
```

次に、必要なprimary fieldsを指定してsummaryを一cellへ絞ります。

```bash
scripts/query-agent-duration-atlas \
  generated/duration-atlas/current.json \
  --mode summary \
  --format markdown \
  --max-rows <context-row-cap> \
  --max-output-bytes <context-byte-cap> \
  --family <family> \
  --size <S-or-M-or-L> \
  --provider <provider> \
  --requested-model <requested-model-id> \
  --setting-status <applied-or-rejected-or-not-advertised-or-unknown> \
  --participants-actual <observed-participant-count> \
  --workers-actual <observed-worker-count> \
  --execution-surface <surface> \
  --image-digest <runtime-image-digest>
```

`--setting-applied-value`は`applied_value`が実在するsettingだけにmatchします。Requested-onlyまたはunknown settingは、requested値が同じでもmatchしません。Summaryが複数cellにmatchすると`refine`を返し、勝手にpoolしません。Matchが無ければ`unmeasured`とavailable identifiersだけを返します。

`compare`はuserが明示したdimensionだけを`--compare-by`へ、`curve`は観測済みの`participants-actual` / `workers-actual` / `peak-concurrent`だけを`--curve-by`へ指定します。Curve outputのinterpolationは常に`none`です。`audit`はsource run digestとstudy report pathを返し、`explain`は解釈referenceを返します。

### 6.8 Markdown study reportを生成する

```bash
scripts/report-agent-duration-study \
  generated/duration-atlas/current.json \
  --catalog experiments/multi-agent-duration/catalog/cases.json \
  --output docs/agents/duration-atlas/studies/<study-id>.md \
  --max-series <explicit-series-cap> \
  --max-cases <explicit-case-strata-cap> \
  --max-output-bytes <explicit-report-byte-cap>
```

Reportはvalidated atlasだけを読み、raw runを直接読みません。Methodology、run-set digest、observation window、exact environment/model/requested/applied/surface、family/size coverage、各caseのraw point/range、quality/censor counts、content-free scoreとfailed IDs、limitationsを出します。Catalog digestが一致しない、case revisionが違う、atlas caseがcatalogに無い、または36 cellの一部が未測定なら明示します。Derived Markdownはcap検査後にatomic create/replaceされます。

## 7. lookup-agent-duration skill

Target project向けcopy sourceは[`project/.codex/skills/lookup-agent-duration/`](../../../project/.codex/skills/lookup-agent-duration/SKILL.md)です。Project templateを導入すると、skillはtargetの`.codex/skills/lookup-agent-duration/`に置かれます。既存projectへ追加するときは、既存`.codex`内容を確認してこのdirectoryだけをcopyします。

```bash
mkdir -p <target-project>/.codex/skills
cp -a \
  project/.codex/skills/lookup-agent-duration \
  <target-project>/.codex/skills/
```

Skill wrapperはproviderを呼ばず、bounded query CLIを実行します。

```bash
python3 <target-project>/.codex/skills/lookup-agent-duration/scripts/query_atlas.py \
  --mode summary \
  --format markdown \
  --max-rows <context-row-cap> \
  --max-output-bytes <context-byte-cap> \
  --family <family> \
  --size <S-or-M-or-L>
```

Atlas discovery orderは次です。

1. wrapperの`--atlas <path>`
2. `AGENT_DURATION_ATLAS_PATH`
3. current working directoryまたはskill directoryから上方向に見つかる`generated/duration-atlas/current.json`
4. skill package内の`assets/current.json`がある場合
5. image同梱の`/usr/local/share/mira-duration-atlas/current.json`

`--print-atlas-path`で実際に選ばれたsourceを確認できます。`AGENT_DURATION_QUERY_COMMAND`はquery executableを明示的に差し替えるoperator overrideです。

Dev Container imageは、root-ownedな`query-agent-duration-atlas` runtimeと、build時点のversioned system snapshotを同梱します。Target projectの`PYTHONPATH`をruntimeへ持ち込まず、bundled schemaで検証します。Project aggregateまたは`AGENT_DURATION_ATLAS_PATH`はsystem snapshotより優先されるため、project-localな新しいatlasはimageを変えず利用できます。System snapshot自体を更新した場合はDev Containerをrebuildしてください。単なるwindow reload、container restart、reopenではimage内snapshotは更新されません。

Rebuild後はproviderを呼ばずにinstall surfaceを確認できます。

```bash
command -v query-agent-duration-atlas
test -r /usr/local/share/mira-duration-atlas/current.json

query-agent-duration-atlas \
  /usr/local/share/mira-duration-atlas/current.json \
  --mode coverage \
  --format json \
  --max-rows <context-row-cap> \
  --max-output-bytes <context-byte-cap>
```

VS Code / Cursorではsystem snapshotを更新したcommitへ移動した後、`Dev Containers: Rebuild and Reopen in Container`を実行します。Project-local aggregateだけを更新した場合はrebuild不要です。

## 8. Evidenceの読み方

### Requested / resolved / applied

- `requested_alias`はoperatorがmanifest/CLIへ渡したmodel名です。
- `resolved_id`はprovider/runtimeが確認できた場合だけ存在します。`identity_confidence`を必ず併記します。
- generation settingは`requested_value`と`status`を常に分けます。
- `applied_value`は`status=applied`のときだけ存在します。`unknown`、`rejected`、`not-advertised`から生成しません。
- CLI version、source、execution surface、permission mode、runtime image/environmentが変われば別seriesです。

### Quality

- `quality-pass-user-result`はquality-passしたrunのuser-result waitです。
- `quality-fail-terminal`と`quality-unknown-terminal`は失敗またはquality不明のterminal observationで、成功時間へ混ぜません。
- Scoreは`criterion`または`aggregate-check`のresolutionを保持します。
- `failed_check_ids`はatlas sampleに存在するときだけ表示します。Rubric textや欠けたcriterionをreport/query側で推測しません。
- Offline evaluator runtimeはuser waitとは別metricです。

### Censoringとfirst artifact

- `right-censored`はtimeout capまで未完了だった観測です。完了時間ではありません。
- `administratively-censored`はcancel/interruptionです。
- Censored terminal値にはsafety capを併記します。
- First artifact時間は`progress-envelope`が観測されたときだけ存在します。Final response timeから逆算しません。

### Evidence state

| State | 許される表示 |
| --- | --- |
| `single-observation` | 一件のraw pointとexact conditions |
| `same-case-repeat` | 同一case内のraw pointsとobserved min/max |
| `family-provisional` | 複数case strataがある事実。family-wide typical値とは呼ばない |
| `not-assessed` characterization | study-specific precision/coverage criteriaが無いため昇格しない |

## 9. Failure、resume、exit status

- Configuration/schema/input errorは通常exit 2です。
- Corpus auditはcalibration failをexit 1、passをexit 0で返します。
- Batch runnerはdry-run/completedをexit 0、deadlineまたはinfrastructure stopをexit 1で返します。
- Queryの`unmeasured`は正しいdata answerであり、command failureではありません。
- Batch manifestのcatalog digestが現在のcatalogと違えば実行しません。新しいcatalog revisionには新しいmanifestを作ります。
- Atlasはduplicate run IDやconflicting case revisionを受理しません。
- Query/reportは未知atlas schemaをfail closedします。
- Atomic raw record/manifest outputは既存fileを上書きしません。Atlas/reportはderived artifactなので、完全な新内容を用意してcap/schemaを検査した後だけatomic replaceします。

## 10. Datasetを更新するときのchecklist

1. Caseの意味を変える場合は、該当caseの6 design docsを先にreviewする。
2. Family fragment、capsule、recipe/evaluator、focused testを同じcase identityへ揃える。
3. Provider-free corpus auditでinitial fail、known-good、negative mutantsを通す。
4. Catalog revision/published timestampを明示してaggregateを再composeする。
5. 新しいcatalog digest、study/block/run ID、series row、repeat、budgetを持つfinite manifestを作る。
6. Dry-runを確認し、credentialが有効な明示seriesだけをlive実行する。Unavailable seriesは未測定のまま残す。
7. Immutable run recordsからatlasを再buildし、source run-set digestを確認する。
8. Coverage/summary queryとMarkdown study reportを生成し、unmeasured、quality、censoring、requested/applied差をreviewする。
9. `generated/duration-atlas/current.json`をtarget projectへ提供する。
10. Versioned system snapshotを更新した場合はDev Container imageをrebuildする。
11. Skill contractを変更した場合は`project/.codex/skills/lookup-agent-duration/`からtarget projectのcopyを更新する。

Datasetを増やしても、atlasからmodel/provider/agent数のdefaultやrouting policyを生成しません。Atlasが提供するのは、projectが自分の条件を組み立てるための、exactで欠測を隠さない観測材料です。
