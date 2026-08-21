# 第2ターン: 安定・高速なマルチエージェント実行基盤として再検討

調査日: 2026-08-11

## このターンの結論

第1ターンの `native-first + thin policy layer` は方向としては残りますが、**policy だけでは足りません**。

安定的にマルチエージェントを回して開発を速くするには、このリポジトリが提供すべきものを次のように言い換える必要があります。

> **agent の頭脳や会話UIではなく、再現可能な実行環境、workspace lease、資源配分、検証、成果回収を提供する multi-agent execution fabric**

native client は planner / orchestrator として使います。一方、container 側は「どの agent でも同じ条件で安全に速く作業できる」ことを保証します。

また、現行の「1 agent 名 = 1 session = 1 branch = 1 worktree」という結合をやめ、次を基本単位にするべきです。

```text
1 job
  = 1 immutable base SHA
  + 1 role definition
  + 1 isolated workspace lease
  + 1 or more attempts
  + 1 structured result
```

role は再利用可能な設定、job は一度きりの仕事、attempt は再試行単位です。この3つを分けない限り、stale session、古い branch、再試行による二重編集を安定して扱えません。

## 1. 「安定」と「高速」を分解する

### 安定とは

- すべての write job が、明示された同一の base commit から始まる。
- agent 同士が同じ working tree、Git index、branch、port、service 名を奪い合わない。
- provider 障害、process crash、container restart、timeout の後に「何が起きたか」が分かる。
- incomplete な結果を completed と誤認しない。
- CLI update で option や event schema が変わっても、安定 channel が突然壊れない。
- 誰が code を統合・push できるかが一意である。
- secret と transcript が他 agent や Git に漏れない。

### 高速とは

- agent 起動数が多いことではなく、**検証済み成果が integration branch に入るまでの時間が短い**こと。
- read-heavy な探索は同じ snapshot 上で即座に fan-out できる。
- write-heavy な仕事は、競合しない単位だけを並列化する。
- environment setup、dependency install、image pull を毎回繰り返さない。
- agent の待ち時間と、test/build の CPU・memory 消費を別に制御する。
- merge conflict、重複調査、説明不足による再実装を減らす。

したがって「最大 agent 数」は主要KPIではありません。測るべき候補は次です。

- queue 待ち時間
- workspace 準備時間
- agent 実行時間
- validation 時間
- integration までの総時間
- conflict / retry / manual rescue 率
- task 完了率
- agent-hours あたりの採用された変更量

数値目標は、まず現在の wrapper と native client で baseline を取ってから決めるべきです。

## 2. 現行方式を安定性の観点で壊してみる

### 2.1 role、job、session、branch が同一名に結合している

`--agent implementer` は次を同時に意味します。

- role 名
- session ID の保存先
- lock 名
- worktree path
- branch 名
- log path

同じ implementer を別 task に再利用すると、過去の会話と古い branch を暗黙に resume します。branch が存在すれば現在の base branch から作り直さず、その branch の続きを使います。

これは会話継続には便利ですが、再現可能な job 実行には不向きです。role は `reviewer` のように固定でも、job ID と base SHA は毎回異なるべきです。

### 2.2 worktree の開始点が暗黙

新規 worktree は起動時の `HEAD` から作られます。すでに branch があれば、その branch を再利用します。

- uncommitted / untracked な変更は普通の Git worktree へ渡らない。
- manager が task A と task B の間に commit しても、既存 agent branch は自動更新されない。
- base branch が進んだ後に古い session を resume すると、agent が何を前提にしているか分かりにくい。

安定させるには job 作成時に `base_sha` を固定し、結果にも必ず記録する必要があります。dirty tree を含めたい場合は「暗黙に見える」挙動ではなく、明示的 snapshot を作る必要があります。

### 2.3 `nohup` は durability ではない

`nohup` は terminal 切断には耐えますが、次には耐えません。

- devcontainer stop / rebuild
- WSL / host restart
- process kill
- provider outage 後の再試行
- disk full
- orphan process

