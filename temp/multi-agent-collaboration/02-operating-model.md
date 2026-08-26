# 推奨operating model: collaboration modeを独立させる

検討日: 2026-08-26

## 0. Outcome

現在の基盤へ不足しているのは、もう一つのagent runnerではなく、primaryが「なぜ複数agentを使うか」「どんな相互作用をさせるか」「いつ止めるか」を選ぶためのoperating modelです。

推奨構成は次です。

```text
user goal
  -> expected multi-agent value
     throughput | coverage | diversity | deliberation |
     experiment | assurance | continuity
  -> collaboration mode
     solo | dispatch | fanout | panel | critique | deliberation |
     variants | maker-checker | red-team | pipeline |
     sentinel | event-triggered
  -> role assignment
     primary | researcher | implementer | reviewer | evaluator
  -> execution lane
     read | write | isolated
  -> lifecycle
     one-shot | bounded rounds | scheduled finite runs | event-triggered finite runs
  -> authority and integration
     primary / single writer
```

この順序にすると、`read = research fan-out`のような固定対応から離れられます。たとえば同じLane Rでも、独立panel、critique round、red-team、scheduled scoutは異なる知的効果を持ちます。同じ`variants` modeでも、設計案だけならLane R、prototypeならLane W、untrusted dependency比較ならLane Iです。

## 1. 4つの直交軸

| 軸 | 答える問い | 例 |
|---|---|---|
| collaboration mode | agent同士をどう関係づけるか | fanout、panel、critique、variants |
| role | 各agentが何に責任を持つか | proposer、researcher、implementer、reviewer |
| lane | どの隔離・permissionで実行するか | read、write、isolated |
| lifecycle | いつ何回起動し、いつ止めるか | one-shot、2 round、weekly、on-PR |

この上に、primary / integratorがauthorityを持ちます。modeを選んでも、workerが自動的にmerge、push、permission昇格、schedule変更をできるようにはしません。

## 2. Mode選択の入力

primaryは次を0（低い）〜2（高い）で短く評価します。厳密な数式ではなく、不要なfan-outを避けるdecision cardです。

| factor | 低い | 高い時の示唆 |
|---|---|---|
| decomposability | 同じ箇所を触る | dispatch / fanoutしやすい |
| ambiguity | 正解と手順が明確 | panel / critique / deliberationが効く |
| consequence | 間違ってもすぐ戻せる | maker-checker / red-teamが効く |
| evaluability | 良し悪しが主観的 | variantsを実測で選べる |
| implementation cost | prototypeも重い | variantsの本数を抑える |
| context coupling | 全体文脈が必須 | 小さなtaskへの分割が効きにくい |
| diversity potential | 観点を変えにくい | panelの追加価値が低い |
| recurrence | 一回限り | sentinel / event-triggered候補 |

### 軽量routing

1. 一人で短く正しく終わるか。yesなら`solo`。
2. 独立artifactへ分割できるか。yesなら`dispatch`または`fanout`。
3. 実装前の選択肢が不明か。yesなら独立`panel`。
4. 初案はあるがriskが読めないか。yesなら`critique`または`red-team`。
5. disagreementが根拠交換で解けそうか。yesならbounded `deliberation`。
6. 同じacceptanceで小さく複数案を作れるか。yesなら`variants`。
7. write成果の誤りが高コストか。yesなら`maker-checker`。
8. 同じ問いが時間やeventとともに繰り返すか。yesなら`sentinel` / `event-triggered`。

複数modeは組み合わせられます。ただし一つのphaseへ同時に3 mode以上を積まず、たとえば`panel -> variants -> maker-checker`のようにstageを分けます。

## 3. Collaboration plan card

複数agentを使う前に、primaryは最低限これを決めます。

```yaml
goal: このcollaborationで決める、または作るもの
why_multi_agent: 得たい価値と、soloより有利な理由
mode: panel | critique | variants | ...
participants:
  - role: researcher
    perspective: performance
independence: first_round_blind | shared_context | sequential_handoff
shared_facts: 全員が同じものとして扱う入力
artifact_flow: 誰から誰へ何を渡すか
round_budget: 1
time_budget: 20m
usage_budget: provider固有上限またはcapacity unit
evaluation: 判断基準とevidence
lane_and_workspace: read / write / isolatedとbase SHA
authority: 最終判断、integration、schedule変更のowner
stop_conditions:
  - 新しいevidenceが出ない
  - acceptanceを満たす案が一つに絞れた
```

