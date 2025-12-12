# project/AGENTS.md（サブエージェント用：project配下のみを対象にする指示テンプレ）

この `project/AGENTS.md` は、**サブエージェント（implementer/reviewer/triage）に渡す指示**です。  
目的は「サブエージェントが **project配下だけ**を見て作業する」運用を徹底することです。

> 注意: 技術的に“強制隔離”するものではなく、運用ルールとしてスコープを縛ります。  
> `codex-second-agent` 実行時に `-- --cd project` を付けて **実行ディレクトリも project に固定**してください。

---

## スコープ（最重要）

- **見てよい/触ってよい**: `project/` 配下のみ
- **見ない/触らない**:
  - リポジトリルート配下の `scripts/` / `.devcontainer/` / `docs/` / `README.md` / `AGENTS*.md` など
  - project外のファイルを参照してよいか迷ったら、必ず管理者へ質問して止まる

## 役割別の期待

- **implementer**
  - `project/` 配下のみで実装し、`project/` 配下のテスト/ビルドが通る状態まで持っていく
  - `git status -sb` を確認し、必要ならコミットしてブランチ先端を進める
- **reviewer**
  - `project/` 配下だけの差分レビューを行う（Must/Should/Nice）
- **triage**
  - `project/` 配下のログ/コードから原因切り分け。必要な追加情報があれば管理者に要求

## 実行コマンド（管理者が使う想定）

### implementer を project 固定で起動

```bash
cat <<'PROMPT' | nohup codex-second-agent --agent implementer --post-git-status -- --cd project - > /tmp/implementer.out 2>&1 &
あなたは implementer です。
- 作業対象は project/ 配下のみ
- 変更は project/ 配下のみに限定

要件:
- ...
制約:
- 依存追加は事前承認
完了条件:
- project/ 配下のテストが通る
PROMPT
echo "pid=$!"
```

### reviewer を project 固定で起動

```bash
cat <<'PROMPT' | nohup codex-second-agent --agent reviewer -- --cd project - > /tmp/reviewer.out 2>&1 &
あなたは reviewer です。
- レビュー対象は project/ 配下の差分のみ
- 指摘は Must/Should/Nice に分ける
PROMPT
echo "pid=$!"
```

## ログ/スコープ確認（迷子防止）

```bash
codex-second-agent --agent implementer paths
codex-second-agent --agent implementer status --verbose
codex-second-agent --agent implementer doctor
```

`paths` の `effective_cd` が `.../project` になっていることを必ず確認してください。


