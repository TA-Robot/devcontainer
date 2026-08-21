# 第3ターン: 推奨構成と段階移行

検討日: 2026-08-11

## 0. 結論

このリポジトリは、独自の「マルチエージェント製品」を作るのではなく、**複数のnative agentを安全かつ再現可能に走らせるexecution fabric**へ刷新するのがよいです。

推奨するstable defaultは次です。

1. **対話・計画・subagent生成はCodex / Claude Code / Cursorのnative機能に任せる。**
2. **read-only fan-outは同一checkoutでnative subagentを使う。**
3. **write taskは同一devcontainer内のjob単位worktreeで分離する。** これを最速の標準経路にする。
4. **Docker操作、service起動、強いcredential分離が必要なtaskだけ、別worker / Docker Sandbox / cloudへ送る。**
5. リポジトリ側の新しい共通層は、会話を解釈せず、`base SHA`、workspace lease、attempt、process、resource namespace、structured result、回収を管理する。
6. **main / integrationへの反映はsingle-writer**にし、agent間の交換境界はGit commitと共通result schemaにする。
7. toolchainはrepoで固定するstable channelを既定にし、host同期やlatestはedge channelへ分離する。
8. 現行`second-agent`には新機能を足さず、並行導入と観測期間を経て段階廃止する。

この構成なら、native agentの進化を取り込みながら、現在のwrapperが持つworkspace保護の価値は失いません。また、毎回worker containerを起動する構成より速く、native-onlyよりwrite競合と障害回復を制御できます。

## 1. 最終的な設計判断

| ID | 判断 | 採用理由 |
|---|---|---|
| D1 | native-first、fabric-second | provider固有の会話、subagent、UIを再実装しないため |
| D2 | read / write / isolatedの3 lane | taskごとに必要な隔離強度とstartup costが違うため |
| D3 | stable write laneは同一container + Git worktree | trusted local developmentで最も低遅延だから |
| D4 | jobとattemptを分離 | retry時に過去のprocess、log、成果物を上書きしないため |
| D5 | jobはimmutableな`base_sha`を持つ | branch前進やsession再利用による再現性喪失を防ぐため |
| D6 | 共通層はstructured final resultを扱う | provider JSONL eventの互換層を保守しないため |
| D7 | metadataはSQLite、実装はまずPython標準ライブラリ | transactionが必要だが新規runtime依存を増やさないため |
| D8 | safe default、trustedは明示opt-in | native child agentにも親の強い権限が伝播し得るため |
| D9 | Docker Agent / Docker Sandboxesはoptional pilot | 有力だがstable coreの必須依存にするには新しく、host要件も増えるため |
| D10 | local workflow engineやTemporalは導入しない | hostを越える耐久性が必須になるまで運用コストが勝るため |
| D11 | integrationはsingle-writer | 並列実装と最終branchの整合性を別問題として扱うため |
| D12 | legacy stateは自動変換しない | session / branchの意味が新モデルと異なり、安全な1対1変換ができないため |
| D13 | local supervisorはjob実行だけを扱う | terminal切断耐性を得つつ、会話やplannerをservice化しないため |

## 2. 目標と非目標

### 2.1 目標

- containerをrebuildしても、同じcommitから同じtoolchainを得られる。
- 複数のread taskを、workspaceを複製せずすぐfan-outできる。
- 複数のwrite taskを、互いのworking treeを壊さず並列実行できる。
- agent / terminal / containerが途中で落ちても、状態を誤って`completed`にしない。
- CodexとClaude Codeを、会話形式ではなく同じtask / result contractで扱える。
- 高速なtrusted laneと、遅くても強く隔離されたlaneを選べる。
- CLI更新による破壊をstable利用者へ出す前に検知できる。
- 運用手順を、現在の`nohup`、PID推測、複数log追跡中心の文書から大幅に短くする。

### 2.2 非目標

- provider間で会話sessionを移植する。
- Codex / Claude Code / Cursorのplanner、subagent UI、memoryを再実装する。
- raw JSONL eventを完全な共通event modelへ変換する。
- 同一privileged container内のprocess間にsecurity boundaryがあると主張する。
- main branchへの自動force mergeや、競合の無人解決を行う。
- local containerをmulti-host durable workflow systemにする。
- 第1段階でDinD、credential、toolchain、orchestrationを同時に全面置換する。

## 3. 推奨アーキテクチャ