現行 state には job PID、process group、heartbeat、attempt、terminal state がありません。`session_id` が存在しても job が running なのか、途中で死んだのかは判定できません。

### 2.4 timeout と retry の意味が弱い

現在は外側から `timeout` で CLI を止められますが、task の再試行契約はありません。

partial edit 後に同じ worktree / session を再実行すると、同じ操作を重ねる可能性があります。安全な retry は次のどちらかです。

1. checkpoint commit から継続する。
2. 新しい attempt を元の base SHA から始め、古い attempt を破棄する。

「同じ command をもう一度」は agent task では一般に idempotent ではありません。

### 2.5 shared Docker daemon は別の競合面

Git worktree を分けても、worker が同じ Docker daemon を使うと次は共有です。

- container 名
- Compose project 名
- network / volume
- host port
- image tag
- build cache
- daemon 全体の操作権限

ある agent の `docker compose down -v` や prune が別 agent の環境を壊せます。現在の Docker-in-Docker は host daemon との分離にはなっても、**同じ devcontainer 内の agent 間分離にはなりません**。

### 2.6 danger override が role ごとの最小権限を壊す

Codex subagent は親 turn の sandbox / approval override を継承し、Claude subagent も親の `bypassPermissions` が優先されます。

現在の通常 `codex` / `claude` wrapper は danger / permission bypass を常時注入するため、reviewer を project config 上 read-only にしても、親の live override が優先される可能性があります。

native multi-agent の least privilege を使うなら、coordinator の通常起動を dangerous-by-default にしてはいけません。bypass は、外側に本当の sandbox がある worker lane でだけ使うのが筋です。

### 2.7 host CLI sync と reproducibility が衝突する

container 起動時に host と同じ CLI version を npm install する現在の方式は、利用者の操作感を揃えるには便利です。しかし stable environment としては次の問題があります。

- 同じ Git commit の container が、host ごとに別 version になる。
- `postStartCommand` が network / npm registry に依存する。
- wrapper contract test を通していない version が即座に導入される。
- container を開き直しただけで native capability や event schema が変わる。

安定 channel では repo lock を正本にし、host sync は `edge` profile の opt-in に反転する方がよいです。

## 3. 実行を3つの lane に分ける

すべての subagent を同じ重さで隔離すると遅くなり、すべてを同じ container で動かすと不安定になります。task の性質で lane を分けます。

### Lane R: read-only fan-out

用途:

- codebase exploration
- security / correctness / test review
- docs 調査
- log 分析

方式:

- native subagent を使う。
- 同一の base snapshot を共有してよい。
- filesystem は read-only、または write tool を与えない。
- worktree や worker container を原則作らない。
- 結果は共通 JSON Schema または短い finding format で親へ返す。

これは最も速く、native multi-agent が最も得意な lane です。

### Lane W: isolated write workspace

用途:

- 通常の機能実装
- bug fix
- test 追加
- docs / code の独立変更

方式:

- job ごとに新しい branch と worktree を作る。
- base SHA を固定する。
- role と job ID を分離する。
- 1 worktree に同時に1 writerだけを許す。
- provider session は native 側が所有する。
- worker は commit SHA と structured result を返す。
- integration branch へ書けるのは coordinator / merge gate だけにする。

速度のため、trusted local task は同じ devcontainer 内の別 process + worktree でよい。ただし Docker service や強い隔離が必要なら Lane I へ送ります。

### Lane I: isolated runtime

用途:

- `docker compose` や test DB を使う task
- port を公開する application
- unknown dependency / generated script を実行する task
- credential exposure を小さくしたい task
- 長い autonomous implementation

方式候補:

- ephemeral worker container
- private nested Docker daemon を持つ worker
- Docker Sandbox の clone mode
- hosted / self-hosted cloud agent

workspace だけでなく process、network、Docker daemon、resource、credential を分離します。startup は Lane W より重いので全 task には使いません。

## 4. 推奨する全体像の暫定形

