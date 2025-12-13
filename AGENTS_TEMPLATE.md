# AGENTS_TEMPLATE.md（別プロジェクト開発用テンプレ）

このファイルは、**この devcontainer 基盤を使って開発する“別プロジェクト”側**に置くためのテンプレです。  
対象プロジェクトに `AGENTS.md` としてコピーし、`<<...>>` を埋めて使ってください。

---

## このプロジェクト情報（埋める）

- **project 名**: `<<project-name>>`
- **project の実体ディレクトリ**: `project/<<name>>/`（例: `project/app/`）
- **実行/テストコマンド**:
  - `<<test-cmd>>`（例: `python -m unittest -v` / `npm test`）
  - `<<lint-cmd>>`（任意）

---

## 役割（最小固定 + タスク派生）

このテンプレでは、役割名を「固定の数種類」に縛らず、**タスク単位で役割（= agent 名）を派生させて並列稼働**させる運用を推奨します。

- **固定（最小）**
  - **管理者（main/manager）**: 実装しない。管理・判断・統合・ドキュメント整備に徹する
- **タスク派生（並列実行の主役）**
  - **`implementer-taskXXXX`**: 実装・テスト・コミット（task ごとに分割し、同時に複数走らせる）
  - **`reviewer-taskXXXX`**: レビュー（Must/Should/Nice）・リスク洗い出し（task ごとに分割して並列レビュー可）
  - **`triage-taskXXXX`**: 調査・原因切り分け（ログ/再現/最小ケース作成）。実装に入る場合は `implementer-*` へ引き継ぐ
  - **`newbie-taskXXXX`**: 新人。**質問だけ**して前提/仕様/運用知識を掘り起こす（原則コードは触らない）

### 命名ルール（例）

- **粒度**: “1 タスク=1 agent” を基本にする（衝突や手戻りを減らし、worktree を自然に分離できる）
- **推奨フォーマット**: `<role>-<topic>-<id>`
  - 例: `implementer-auth-0123`, `triage-flakytest-045`, `reviewer-api-0123`, `newbie-onboarding-001`
- **依頼文の先頭に必ず書く**:
  - 対象タスク ID / 対象ディレクトリ / 完了条件 / 成果物（差分 or コミット）/ 相談事項

---

## 開発方針: t-wada 式 TDD（推奨）

このテンプレの基本スタイルは **t-wada 式 TDD** を前提にします。

- **基本サイクル**: Red → Green → Refactor
  - **Red**: まず小さな失敗テストを書く（仕様を一つだけ表現）
  - **Green**: 最小の実装で通す
  - **Refactor**: ふるまいを変えずに整理する（重複排除・命名改善・責務分離）
- **粒度**: “小さく・早く” を優先（コミットも小さく）
- **テストの責務**:
  - 仕様の表明（例: 入力 → 出力、エラー条件）
  - 変更検知（回帰防止）
- **モックの方針**:
  - 最初からモックありきにしない（まず純粋関数化/設計でテスト容易に）
  - I/O 境界（HTTP/DB/FS など）だけを最小限に切り出して必要ならモック
- **既存コード改修の入口**:
  - 仕様が曖昧なら「characterization test（現状のふるまい固定）」から入る

管理者は依頼文に **テストコマンド（<<test-cmd>>）**と **TDD 前提**を明記してください。

---

## project/docs（管理者が整備する前提）

このテンプレ運用では、管理者が `project/docs/` を継続的に整備します。

- **管理者が書く**（推奨）:
  - `project/docs/runbook.md`: 実行手順・リリース手順・よくある事故と対処
  - `project/docs/decisions.md`: 重要な設計判断（短い箇条書きで OK）
- **サブエージェントは参照 OK**だが、**更新は原則しない**（更新が必要なら管理者に提案）

### 改善ループ（新人エージェントで質問 → ドキュメント追記）

運用が安定してくるほど「暗黙知」が増えるので、定期的に **`newbie-*`** を立てて **質問させ、回答を管理者が `project/docs/` に追記**して整備します。

- **頻度（例）**: 週 1 / スプリント末 / 大きな変更の直後（どれかで OK）
- **進め方**
  - `newbie-*` に「プロジェクトを理解するための質問を _10〜20 個_ 出す」依頼をする（コード改変は禁止）
  - 管理者が回答し、**恒久情報は `project/docs/runbook.md` / `project/docs/decisions.md` に追記**する
  - 依頼テンプレや注意事項（スコープ、危険操作、標準コマンド等）は必要に応じて `AGENTS.md` に反映する

---

## 「project 配下だけを見せる」運用（推奨）

サブエージェントは、リポジトリ全体を見せるのではなく **project 配下のみ**を対象にすると安全です。

- このテンプレと合わせて、対象リポジトリに **`project/AGENTS.md`（サブ向け指示）**を置く運用を推奨します
- `codex-second-agent` は通常「起動場所の git root」を workspace として扱いますが、**サブエージェントは project 側の Git を workspace として固定**するのが安全です
  - まず `codex-second-agent workspace init <path-to-project-git>` を実行し、対象プロジェクト（git repo root）を保存します
  - 以降、サブエージェント実行はその workspace を基準に worktree/log/state を作るようになります
  - 重要: これは技術的な強制隔離ではありません（ルールで縛る運用）。ただし、親リポジトリの worktree を誤って作る事故は防げます

例（implementer を project 固定で起動）:

```bash
# まず最初に、対象プロジェクト（git repo root）を保存しておく
codex-second-agent workspace init project/<name>

mkdir -p .codex-second-agent/nohup .codex-second-agent/tickets

# 1) 要件チケット（ファイル）を用意する（テンプレからコピーして“ちゃんと編集”する）
ticket=.codex-second-agent/tickets/task-0001.md
cp project/docs/tickets/task-ticket.template.md "$ticket"
# エディタで開いて埋める（例）
# ${EDITOR:-vi} "$ticket"

# 2) 起動時に「チケットをstdinで渡す」（必要なら envsubst 等で展開して渡す）
agent=implementer-task0001
out=.codex-second-agent/nohup/${agent}.out
cat "$ticket" | nohup codex-second-agent --agent "$agent" --post-git-status - -- --cd project > "$out" 2>&1 &
echo "pid=$!"

# 3) 回収後にチケットを削除（終了確認・ログ回収が済んでから）
# rm -f "$ticket"
```

---

## codex-second-agent の使い方（要点）

### codex-second-agent とは？どこにある？

- **何か**: `codex exec` を「セッション ID 自動保持」「agent 別 worktree」「ログ保存」付きで呼び出すラッパー
- **この基盤リポジトリでの実装**: `scripts/codex-second-agent`
- **コンテナ内の PATH**: 環境によっては `codex-second-agent` が PATH に入っていないことがあります（その場合は `scripts/codex-second-agent` を直接実行）

### 基本

```bash
codex-second-agent "READMEを要約して"
```

2 回目以降は、同じワークスペース（Git ルート）であれば自動的に前回セッションを `resume` します。

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
- ホーム配下に増えるのが気になる場合は、workspace 配下に置けます:

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

### 起動テンプレ（チケットファイル → stdin で起動）

```bash
mkdir -p .codex-second-agent/nohup .codex-second-agent/tickets

# 1) 要件チケット（ファイル）を用意する（テンプレからコピーして“ちゃんと編集”する）
ticket=.codex-second-agent/tickets/task-0001.md
cp project/docs/tickets/task-ticket.template.md "$ticket"
# エディタで開いて埋める（例）
# ${EDITOR:-vi} "$ticket"

# 2) チケットを stdin で渡して起動する（タスクごとに agent 名を分ける）
agent=implementer-task0001
out=.codex-second-agent/nohup/${agent}.out
cat "$ticket" | nohup codex-second-agent --agent "$agent" --post-git-status - > "$out" 2>&1 &
echo "pid=$!"

# 3) 回収後にチケットを削除（終了確認・ログ回収が済んでから）
# rm -f "$ticket"
```

### ログの見方（重要）

- **最優先（推奨）**: `transcript.jsonl`（1 リクエスト=1 行）
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
mkdir -p .codex-second-agent/nohup .codex-second-agent/tickets

# 1) レビューチケット（ファイル）を用意する（テンプレからコピーして“ちゃんと編集”する）
ticket=.codex-second-agent/tickets/review-0001.md
cp project/docs/tickets/task-ticket.template.md "$ticket"
# ${EDITOR:-vi} "$ticket"
# （埋め方の例）
# - role/agent: reviewer-task0001
# - related.commits: <hash>
# - Acceptance Criteria: Must/Should/Nice で出す、など

# 2) stdin で渡して起動する（必要なら task ごとに reviewer-taskXXXX を作る）
agent=reviewer-task0001
out=.codex-second-agent/nohup/${agent}.out
cat "$ticket" | nohup timeout 120s codex-second-agent --agent "$agent" - > "$out" 2>&1 &
echo "pid=$!"

# 3) 回収後にチケットを削除（終了確認・ログ回収が済んでから）
# rm -f "$ticket"
```

---

## 管理者のチェックリスト（短縮版）

- **依頼前**:
  - `project/docs/runbook.md` に「実行/テスト/確認方法」が書かれている
  - `workspace init` が対象プロジェクトを指している
  - **TDD 前提**（Red/Green/Refactor、最小ステップ、テストを先に）を依頼文に明記
- **依頼後**:
  - `transcript.jsonl` で進捗確認（`nohup` が空でも慌てない）
  - 必要なら `--post-git-status` で未コミット滞留を早期検知
- **取り込み前**:
  - `<<test-cmd>>` を実行して OK
  - reviewer の Must が潰れている
- **後片付け**:
  - 回収が済んだチケット（`.codex-second-agent/tickets/*.md`）を削除する

---

## 典型フロー（管理者 / サブ）

### 1) 管理者: 要件 → 依頼（バックグラウンド）

- 依頼文に必ず含める:
  - 目的/スコープ
  - 制約（触ってよいディレクトリ、依存追加可否、危険操作禁止など）
  - 成果物（ファイル/コマンド/テスト）
  - 完了条件（例: `bash -n ...` / `python -m pytest` / `npm test` など）
  - （推奨）要件はチケットファイル（`.codex-second-agent/tickets/...`）として残し、起動時に stdin で渡す

### 2) implementer: 実装 → テスト → コミット

- `--post-git-status` を付けると未コミット滞留が早期に見つかります

### 3) 管理者: reviewer にレビュー依頼（バックグラウンド）

- commit hash / ブランチ名 / 変更範囲 を明示
- 指摘は Must/Should/Nice に分けてもらう

### 4) implementer: 指摘反映 → 再テスト → 追加コミット

### 5) 管理者: 取り込み判断・統合・後片付け

- 不要になった worktree は削除（上記 `worktree remove`）
- 回収が済んだチケットは削除（`.codex-second-agent/tickets/`）