```text
Host
├─ repository / Dev Container Feature lock
├─ optional isolated runtime
│  ├─ Docker Sandbox clone
│  ├─ disposable worker container
│  └─ hosted agent / CI
└─ Coordinator devcontainer (stable execution environment)
   ├─ native clients
   │  ├─ Codex CLI + native subagents
   │  ├─ Claude Code + native subagents
   │  └─ Cursor agent UI
   ├─ agentctl / agentd  [working names]
   │  ├─ project identity
   │  ├─ job / attempt state
   │  ├─ worktree lease
   │  ├─ process group + heartbeat
   │  ├─ resource namespace
   │  └─ result validation
   ├─ persistent state + bounded logs
   ├─ shared caches and shared DinD (trusted-fast lane only)
   └─ single-writer integration gate
      ├─ validate result
      ├─ inspect commit
      ├─ integrate in dependency order
      └─ run aggregate tests / push / PR
```

`agentctl`と`agentd`は仮称です。名称より境界が重要です。providerにtaskを考えさせるorchestratorではなく、**jobを実行可能なworkspaceへ割り当て、終了状態を正しく回収するbroker**に限定します。

## 4. 3つのexecution lane

### 4.1 Lane R: read-only native fan-out

対象:

- repository調査
- architecture review
- failing testの原因候補調査
- security / documentation review
- 独立した比較や反証

構成:

- native subagentを使用する。
- 同じcheckout / snapshotを共有する。
- filesystemはread-only相当のroleにする。
- worktreeは作らない。
- resultだけ親agentへ返す。

利点はstartupがほぼなく、repository cacheも共有できることです。read taskに毎回worktreeを作ると、管理対象とdisk I/Oだけが増えます。

### 4.2 Lane W: same-container isolated write workspace

対象:

- 通常の実装
- test追加
- doc更新
- 互いに独立した複数componentの修正

構成:

- `1 job = 1 base SHA + 1 branch + 1 worktree lease`。
- retryは同じjobの新しいattemptとして記録する。
- agentのrole名ではなくjob IDをbranch / worktree名に使う。
- provider processはworktreeをcwdとして起動する。
- job固有のCompose project、network label、temporary path、割当portを渡す。
- 完了時はcommit SHAとstructured resultを返す。

これは**performance boundaryとaccidental-write boundary**です。同一containerのUID、credential、Docker daemonを共有するため、悪意あるprocessに対するsecurity boundaryではありません。

### 4.3 Lane I: isolated runtime

対象:

- `docker compose down -v`など破壊範囲の大きい操作
- private Docker daemonが必要なintegration test
- untrusted dependency / codeの実行
- workerへGitHub / SSH credentialを見せたくないtask
- 長時間処理やhost外durabilityが必要なtask

候補:

- Docker Sandbox clone mode
- disposable worker container + separate daemon
- CI / hosted agent

このlaneではsandbox境界の内側でno-prompt / bypass modeを使う余地があります。ただし、credential proxyやnetwork policyを含めた境界を実測してから有効化します。

### 4.4 lane routing

| 質問 | yesの場合 |
|---|---|
| taskはwrite不要か | Lane R |
| writeするが、trusted codeで通常のunit testだけか | Lane W |
| shared Docker daemonやport衝突を完全には避けられないか | Lane I |
| host credentialをworkerから隠す必要があるか | Lane I |
| host/container restart後もprocess継続が必須か | hosted / external durable lane |
| 判断できないか | Lane WでなくLane I、または人の確認 |

role定義からlaneを推測してもよいですが、最終的な選択はjob作成時に明示し、実行中に暗黙upgradeしません。

## 5. 基本単位: role、job、attempt

現行`second-agent`では、agent名がrole、session、branch、worktree、lock、log名を兼ねています。新設計では分離します。

### 5.1 role

再利用可能なpolicyです。

- 例: `researcher`、`implementer`、`reviewer`
- provider固有prompt / config
- read/write permission
- validation profile
- default laneとresource class

roleは「誰として振る舞うか」であり、実行instanceではありません。

### 5.2 job

一度の作業要求です。

- random / sortableな`job_id`
- `project_id`
- immutableな`base_sha`
- `role`
- `lane`
- task envelope
- expected result schema
- dependency job IDs
- created / terminal state

同じroleを同時に10 job起動しても衝突しません。

### 5.3 attempt

jobを実際に実行した1回です。

- `attempt_id`
- providerとcapability snapshot
- process group / external runtime ID
- worktree lease
- started / heartbeat / finished timestamp
- exit codeとexit reason
- log / result path
- optional provider session ID

retry時は古いattemptを上書きせず、新しいattemptを追加します。provider-native resumeはattempt内の継続として扱い、clean retryとは区別します。

## 6. 最小control planeの境界

### 6.1 所有するもの

