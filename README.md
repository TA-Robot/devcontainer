# Cursor Dev Container

Cursor / VS Code 用の高権限 devcontainer 環境。AI コーディングツール（Codex CLI、Gemini CLI、Claude Code、Grok Build）を統合し、**信頼済みのローカル開発環境**で素早く作業するための基盤を提供します。

## 特徴

- **Ubuntu 22.04** ベース
- **Node.js 22.x** プリインストール
- **AI ツール統合**: Codex CLI、Fugu wrapper、Gemini CLI、Claude Code、Grok Build がすぐに使える
- **再現可能なstable toolchain**: Feature、Node、global npm tool、AI CLIを固定し、起動時installなし
- **明示的なedge channel**: 必要なときだけホストのCodex / Gemini / Claude Code / Grok versionへ同期
- **Docker-in-Docker**: コンテナ内でDockerを利用可能
- **ホスト設定の引き継ぎ**: SSH鍵、Git設定、認証情報を自動マウント
- **Mira Companion v2**: Codex / Claude / Grokのinteractive sessionとagentctl-managed jobが小さなpixel-art世界の動きになるbottom-panel companionを自動導入
- **Adaptive collaboration playbook**: 期待する効果と律速要因からagent同士の関係を組み立て、人数・interaction・候補数はprojectごとの観測で調整
- **Zero-input collaboration observation**: provider hookとagentctl lifecycleからsolo / delegated episodeの時間・worker・test・rework proxyを内容抜きで自動保存
- **Agent duration atlas**: 12 family × S/M/Lの有限corpus、quality/censoring付き実測record、exact-match query skillを提供

ミラのpersonaは `AGENTS.md`、再利用templateは `AGENTS_TEMPLATE.md`、companion architectureは [`docs/mira/architecture.md`](docs/mira/architecture.md)、visual asset contractは [`docs/mira/assets.md`](docs/mira/assets.md) を参照してください。

## クイックスタート

### 1. 前提条件

ホスト側に以下のディレクトリを作成しておく（存在しない場合）:

```bash
mkdir -p ~/.codex ~/.config/gemini ~/.claude ~/.grok
[ -s ~/.claude.json ] || printf '{}\n' > ~/.claude.json
```

`~/.claude.json` は devcontainer 起動前にも自動作成されますが、手動で mount 元を確認したい場合は上記を実行してください。

### 2. コンテナを起動

Cursor / VS Code でこのフォルダを開き、「Reopen in Container」を選択。

### 3. AI ツールを使う

```bash
# Codex CLI（safe既定: providerのapproval / sandboxを維持）
codex "ファイルを整理して"

# Codex CLI（trusted-fast: sandbox / approvalを明示的に迂回）
codex-trusted "テストを書いて"

# Codex CLI（フルオートモード）
codex-full "リファクタリングして"

# 旧aliasは移行互換として残る
codex-auto "テストを書いて"

# Fugu（Codex CLI + Sakana provider、既定モデルは fugu-ultra）
fugu exec "READMEを要約して"
fugu --model fugu exec "軽めのタスク"

# Gemini CLI
gemini

# Claude Code（safe既定）
claude

# Claude Code（trusted-fast: permission checkを明示的に迂回）
claude-trusted "テストを書いて"

# 旧aliasは移行互換として残る
claude-yolo "テストを書いて"

# Grok Build（safe既定）
grok

# Grok Build（trusted-fast: permission / sandboxを明示的に迂回）
grok-trusted -p "テストを書いて"

# 旧aliasは移行互換として残る
grok-yolo -p "テストを書いて"

# stable toolchain / provider capability / legacy stateを診断
agentctl doctor
agentctl doctor --json
```

image内Codexはversion pin / stable-edge同期をこのrepositoryが所有するため、system configでstartup update checkを無効化しています。通常の`codex`はproject trustを自動変更しません。明示的な`codex-trusted`だけは、full-access opt-inと同じscopeで起動時のcurrent working directoryをそのinvocation中だけtrusted projectとして渡し、headless goal投入前のonboarding promptを避けます。別directoryを対象にする場合は、起動前に移動するか`DEVCONTAINER_CODEX_TRUSTED_PROJECT_DIR`へabsolute pathを指定します。