`why_multi_agent`が書けない場合は`solo`へ戻します。

## 4. Core mode contract

| mode | dispatch contract | output | stop condition |
|---|---|---|---|
| `solo` | primaryが直接処理 | completed result | task完了 |
| `dispatch` | bounded scope + expected artifact | artifact / result | artifact受領 |
| `fanout` | non-overlap shard + common output format | shard results | required shard回収 |
| `panel` | first roundを独立、観点を分ける | recommendation + assumptions + confidence | primaryが比較可能 |
| `critique` | proposalとclaim IDを渡す | Must / Should finding + revision request | 1 revision、未解決risk記録 |
| `deliberation` | disagreementだけをround inputにする | claim ledger差分 | 通常2、最大3 round |
| `variants` | 同一base / scope / acceptance | candidate commit + benchmark | evaluatorがgateを満たすwinner判定 |
| `maker-checker` | makerとcheckerを分離 | implementation + independent findings | Must解消と再検証 |
| `red-team` | asset / boundary / allowed attackを明示 | exploit evidence / blocked path | risk分類かtimebox到達 |
| `pipeline` | 前段artifact schemaを固定 | stage result | 各stage acceptance |
| `sentinel` | schedule + finite task template + hard limits | report / candidate job | run deadline、circuit breaker |
| `event-triggered` | event filter + dedupe key | bounded workflow result | event単位で一回terminal |

## 5. Advice / dialogueのresult format

read-only agentの自由文を単に並べるのではなく、最低限次を返します。

```text
recommendation
evidence
assumptions
alternatives considered
risks / failure modes
unknowns
confidence: low | medium | high
disconfirming test
```

複数roundではclaimへstable IDを付けます。

```text
C1: proposed claim
  evidence: E1, E2
  challenges: Q1
  status: open | accepted | rejected | test-needed
```

primaryは全文transcriptを次roundへ流さず、open claim、disagreement、追加evidenceだけを渡します。これでcontext増加と人格的debateを抑えます。

## 6. Direct agent-to-agent dialogue

### default: primary-mediated rounds

primaryが各roundの問いを作り、回答を要約して次roundへ渡します。判断過程とstop conditionが見え、native provider間でも使えるため、これをstable defaultにします。

### optional: bounded peer exchange

providerがagent間messageを正式に支援し、delegationが許可されている場合だけ使えます。

- facilitatorを一人決める。
- participantとtopicを固定する。
- message数またはround数を先に制限する。
- code write、permission変更、nested spawnは禁止する。
- primaryがいつでもinterruptできる。
- 最後は各agentの同意文ではなく、claim ledgerとevidenceをprimaryへ返す。

自由会話を「深く考えた証拠」とみなしません。同じ主張を言い換えるだけになったら終了します。

## 7. Variant comparison protocol

1. primaryが共通brief、full base SHA、allowed paths、acceptance、benchmark fixtureを固定する。
2. 各variantを別job ID、branch、worktreeへ割り当てる。
3. agent同士へ途中実装を見せず、探索の独立性を守る。
4. correctness / safety gateを先に適用し、不合格案をperformance比較へ進めない。
5. evaluatorは可能ならauthor / providerを伏せて採点する。
6. scoreは少なくともcorrectness、scope、maintainability、performance、risk、migration costを含む。
7. primaryがwinner、再実験、hybridのどれかを決める。
8. hybridは新しいintegration taskとして検証する。

variant数は通常2、安価で明確な理由がある時だけ3にします。

## 8. Scheduled / event-driven architecture

### 原則

「agentを常駐させる」のではなく、schedule serviceが既存task templateから**有限job**を発行します。agentの会話sessionはrun間で暗黙resumeせず、継続記憶はbounded artifactだけにします。

### Schedule definition案