- projectの安定identity
- job / attemptのstate transition
- immutable base SHA
- worktree / branch lease
- process groupまたはexternal runtime ID
- heartbeat、cancel、orphan detection
- Compose project / port / temporary directoryなどのresource lease
- task / result schema validation
- bounded stdout/stderr logとretention
- commit SHAの回収
- GC候補の列挙と明示削除

### 6.2 所有しないもの

- conversation transcriptの正規化
- provider内のsubagent topology
- planner / task decomposition
- token accountingの完全な共通化
- provider固有の途中event parser
- model名のshell scriptへのhardcode
- 暗黙retry
- 自動merge、push、PR作成
- 同一container内のsecurity isolation

### 6.3 CLI surface案

```text
agentctl doctor [--json]
agentctl job create --role ROLE --lane read|write|isolated \
  --base SHA --task TASK.json
agentctl job run JOB_ID --provider codex|claude [--detach]
agentctl job list [--state STATE] [--json]
agentctl job show JOB_ID [--json]
agentctl job cancel JOB_ID
agentctl job retry JOB_ID --clean
agentctl job validate JOB_ID
agentctl job collect JOB_ID
agentctl gc --dry-run
agentctl gc --job JOB_ID
```

v1では`create`と`run`を分けます。これにより、作成したjobのbase、lane、permission、resource見積もりを実行前に検査できます。短い利用向けに、将来`agentctl run ...`をsugarとして追加できます。

`--detach`は単なる`nohup` wrapperにしません。CLIはlocal supervisorへjobをsubmitし、専用runnerが標準入力を閉じ、専用logへredirectし、新しいprocess groupを作ります。PIDだけでなくprocess start timeも記録します。

### 6.4 local supervisor

terminal切断後もjobを追跡するため、container内に小さなlocal supervisorを置きます。

```text
agentctl          # Unix socket経由のCLI
  -> agentd       # state、capacity、lease、cancel、reconciliation
     -> runner    # 1 attemptのprovider processとlog / heartbeatを所有
```

- `agentd`はremote network portを開かず、owner-onlyのUnix socketを使う。
- runnerはagentdから独立したprocess groupで動き、CLIやeditorの切断では終了しない。
- runnerがproviderのexitを回収し、結果をtransactionで記録する。
- agentd再起動時はrunner PID、process start time、heartbeatを照合する。
- container再起動時は全runnerが消えるため、該当attemptを`orphaned`へ遷移する。
- containerの`--init`を維持し、zombie reapをscenario testする。
- schedulerはlocal capacityとFIFO / explicit priorityまでに留め、workflow DAG engineにはしない。

これにより、`nohup`の空logやshell PID推測を運用契約にしなくて済みます。実装はPython標準ライブラリを第一候補とし、service manager、Redis、message brokerは追加しません。prototypeでdaemon自体が不安定なら、常駐serviceを増築せず、foreground-onlyへ安全に縮退します。

### 6.5 state transition

```text
created
  ├─ waiting_capacity
  │   └─ preparing
  └─ preparing
      ├─ ready
      │   └─ running
      │       ├─ succeeded
      │       ├─ failed
      │       ├─ cancelled
      │       └─ orphaned
      └─ rejected

succeeded ──validate──> validated
failed/orphaned/cancelled ──retry --clean──> new attempt / preparing
```

`processがいない`ことと`succeeded`は同義にしません。`succeeded`には正常exit、result schema合格、期待したcommit状態の3つが必要です。validation failureはprocess failureと分けて記録します。

### 6.6 metadata store

第1候補はPython標準ライブラリの`sqlite3`です。

最小table:

```text
projects(project_id, git_common_dir, created_at)
jobs(job_id, project_id, base_sha, role, lane, resource_class, priority,
     task_path, state, queue_reason, created_at)
job_dependencies(job_id, depends_on_job_id)
attempts(attempt_id, job_id, number, provider, state,
         pid, process_started_at, runtime_id,
         started_at, heartbeat_at, finished_at,
         exit_code, exit_reason, result_path, head_sha)
leases(lease_id, attempt_id, kind, value, acquired_at, released_at)
validations(validation_id, attempt_id, profile, status, report_path, finished_at)
```

SQLiteを選ぶ理由は、複数agentが同時にstate JSONを書き換える競合をtransactionで防げる一方、Redisやserverを増やさずに済むためです。prompt全文、raw transcript、secretはDBへ保存しません。

project identityはpath hashだけにしません。候補はlocal Git configへ生成UUIDを保存し、移動後も同じcloneを識別する方法です。ただしworktree間の共通config挙動とclone時の期待をspikeで確認し、問題があればGit common dirのinode/pathと明示registrationを組み合わせます。

### 6.7 filesystem layout案

