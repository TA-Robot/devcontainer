# Architecture Notes

## Positioning

このリポジトリは、次の 2 つを提供する基盤です。

- 高権限 devcontainer
- `codex-second-agent` による sub-agent 実行ラッパー

目的は **trusted local development を速くすること** であり、未検証コードを隔離する sandbox を提供することではありません。

## Trust Boundary

この基盤の前提は次のとおりです。

- devcontainer はホスト資格情報をマウントする
- devcontainer は `docker-in-docker` 前提の高権限設定で動く
- `codex-second-agent` は常に `--dangerously-bypass-approvals-and-sandbox` を付ける

したがって、「安全」は **強い隔離** ではなく **信頼済み環境の中でスコープ事故を減らす** という意味に限定されます。

## Scope Model

`codex-second-agent` の sub-agent (`--agent` が `default` 以外) は、configured workspace を基準に動かします。

- `workspace init <path-to-project-git>` を必須にする
- sub-agent の `--cd` / `--add-dir` は workspace 内だけを許可する
- workspace 内の相対パスは agent worktree 側へ写像する

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
- `--add-dir` で workspace 外を追加する必要がない
- manager と sub-agent で参照する正本がズレにくい

## Preferred Operating Modes

### 1. Recommended: target project git root as workspace

```bash
codex-second-agent workspace init <path-to-project-git>
codex-second-agent --agent implementer "..."
```

- 通常 `--cd` は不要
- docs / tickets も workspace 内に置く

### 2. Allowed: parent repo as workspace, subdir via `--cd`

```bash
codex-second-agent workspace init .
codex-second-agent --agent implementer "..." -- --cd packages/api
```

- monorepo の一部だけを触らせたいときに使う
- `--cd` / `--add-dir` は workspace 内のみ許可

## Non-Goals

この基盤の非目標:

- untrusted code execution の隔離
- host secrets を渡さない実行環境
- policy enforcement を越えたセキュアコンテナ境界の提供

それが必要なら、credential mount を外した別 devcontainer / VM / remote sandbox を使うべきです。