```text
Host / external durable layer
  ├─ pinned artifacts and credential boundary
  ├─ optional cloud / durable queue
  └─ sandbox or worker lifecycle
                 │
Coordinator devcontainer
  ├─ Cursor / Codex / Claude native planner UI
  ├─ task registry (job != role != attempt)
  ├─ workspace lease + resource / port allocation
  ├─ capability doctor
  └─ single-writer integration gate
        ├─ Lane R: native read-only subagents, shared snapshot
        ├─ Lane W: top-level agent session, exclusive worktree
        └─ Lane I: isolated worker/sandbox, private clone/runtime
```

重要なのは、coordinator が各 provider の conversation を複製管理しないことです。共通化するのは次だけです。

- task envelope
- job / attempt state
- workspace lease
- base / result commit
- acceptance result
- provider session への参照

## 5. provider-neutral contract は会話ではなく入出力に置く

Codex CLI と Claude Code はどちらも、最終出力を JSON Schema へ制約する option を持っています。

- Codex: `--output-schema`
- Claude Code: `--json-schema`

したがって provider の JSONL event を全文正規化せず、共通の completion schema だけを定義できます。

### task envelope の候補

```text
job_id
base_sha
role
mode: read | write | isolated
scope_paths
dependencies
acceptance_commands
timebox
resource_class
provider_preference
```

### result envelope の候補

```text
job_id
attempt_id
status: completed | blocked | failed
base_sha
head_sha
changed_paths
validation[]
findings[]
blockers[]
provider_session_ref
```

manager 向けの背景説明は Markdown ticket のままで構いません。220行の ticket 全体を machine state にせず、小さい envelope から詳細 Markdown を参照する形が扱いやすいです。

## 6. 代表シナリオで反証する

### 6.1 並列 read-only review

望ましい流れ:

1. coordinator が base SHA を固定する。
2. security / correctness / tests の native subagent を同時に起動する。
3. 全員 read-only で同じ snapshot を読む。
4. result schema に finding、severity、evidence、file reference を返す。
5. coordinator が重複を除き統合する。

判定:

- 現行 wrapper の agent worktree は過剰。
- native-only が最速で十分。
- model / reasoning を役割別に変える価値が高い。
- concurrency 上限と token / rate-limit 監視は必要。

### 6.2 並列 implementation

望ましい流れ:

1. plan を file ownership または依存関係で分割する。
2. 各 job を同じ base SHA から別 worktree に作る。
3. agent は担当 worktree だけを変更する。
4. 各 worker が test と commit を行い、result envelope を返す。
5. coordinator が依存順に cherry-pick / merge し、integration test を再実行する。

判定:

- pure native-only は、client 自身が worktree を管理する場合だけ十分。
- Codex CLI subagent 単位の worktree 隔離は現行公式情報で確認できないため、terminal-first では workspace broker が必要。
- file ownership を分けられない task は、無理に並列実装せず competing-plan / review だけを並列化する方が速い。

### 6.3 長時間 background task

必要なレベルを分けます。

| 要求 | 適した方式 |
|---|---|
| terminal を閉じても同じ container 内で継続 | native background UI、tmux、local supervisor |
| devcontainer restart 後に状態を説明できる | persistent job registry + orphan detection + explicit retry |
| process をそのまま restart 後も継続 | local container だけでは不可 |
| host restart や数日間の実行に耐える | hosted agent、host-level daemon、durable workflow engine |

container 内 daemon に Temporal 相当を再実装するのは避けるべきです。Cursor も長時間 agent の retry、node failure、hibernation 対応を自前で積み上げる途中で Temporal へ移行しています。

このリポジトリでは「restart 後に orphan と判定し、安全に新 attempt を作れる」ところまでを local contract にし、本当の continuous execution は外部 lane へ送るのが現実的です。

### 6.4 provider fallback

session の途中で Codex から Claude へ切り替えるのではなく、次を渡し直します。

- task envelope
- immutable base SHA
- 前 attempt の commit または patch
- validation result
- blockers / findings

新 provider は新 attempt として開始します。これなら transcript の互換性を作る必要がありません。

### 6.5 Docker service を伴う並列 task

最低限必要な仕組み:

- `COMPOSE_PROJECT_NAME` を job ごとに一意化
- container / network / volume に job label を付ける
- fixed host port を禁止し、必要時だけ port allocator が割り当てる
- cleanup は label / job ID で対象を確定する
- image tag を job ID または content digest で分離する

ただし shared daemon では、agent が daemon 全体を操作できる問題は残ります。信頼境界が必要なら Lane I の private Docker daemon を使います。

### 6.6 container / process crash

job state は少なくとも次の遷移を持つべきです。

```text
queued
  -> preparing
  -> running
  -> validating
  -> ready_to_integrate
  -> completed

任意の途中状態
  -> blocked | failed | canceled | orphaned
```

`session_id` の有無ではなく、process / container identity、heartbeat、exit reason、attempt を記録します。SQLite は Python 標準ライブラリで使え、複数 process の atomic transition を素朴な JSON file 群より安全に扱えます。ただし実装採否は第3ターンで決めます。

## 7. 実行トポロジー比較

| topology | 起動速度 | agent 間隔離 | Docker 分離 | container 外durability | 保守・前提 |
|---|---:|---:|---:|---:|---|
| 同一 devcontainer + native subagent | 最速 | 低 | なし | なし | 最小 |
| 同一 devcontainer + job worktree | 高 | Gitのみ中 | なし | なし | 小さなbroker |
| coordinator + ephemeral worker container | 中 | 中〜高 | 設計次第 | 低 | image / volume / lifecycle管理 |
| Docker Sandbox clone mode | 中〜低 | 高 | private daemon | VM stop/restartまでは保持 | 新しいhost runtime、KVM、disk |
| hosted / self-hosted cloud worker | 低〜中 | 高 | 高 | 高 | provider・費用・network |

単一 topology を標準にするより、R/W/I の lane routing の方が速度と安定性を両立できます。

## 8. 新しく見つかった外部候補

### 8.1 Docker Agent

Docker Agent は、今回自作しようとしている機能とかなり重なります。

- YAML / HCL の multi-agent 定義
- provider 切り替え
- subagent delegation
- headless mode と structured output
- SQLite session
- worktree 起動
- background job / task DB / shared plan
- OpenTelemetry
- tmux + worktree の Kanban board
- MCP / A2A / ACP / HTTP surface

これは強い比較対象です。特に `docker agent board` は「1 card = 1 tmux session + 1 worktree」をすでに提供しています。

ただし、2026年夏時点で Docker Agent という名称・製品面は新しく、現在の調査環境にも未導入です。また、GPT / Claude model を使えることと、Codex CLI / Claude Code の coding harness をそのまま使うことは同義ではありません。

結論:

- 自前 SDK control plane を作る前に必ず実機比較する。
- ただし stable core へ即採用せず、experimental profile として quality、resume、worktree、権限、upgrade を測る。

### 8.2 Docker Sandboxes

Docker Sandboxes は agent ごとに microVM、private Docker Engine、network policy、credential proxy を提供します。`--clone` では host repo をread-onlyにし、agent が private clone で作業できます。

これは Lane I の要求に非常によく合います。特に、現在の「privileged devcontainer + 全 agent 共有 DinD」より明確な境界を作れます。

ただし次のコストがあります。

- 各 sandbox が VM、Docker images、volumes を保持し disk を使う。
- sandbox 間で Docker layer を共有しない。
- KVM と host-side setup が必要。
- product / CLI が新しく、release cadence が速い。
- default direct mount では workspace 自体は隔離されないため、parallel write には clone mode が必要。

現在の調査環境では `sbx` は未導入です。`/dev/kvm` は存在しますが、利用者の group / setup も含めて検証が必要です。

結論:

- stable default ではなく high-isolation lane の有力 pilot。
- devcontainer の中からさらに起動するより、host 側の worker manager として使う方が自然。

### 8.3 Temporal などの durable workflow engine

数日単位、host failure、fleet scheduling、retry を本当に要件化するなら、local Bash や小さな daemon の延長では扱わない方がよいです。