```text
/var/lib/agentctl/                 # named volume、0700
├─ state.db
├─ projects/<project-id>/
│  ├─ jobs/<job-id>/
│  │  ├─ task.json
│  │  └─ attempts/<n>/
│  │     ├─ result.json
│  │     ├─ process.log
│  │     └─ validation.json
│  └─ worktrees/<job-id>/
└─ locks/

/var/cache/agentctl/               # optional shared caches
/tmp/agentctl/<job-id>/            # disposable attempt temp
```

実装時はremote userが書ける専用volumeへ置き換えます。repository内にはruntime stateを置かず、成果として明示されたtask/result contractだけを必要に応じて保存します。

### 6.8 capacity control

高速化にはagent数を増やすだけでなく、editorとtestをresource starvationから守る必要があります。

- native Lane Rの推論fan-out上限はprovider側設定に任せる。
- fabricはLane W / Iのprocess、memory、Docker integration slotだけを管理する。
- `light`、`write`、`integration`、`isolated`のresource classを持つ。
- shared DinDを使う重いintegration jobは、実測するまで少数slotに制限する。
- capacityがなければ`waiting_capacity`としてqueueし、無理に起動しない。
- priorityはinteractive、normal、backgroundの3段階までに限定し、agingでstarvationを防ぐ。
- CPU / memoryの初期値はhost規模から決め打ちせず、containerで検出しbenchmarkで調整する。

LLM requestの並列数と、build / test processの並列数は別のbudgetです。read agentを増やした結果、4つのpackage installやbrowser testが同時に走る構成を避けます。

### 6.9 observability

通常運用で見るのはprovider raw eventではなく、次のjob-level情報です。

- current state、lane、role、provider、base / head SHA
- queue reason、lease、resource class
- start / heartbeat / elapsed time
- last bounded log lines
- exit reasonとretry可能性
- validation結果
- disk / worktree / Docker resourceのcleanup status

metricsはlocal JSON / logから始めます。OTel backendは必要になった時にexporterとして足し、v1の必須依存にはしません。

## 7. providerとの接続

### 7.1 native interactive path

人がCodex / Claude Code / Cursorを直接使い、そのnative subagentにLane Rを任せます。Lane Wが必要なら、親agentが`agentctl job create/run`を呼びます。native UIとconversation historyはproviderが所有します。

### 7.2 headless path

無人jobはprovider CLIのheadless commandをadapterから起動します。

- Codexはfinal output schemaを指定する。
- Claude CodeもJSON schemaを指定する。
- provider固有event streamはdebug時だけ保持し、共通APIにしない。
- adapterはpromptを自由に解析せず、task envelopeから決まったfieldsを渡す。
- capability検査で必要flagがないversionは起動前にrejectする。

adapter interfaceは次程度に留めます。

```text
prepare(provider, role, task, workspace, result_schema) -> argv + env
start(argv, env, cwd) -> process handle
collect(process handle, result_path) -> provider result
classify_exit(exit code, stderr tail) -> retryable | terminal | unknown
```

provider session IDはdebug / explicit resume用のoptional metadataです。job identityには使いません。

SDKやapp-serverは、途中eventを使ったprogrammatic steering、turn-level cancel、remote UIが本当に必要になった時の次段階です。v1はCLIの公式headless surfaceとfinal schemaで接続し、SDK control planeを先に作りません。

### 7.3 共通task envelope

```json
{
  "schema_version": 1,
  "job_id": "01J...",
  "base_sha": "<40-hex>",
  "objective": "...",
  "scope": {
    "allowed_paths": ["scripts/", "docs/"],
    "forbidden_paths": [".devcontainer/"]
  },
  "acceptance": [
    {"kind": "command", "value": "scripts/test-example.sh"}
  ],
  "constraints": ["Do not push", "Commit changes before returning"]
}
```

schemaはtaskの意味を機械可読にする最小部分だけを固定し、詳細contextはMarkdown fileを参照可能にします。220行のticket templateを毎回埋める運用にはしません。

### 7.4 共通result envelope

```json
{
  "schema_version": 1,
  "job_id": "01J...",
  "status": "completed",
  "summary": "...",
  "head_sha": "<40-hex>",
  "changed_paths": ["scripts/example"],
  "checks": [
    {"command": "scripts/test-example.sh", "status": "passed", "exit_code": 0}
  ],
  "risks": [],
  "followups": []
}
```

`changed_paths`や`head_sha`はagentの申告だけを信頼せず、brokerがGitから再計算して照合します。resultは短く保ち、full transcriptの代用にしません。

## 8. permission profile

### 8.1 safe（既定）

- 通常の`codex` / `claude`はdanger bypassを自動注入しない。
- reviewer / researcherはread-only。
- implementerは割当worktreeだけwrite対象にする。
- push / merge / credential利用はcoordinatorに限定する。
- command approvalやprovider sandboxを有効にしたままにする。

