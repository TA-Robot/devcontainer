# AGENTS_TEMPLATE.md（このdevcontainer基盤を使って「別プロジェクト」を開発するためのテンプレ）

このファイルは、**このリポジトリ（devcontainer基盤）を使って開発する“別プロジェクト”側**に置くためのテンプレです。  
対象プロジェクトの `AGENTS.md` としてコピーして使ってください（必要に応じて要件に合わせて編集）。

---

## マルチエージェント運用ポリシー（重要）

- **メインエージェント（管理者）は実装しない**
  - 変更案の整理、タスクの切り出し、サブエージェントへの依頼、ログ/差分レビュー、取り込み判断に徹する
  - `git add/commit` の実行主体も原則サブエージェント（または明示的に「管理者が取り込む」工程のみ）
- **サブエージェントは役割で分ける**
  - `implementer`: 実装・テスト・コミット
  - `reviewer`: レビュー・指摘・リスク洗い出し
  - `triage`: 調査・原因切り分け・影響範囲特定（必要なら）
- **待ち時間削減のため “基本バックグラウンド実行”**
  - サブエージェント起動はバックグラウンドで走らせ、ログ（`events.jsonl` / `transcript.jsonl`）を見ながら次の作業を進める

---

## 「project配下だけを見せる」運用（推奨）

サブエージェントは、リポジトリ全体を見せるのではなく **project配下のみ**を対象にすると安全です。

- このテンプレと合わせて、対象リポジトリに **`project/AGENTS.md`（サブ向け指示）**を置く運用を推奨します
- `codex-second-agent` は通常「起動場所の git root」をworkspaceとして扱いますが、**サブエージェントは project 側のGitをworkspaceとして固定**するのが安全です
  - まず `codex-second-agent workspace init <path-to-project-git>` を実行し、対象プロジェクト（git repo root）を保存します
  - 以降、サブエージェント実行はそのworkspaceを基準に worktree/log/state を作るようになります
  - 重要: これは技術的な強制隔離ではありません（ルールで縛る運用）。ただし、親リポジトリのworktreeを誤って作る事故は防げます

例（implementer を project 固定で起動）:

```bash
# まず最初に、対象プロジェクト（git repo root）を保存しておく
codex-second-agent workspace init project/<name>

mkdir -p .codex-second-agent/nohup
cat <<'PROMPT' | nohup codex-second-agent --agent implementer --post-git-status - > .codex-second-agent/nohup/implementer.out 2>&1 &
project/<name>/ 配下のみを対象に実装して。
PROMPT
```

---

## codex-second-agent の使い方（要点）

### codex-second-agent とは？どこにある？

- **何か**: `codex exec` を「セッションID自動保持」「agent別worktree」「ログ保存」付きで呼び出すラッパー
- **この基盤リポジトリでの実装**: `scripts/codex-second-agent`
- **コンテナ内のPATH**: 環境によっては `codex-second-agent` がPATHに入っていないことがあります（その場合は `scripts/codex-second-agent` を直接実行）

### 基本

```bash
codex-second-agent "READMEを要約して"
```

2回目以降は、同じワークスペース（Gitルート）であれば自動的に前回セッションを `resume` します。

### エージェントを分ける（マルチエージェント）

```bash
codex-second-agent --agent reviewer "この差分をレビューして"
codex-second-agent --agent implementer "このissueを実装して"
```

### 状態/場所確認（迷子防止）

```bash
codex-second-agent status
codex-second-agent status --verbose
codex-second-agent paths
codex-second-agent doctor
```

### worktree の配置

- デフォルトは `<repo>/.codex-second-agent/<workspace_hash>/worktrees/<agent>/`
- ホーム配下に増えるのが気になる場合は、workspace配下に置けます:

```bash
CODEX_SA_WORKTREES_MODE=workspace codex-second-agent paths
# または
codex-second-agent --worktrees-in-workspace paths
```

### worktree の後片付け

```bash
codex-second-agent worktree remove <agent>        # ブランチも整理（既定）
codex-second-agent worktree remove <agent> --keep-branch
```

### 未コミット滞留の検知（推奨）

```bash
codex-second-agent --agent implementer --post-git-status "..."
# または
CODEX_SA_POST_GIT_STATUS=1 codex-second-agent --agent implementer "..."
```

---

## バックグラウンド実行（推奨）

### 起動テンプレ（nohup）

```bash
mkdir -p .codex-second-agent/nohup
cat <<'PROMPT' | nohup codex-second-agent --agent implementer --post-git-status - > .codex-second-agent/nohup/implementer.out 2>&1 &
要件:
- ...
制約:
- ...
成果物:
- ...
完了条件:
- ...
PROMPT
echo "pid=$!"
```

### ログの見方（重要）

- 実体パスの確認:

```bash
codex-second-agent --agent implementer paths
```

- 会話ログ（読みやすい）: `transcript.jsonl`

```bash
tail -n 5 .codex-second-agent/<workspace_hash>/agents/implementer/logs/transcript.jsonl
```

- 生イベント（デバッグ向け）: `events.jsonl`

```bash
tail -n 50 .codex-second-agent/<workspace_hash>/agents/implementer/logs/events.jsonl
```

---

## 典型フロー（管理者 / サブ）

### 1) 管理者: 要件→依頼（バックグラウンド）

- 依頼文に必ず含める:
  - 目的/スコープ
  - 制約（触ってよいディレクトリ、依存追加可否、危険操作禁止など）
  - 成果物（ファイル/コマンド/テスト）
  - 完了条件（例: `bash -n ...` / `python -m pytest` / `npm test` など）

### 2) implementer: 実装→テスト→コミット

- `--post-git-status` を付けると未コミット滞留が早期に見つかります

### 3) 管理者: reviewer にレビュー依頼（バックグラウンド）

- commit hash / ブランチ名 / 変更範囲 を明示
- 指摘は Must/Should/Nice に分けてもらう

### 4) implementer: 指摘反映→再テスト→追加コミット

### 5) 管理者: 取り込み判断・統合・後片付け

- 不要になった worktree は削除（上記 `worktree remove`）