ただし現時点で Temporal をこの repo の依存へ加えるのは重すぎます。採用閾値は次のように置きます。

- job が devcontainer / host lifecycle を越えて継続しなければならない。
- 複数 machine へ worker を配置する。
- retry / compensation / upgrade compatibility を監査可能にする必要がある。

この閾値を超えるまでは hosted agent を利用するか、local では orphan detection + manual retry に留めます。

## 9. container image 自体の刷新条件

### 9.1 stable / edge channel を分ける

#### stable

- base image digest を固定する。
- Dev Container Features lockfile をcommitし、frozen mode で検証する。
- AI CLI / Docker Agent 等を repo manifest で固定する。
- `postStartCommand` では package install しない。
- capability contract test を通過した version だけを昇格する。
- 通常コマンドは safe default。

#### edge

- host CLI sync や最新版を明示 opt-in で使う。
- native feature の先行評価に使う。
- stable workspace state と混在させない。

Dev Container CLI は現在、Feature lockfile を通常生成でき、`--frozen-lockfile` を提供しています。この repo にも解決済みdigestを含む `.devcontainer/devcontainer-lock.json` が存在しますが、現時点では未追跡です。第3ターンでは、これを正式な再現性契約へ入れるかを決めます。

### 9.2 image build と runtime update を分ける

現在の良い点:

- Ubuntu base digest が固定されている。
- Node archive checksum が固定されている。
- AI CLI の fallback version が build arg 化されている。

残る問題:

- TypeScript / ESLint / Prettier は version 未固定。
- apt package は rebuild 時に変わる。
- host sync が runtime に toolchain を変更する。

すべての apt package を手でpinするより、検証済み prebuilt image をdigestで配布し、定期 update PR で再build・testする方が運用しやすいです。

### 9.3 capability-based doctor

version 比較だけでなく、必要な surface を実際に確認します。

- Codex multi-agent enabled
- Codex structured output / resume / sandbox option
- Claude custom agents / background / worktree / JSON schema
- Git worktree support
- Docker / Compose availability
- cgroup / disk / KVM readiness
- provider auth は有効か。ただし secret 値は出さない。

contract が欠ければ、silent fallback せず lane を unavailable にします。

### 9.4 配布単位を分ける

「この repo の Dockerfile を全 project が直接使う」だけでは、project 固有の依存と基盤更新が密結合になります。将来の配布単位は次のように分ける余地があります。

| 配布物 | 責務 | 更新頻度 |
|---|---|---|
| verified coordinator image | OS、Git、Docker、固定済みagent CLI、broker runtime | 基盤の定期更新 |
| optional Dev Container Feature | broker / doctor / shared policy command | 小さな機能更新 |
| target-project worker setup | language runtime、dependency install、test service | projectごと |
| project agent contract | roles、scope、acceptance、task / result schema | code変更と一緒 |

prebuilt coordinator image をdigest指定すれば、毎回すべてをbuildするより起動が速く、aptの変動も閉じ込められます。Feature化する場合もversionとdigestをlockし、container開始時に最新版を取得する方式にはしません。

この分割は、基盤repoへサンプルアプリを追加せず、target project側の環境を尊重する現在のルールとも整合します。

### 9.5 検証を4層に分ける

すべてのtestで実providerを呼ぶと遅く高価になり、fakeだけではCLI driftを見逃します。

1. **pure unit**: job state、path、lease、retry、cleanupをfake processで高速検証する。
2. **CLI surface contract**: `--help`、feature list、schema optionなどを認証なしで検証する。
3. **container integration**: 2 worktree、port namespace、process kill、orphan recovery、resource limitをlocal fixture repoで検証する。
4. **live canary**: toolchain update時だけ、小さなreal provider taskでread、write、structured result、cancelを確認する。

stable imageへ昇格する条件は4層すべての通過とし、通常の開発testは1〜3を中心にします。これなら速度と実際の互換性確認を両立できます。

## 10. 資源、cache、port の設計

### concurrency を2種類に分ける

- **inference concurrency**: provider rate limit、token budget、agent thread 上限
- **execution concurrency**: CPU、memory、disk I/O、Docker build、test DB