### 8.2 trusted-fast（明示）

- 現行相当のbypassは`codex-trusted`、`claude-trusted`など明示名にする。
- trusted local codeだけに使用する。
- same-container Lane Wはこのprofileを選べる。
- 実行logへprofile名を記録する。
- 「security boundaryなし」をdoctor / docsに表示する。

### 8.3 isolated-autonomous（明示）

- Lane Iだけで選べる。
- host repositoryはclone / snapshotとして渡す。
- private Docker daemonを使う。
- credentialはtaskごとの最小scopeにする。
- sandbox外へのwrite / network / pushをpolicyで制限する。

現行containerはprivilegedかつhost credentialを直接mountしているため、safe profileを付けるだけで強いsecurity isolationにはなりません。第1段階の目的はaccidental damageを減らすことです。security boundaryが必要ならLane Iへrouteします。

## 9. containerのstable / edge channel

### 9.1 stable channel

- base image digestを固定する。
- Dev Container Feature lockfileをcommitし、frozen lockでbuildする。
- AI CLI versionをDockerfile / manifestで固定する。
- TypeScript、ESLint等のglobal packageもversion固定する。
- container start時にpackage installを行わない。
- build済みimageをdigestで利用できる形を目標にする。
- updateはbotまたは明示commandでPR化し、contract test後にmergeする。

### 9.2 edge channel

- host CLIとのversion同期やlatest試験を明示opt-inにする。
- stableと同じstate volumeを無条件に共有しない。
- capability reportとcanary結果を残す。
- edge failureはstable起動を壊さない。

現在の`postStartCommand`によるhost version同期は起動ごとのnetwork / install /破壊リスクを持ちます。便利さは残しつつ、stable defaultから外します。

### 9.3 update flow

```text
version proposal
  -> image build with frozen Feature lock
  -> CLI surface contract tests
  -> fake-provider broker tests
  -> two-provider live canary
  -> parallel worktree / Docker collision scenario
  -> edge soak
  -> stable lock update
```

version番号だけで機能を仮定せず、`doctor`で必要command / flag / schema supportをprobeします。

### 9.4 配布単位

stableの正本は、まずこのrepositoryからbuildされるcoordinator imageとします。

- imageはtoolchain、native CLI、fabric、schemaを一緒にversion付けする。
- build provenanceとimage digestをreleaseへ記録する。
- target projectはproject固有role / acceptanceだけを持つ。
- schema versionとfabric versionのcompatibilityをdoctorで検査する。

独自base imageを使いたいproject向けのDev Container Feature化は、第1版が安定した後の配布optionです。最初からDockerfile installとFeature installの2経路を同時保守しません。Featureを追加する場合は、追加理由、影響範囲、image方式との違い、削除手順を文書化します。

## 10. Dockerとresource isolation

### 10.1 stable defaultではDinDを直ちに置換しない

現在のDinDは開発速度と互換性に寄与しています。orchestration刷新と同時にsidecar化やrootless化まで行うと、bind mount path、BuildKit cache、Compose、portの問題が混ざります。

まずLane Wで次を必須にします。

- `COMPOSE_PROJECT_NAME=agent_<job-id>`
- job labelをcontainer / network / volumeへ付与
- dynamic port leaseまたは内部network-only service
- job固有temp / artifact path
- cleanupはlabelとleaseに限定
- `docker system prune`やscope不明の`compose down -v`を拒否

ただし、同じdaemonのimage cache、volume、privileged controlは共有されます。完全分離が必要なtaskはLane Iです。

### 10.2 将来のseparate daemon spike

以下を測ってから、DinD sidecarまたはprivate daemonをstableへ昇格します。

- workspace bind mountのpath整合
- BuildKit cache hit率
- startup / teardown時間
- Compose compatibility
- disk growthとGC
- credential exposure
- editor / test UX

`--privileged`削除も重要ですが、本刷新とは別ADRとcommit列にします。

## 11. project側のcontract

対象projectへコピーするtemplateは、wrapper操作説明ではなくroleとacceptanceに集中させます。

提案構成:

```text
AGENTS.md                         # project共通の境界と検証command
.agent/
├─ roles/
│  ├─ researcher.md
│  ├─ implementer.md
│  └─ reviewer.md
├─ schemas/
│  ├─ task.schema.json
│  └─ result.schema.json
└─ config.json                   # lane / validation / resource defaults
.codex/agents/*.toml             # thin provider mapping
.claude/agents/*.md              # thin provider mapping
docs/agents/runbook.md           # failure / recovery / integration only
```