### 4. Native multi-agent contractをprojectへ導入する

新規projectでは独自wrapperから始めず、このrepositoryの`project/`をcopy sourceとして使います。既存の`AGENTS.md`やprovider設定を上書きしないよう差分を確認し、`<<...>>`をproject固有値へ置き換えてください。`AGENTS_TEMPLATE.md`は同じcontractをmanager向け説明込みで展開した版です。

```text
AGENTS.md                         project共通のscope / lane / permission / integration
CLAUDE.md                        Claude CodeからAGENTS.mdをimport
.agent/                          provider-neutralなrole、task / result schema、examples
.codex/agents/*.toml             Codex native custom agents
.claude/agents/*.md              Claude Code native subagents
.grok/agents/*.md                Grok Build native custom agents
docs/agents/runbook.md           failure recovery / integration / GC
```

通常の調査とreviewは`researcher` / `reviewer` native subagentへfan-outします。実装用`implementer`は、primaryがimmutable base SHAから専用worktreeを割り当てた後だけ使います。untrusted codeや破壊的Docker操作は同一containerへ混ぜずisolated laneへ送ります。

agent同士の関係はlane、role、時間上のlifecycleとは別に設計します。soloより改善するmechanismと今回のbinding constraintを先に確認し、`solo / delegate / consult / compete / verify`を現在のrelation aliasとして必要な協働を組み立てます。人数、interaction、candidate数、blindnessはglobal defaultにせず、独立artifact、固有の観点、識別可能な案、検査したいfailure modeとproject-local evidenceから決めます。定期・event駆動workは無期限sessionではなく有限jobとして扱い、scheduler runtimeが未実装の間は存在を仮定しません。選択手順、parameterの意味、安全なstop conditionは[`collaboration model`](docs/agents/collaboration-model.md)とtarget copyの[`collaboration playbook`](project/docs/agents/collaboration-playbook.md)を参照してください。

人間へ日報やform入力を要求しません。Codex / Claude / Grok hookと`agentctl` eventは、prompt、code、command、pathを保存せず、solo / delegated turnのduration、worker start / stop、peak concurrency、test outcome、rework / post-worker-tail proxyを`$MIRA_COMPANION_EPISODE_DIR/collaboration-episodes.json`へ自動保存します。このdevcontainerではrebuild後も残るnamed volume上の`/var/lib/mira-observations`です。optionalなdecision contractをtaskへ添付した`agentctl` jobだけは、IDをopaque化してrelation、lifecycle、expected mechanism、binding constraintと相関できます。`report-agent-collaboration-evidence`とtargetの`$review-collaboration-evidence`はepisode本文を出さずworkspace-localな記述統計を返します。欠測は推測せず`unknown / unmeasured`です。schema、coverage、retention、privacyは[`zero-input collaboration observation`](docs/agents/collaboration-observation.md)を参照してください。

Controlled corpusの所要時間は別のduration atlasへ保存します。36 caseの存在はmodel/provider/relationの全組合せを測定済みという意味ではなく、単一観測、quality-fail、requested-only effort、timeoutを分離したままexact条件で参照します。Dev Container内では`query-agent-duration-atlas`、target projectでは`project/.codex/skills/lookup-agent-duration/`を利用できます。計測、有限batch、resume、欠測の読み方は[`duration atlas operator guide`](docs/agents/duration-atlas/README.md)が正本です。

native childはparent sessionのlive permissionを継承し得ます。read-only agent fileを置いただけで強いruntime overrideが弱まるとはみなしません。safe Lane Rならparentもsafeにします。session / workspace全体へ`trusted-fast`を明示許可した場合だけ、boundedなconsult / verify childを同じtrusted permissionで動かせます。この場合はLane Rや強制read-onlyと呼ばず、`trusted advisory`として記録します。

