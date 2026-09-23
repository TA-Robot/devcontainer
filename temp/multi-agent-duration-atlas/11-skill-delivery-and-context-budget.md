# Skill deliveryとcontext budget設計

## 1. 目的

詳細なrun evidenceと、通常のcoding turnで必要な時間referenceは同じ粒度ではありません。

```text
raw run evidence / detailed study docs
  -> versioned aggregate
    -> deterministic bounded query
      -> compact skill response
```

devcontainer側には再検証可能な詳細を残し、target projectのagentへは必要なcellだけをskill経由で渡します。skillはatlas全体をpromptへ注入せず、selection ruleも生成しません。

## 2. Proposed skill

候補名: `lookup-agent-duration`

trigger例:

- 「Pythonの中規模bug diagnosisは何分くらいだった？」
- 「Codexのeffort別の実測時間を見せて」
- 「Grok 4.5と4.6のreview時間を比較した観測はある？」
- 「2 workerからsafe widthまでの並列化curveを確認して」
- 「agent同士の対話を一exchange増やすと過去には何分増えた？」
- 「このtaskに近いduration dataがあるか。なければ未測定と教えて」

skillの役割は**検索、条件照合、bounded rendering**です。taskの状況から構成を決定したり、未測定値を予測したりしません。

## 3. Skill package shape

`skill-creator`のprogressive disclosureに合わせます。

```text
lookup-agent-duration/
  SKILL.md
  agents/
    openai.yaml
  scripts/
    query_atlas.py
  references/
    profile-fields.md
    interpretation.md
```

skill内にREADME、change log、全study report、raw runを複製しません。

### SKILL.md

短いcore workflowだけを置きます。

1. user taskから明示されたfamily、size/profile、language、model/effort、collaboration、surface、contextを抽出する
2. 不明fieldを勝手に補完せず、query scriptへknown filterだけ渡す
3. exact cellを優先してbounded queryする
4. evidence state、観測window、identity/settings confidence、censoringを必ず表示する
5. `unmeasured`を許容し、近いcellを同一値として補間しない
6. decision/routing recommendationは、userがproject条件を別途与えた場合だけatlas外の判断として明示する

SKILL本文は500 lines未満という上限よりかなり短くし、一般的な統計説明や全field enumを置きません。

### `scripts/query_atlas.py`

data integrityとcontext capは自然言語instructionではなくdeterministic scriptで守ります。

- schema/version/digest検証
- exact primary-stratum filtering
- covariate filtering
- stale/unmeasured/not-observedの保持
- accepted-onlyとcensoring-aware viewの同時取得
- first-artifact resolutionが違うseriesの非混合
- raw secondsからdisplay resolutionへのrounding
- bounded row/byte/token estimate
- truncation時の明示とrefinement hint
- MarkdownとJSONのcompact output
- detailed documentへのrelative link/record ID

scriptはrouting score、provider ranking、nearest-neighbor duration推定を実装しません。

### References

- `profile-fields.md`: field enum、primary stratum / covariate / diagnosticの意味。queryが曖昧な場合だけ読む
- `interpretation.md`: censoring、evidence state、stale、unknown、online/offlineの短い解釈。結果説明が必要な場合だけ読む

詳細methodologyはdevcontainer側のauthoritative docsへlinkし、skill referenceへ重複コピーしません。referenceはSKILL.mdから一段で到達させ、深いlink chainを作りません。

## 4. Data layers

### L0: private/raw evidence

```text
/var/lib/mira-observations/duration-atlas/runs/...
/var/lib/mira-observations/duration-atlas/artifacts/...
```

- exact run eventと必要なlocal artifact
- prompt/transcript/goldはcontent-free aggregateと分離
- skillは通常この層を直接読まない

### L1: immutable study report

```text
docs/agents/duration-atlas/studies/<study-id>.md
```

- methodology、environment、全sample、invalid/censored、limitations
- 人間がauditするときの詳細
- skillは「詳細を見せて」と明示されたときだけ該当sectionを参照する

### L2: machine aggregate

```text
generated/duration-atlas/current.json
generated/duration-atlas/manifest.json
```

- primary-stratum key
- compact statisticsとsource study/run digest
- no prompt/transcript/private reasoning
- query scriptの通常input

### L3: compact answer

一回のskill invocationで必要cellだけを返します。L1/L0を全loadしません。

## 5. Context budget contract

数値はquality defaultではなくcontext-safety capとして扱います。実装時に設定可能にし、出力へcapの役割を明記します。

query configは`maxRows`と`maxOutputBytes`を必須にし、未設定・非正値ならunbounded fallbackせず失敗させます。具体値はskill forward-testで「必要な一cellを欠かさず、compare/curveがcontextを圧迫しない」ことを確認して決めるcontext-safety capであり、統計精度や推奨configurationの値ではありません。token数はmodel tokenizer依存なので補助estimateとし、byte capをdeterministic boundaryにします。

### Default compact mode

