# Cursor Dev Container

Cursor / VS Code 用の高権限 devcontainer 環境。AI コーディングツール（Codex CLI、Gemini CLI、Claude Code）を統合し、**信頼済みのローカル開発環境**で素早く作業するための基盤を提供します。

## 特徴

- **Ubuntu 22.04** ベース
- **Node.js 22.x** プリインストール
- **AI ツール統合**: Codex CLI、Gemini CLI、Claude Code がすぐに使える
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
- AI 認証情報は **read-only mount + container local copy** として扱い、ホスト側へは書き戻しません
- `docker-in-docker` を前提にした高権限設定です
- `codex-second-agent` は常に `--dangerously-bypass-approvals-and-sandbox` を付けます

使いどころ:

- 信頼しているコードベースを、信頼しているローカルマシン上で素早く開発したい場合

使うべきでない場面:

- 未検証コードを隔離したい場合
- ホスト資格情報をコンテナへ渡したくない場合
- 強いマルチテナント隔離が必要な場合

設計方針と推奨レイアウトは [docs/architecture.md](/home/asakura/devcontainer/docs/architecture.md) を参照してください。

## Cursorエージェント向け: Codex セカンドエージェント用ツール

このリポジトリには、`codex exec` を使って **非対話で呼べる“セカンドエージェント”口**として `codex-second-agent` を同梱しています。
セッションID(thread_id)は **ツール側が target workspace ごとの state ディレクトリに保存**するため、CursorエージェントがIDを覚えておく必要がありません。

### 使い方（Cursorエージェント向け）

この基盤リポジトリ自身の開発ルールは `AGENTS.md`、別プロジェクトでの運用手順は `AGENTS_TEMPLATE.md` と `project/AGENTS.md` を参照してください。

### 内部の挙動（実装の要点）

- `codex-second-agent` は内部で `codex exec --json ...` を実行します
- JSONLの `thread.started.thread_id` を抽出してセッションIDとして保存し、2回目以降は `codex exec resume <id> ...` で継続します
- 実行状態の保存先はデフォルトで `<workspace>/.codex-second-agent/<workspace_hash>/agents/<agent>/session_id` です
  - 同じ target workspace を別の control repo から呼んでも、session / logs / worktrees を共有します
  - `CODEX_SA_STATE_DIR` で保存先ルートを変更できます
- `workspace init` の設定自体は control repo 側の `.codex-second-agent/control/<control_hash>/config/` に保存します
- メインエージェント↔サブエージェントの会話ログは `<workspace>/.codex-second-agent/<workspace_hash>/agents/<agent>/logs/` に保存されます
  - `events.jsonl`: `codex --json` の生イベント（JSONL）を追記
  - `transcript.jsonl`: 1リクエスト=1行で `agent` / `cd` / `prompt` / `response` をまとめたログ（JSONL）
  - `CODEX_SA_LOG_DIR` でログ保存先ディレクトリを変更できます
- エージェント用の作業ディレクトリ（git worktree）は次のいずれかに作成します
  - **デフォルト**: `<workspace>/.codex-second-agent/<workspace_hash>/worktrees/<agent>/`
  - `CODEX_SA_WORKTREES_MODE=workspace` または `--worktrees-in-workspace` を使う場合: `<workspace>/.codex-worktrees/<agent>/`
  - `CODEX_SA_WORKTREES_DIR` を指定した場合: 指定パス配下
  - **非defaultエージェントは、未作成なら自動でworktreeを作成**してそこで実行します（`CODEX_SA_AUTO_WORKTREE=0` または `--no-auto-worktree` で無効化）
  - **非defaultエージェントの path 系オプション（`--cd` / `--add-dir`）は configured workspace 内だけ**を許可し、必要なら対応する worktree パスへ写像します

### `workspace init` と `--cd` の使い分け

- `workspace init .` のように **親リポジトリを workspace** にした場合は、必要に応じて `-- --cd <workspace-relative-subdir>` を付けます
- `workspace init <path-to-project-git>` のように **対象プロジェクトの Git ルート自体を workspace** にした場合は、通常 `--cd` は不要です
  - この場合の `effective_cd` は agent worktree のルートになります
