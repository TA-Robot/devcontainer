# AGENTS.md（このリポジトリ自身の開発用）

この `AGENTS.md` は **devcontainer基盤リポジトリ（このリポジトリ自身）を改修する際のガイド**です。  
この基盤を使って **別プロジェクト** を開発する場合は、`AGENTS_TEMPLATE.md` を対象プロジェクトにコピーして使ってください。

## このリポジトリの責務

- **開発コンテナ基盤**の提供（`.devcontainer/`）
- `codex-second-agent`（`scripts/`）の提供と運用ドキュメント整備

## 対象ディレクトリ

- **実装**: `scripts/`
- **ドキュメント**: `README.md` / `AGENTS.md` / `AGENTS_TEMPLATE.md` / `docs/`
- **コンテナ定義**: `.devcontainer/`

## ルール（このリポジトリ開発向け）

- **このリポジトリにサンプルアプリ/デモプロジェクトを追加しない**
  - 「別プロジェクトでの開発運用」自体は `AGENTS_TEMPLATE.md` にまとめる
- **依存関係の追加は慎重に**
  - 追加理由・影響範囲・代替案・削除手順まで残す
- **変更は小さく分割してコミット**
  - 例: 機能追加 / バグ修正 / ドキュメント はコミットを分ける

## 最低限の確認コマンド

`scripts/codex-second-agent` を触ったら:

```bash
bash -n scripts/codex-second-agent
```

## 参照（別プロジェクト向けテンプレ）

- `AGENTS_TEMPLATE.md`: マルチエージェント運用（管理者/実装者の分業、バックグラウンド実行、ログ追跡）用テンプレ
- `project/AGENTS.md`: サブエージェントを **project配下だけ**で動かすための指示テンプレ（対象プロジェクトへコピーして利用）


