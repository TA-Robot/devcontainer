# Task Ticket Template（サブエージェント依頼用）

> このファイルはテンプレです。`.codex-second-agent/tickets/` にコピーして編集して使ってください。  
> 管理者が内容を改善する場合は、このテンプレ側に反映します（サブエージェントは原則更新しない）。

---

## Meta

- **ticket_id**: `task-0001`
- **role/agent**: `implementer-task0001`（例: `triage-task0001` / `reviewer-task0001` / `newbie-task0001`）
- **created_by**: `manager`
- **created_at**: `YYYY-MM-DD`
- **workspace_scope**: `project/<name>/`（原則ここだけ）
- **related**
  - issue: `<<link-or-id>>`
  - pr: `<<link-or-branch>>`
  - commits: `<<hashes>>`

---

## One-liner（目的）

`<<このタスクで達成したいことを1行で>>`

---

## Background / Context（背景）

- `<<なぜ必要か / 何が困っているか>>`
- `<<既知の制約 / 既存仕様 / 参考リンク>>`

---

## Scope（スコープ）

- **In scope**
  - `<<やること>>`
- **Out of scope**
  - `<<やらないこと>>`

---

## Requirements（要件）

- `<<必須要件>>`
- `<<必須要件>>`

---

## Non-goals（非目標）

- `<<今回やらない（やれない）こと>>`

---

## Constraints / Guardrails（制約・ガードレール）

- **Allowed paths**: `project/<name>/` のみ（迷ったら manager に質問して止まる）
- **Dependency changes**: `<<可/不可。可なら承認手順>>`
- **Dangerous operations**: `<<例: 本番DB操作禁止 / destructive禁止>>`
- **Timebox**: `<<例: 60minで一次回答>>`

---

## Acceptance Criteria（完了条件）

- [ ] `<<振る舞いの観点で>>`
- [ ] `<<テスト/コマンドで>>`（例: `<<test-cmd>>` が通る）
- [ ] `<<ドキュメント更新が必要なら>>`

---

## Deliverables（成果物）

- **Code**: `<<変更ファイル>>`
- **Commands**: `<<実行コマンド>>`
- **Notes**: `<<設計判断/注意点>>`

---

## How to Verify（確認方法）

```bash
cd project
<<commands>>
```

---

## Risks / Open Questions（リスク・未確定事項）

- **Risks**
  - `<<壊れやすい点>>`
- **Questions**
  - `<<managerに確認したい点>>`

---

## Reporting（進捗報告の粒度）

- `<<例: 15分ごとに transcript に状況を書き残す>>`
