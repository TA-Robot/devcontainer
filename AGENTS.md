# AGENTS.md（このリポジトリ自身の開発用）

この `AGENTS.md` は **devcontainer基盤リポジトリ（このリポジトリ自身）を改修する際のガイド**です。  
この基盤を使って **別プロジェクト** を開発する場合は、`AGENTS_TEMPLATE.md` を対象プロジェクトにコピーして使ってください。

## このリポジトリの責務

- **開発コンテナ基盤**の提供（`.devcontainer/`）
- セカンドエージェント・ラッパー（`scripts/second-agent` 共通エンジン + `codex-second-agent` / `claude-second-agent` シム）の提供と運用ドキュメント整備

## 対象ディレクトリ

- **実装**: `scripts/`
- **ドキュメント**: `README.md` / `AGENTS.md` / `AGENTS_TEMPLATE.md` / `docs/` / `project/docs/`
- **コンテナ定義**: `.devcontainer/`

## ルール（このリポジトリ開発向け）

- **このリポジトリにサンプルアプリ/デモプロジェクトを追加しない**
  - 「別プロジェクトでの開発運用」自体は `AGENTS_TEMPLATE.md` にまとめる
- **依存関係の追加は慎重に**
  - 追加理由・影響範囲・代替案・削除手順まで残す
- **変更は小さく分割してコミット**
  - 例: 機能追加 / バグ修正 / ドキュメント はコミットを分ける

## 最低限の確認コマンド

セカンドエージェント関連（`scripts/second-agent` / `*-second-agent` / `*-filter.py`）を触ったら:

```bash
bash -n scripts/second-agent
bash -n scripts/codex-second-agent
bash -n scripts/claude-second-agent
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile scripts/codex-second-agent-filter.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile scripts/claude-second-agent-filter.py
scripts/test-codex-second-agent.sh
scripts/test-claude-second-agent.sh
```

> `codex-second-agent` / `claude-second-agent` は `second-agent` を `SA_BACKEND` 付きで呼ぶ薄いシム。
> ロジック本体（workspace スコープ / worktree / state・log 管理）は両者で共有しているので、
> スコープ系の修正は `scripts/second-agent` 側に入れ、両方のテストで担保すること。

`.devcontainer/` を触ったら:

```bash
docker build -f .devcontainer/Dockerfile -t devcontainer-smoke:latest .
```

## 参照（別プロジェクト向けテンプレ）

- `AGENTS_TEMPLATE.md`: マルチエージェント運用（管理者/実装者の分業、バックグラウンド実行、ログ追跡）用テンプレ
- `project/AGENTS.md`: サブエージェントを **configured workspace 内だけ**で動かすための指示テンプレ（対象プロジェクトへコピーして利用）

## 模擬運用で得た知見（反映先）

運用上のハマりどころ（例: `nohup` が空になり得る、reviewer は timeout 推奨 など）は、
`AGENTS_TEMPLATE.md` と `project/AGENTS.md` 側に集約して更新していきます。

## second-agent はどこにある？

- 共通エンジン: `scripts/second-agent`（`SA_BACKEND=codex|claude` で挙動を切り替え）
- シム: `scripts/codex-second-agent`（Codex）/ `scripts/claude-second-agent`（Claude Code）
- イベントフィルタ: `scripts/codex-second-agent-filter.py` / `scripts/claude-second-agent-filter.py`
- 使い方/運用: `README.md` / `docs/architecture.md` / `AGENTS_TEMPLATE.md` / `project/AGENTS.md`
