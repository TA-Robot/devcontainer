# Codex Agent / サブエージェント連携

メインエージェントから **「セカンドエージェント」的に呼び出す**ための入口として `codex-second-agent` を提供します。
目的は次の2点です:

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