model 応答待ちの agent は CPU をほぼ使わなくても、その agent が同時に test を始める可能性があります。単一の `max_agents` だけでは制御できません。

resource class の例:

- `read-light`
- `write-normal`
- `test-heavy`
- `docker-heavy`
- `browser`

worker container lane では cgroup の CPU / memory / pids limit を付けます。同一 devcontainer process lane では強いlimitが難しいため、まず scheduler のslot制御を使います。

### cache は共有範囲を限定する

共有しやすいもの:

- package download cache
- Git object store
- immutable compiler / build cache
- prebuilt image layers

共有しないもの:

- working tree の `node_modules` 等の mutable install tree
- test DB data
- provider session directory
- application runtime state

worktree を repository 配下の ignored directoryへ深く入れると、file watcher、search、Docker build context に拾われやすくなります。runtime workspace は外部 persistent volume 配下へ置き、project からは broker 経由で参照する方が安定しそうです。

### port はjobの資源

- agent に固定 port を自由入力させない。
- service 間通信は job 固有 network 内の名前解決を使う。
- human / browser access が必要な場合だけ loopback の空き port を broker が割り当てる。
- mapping を job state に記録し、cleanup 対象を確定する。

## 11. credential とGit権限

現在は host の `.codex`、`.claude`、SSH、Git設定などを coordinator container にmountします。全workerを同じcontainer processとして動かすと、全agentが同じ資格情報とmutable user configを見ます。

安定性・事故範囲を改善する原則:

- project agent definition はrepo内へ置く。
- worker に SSH private key やGitHub push tokenを渡さない。
- worker はcommitを作るだけにし、push / merge はcoordinatorだけが行う。
- provider auth と user customization を可能なら分離する。
- isolated lane では credential proxy または job-specific secret injection を使う。
- transcript / raw event の無制限保存をやめ、既定ではprovider native storageへの参照だけを残す。
- raw log が必要なら size limit、retention、redaction を持たせる。

完全にtrustedなlocal laneでは同一credentialを受け入れてもよいですが、それをsecurity boundaryとは呼ばないことが重要です。

## 12. integration は必ずsingle-writerにする

複数agentが速く書けても、main / integration branchへ全員が書くと不安定になります。

workerの完了条件:

- changesがcommitされている。
- result envelopeがschemaを満たす。
- `head_sha` が記録されている。
- task-level acceptanceが通っている。
- untracked / uncommitted changeが残っていない、または明示報告されている。

coordinatorの責務:

- baseとの関係を検証する。
- dependency順に取り込む。
- conflict時に自動forceしない。
- integration testを再実行する。
- review gateを通す。
- push / PR作成を行う。

agent間の直接messageより、Gitとstructured resultを統合境界にする方がproviderに依存せず安定します。

## 13. failure mode と望ましい回復

| failure | 現行で起こり得ること | 望ましい扱い |
|---|---|---|
| provider 429 / outage | CLI終了、手動再実行 | retryable分類、backoff、新attemptまたはnative resume |
| agent hang | timeoutで突然終了 | process-group cancel、exit reason、partial result保全 |
| container restart | process消失、session fileだけ残る | runningをorphanedへ遷移し、明示retry |
| partial edit後のretry | 二重編集 | checkpoint継続かclean attemptのどちらかを選ぶ |
| base branch前進 | stale branch継続 | jobのbase SHAは固定、integration時に競合検出 |
| 2 agentが同じport使用 | 起動失敗 / 相互干渉 | port allocator / job network |
| `compose down -v` | 別agentのservice削除 | unique project + label、またはprivate daemon |
| disk full | log / image / worktree作成失敗 | quota、retention、GC、preflight disk check |
| CLI自動更新 | wrapper parser破損 | stable lock + canary contract test |
| secretがprompt/logへ混入 |無制限JSONLへ残る |保存最小化、redaction、retention |
| merge conflict | 人が後から発見 | integration gateで即検出し、新しい修正jobへ |

## 14. 第1ターンから変わった判断