`.agent/`は提案名であり、providerやDocker Agentの既存探索pathと衝突しないかspike後に確定します。

`AGENTS_TEMPLATE.md`は次へ縮小します。

- source-of-truthとなるproject scope
- roleごとのwrite permission
- test / lint / build command
- commit / integration contract
- 3 laneのrouting条件
- secret / destructive command policy

次はprovider-native定義へ移します。

- subagentの起動方法
- model / reasoning設定
- background / resume操作
- UI固有の表示方法

次はrunbookへ移します。

- orphan recovery
- port / Docker collision
- clean retry
- GC
- legacy session cleanup

## 12. integration protocol

workerはmainへmerge / pushしません。完了時に次を満たします。

1. worktreeが期待したbase SHAから派生している。
2. changeがjob branchへcommitされている。
3. untracked / dirty stateを明示している。
4. result schemaを満たす。
5. task-level checksを実行した、または実行不能理由を返す。
6. brokerが`head_sha`、changed paths、checksを照合する。

coordinatorだけが次を行います。

1. dependency graphとbaseを確認する。
2. changeをreviewする。
3. cherry-pick / merge / rebaseの方法を選ぶ。
4. conflictを別の修正jobまたは人へ戻す。
5. aggregate testsを実行する。
6. push / PR作成を行う。

「2 agentが同じfileを触らない」だけでは十分ではありません。schema、generated file、lockfile、database migrationの論理競合はintegration gateで扱います。

## 13. restart、retry、durability

### 13.1 terminal切断

detach実行はstdin / stdout / process groupを正しく分離し、broker stateとlogを残します。単なるshell backgroundや`nohup`の成功表示を完了判定にしません。

### 13.2 agent process crash

- exit codeとstderr tailを分類する。
- partial worktreeを保持する。
- jobを勝手にretryしない。
- 人またはpolicyが`retry --clean`かprovider-native resumeを選ぶ。

### 13.3 container restart

- startup reconciliationで`running` attemptを確認する。
- PIDとprocess start timeが一致しなければ`orphaned`にする。
- worktreeとlogは保持する。
- 新しいclean attemptを明示作成する。

local container restart後にprocessが継続するとは約束しません。約束するのは、**消えたprocessを成功扱いせず、回収可能な状態を残すこと**です。

### 13.4 host restart / multi-host durability

これがSLOになるtaskはLane Iのhosted runtimeへ送ります。Temporal相当をdevcontainer内に再構築しません。

## 14. Docker Agent / Docker Sandboxesの位置づけ

### 14.1 Docker Agent

判断: **比較pilot。stable coreには入れない。**

評価する価値がある点:

- declarative multi-agent definition
- worktree / task / background execution
- session persistence
- structured output
- observability / protocol support
- board UI

昇格条件:

- native Codex / Claude利用よりtask品質や回収性が明確に良い。
- provider最新機能への追従遅延が許容範囲。
- upgrade / rollbackがreproducible。
- 既存task/result contractをそのまま使える。
- 追加daemon / session DBの運用コストが小さい。

満たさなければ参考実装に留めます。

### 14.2 Docker Sandboxes

判断: **Lane Iの第一pilot候補。stable利用の必須条件にはしない。**

private daemon、clone mode、credential proxyは目的に合います。一方、host側導入、KVM、disk、cache、startup、Linux環境差を測る必要があります。

### 14.3 hosted agent / CI

判断: **長時間耐久性と外部reviewの逃げ道として保持。**

local fast pathを置換せず、host restartを越える必要のあるjobだけrouteします。

## 15. 現行`second-agent`の移行

### Phase A: freeze

- security / data-loss bug以外の新機能を止める。
- READMEでlegacy statusと予定を明示する。
- `doctor` / inventoryでactive session、worktree、branch、logを列挙できるようにする。
- 既存stateを自動削除しない。

### Phase B: parallel opt-in

- 新しい`agentctl`を別commandとして導入する。
- old shimを内部でsilent redirectしない。
- 同じrepresentative taskを旧新両方で比較する。
- project templateは新方式を既定にし、旧手順をlegacy sectionへ移す。

### Phase C: default switch

以下を満たしたら新方式をdefaultにします。

- 2 providerのcontract testsが通る。
- 2並列write + Docker namespace testが通る。
- kill / orphan / clean retry scenarioが通る。
- 1 release cycle以上、重大なstate lossがない。
- active legacy sessionのinventoryとcleanup手順がある。

### Phase D: remove

- `codex-second-agent` / `claude-second-agent`はdeprecation errorまたはmigration案内にする。
- provider JSONL filterを削除する。
- legacy logs / worktreesはユーザー確認なしに消さない。
- compatibility期間終了と削除versionをrelease noteへ残す。