```yaml
schedule_id: weekly-toolchain-canary
enabled: false
trigger:
  kind: cron
  expression: "0 9 * * 1"
  timezone: Asia/Tokyo
task_template: docs/agents/schedules/toolchain-canary.json
base_policy: registered_head
provider: codex
role: researcher
lane: read
permission_profile: safe
overlap_policy: forbid
limits:
  max_runs_per_day: 1
  max_concurrent_runs: 1
  max_wall_time_seconds: 900
  max_attempts: 1
  usage_units_per_run: 1
  usage_units_per_day: 1
failure_policy:
  backoff_seconds: [300, 1800, 7200]
  open_circuit_after: 3
output_policy:
  retention_runs: 12
  write_candidate_only: false
```

### 必須state

- last scheduled / started / terminal timestamp
- immutable trigger IDとdedupe key
- current run job ID
- consecutive failure countとcircuit state
- daily run / usage count
- next eligible run
- schedule definition revision
- last resultへのowner-only path

### Write policy

- defaultはLane Rのreportだけ。
- Lane Wを許す場合も、allowed pathsとacceptanceを固定したcandidate commitまで。
- dependency update、migration、lockfile、secret、外部messageは個別opt-in。
- auto merge、push、PR、release、destructive cleanupはscheduleから行わない。

### Missed run / overlap

- rebuild中に逃したrunを無制限catch-upしない。既定は最新一回だけ。
- 前runがactiveなら既定`forbid`でskipし、重複起動しない。
- provider outage時はfailure budget内でbackoffし、連続失敗でcircuitを開く。
- schedule自身がcircuitを閉じたりquotaを増やしたりしない。

## 9. Component ownership

| component | 所有するもの | 所有しないもの |
|---|---|---|
| primary / native orchestrator | mode選択、task分解、round進行、synthesis | process durability、worktree lease |
| provider-native subagents | read consultation、peer message、interactive work | cross-provider durable workflow |
| `agentctl` | finite job、attempt、workspace、process、result | 会話内容、debateの意味、winner判断 |
| future scheduler | trigger、dedupe、limits、finite job発行 | open-ended objective、auto integration |
| Mira Companion | sanitized mode / lifecycle表示 | agent steering、approval、scheduler authority |

`agentctl`へconversation graphを入れません。scheduled jobはcontrol-plane responsibilityに合いますが、panelやdebateはprimary / provider-native layerに残します。

## 10. 段階導入

### C0: guidance

- 60候補をcatalog化する。
- 12 core mode、routing、stop conditionをplaybookへ入れる。
- root / target `AGENTS.md`から参照する。

### C1: reusable briefs

- collaboration plan templateを追加する。
- panel、critique、variant、scheduleのexampleを追加する。
- providerに依存しないresult fieldsを試運用する。

### C2: observation

- mode、agent数、round数、elapsed time、accepted artifact、reworkをcontent-free metadataとして記録する。
- solo baselineと比較し、coordination overheadを測る。
- mode別の失敗とstop condition逸脱をreviewする。

### C3: machine-readable plan

- 観測で価値が確認できたfieldだけschema化する。
- task/result schema version 1へ無理に混ぜず、collaboration planを別contractにする。
- native session IDやtranscriptを共通schemaへ固定しない。

### C4: scheduler pilot

- disabled-by-defaultのschedule store、manual dry-run、next-run previewを実装する。
- read-only sentinel一種類でdedupe、overlap、budget、circuit breakerを検証する。
- container restart、clock jump、provider outage、duplicate triggerをfault injectionする。

### C5: scheduler write candidate / UI

- Lane W candidate jobを明示opt-inで追加する。
- Miraへmode、round、scheduled run、circuit-openをcontent-free eventで表示する。
- auto integrationは追加しない。

## 11. 成功指標

- fanoutでcritical pathが実際に短縮したか。
- panelがsoloでは出なかったdecisive evidenceやriskを出したか。
- deliberationでclaim statusが変わったか。言い換えだけではないか。
- variantsで事前評価基準によりwinnerを選べたか。
- maker-checkerでintegration前にMust findingを捕まえたか。
- recurring runがquota、deadline、overlap、circuitを一度も越えなかったか。
- primaryのsynthesis / review時間を含めてもnet gainがあったか。
- userがagent topologyではなく、判断と成果を理解できたか。

token量、agent数、message数、議論時間は成功指標にしません。
