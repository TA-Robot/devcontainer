# Architecture Notes

## Positioning

このリポジトリは、次の 2 つを提供する基盤です。

- 高権限 devcontainer
- セカンドエージェント実行ラッパー（共通エンジン `second-agent` + バックエンド別シム `codex-second-agent` / `claude-second-agent`）

目的は **trusted local development を速くすること** であり、未検証コードを隔離する sandbox を提供することではありません。

## Trust Boundary

この基盤の前提は次のとおりです。

- devcontainer はホスト資格情報をマウントする
- AI 認証情報は read-only mount し、container local へコピーして使う
- devcontainer は `docker-in-docker` 前提の高権限設定で動く
- セカンドエージェントは常に権限バイパスを付ける（codex: `--dangerously-bypass-approvals-and-sandbox` / claude: `--dangerously-skip-permissions`）

したがって、「安全」は **強い隔離** ではなく **信頼済み環境の中でスコープ事故を減らす** という意味に限定されます。

## Scope Model

セカンドエージェント（`codex-second-agent` / `claude-second-agent`）の sub-agent (`--agent` が `default` 以外) は、configured workspace を基準に動かします。スコープ制御は共通エンジン `second-agent` に実装され、両バックエンドで共有されます。

- `workspace init <path-to-project-git>` を必須にする
- runtime state (session / logs / worktrees) は target workspace 側へ置く
- `workspace init` の設定は control repo 側へ置く
- sub-agent の `--cd` / `--add-dir` は workspace 内だけを許可する
- workspace 内の相対パスは agent worktree 側へ写像する
- backend ごとに state / worktree を分離する（codex: `.codex-second-agent` + `agent/<name>` ブランチ / claude: `.claude-second-agent` + `claude-agent/<name>` ブランチ）
- claude には `--cd` が無いため、wrapper が effective_cd へ `cd` して実行ディレクトリを合わせる

これは wrapper レベルの **運用境界** です。OS-level isolation ではありません。

## Recommended Target-Project Layout

target project 側では、sub-agent が読む運用情報を **workspace 内** に置きます。

```text
<target-project-git>/
  AGENTS.md
  docs/
    agents/
      runbook.md
      decisions.md
      plan.md
      tickets/
        task-ticket.template.md
        ready/
        running/
        done/
```

理由:

- `workspace init <path-to-project-git>` 後も runbook / tickets / decisions をそのまま参照できる
- runtime state が target workspace 側へまとまり、別 control repo からでも resume できる
- `--add-dir` で workspace 外を追加する必要がない
- manager と sub-agent で参照する正本がズレにくい

## Preferred Operating Modes

どちらの例も `codex-second-agent` を `claude-second-agent` に置き換えれば Claude バックエンドで同じように動きます（CLI 表面は共通）。

### 1. Recommended: target project git root as workspace

```bash
codex-second-agent workspace init <path-to-project-git>
codex-second-agent --agent implementer "..."
```

- 通常 `--cd` は不要
- docs / tickets も workspace 内に置く
- `.gitignore` には `.codex-second-agent/` `.codex-worktrees/` `.claude-second-agent/` `.claude-worktrees/` を入れる

### 2. Allowed: parent repo as workspace, subdir via `--cd`

```bash
codex-second-agent workspace init .
codex-second-agent --agent implementer "..." -- --cd packages/api
```

> claude バックエンドでも `-- --cd packages/api` は同じ意味で使えます。claude 自体に `--cd`
> フラグは無いので、wrapper が指定サブディレクトリ（worktree 内へ写像済み）へ `cd` して実行します。

- monorepo の一部だけを触らせたいときに使う
- `--cd` / `--add-dir` は workspace 内のみ許可

## Non-Goals

この基盤の非目標:

- untrusted code execution の隔離
- host secrets を渡さない実行環境
- policy enforcement を越えたセキュアコンテナ境界の提供

それが必要なら、credential mount を外した別 devcontainer / VM / remote sandbox を使うべきです。
