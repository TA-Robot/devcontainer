# Codex Agent / サブエージェント連携

メインエージェントから **「セカンドエージェント」的に呼び出す**ための入口として `codex-second-agent` を提供します。
目的は次の2点です:

- **マルチエージェント運用**: エージェントごとにセッション/ログ/作業ディレクトリを分離して並行作業できる
- **管理者（メイン）と実装者（サブ）の分業**: メインは管理・判断に徹し、実装はサブエージェントに委譲できる

## 運用ポリシー（重要）

- **メインエージェント（管理者）は実装しない**
  - 変更案の整理、タスクの切り出し、サブエージェントへの依頼、ログ/差分レビュー、取り込み判断に徹する
  - `git add/commit` の実行主体も原則サブエージェント（または明示的に「管理者が取り込む」工程のみ）
- **サブエージェントは役割で分ける**
  - `implementer`: 実装・テスト・コミット
  - `reviewer`: レビュー・指摘・リスク洗い出し
  - `triage`: 調査・原因切り分け・影響範囲特定（必要なら）
- **待ち時間削減のため “基本バックグラウンド実行”**
  - サブエージェント起動はバックグラウンドで走らせ、ログ（`events.jsonl` / `transcript.jsonl`）を見ながら次の依頼やレビュー準備を進める

## 使い方
### 基本
```bash
codex-second-agent "このリポジトリのREADMEを要約して"
```
2回目以降は、同じワークスペース（Gitルート）であれば自動的に前回セッションを `resume` します。

## 運用イメージ（どの段階で worktree？）

- **worktreeを使わない段階（軽い相談/調査）**
  - 例: README要約、仕様質問、エラー原因の切り分け、方針検討
  - コマンド例:

```bash
codex-second-agent --agent default "このエラーの原因を推測して。次に見るべきファイルも挙げて。"
```

- **worktreeを使う段階（実装/修正を伴う“長い作業”）**
  - 例: issue実装、リファクタ、バグ修正、テスト追加
  - **エージェント名を切ると、そのエージェント専用worktreeで作業**する運用（デフォルト）
  - コマンド例:

```bash
codex-second-agent --agent implementer "このissueを実装して。小さなコミットに分けて。"
```

## なぜコマンドで呼ぶの？

- Cursorのメインエージェントから「外部のサブエージェント（Codex CLI）」を安定して呼ぶための **入口**です
- ただしメイン側は基本 **この1コマンドを呼ぶだけ**で、sessionやworktreeはツール側で面倒を見ます

### エージェントを分ける（マルチエージェント）

```bash
codex-second-agent --agent reviewer "この差分をレビューして"
codex-second-agent --agent implementer "このissueを実装して"
```

### エージェント一覧

```bash
codex-second-agent agents
```

### エージェント用 worktree

```bash
codex-second-agent worktree create reviewer   # 事前に作る場合（任意）
codex-second-agent worktree list
```

### stdin からプロンプトを渡す（長文向け）
```bash
cat <<'PROMPT' | codex-second-agent -
次の方針でレビューして:
- 重要な仕様漏れ
- セキュリティ/権限/危険コマンド
- 依存関係の追加有無
PROMPT
```
### 状態確認 / リセット
```bash
codex-second-agent status
codex-second-agent status --verbose
codex-second-agent paths
codex-second-agent doctor
codex-second-agent reset
```

## worktree / state / logs の場所（迷子防止）

`codex-second-agent` は、ワークスペース（Gitルート）ごとにハッシュ化したディレクトリ配下に状態を保存します。
場所が気になったら `codex-second-agent paths` で **state/log/worktree の実体パス**を確認できます。

特に worktree の既定位置は次です（必要なら環境変数で変更可能）:

- `CODEX_SA_STATE_DIR`: 既定 `~/.codex/cursor-second-agent`
- `CODEX_SA_WORKTREES_DIR`: 既定 `<state>/<workspace_hash>/worktrees`
- `CODEX_SA_LOG_DIR`: 既定 `<state>/<workspace_hash>/agents/<agent>/logs`

### worktreeをworkspace配下に置きたい場合

ホーム配下に worktree が増えるのが気になる場合、次のどちらかで **workspace配下**（例: `<repo>/.codex-worktrees/`）にできます。

- `CODEX_SA_WORKTREES_MODE=workspace` を設定する
- `codex-second-agent --worktrees-in-workspace ...` を使う

## バックグラウンド実行（推奨）

### ねらい

- サブエージェントの応答待ちで手が止まるのを避ける
- メイン（管理者）が「次の依頼文」「レビュー観点」「差分取り込み手順」を並行で準備できる

### 起動テンプレ（nohup）

```bash
# implementer に実装を投げる（バックグラウンド）
cat <<'PROMPT' | nohup codex-second-agent --agent implementer --post-git-status - > /tmp/implementer.out 2>&1 &
要件:
- ...
制約:
- ...
成果物:
- ...
PROMPT
echo "pid=$!"
```

### ログの見方（重要）

- **実体パスの確認**:

```bash
codex-second-agent --agent implementer paths
```

- **会話ログ（読みやすい）**: `transcript.jsonl` を tail

```bash
# 例: 最後の応答を見る（1行=1リクエスト）
tail -n 5 ~/.codex/cursor-second-agent/<workspace_hash>/agents/implementer/logs/transcript.jsonl
```

- **生イベント（デバッグ向け）**: `events.jsonl`

```bash
tail -n 50 ~/.codex/cursor-second-agent/<workspace_hash>/agents/implementer/logs/events.jsonl
```

## 典型フロー（管理者がやること / サブがやること）

### 1) 管理者: 要件を固めて implementer に依頼（バックグラウンド）

- **依頼文に必ず含める**:
  - 目的/スコープ（何をどこまでやるか）
  - 制約（触ってよいディレクトリ、追加依存可否、危険操作禁止など）
  - 成果物（ファイル/コマンド/テスト）
  - 完了条件（例: `bash -n ...` / `python -m pytest` / `npm test` など）

### 2) implementer: 実装→テスト→コミット

- `--post-git-status`（または `CODEX_SA_POST_GIT_STATUS=1`）を使うと、**未コミット滞留**が早期に見つかります

### 3) 管理者: reviewer にレビュー依頼（バックグラウンド）

- commit hash / ブランチ名 / 変更範囲 を明示して依頼
- 指摘は Must/Should/Nice に分けてもらう

### 4) implementer: 指摘反映→再テスト→追加コミット

### 5) 管理者: 取り込み判断・統合・後片付け

- パス確認: `codex-second-agent paths`
- 不要になった worktree は削除:

```bash
codex-second-agent worktree remove <agent>        # ブランチも整理（既定）
codex-second-agent worktree remove <agent> --keep-branch
```