templateとschemaの整合性確認:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate-agent-contracts.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest scripts/test-agent-contracts.py
```

Phase 3a–3eのwrite fabricはforegroundとsupervisor-managed detachの両方を利用できます。

```bash
agentctl project register
agentctl job create --task docs/agents/tasks/task-0001.json
agentctl job run <job-id> --provider codex   # または claude / grok
agentctl job run <job-id> --provider codex --detach
agentctl job cancel <job-id>
agentctl job validate <job-id>
agentctl job collect <job-id> --json
agentctl job logs <job-id> --lines 80
agentctl gc --dry-run --job <job-id> --json
```

write providerはGit common metadataへ直接commitせず、`ready_for_commit`を返します。brokerがscope、HEAD、dirty pathsをGitから照合してjob branchへcommitするため、Codexのsafe sandboxを崩さずlinked worktreeを使えます。state、attempt evidence、worktreeは`/var/lib/agentctl`のnamed volumeへ保存されます。detachはowner-only Unix socketのlocal supervisorへ渡され、PID＋process start time、heartbeat、process-group cancel、restart時orphan判定に加え、resource class別capacity、priority queue、Compose namespace、integration port leaseを持ちます。validated jobは`collect`でdependency順・commit候補・path overlap・checks/risksをimmutable reportへ集約しますが、merge/pushは行いません。運用時のlog viewはboundedかつbest-effortでsecretをredactし、provider終了後のraw logは8 MiB、runner logは1 MiB、live supervisor logは2 MiBのtailへ制限します。`gc --dry-run`はcanonical path、Git identity、integration evidence、job固有Docker labelまで再確認しますが、削除は一切行いません。jobの開始・成功・失敗・cancel・orphanはprovider / roleだけのsanitized eventとしてMira Worldへ自動反映されます。CLI、state、failure semanticsは[`docs/agentctl.md`](docs/agentctl.md)を参照してください。

Lane Iはまだstable runtimeを持たず、同一containerへfallbackしません。optional runtimeの導入前probeと、model request/image pullなしのprivate-daemon比較は`python3 scripts/benchmark-isolated-runtime-pilot.py --probe-only` / `--repetitions 5`で実行できます。現時点の結果と「privileged DinDをsecurity boundaryにはしない」という判断は[`docs/agents/isolated-runtime-pilot-2026-08-12.md`](docs/agents/isolated-runtime-pilot-2026-08-12.md)にあります。

設計判断は[`ADR-0001`](docs/adr/0001-native-first-multi-agent-execution.md)、target contractの全体像は[`AGENTS_TEMPLATE.md`](AGENTS_TEMPLATE.md)、実行fabricは[`docs/agentctl.md`](docs/agentctl.md)、失敗時の正本は[`project/docs/agents/runbook.md`](project/docs/agents/runbook.md)です。

### 5. Mira Companionを有効にする

devcontainerにeditorがattachした後、local VSIXをpackageしてremote側のVS Code / Cursorへ自動導入します。専用のActivity Barやsidebarは作らず、VS Code下部に短い`Mira World` panelを1つ追加します。workspace初回とremote runtimeのrebuild直後だけ自動で復帰し、同じruntimeでのreload以後はVS Codeが記憶するpanelの開閉状態を尊重します。status bar右側の小さなMiraはworldを再度開くtoggleです。

Codex / Claude / Grok連携はimage内のcontainer-managed hookで行います。配置先はそれぞれ`/etc/codex/requirements.toml`、`/etc/claude-code/managed-settings.d/50-mira-companion.json`、`/etc/grok/managed_config.toml`です。Codexのcentrally managed lifecycle defaultは`/etc/codex/config.toml`へ分離しています。Claude / Grok側も既存hookへ加算され、bind mountした`~/.claude` / `~/.grok`、認証、permission、sandboxを変更しません。対象projectへhookをコピーしたり、projectごとに信頼したりする必要もありません。さらに`agentctl`経由のCodex / Claude / Grok jobは共通brokerから同じbridgeへ接続され、provider別人数とresearcher / reviewer / implementerのrole spriteとして表示されます。調査なら資料庫、planningなら作戦卓、編集やshellなら工房、testならsignal gate、delegationならdispatch dockへミラが自動で歩き、到着後に状態別animationへ変わります。idle中も低頻度でmap内を散歩します。

状態ファイルをまだ一度も受信していない場合は、HUDへ`activity未接続`と表示します。imageを更新した直後はeditorをreloadし、新しいCodex / Claude / Grok sessionを開始してください。正常に接続され、active workがなければ`待機中`になります。direct CLIではprovider自身のlifecycleとnative subagent、`agentctl`ではdurable job transitionを観測します。

ハイタッチ、なでる、常設menuはありません。長い作業の完了、test recovery、badge獲得など自然な区切りにだけ、ミラの近くへ45秒で消えるone-click popが現れます。押さなくても損はなく、clickによるXP差もありません。motionは`auto` / `subtle` / `full` / `off`、status toggleは表示 / 非表示を選べます。

自動導入されなかった場合:

```bash
scripts/install-mira-vscode-extension
```

新規containerでremote editor CLIが準備される前に導入処理が走らないよう、AI CLI同期は`postStartCommand`、Mira導入は`postAttachCommand`に分離しています。PATH上にremote CLIがないlifecycle shellでは`code-server` / `cursor-server`を直接使い、install後に期待versionが一覧へ現れたことまで確認します。editor attach中は30秒以内にCLIが見つからなければlifecycle errorにします。一方、CLIだけで行うheadless `devcontainer up`は正しいorchestration runtimeなので、待機せずMira導入だけをskipして成功します。判定を明示したい時は`MIRA_COMPANION_ATTACH_MODE=editor|headless`を使えます。

Command Paletteの`ミラ: Mira Worldを開く`でも再表示できます。Mira全体を止める場合は、devcontainerを開く前にホスト側で`MIRA_COMPANION_ENABLED=0`を設定します。hookは残して拡張の自動導入だけを止める場合は`MIRA_COMPANION_INSTALL=0`を使います。

## Trust Model

この devcontainer は **sandbox ではありません**。利便性を優先した、信頼済みホスト向けの構成です。

- ホストの SSH / Git / AI 認証情報をマウントします
- AI 認証情報は **ホスト側ディレクトリ/ファイルを直接 bind mount** します。ホスト側の更新はコンテナへ即時反映され、コンテナ側の更新もホスト側へ書き戻されます
- `docker-in-docker` を前提にした高権限設定です
- devcontainer 内の通常 `codex` / `claude` / `grok` はproviderのapproval / sandboxを維持します
- `codex-trusted` / `claude-trusted` / `grok-trusted`だけが明示的に権限バイパスを付けます
- `codex-second-agent` / `claude-second-agent` も常に権限バイパス用フラグを付けます

使いどころ:

- 信頼しているコードベースを、信頼しているローカルマシン上で素早く開発したい場合

使うべきでない場面:

- 未検証コードを隔離したい場合
- ホスト資格情報をコンテナへ渡したくない場合
- 強いマルチテナント隔離が必要な場合

設計方針は [`docs/architecture.md`](docs/architecture.md)、toolchain更新手順は
[`docs/toolchain.md`](docs/toolchain.md) を参照してください。

## Legacy compatibility: second-agent wrapper

> **Legacy / feature frozen:** この節のwrapperは並行移行中の互換surfaceです。
> security、data-loss、CLI compatibility以外の機能は追加しません。新設計と
> 非破壊inventoryは [`ADR-0001`](docs/adr/0001-native-first-multi-agent-execution.md) と
> [`legacy-second-agent.md`](docs/agents/legacy-second-agent.md) を参照してください。既存jobの継続・回収・削除手順は
> [`legacy-second-agent-runbook.md`](docs/agents/legacy-second-agent-runbook.md)が正本です。

このリポジトリには、**非対話で呼べる“セカンドエージェント”口**を同梱しています。Codex 用の `codex-second-agent` と Claude Code 用の `claude-second-agent` があり、どちらも共通エンジン `second-agent`（`scripts/second-agent`）の薄いシムです。CLI 表面（サブコマンド/オプション）は共通なので、`codex-second-agent` を `claude-second-agent` に置き換えるだけでバックエンドを切り替えられます。

Grokはこのfeature-frozen wrapperへ追加しません。新規のGrok jobはnative `.grok/agents/`と`agentctl --provider grok`を使い、3つ目のbackendを旧bash engineへ増築しない方針です。

セッションIDは **ツール側が target workspace ごとの state ディレクトリに保存**するため、CursorエージェントがIDを覚えておく必要がありません。

### バックエンドの違い（要点）

| 項目 | `codex-second-agent` | `claude-second-agent` |
|------|----------------------|------------------------|
| 内部実行 | `codex exec --json` | `claude -p --output-format stream-json --verbose` |
| 権限バイパス | `--dangerously-bypass-approvals-and-sandbox --search` | `--dangerously-skip-permissions` |
| 作業ディレクトリ | `--cd <path>` を渡す | flag が無いため wrapper が `cd` する |
| セッション継続 | `codex exec resume <id>` | `claude -r <id>` |
| 固定モデル | `gpt-5.5`（`CODEX_SA_MODEL` で上書き可） | `opus`（`CLAUDE_SA_MODEL` で上書き可） |
| 環境変数プレフィックス | `CODEX_SA_*` | `CLAUDE_SA_*` |
| state ディレクトリ | `.codex-second-agent` | `.claude-second-agent` |
| worktree ブランチ | `agent/<name>` | `claude-agent/<name>` |

### 互換wrapperの参照先

新規projectの運用手順をこの節からcopyしないでください。native-first templateは`AGENTS_TEMPLATE.md`と`project/`、既存wrapperの具体的なrecovery操作は`docs/agents/legacy-second-agent-runbook.md`を参照します。

### 内部の挙動（実装の要点）

以下の `<be>` は backend 名（`codex` / `claude`）、`<PREFIX>` は環境変数プレフィックス（`CODEX_SA` / `CLAUDE_SA`）を表します。workspace スコープ・worktree・state/log 管理は共通エンジン `second-agent` が担います。

- バックエンドの JSONL イベントからセッションIDを抽出して保存し、2回目以降は resume で継続します
- 実行状態の保存先はデフォルトで `<workspace>/.<be>-second-agent/<workspace_hash>/agents/<agent>/session_id` です
  - 同じ target workspace を別の control repo から呼んでも、session / logs / worktrees を共有します
  - `<PREFIX>_STATE_DIR` で保存先ルートを変更できます
- `workspace init` の設定自体は control repo 側の `.<be>-second-agent/control/<control_hash>/config/` に保存します
- メインエージェント↔サブエージェントの会話ログは `<workspace>/.<be>-second-agent/<workspace_hash>/agents/<agent>/logs/` に保存されます
  - `events.jsonl`: バックエンドの生イベント（JSONL）を追記
  - `transcript.jsonl`: 1リクエスト=1行で `agent` / `cd` / `prompt` / `response` をまとめたログ（JSONL）
  - `<PREFIX>_LOG_DIR` でログ保存先ディレクトリを変更できます
- エージェント用の作業ディレクトリ（git worktree）は次のいずれかに作成します
  - **デフォルト**: `<workspace>/.<be>-second-agent/<workspace_hash>/worktrees/<agent>/`
  - `<PREFIX>_WORKTREES_MODE=workspace` または `--worktrees-in-workspace` を使う場合: `<workspace>/.<be>-worktrees/<agent>/`
  - `<PREFIX>_WORKTREES_DIR` を指定した場合: 指定パス配下
  - **非defaultエージェントは、未作成なら自動でworktreeを作成**してそこで実行します（`<PREFIX>_AUTO_WORKTREE=0` または `--no-auto-worktree` で無効化）
  - **非defaultエージェントの path 系オプション（`--cd` / `--add-dir`）は configured workspace 内だけ**を許可し、必要なら対応する worktree パスへ写像します

### `workspace init` と `--cd` の使い分け

- `workspace init .` のように **親リポジトリを workspace** にした場合は、必要に応じて `-- --cd <workspace-relative-subdir>` を付けます
- `workspace init <path-to-project-git>` のように **対象プロジェクトの Git ルート自体を workspace** にした場合は、通常 `--cd` は不要です
  - この場合の `effective_cd` は agent worktree のルートになります
- `--cd` は両バックエンド共通で使えます（claude では wrapper が指定先へ `cd` し、claude 自体には渡しません）
- sub-agent に共有コンテキストを渡したい場合も、`--add-dir` で workspace 外は渡せません
  - 共有したい runbook / ticket / decision log は対象 workspace 側へミラーするか、prompt に要点を転記してください
- `workspace init` 時に対象 repo の `.gitignore` へ `.codex-second-agent/` `.codex-worktrees/` `.claude-second-agent/` `.claude-worktrees/` を**自動追記**します（不足分のみ。手動で入れてもOK）

### 運用に効くコマンド（抜粋）

`codex-second-agent` は `claude-second-agent` に読み替え可。

- `<be>-second-agent paths`: state/log/worktree の実体パスと `effective_cd` を表示
- `<be>-second-agent status --verbose`: session_id と各種パスをまとめて表示
- `<be>-second-agent doctor`: backend / 環境 / パス / 設定の簡易診断（トラブル切り分け）
- `<be>-second-agent worktree remove <agent> [--keep-branch]`: worktree削除（必要ならブランチも整理）
- `<be>-second-agent worktree prune`: 実体が消えた worktree 登録を掃除（`git worktree prune`）
- `<be>-second-agent --post-git-status ...`（または `<PREFIX>_POST_GIT_STATUS=1`）: 実行後に未コミット変更を要約して検知
- `<PREFIX>_TIMEOUT=120s <be>-second-agent ...`: 実行をタイムアウトで包む（GNU `timeout` 形式）

### 運用上の注意

- セカンドエージェントは **常に権限バイパスを有効化**します（codex: `--dangerously-bypass-approvals-and-sandbox --search` / claude: `--dangerously-skip-permissions`）。運用方針として固定です
- 権限バイパスは危険です。隔離環境ではなく、信頼済みホスト上の高権限運用として扱ってください
- **workspace スコープ制限は「事故低減」であって隔離（security boundary）ではありません。** 実行は常にホスト権限フルです
- 既定エージェント（`default`）も `--cd`/`--add-dir` は**既定で実行対象 repo の中だけ**に制限されます。外を触らせたいときだけ `--allow-outside-workspace`（または `<PREFIX>_ALLOW_OUTSIDE=1`）を付けてください。なお worktree 隔離・セッション分離が欲しいサブエージェント運用では `--agent <name>` を使います
- 使用モデルは固定です（codex: 既定 `gpt-5.5`、`CODEX_SA_MODEL` で上書き可 / claude: 既定 `opus`、`CLAUDE_SA_MODEL` で上書き可）。既定値はコード直書きのため陳腐化し得ます（env でピン留め推奨）
  - `--model` などのモデル選択系オプションは passthrough から除去されます
  - codex は `--config model=...` / `--oss` / `--local-provider` も無視します
  - claude は `--output-format` / `--input-format` / `--permission-mode` / `-p` / `-r` / `--session-id` など、wrapper が固定する実行フラグを passthrough から除去します
  - claude はプロンプトを stdin で受けます。`--` 以降に位置引数（裸の文字列）を置くと二重プロンプトになるため避けてください
- ログ（`events.jsonl` / `transcript.jsonl`）は prompt/response 全文を含み、ローテーションしません。**機微情報をプロンプトに載せない**でください。state 配下は `umask 077`（所有者のみ）で作成します
- プロンプトは codex / claude とも stdin で渡します（`ps` のプロセス一覧に本文が出ません）
- 同一 agent の同時実行は `flock`（利用可能な場合）で直列化します
- state レイアウトは `<state>/VERSION` で版管理され、不一致時は警告します
- 保存済み workspace が移動・削除されて無効になった場合、実行は止まり、`paths` / `doctor` に `workspace_valid: no` が表示されます
- 実体は `bash >= 4.4` を要求します（`set -u` 下の空配列展開のため）

## プリインストールツール

Dockerfileのversionがstableの正本です。stable起動時はhost CLIをprobeせず、npm packageも更新しません。host versionへ追従するのはedgeを明示した場合だけです。

| カテゴリ | ツール |
|----------|--------|
| **ランタイム** | Node.js 22.x, Python 3 |
| **AI CLI** | @openai/codex, @google/gemini-cli, @anthropic-ai/claude-code, Grok Build |
| **開発ツール** | TypeScript, ESLint, Prettier |
| **ユーティリティ** | Git, GitHub CLI, ripgrep, jq, vim |
| **シェル** | Bash, Zsh |

## Fugu wrapper

`fugu` は Codex CLI に Sakana API の provider 設定を付けて起動する薄い wrapper です。既定モデルは `fugu-ultra` です。

```bash
fugu exec "READMEを要約して"
fugu exec --json "この差分をレビューして"
fugu --model fugu exec "軽めのタスク"
fugu --model fugu-ultra exec "重めのレビュー"
```

API key は次の順で使います。

1. 環境変数 `SAKANA_API_KEY`
2. `--api-key-file PATH`
3. `/workspace/fugu-api`
4. 実行ディレクトリの `./fugu-api`

`fugu-api` は秘密情報なので `.gitignore` に入れています。ホスト側のこのリポジトリ直下に置くと、devcontainer 内では `/workspace/fugu-api` として参照されます。

## マウント設定

| ホスト | コンテナ | 用途 |
|--------|----------|------|
| `~/.ssh` | `/home/devuser/.ssh` | SSH鍵（Git操作） |
| `~/.gitconfig` | `/home/devuser/.gitconfig` | Git設定 |
| `~/.codex` | `/home/devuser/.codex` | Codex認証情報・設定 |
| `~/.config/gemini` | `/home/devuser/.config/gemini` | Gemini CLI設定 |
| `~/.claude.json` | `/home/devuser/.claude.json` | Claude Codeグローバル設定・アカウント情報 |
| `~/.claude` | `/home/devuser/.claude` | Claude Code認証情報・設定 |
| `~/.grok` | `/home/devuser/.grok` | Grok Build認証情報・設定・session |
| `~/.cache/devcontainer-ai-cli` | `/opt/devcontainer-host-ai-cli` | CLI version manifest（read-only、credential なし） |

AI CLI の認証ディレクトリ/ファイルは CLI の標準パスへ直接 mount するため、ホスト側でログインし直した token 更新はコンテナ内からそのまま見えます。
コンテナ内でログイン・token refresh が発生した場合も、同じホスト側パスへ書き戻されます。

## Stable / edge AI CLI channel

既定のstableはimage-pinned packageをそのまま使います。`grok` wrapperはbackground self-updateも抑止し、更新の所有権をstable/edge channelへ一本化します。

```bash
agentctl doctor --json
```

host側CLIのversionをcanaryしたい場合だけ、devcontainerを開く前にhostで設定します。

```bash
export DEVCONTAINER_AI_CLI_CHANNEL=edge
```

edgeでは次の順でhost側versionを反映します。

1. ホストの `initializeCommand` が `codex --version` / `gemini --version` / `claude --version` / `grok --version` を検出し、`~/.cache/devcontainer-ai-cli/versions.env` にバージョン番号だけを保存
2. cache ディレクトリをコンテナへ read-only mount
3. `postStartCommand` が差分のあるnpm packageとGrok公式binaryを `/opt/devcontainer-ai-cli` へ導入

ホストの実行ファイル自体は mount しません。Codex などには OS / CPU 別の native package が含まれるため、バージョンだけを合わせてコンテナ向け package を導入します。

host側でCLIをupdateした後はdevcontainerを開き直してください。edge同期にはnpm registryと`x.ai`への接続が必要です。stableへ戻すには環境変数をunsetし、image-pinned prefixへ戻すためcontainerをrebuildします。

確認:

```bash
codex --version
gemini --version
claude --version
grok --version
fugu --version  # Fugu は Codex CLI を利用するため、Codex と同じ version
```

hostに存在しないCLIはimage versionを維持します。旧`DEVCONTAINER_AI_CLI_SYNC=1`はedge opt-in、`=0`はhost probe/sync無効として移行期間だけ維持します。詳細と更新手順は [`docs/toolchain.md`](docs/toolchain.md) を参照してください。

`fugu`自体はnpm packageではなく、このrepositoryの`scripts/fugu`を呼ぶwrapperです。実行engineのCodex versionは選択中のstable / edge channelに従います。

## 環境変数

ホスト側で以下の環境変数が設定されていれば、remote editorとintegrated terminalのprocessへ引き継がれます。stable imageのENVには保存しません:

- `OPENAI_API_KEY`
- `SAKANA_API_KEY`
- `GEMINI_API_KEY`
- `ANTHROPIC_API_KEY`
- `XAI_API_KEY`

通常の`codex` / `claude` / `grok`は危険flagを自動付与しません。明示的なtrusted commandだけが次を付けます。

- `codex-trusted`: `--dangerously-bypass-approvals-and-sandbox`
- `claude-trusted`: `--dangerously-skip-permissions`
- `grok-trusted`: `--permission-mode bypassPermissions --sandbox off`

旧automationを一時的に互換動作させる環境変数も残していますが、新規利用ではtrusted commandを使ってください。

```bash
DEVCONTAINER_CODEX_DANGEROUS_DEFAULT=1 codex
DEVCONTAINER_CLAUDE_DANGEROUS_DEFAULT=1 claude
DEVCONTAINER_GROK_DANGEROUS_DEFAULT=1 grok
```

実体の CLI は `/opt/devcontainer-ai-cli/bin/codex` / `/opt/devcontainer-ai-cli/bin/claude` / `/opt/devcontainer-ai-cli/bin/grok` に置き、`/usr/local/bin` の wrapper から呼び出します。

## エイリアス

| エイリアス | 展開 |
|------------|------|
| `codex-trusted` | explicit trusted-fast executable |
| `codex-auto` | `codex-trusted`（legacy alias） |
| `codex-full` | `codex --full-auto` |
| `codex-ask` | `codex`（legacy alias） |
| `fugu-ultra` | `fugu --model fugu-ultra` |
| `claude-trusted` | explicit trusted-fast executable |
| `claude-yolo` | `claude-trusted`（legacy alias） |
| `claude-ask` | `claude`（legacy alias） |
| `grok-trusted` | explicit trusted-fast executable |
| `grok-yolo` | `grok-trusted`（legacy alias） |
| `grok-ask` | `grok`（legacy alias） |

## カスタマイズ

### 拡張機能の追加

`.devcontainer/devcontainer.json` の `customizations.vscode.extensions` に追加:

```json
"extensions": [
  "ms-python.python",
  "esbenp.prettier-vscode",
  // 追加したい拡張機能
]
```

### パッケージの追加

`.devcontainer/Dockerfile` の `npm install -g` セクションに追加:

```dockerfile
RUN npm install -g \
    typescript@<exact-version> \
    ts-node@<exact-version> \
    # 追加したいパッケージ