session stateの移行は行わず、必要ならold sessionを完了させてcommit SHAを新方式へ渡します。

## 16. 小さく分ける実装ロードマップ

各番号は原則1 commitまたは独立PRです。機能、container、docsを無理に同じcommitへ混ぜません。

### Phase 0: baselineとADR

1. 本検討からADRを作り、3 laneとownership boundaryを確定する。
2. 代表scenarioと測定scriptを追加する。
3. 現行`second-agent`のbaseline latency、failure、disk使用量を記録する。
4. legacy feature freezeを文書化する。

### Phase 1: container再現性とsafe default

5. 既存Feature lockfileの内容と生成手順を確認し、所有者と調整してcommitする。
6. frozen lock buildをCI / smoke commandへ追加する。
7. global npm packageをversion固定する。
8. host AI CLI syncをedge opt-inへ変更する。
9. normal commandからdanger default injectionを外す。
10. trusted alias / profileを明示追加する。
11. capability-based `doctor --json`を追加する。
12. stable update canaryのcontract testsを追加する。

Phase 1で`.devcontainer/`を触るため、リポジトリ指定のDocker build smokeを必ず実行します。

### Phase 2: native-first project contract

13. 共通task / result JSON schemaを追加する。
14. Codex native agent定義のthin templateを追加する。
15. Claude native subagent定義のthin templateを追加する。
16. `AGENTS_TEMPLATE.md`からwrapper choreographyを分離する。
17. `project/AGENTS.md`をlane / permission / integration中心へ縮小する。
18. failure recoveryを`docs/` runbookへ集約する。

### Phase 3: job / workspace fabric

19. Python標準ライブラリでproject / job / attempt schemaを実装する。
20. immutable base SHAとjob-ID branchを実装する。
21. worktree lease、path validation、lockを実装する。
22. foreground process executionとstate transitionを実装する。
23. local supervisor / runnerとowner-only Unix socketを実装する。
24. detach、process-group cancel、heartbeat、orphan reconciliationを実装する。
25. capacity / resource classとqueueを実装する。
26. Codex headless adapterとresult validationを追加する。
27. Claude headless adapterとresult validationを追加する。
28. resource / Compose project / port leaseを追加する。
29. `collect`とsingle-writer integration reportを追加する。
30. bounded log、redaction、retention、`gc --dry-run`を追加する。

`scripts/second-agent`に新modelを継ぎ足さず、新しいmodule / commandとして作ります。既存bashのpath validationとtest fixtureは、意味が一致する範囲だけ再利用します。

### Phase 4: isolated lane pilot

31. Docker Sandbox cloneのstartup、cache、disk、credential、Git回収を測る。
32. disposable worker / private daemonとの比較を行う。
33. Docker Agentを同じbenchmark task / result contractで比較する。
34. 合格したruntimeだけoptional adapterとして追加する。

### Phase 5: legacy retirement

35. old commandsへdeprecation warningを追加する。
36. migration inventory / cleanup commandを提供する。
37. default docsからlegacy pathを外す。
38. 観測期間とrelease告知後にold filters / engineを削除する。

## 17. verification matrix

| 層 | test | 合格条件 |
|---|---|---|
| unit | path、name、state transition、lease、schema | fake providerでdeterministicに通る |
| CLI contract | Codex / Claude helpと必要flag | stable lockの両CLIでcapabilityあり |
| container | frozen build / start / doctor | 起動時installなし、期待version一致 |
| Git concurrency | 同じbaseから2 write job | primary checkout非変更、別branch / worktree |
| process recovery | kill -9 / terminal切断 / container restart | false successなし、orphan判定、clean retry可 |
| permission | reviewerがwriteを試行 | safe profileでは拒否される |
| Docker | 2 Compose job同時実行 | project / port / cleanupが相互非干渉 |
| result | Codex / Claudeで同じschema | broker再計算と一致する |
| integration | dependencyあり2 commit | single-writerが順序と競合を検出 |
| secrets | worker env / log / result確認 | 不要credentialとraw secretが残らない |
| upgrade | CLIを1 version進める | stable切替前にbreaking surfaceを検知 |
| live canary | 小さな実task | provider outage以外で回収可能 |

## 18. performance SLOの決め方

最初から根拠のない秒数を固定せず、現行baselineを測ってからthresholdを設定します。最低限測るものは次です。

- container cold build / warm start
- Lane Rのfirst useful result
- Lane Wのworktree ready time
- provider process start time
- 2 / 4並列時のCPU、memory、disk I/O
- image / package cache hit率
- isolated lane startup / teardown
- completed jobあたりのmanual recovery回数
- conflict / retry / orphan率
- stale worktree / log / volumeのdisk growth