- exact matchを優先
- userが指定した比較軸以外は展開しない
- full raw sampleではなくband + counts + evidence state
- detailed study linkを返す
- cap到達時はsilent truncationせず`truncated=true`と、追加filter候補を返す

### Drill-down modes

| Mode | 用途 | Loadするもの |
| --- | --- | --- |
| `summary` | 一つのtask/configの時間目安 | exact aggregate cell |
| `compare` | userが指定したmodel/effort/configだけ比較 | selected cells |
| `curve` | worker width/dialogue depth | one configuration curve |
| `coverage` | 未測定/staleを確認 | compact coverage index |
| `explain` | 統計やfieldの意味 | relevant reference file |
| `audit` | 個別studyの根拠確認 | requested study doc only |

`audit`以外で全runをcontextへ展開しません。「全部見せて」と言われた場合も、まずindexとclickable detailed docsを返し、明示されたstudyだけを開きます。

## 6. Compact response contract

```text
Matched profile
  family / S-M-L profile / language / oracle

Observed configuration
  model identity confidence / applied setting / surface / context

Duration
  first valid artifact: <raw point | same-case range | family band | not observed>
  user result, quality-pass: <raw point | same-case range | family band | unavailable>
  censoring-aware wait: <unfinished at cap / restricted summary>
  aggregate worker time: <band>

Evidence
  n_cases / n_runs / n_pass / n_censored
  observation window / state / stale marker

Limits
  exact missing fields, no interpolation
  link to detailed study
```

この順なら、一つの短い回答で具体的な分数、信頼度、欠測を渡せます。

renderingはevidence stateに従います。`single-observation`はraw point、`same-case-repeat`はcase range、`family-provisional/characterized`だけがfamily bandを出します。常設placeholderがband生成を強制しないよう、該当しないfieldはstate付きで非掲載または`unavailable`にします。

## 7. Query semantics

### Exact query

primary stratumが一致するcellだけを返します。applied effort不明のrunを`high` queryへ入れません。

### Partial query

userがmodelやsurfaceを指定していない場合、skillは「全modelを大量表示」せず、利用可能なdimension valueとcompact countを返してrefineできます。明らかに少数なら一覧表示してもよいですが、context capを優先します。

### No exact data

```text
status: unmeasured
missing profile dimensions: ...
measured adjacent profiles: identifiers only
```

近傍profileの時間を回答値として代用しません。userが明示的にadjacent evidenceを求めたときだけ、差分condition付きで別表にします。

### Stale data

旧seriesの時間を消しませんが、現行modelの値として表示しません。観測window、stale reason、新series coverageを返します。

## 8. Distribution / discovery

このrepositoryはtarget project templateを`project/`に持つため、実装候補は次です。

```text
project/.codex/skills/lookup-agent-duration/
```

repository自身でも使う場合は、canonical skill sourceとcopy/install手順を一つにし、二重保守しません。data discoveryはhard-coded workspace pathを避け、次の明示順を候補にします。

1. `AGENT_DURATION_ATLAS_PATH`
2. target projectのversioned aggregate path
3. devcontainer image/shared installed aggregate path
4. not foundとして明示

locationの最終決定はskill実装開始時に行います。personal skillとして`~/.codex/skills`へ置くのか、target templateへ配布するのかで更新責務が変わるためです。

discovery順は実装時に一つのcontractへ凍結し、複数候補が同時に存在する場合はmanifest ID/sourceを表示します。silentに古いimage snapshotをproject aggregateより優先しません。

## 9. Versioning and freshness

- skill versionとatlas schema versionを分ける
- aggregate manifestへgeneratedAt、source digests、series windowを持たせる
- skillが未知schemaを黙って読むことを禁止する
- stale seriesはquery resultに残す
- model alias更新で旧dataを上書きしない
- skill更新なしでaggregateだけ更新できる設計にする

## 10. Validation plan

実装時は`skill-creator`の手順を使います。

1. skill locationを確定
2. `init_skill.py`で`SKILL.md`、`agents/openai.yaml`、必要resourceだけを生成
3. query scriptを実data/fixtureでtest
4. `quick_validate.py`でskill packageを検証
5. fresh agentへraw skillとquery requestだけを渡してforward-test
6. expected answerや設計意図をforward-test agentへ漏らさない

Forward-test cases:

- exact measured cellを短く返せる
- requested vs applied effortを混ぜない
- progressなしでfirst artifactを出さない
- stale/unmeasuredを補間しない
- censored failureを隠さない
- compare指定外の大量cellを出さない
- detailed evidence要求時だけ該当studyを読む

## 11. Repository roadmapへの追加

skill化はduration instrumentationより後、aggregate schemaが安定した段階で行います。

```text
correct run record
  -> trustworthy aggregate
    -> bounded query CLI
      -> compact skill
        -> fresh-agent forward test
```

先にskill文章を作って仮data formatへ固定すると、schema変更のたびにcontext contractまで壊れます。query CLIをskillとatlasの境界に置き、skill本体を小さく保ちます。