```

### コンテナ再ビルド

設定変更後は、コマンドパレットから「Dev Containers: Rebuild Container」を実行。

## トラブルシューティング

### マウントエラーが出る

ホスト側にディレクトリが存在しない可能性があります:

```bash
mkdir -p ~/.codex ~/.config/gemini ~/.claude ~/.grok
[ -s ~/.claude.json ] || printf '{}\n' > ~/.claude.json
```

### 認証が効かない

1. ホスト側またはコンテナ側でログインする:
   ```bash
   codex  # 初回は認証フローが走る
   gemini # 初回は認証フローが走る
   claude # 初回は認証フローが走る
   grok   # 初回は認証フローが走る
   ```
2. それでも反映されない場合は、ホスト側の `~/.codex` / `~/.config/gemini` / `~/.claude` / `~/.claude.json` / `~/.grok` が存在することを確認し、devcontainer を開き直してください
3. Claude Code の対話モードだけが login を求める場合は、`~/.claude.json` が `/home/devuser/.claude.json` に mount されているか確認してください
4. `~/.claude.json` が 0 byte だと Claude Code は「corrupted」と判定し onboarding/login に戻ります。空なら `printf '{}\n' > ~/.claude.json` で初期化してください（`initializeCommand` が自動で行いますが、手動でも可）

### ホストと AI CLI のバージョンが合わない

1. ホスト側で `.devcontainer/initialize-host.sh` を実行し、`~/.cache/devcontainer-ai-cli/versions.env` を更新する
2. devcontainer を開き直す
3. 起動ログの `devcontainer: syncing ...` または `already matches the host` を確認する

純粋な `docker restart` ではホスト側の `initializeCommand` は実行されない実装もあります。その場合も上記の手動実行後に再起動すれば、`postStartCommand` が同期します。

### 権限エラー

ホストとコンテナのUID/GIDが異なる場合に発生することがあります。
Dockerfile の `USER_UID` を調整するか、ホスト側のファイル権限を確認してください。

## ライセンス

MIT
