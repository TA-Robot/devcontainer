# Cursor Dev Container

Cursor / VS Code 用の高権限 devcontainer 環境。AI コーディングツール（Codex CLI、Gemini CLI、Claude Code）を統合し、**信頼済みのローカル開発環境**で素早く作業するための基盤を提供します。

## 特徴

- **Ubuntu 22.04** ベース
- **Node.js 22.x** プリインストール
- **AI ツール統合**: Codex CLI、Fugu wrapper、Gemini CLI、Claude Code がすぐに使える
- **Docker-in-Docker**: コンテナ内でDockerを利用可能
- **ホスト設定の引き継ぎ**: SSH鍵、Git設定、認証情報を自動マウント

## クイックスタート

### 1. 前提条件

ホスト側に以下のディレクトリを作成しておく（存在しない場合）:

```bash
mkdir -p ~/.codex ~/.config/gemini ~/.claude
```

### 2. コンテナを起動

Cursor / VS Code でこのフォルダを開き、「Reopen in Container」を選択。

### 3. AI ツールを使う

```bash
# Codex CLI（通常モード）
codex "ファイルを整理して"

# Codex CLI（自動承認モード）
codex-auto "テストを書いて"

# Codex CLI（フルオートモード）
codex-full "リファクタリングして"

# Fugu（Codex CLI + Sakana provider、既定モデルは fugu-ultra）
fugu exec "READMEを要約して"
fugu --model fugu exec "軽めのタスク"

# Gemini CLI
gemini

# Claude Code（通常モード）
claude

# Claude Code（権限確認スキップモード）
claude-yolo "テストを書いて"
```

## Trust Model

この devcontainer は **sandbox ではありません**。利便性を優先した、信頼済みホスト向けの構成です。

- ホストの SSH / Git / AI 認証情報をマウントします
- AI 認証情報は **ホスト側ディレクトリを直接 bind mount** します。ホスト側の更新はコンテナへ即時反映され、コンテナ側の更新もホスト側へ書き戻されます
- `docker-in-docker` を前提にした高権限設定です
- `codex-second-agent` は常に `--dangerously-bypass-approvals-and-sandbox` を付けます

使いどころ:

- 信頼しているコードベースを、信頼しているローカルマシン上で素早く開発したい場合

使うべきでない場面:

- 未検証コードを隔離したい場合
- ホスト資格情報をコンテナへ渡したくない場合
- 強いマルチテナント隔離が必要な場合

設計方針と推奨レイアウトは [docs/architecture.md](/home/asakura/devcontainer/docs/architecture.md) を参照してください。

## Cursorエージェント向け: セカンドエージェント用ツール（Codex / Claude）

このリポジトリには、**非対話で呼べる“セカンドエージェント”口**を同梱しています。Codex 用の `codex-second-agent` と Claude Code 用の `claude-second-agent` があり、どちらも共通エンジン `second-agent`（`scripts/second-agent`）の薄いシムです。CLI 表面（サブコマンド/オプション）は共通なので、`codex-second-agent` を `claude-second-agent` に置き換えるだけでバックエンドを切り替えられます。

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

### 使い方（Cursorエージェント向け）

この基盤リポジトリ自身の開発ルールは `AGENTS.md`、別プロジェクトでの運用手順は `AGENTS_TEMPLATE.md` と `project/AGENTS.md` を参照してください。

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

AI CLI のバージョンは Dockerfile で固定しています（再ビルド時の挙動差分を減らすため）。

| カテゴリ | ツール |
|----------|--------|
| **ランタイム** | Node.js 22.x, Python 3 |
| **AI CLI** | @openai/codex, @google/gemini-cli, @anthropic-ai/claude-code |
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
| `~/.claude` | `/home/devuser/.claude` | Claude Code認証情報・設定 |

AI CLI の認証ディレクトリは CLI の標準パスへ直接 mount するため、ホスト側でログインし直した token 更新はコンテナ内からそのまま見えます。  
コンテナ内でログイン・token refresh が発生した場合も、同じホスト側ディレクトリへ書き戻されます。

## 環境変数

ホスト側で以下の環境変数が設定されていれば、コンテナに引き継がれます:

- `OPENAI_API_KEY`
- `SAKANA_API_KEY`
- `GEMINI_API_KEY`
- `ANTHROPIC_API_KEY`

## エイリアス

| エイリアス | 展開 |
|------------|------|
| `codex-auto` | `codex --dangerously-bypass-approvals-and-sandbox` |
| `codex-full` | `codex --full-auto` |
| `fugu-ultra` | `fugu --model fugu-ultra` |
| `claude-yolo` | `claude --dangerously-skip-permissions` |

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
    typescript \
    ts-node \
    # 追加したいパッケージ
```

### コンテナ再ビルド

設定変更後は、コマンドパレットから「Dev Containers: Rebuild Container」を実行。

## トラブルシューティング

### マウントエラーが出る

ホスト側にディレクトリが存在しない可能性があります:

```bash
mkdir -p ~/.codex ~/.config/gemini ~/.claude
```

### 認証が効かない

1. ホスト側またはコンテナ側でログインする:
   ```bash
   codex  # 初回は認証フローが走る
   gemini # 初回は認証フローが走る
   claude # 初回は認証フローが走る
   ```
2. それでも反映されない場合は、ホスト側の `~/.codex` / `~/.config/gemini` / `~/.claude` が存在することを確認し、devcontainer を開き直してください

### 権限エラー

ホストとコンテナのUID/GIDが異なる場合に発生することがあります。
Dockerfile の `USER_UID` を調整するか、ホスト側のファイル権限を確認してください。

## ライセンス

MIT
