# Codex Agent / サブエージェント連携

メインエージェントから **「セカンドエージェント」的に呼び出す**ための入口として `codex-second-agent` を提供します。
目的は次の2点です:

## 使い方
### 基本
```bash
codex-second-agent "このリポジトリのREADMEを要約して"
```
2回目以降は、同じワークスペース（Gitルート）であれば自動的に前回セッションを `resume` します。
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
codex-second-agent reset
```