最適化の優先順位は、`startup latency -> false failureの削減 -> merge待ち時間 -> token cost`とします。agent数だけをKPIにしません。

## 19. go / no-go gate

新方式をstable defaultへ切り替える条件:

- pinned toolchainでrebuild可能。
- start時にCLI packageを更新しない。
- Codex / Claudeの共通result contractが通る。
- 2 write jobが同じbaseから独立完了する。
- reviewerのwrite制限を実測できる。
- process killとcontainer restartをfalse successなしで回復できる。
- Docker resource cleanupが別jobへ影響しない。
- legacy sessionの列挙と非破壊cleanupが可能。
- runbookだけで第三者が失敗jobを診断できる。

no-go / rollback条件:

- job stateと実processが繰り返し不整合になる。
- primary checkoutまたは他jobを汚す。
- credentialが不要なworker / logへ漏れる。
- stable buildがnetwork上のlatestへ依存する。
- provider updateごとに共通event parserの修正が必要になる。
- native利用より操作が増え、回収性の改善もない。

## 20. 残る重要な未確定点

設計を止める問いではなく、spikeで数字を取る問いです。

1. Lane Wで共有DinDを使う場合、project namespaceだけで実際の対象projectを十分分離できるか。
2. project UUIDをGit local configに置く方式がworktree / clone / remote containerで期待どおりか。
3. Python製agentd / runner + container `--init`で、terminal / editor再接続時のprocess管理が十分か。
4. provider sandboxがworktree pathとstate/result pathの両方を安全に扱えるか。
5. Codex / Claudeのschema outputが長時間taskでもどの程度安定するか。
6. safe defaultへ戻したときのapproval負荷が高速開発を阻害しないか。
7. Docker Sandboxのcache / disk overheadがLane Iの頻度に見合うか。
8. state volumeのbackup / retentionをどこまでこの基盤の責務にするか。

## 21. 最初の90分・最初の1週間・その後

### 最初の90分

- 本文からADR draftを作る。
- 代表taskを3つ選ぶ: read review、通常write、Docker integration。
- 現行方式のtime-to-readyと回復手順を記録する。
- existing untracked lockfileは勝手に変更せず、由来を確認する。

### 最初の1週間

- stable / edge toolchain方針を実装する。
- safe / trusted command surfaceを分ける。
- task / result schemaとfake provider testを作る。
- 2 worktree + 2 Compose namespace spikeを行う。
- job / attempt state machineの最小prototypeを作る。

### prototype合格後

- Codex / Claude adapterを順に追加する。
- templateをnative-firstへ縮小する。
- recovery / GCを完成させる。
- isolated laneをpilotする。
- legacyを1 release cycle以上並行運用してから削除判断する。

## 22. 参照した根拠

### repository / local確認

- `scripts/second-agent`
- `scripts/codex-second-agent`
- `scripts/claude-second-agent`
- `scripts/*-second-agent-filter.py`
- `scripts/sync-host-ai-cli-versions`
- `.devcontainer/Dockerfile`
- `.devcontainer/devcontainer.json`
- `.devcontainer/devcontainer-lock.json`（既存・未追跡、内容のみ確認）
- `AGENTS_TEMPLATE.md`
- `project/AGENTS.md`

### 公式資料

- [Codex: Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents.md)
- [Codex: Worktrees](https://learn.chatgpt.com/docs/environments/git-worktrees.md)
- [Codex SDK](https://learn.chatgpt.com/docs/codex-sdk.md)
- [Claude Code: Subagents](https://code.claude.com/docs/en/agents)
- [Claude Code: Worktrees](https://code.claude.com/docs/en/worktrees)
- [Docker Agent](https://docs.docker.com/ai/docker-agent/)
- [Docker Agent CLI](https://docs.docker.com/ai/docker-agent/features/cli/)
- [Docker Sandboxes](https://docs.docker.com/ai/sandboxes/)
- [Docker Sandboxes isolation](https://docs.docker.com/ai/sandboxes/security/isolation/)
- [Docker Sandboxes architecture](https://docs.docker.com/ai/sandboxes/architecture/)
- [Dev Container CLI](https://github.com/devcontainers/cli)
- [Cursor: What we've learned building cloud agents](https://cursor.com/blog/cloud-agent-lessons)

## 第3ターン終了時の一文

**native agentを頭脳とUIとして活かし、containerは再現可能なtoolchain、job単位worktree、明示的な権限、正しい失敗状態、Git成果物の回収を保証する。速いlaneを標準にし、強い隔離とhostを越える耐久性だけを外へ逃がす。**