- sub-agent に共有コンテキストを渡したい場合も、`--add-dir` で workspace 外は渡せません
  - 共有したい runbook / ticket / decision log は対象 workspace 側へミラーするか、prompt に要点を転記してください
- target project 側の `.gitignore` には `.codex-second-agent/` と `.codex-worktrees/` を入れてください

### 運用に効くコマンド（抜粋）

- `codex-second-agent paths`: state/log/worktree の実体パスと `effective_cd` を表示
- `codex-second-agent status --verbose`: session_id と各種パスをまとめて表示
- `codex-second-agent doctor`: 環境/パス/設定の簡易診断（トラブル切り分け）
- `codex-second-agent worktree remove <agent> [--keep-branch]`: worktree削除（必要なら `agent/<agent>` ブランチも整理）
- `codex-second-agent --post-git-status ...`（または `CODEX_SA_POST_GIT_STATUS=1`）: 実行後に未コミット変更を要約して検知

### 運用上の注意

- `codex-second-agent` は **常に `--dangerously-bypass-approvals-and-sandbox` と `--search` を有効化**します（運用方針として固定）
- `--dangerously-bypass-approvals-and-sandbox` は危険です。隔離環境ではなく、信頼済みホスト上の高権限運用として扱ってください
- 使用モデルは **常に `gpt-5.4`** です
  - `--model` / `--config model=...` / `--config model_provider=...` / `--oss` / `--local-provider` などのモデル選択系オプションは無視されます
- `--profile` は通りますが、wrapper が固定しているモデル / provider 方針は上書きできません
- 保存済み workspace が移動・削除されて無効になった場合、実行は止まり、`paths` / `doctor` に `workspace_valid: no` が表示されます

## プリインストールツール

AI CLI のバージョンは Dockerfile で固定しています（再ビルド時の挙動差分を減らすため）。

| カテゴリ | ツール |
|----------|--------|
| **ランタイム** | Node.js 22.x, Python 3 |
| **AI CLI** | @openai/codex, @google/gemini-cli, @anthropic-ai/claude-code |
| **開発ツール** | TypeScript, ESLint, Prettier |
| **ユーティリティ** | Git, GitHub CLI, ripgrep, jq, vim |
| **シェル** | Bash, Zsh |

## マウント設定

| ホスト | コンテナ | 用途 |
|--------|----------|------|
| `~/.ssh` | `/home/devuser/.ssh` | SSH鍵（Git操作） |
| `~/.gitconfig` | `/home/devuser/.gitconfig` | Git設定 |
| `~/.codex` | `/mnt/host-auth/codex` | Codex認証情報の read-only snapshot |
| `~/.config/gemini` | `/mnt/host-auth/gemini` | Gemini設定の read-only snapshot |
| `~/.claude` | `/mnt/host-auth/claude` | Claude Code認証情報の read-only snapshot |

起動時に `devcontainer-sync-host-auth` がこれらを container local の `~/.codex` / `~/.config/gemini` / `~/.claude` へ同期します。  
container 側の更新はホストへは書き戻されません。

## 環境変数

ホスト側で以下の環境変数が設定されていれば、コンテナに引き継がれます:

- `OPENAI_API_KEY`
- `GEMINI_API_KEY`
- `ANTHROPIC_API_KEY`

## エイリアス

| エイリアス | 展開 |
|------------|------|
| `codex-auto` | `codex --dangerously-bypass-approvals-and-sandbox` |
| `codex-full` | `codex --full-auto` |
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

1. ホスト側で先にログインしておく:
   ```bash
   codex  # 初回は認証フローが走る
   gemini # 初回は認証フローが走る
   claude # 初回は認証フローが走る
   ```
2. コンテナ起動時に host auth snapshot が container local へ同期される
3. コンテナを再起動

補足:
- 認証を永続化したい場合は **ホスト側で** ログインしてください。container 側の `~/.codex` / `~/.config/gemini` / `~/.claude` は local copy です。

### 権限エラー

ホストとコンテナのUID/GIDが異なる場合に発生することがあります。
Dockerfile の `USER_UID` を調整するか、ホスト側のファイル権限を確認してください。

## ライセンス

MIT