### 維持したもの

- native orchestration を標準経路にする。
- provider conversation / raw event を共通runtimeが所有しない。
- provider-neutralityはtask contractとGit成果物で作る。
- SDK control planeを最初から全面開発しない。

### 修正したもの

- thin layer は単なるpolicy launcherでは足りない。
- stable write concurrencyには workspace lease、job state、resource / port namespace、integration gateが必要。
- native-onlyはLane Rには最適だが、terminal-firstのLane Wには不足する。
- devcontainer内のbackground processをdurableと呼ばない。
- dangerous-by-defaultはsecurityだけでなく、native role isolationを無効化し得る安定性問題でもある。

### 新しい有力候補

- Docker Agentを「自前control planeを作る前の比較対象」にする。
- Docker Sandboxes clone modeをhigh-isolation laneとしてpilotする。
- stable / edge toolchain channelを分ける。

## 15. 第3ターンで決めること

第3ターンでは、次を具体的な推奨構成と移行順に落とします。

1. stable default は「同一container + worktree」か「worker container」か。
2. workspace broker の最小コマンドと state schema。
3. Docker Agent / Docker Sandboxes を core、optional、保留のどこへ置くか。
4. safe / trusted / isolated permission profile。
5. CLI lock、Feature lock、update PR、contract test の流れ。
6. 現行 `second-agent` のdeprecationと互換期間。
7. `AGENTS_TEMPLATE.md` と project template をどこまで縮小するか。
8. 実装を小さく分けた刷新backlog。

推奨案を確定する前に、最低限次のspikeを計画へ入れます。

- 同一base SHAから2 write jobを起動し、別worktree・別port・別Compose projectで完了できるか。
- workerを強制終了し、jobがorphanedになってclean attemptを作れるか。
- stable CLIを1段更新し、capability contractで破壊を検知できるか。
- reviewerのwriteが実際に拒否されるか。
- workerからSSH / GitHub credentialが見えないか。
- Docker Agentとnative Codex / Claudeで、同じtaskの品質・時間・token・回収容易性を比較する。
- Docker Sandbox clone modeのstartup、disk、cache、Git回収を測る。

## 16. 参照した根拠

### リポジトリ / ローカル確認

- `scripts/second-agent`
- `scripts/sync-host-ai-cli-versions`
- `.devcontainer/Dockerfile`
- `.devcontainer/devcontainer.json`
- `.devcontainer/devcontainer-lock.json`（既存・未追跡、内容のみ確認）
- local Docker Engine `29.6.0`
- Docker Agent / `sbx` は現在の調査環境に未導入

### 公式資料

- [Codex: Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents.md)
- [Codex: Worktrees](https://learn.chatgpt.com/docs/environments/git-worktrees.md)
- [Codex SDK](https://learn.chatgpt.com/docs/codex-sdk.md)
- [Claude Code: Run agents in parallel](https://code.claude.com/docs/en/agents)
- [Claude Code: Worktrees](https://code.claude.com/docs/en/worktrees)
- [Docker Agent](https://docs.docker.com/ai/docker-agent/)
- [Docker Agent CLI](https://docs.docker.com/ai/docker-agent/features/cli/)
- [Docker Agent tools](https://docs.docker.com/ai/docker-agent/configuration/tools/)
- [Docker Sandboxes](https://docs.docker.com/ai/sandboxes/)
- [Docker Sandboxes isolation](https://docs.docker.com/ai/sandboxes/security/isolation/)
- [Docker Sandboxes architecture](https://docs.docker.com/ai/sandboxes/architecture/)
- [Dev Container CLI lockfiles](https://github.com/devcontainers/cli)
- [Cursor: What we've learned building cloud agents](https://cursor.com/blog/cloud-agent-lessons)

## 第2ターン終了時の一文

**高速化のためにagentを増やすのではなく、readは軽くfan-outし、writeはbase SHAとworkspaceを排他し、重い実行はsandboxへ逃がし、統合だけをsingle-writerにする。その実行契約を再現可能なcontainerとして提供する。**
