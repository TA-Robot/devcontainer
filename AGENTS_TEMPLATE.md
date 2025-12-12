# AGENTS_TEMPLATE.md（別プロジェクト開発用テンプレ）

このファイルは、**このdevcontainer基盤を使って開発する“別プロジェクト”側**に置くためのテンプレです。  
対象プロジェクトに `AGENTS.md` としてコピーし、`<<...>>` を埋めて使ってください。

---

## このプロジェクト情報（埋める）

- **project名**: `<<project-name>>`
- **projectの実体ディレクトリ**: `project/<<name>>/`（例: `project/app/`）
- **実行/テストコマンド**:
  - `<<test-cmd>>`（例: `python -m unittest -v` / `npm test`）
  - `<<lint-cmd>>`（任意）

---

## 役割（固定）

- **管理者（main/manager）**: 実装しない。管理・判断・統合・ドキュメント整備に徹する
- **implementer**: 実装・テスト・コミット
- **reviewer**: レビュー（Must/Should/Nice）・リスク洗い出し
- **triage**: 調査・原因切り分け（必要時）

---

## project/docs（管理者が整備する前提）

このテンプレ運用では、管理者が `project/docs/` を継続的に整備します。

- **管理者が書く**（推奨）:
  - `project/docs/runbook.md`: 実行手順・リリース手順・よくある事故と対処
  - `project/docs/decisions.md`: 重要な設計判断（短い箇条書きでOK）
- **サブエージェントは参照OK**だが、**更新は原則しない**（更新が必要なら管理者に提案）

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
cat <<'PROMPT' | nohup codex-second-agent --agent implementer --post-git-status - -- --cd project > .codex-second-agent/nohup/implementer.out 2>&1 &
project/<name>/ 配下のみを対象に実装して（project/docs を参照し、逸脱するなら管理者へ質問）。
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

- **最優先（推奨）**: `transcript.jsonl`（1リクエスト=1行）
- **次点**: `events.jsonl`（デバッグ向け、生イベント）
- `nohup` の標準出力ファイルは **空のまま**になることがあります（モデル出力はログに集約される前提で運用する）

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

### reviewer は timeout を付けるのが現実的

レビューは長引くことがあるので、バックグラウンド実行では `timeout` を付けて「必ず終了してログが取れる」形にするのがおすすめです。

```bash
mkdir -p .codex-second-agent/nohup
cat <<'PROMPT' | nohup timeout 120s codex-second-agent --agent reviewer - > .codex-second-agent/nohup/reviewer.out 2>&1 &
対象コミット: <hash>
出力: Must/Should/Nice
PROMPT
echo "pid=$!"
```

---

## 管理者のチェックリスト（短縮版）

- **依頼前**:
  - `project/docs/runbook.md` に「実行/テスト/確認方法」が書かれている
  - `workspace init` が対象プロジェクトを指している
- **依頼後**:
  - `transcript.jsonl` で進捗確認（`nohup` が空でも慌てない）
  - 必要なら `--post-git-status` で未コミット滞留を早期検知
- **取り込み前**:
  - `<<test-cmd>>` を実行してOK
  - reviewer の Must が潰れている

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


