# マルチエージェント基盤刷新 検討ログ

このディレクトリは、devcontainer 基盤の刷新案を 3 ターンで検討するための一時ワークログです。
実装方針の正本ではなく、検討完了後に必要な内容だけ `docs/` などへ移します。

## 進め方

| ターン | 目的 | 状態 | 成果物 |
|---|---|---|---|
| 1 | 現状を分解し、評価軸と代替案を発散する | 完了 | [`01-landscape-and-hypotheses.md`](./01-landscape-and-hypotheses.md) |
| 2 | 安定性・速度・隔離・復旧の各面から有力案を反証する | 完了 | [`02-adversarial-comparison.md`](./02-adversarial-comparison.md) |
| 3 | 推奨構成、段階移行、刷新バックログへ収束する | 完了 | [`03-recommendation-and-roadmap.md`](./03-recommendation-and-roadmap.md) |

## 検討上の原則

- 現行実装を無条件に残すことも、流行のネイティブ機能へ無条件に移ることもしない。
- 会話、実行環境、Git、ジョブ状態、監査ログの「所有者」を分けて考える。
- 対話利用と無人自動化を同じ仕組みに押し込まない。
- provider 間の共通化は、実際に交換可能であるべき契約だけを対象にする。
- このリポジトリにサンプルアプリやデモプロジェクトは追加しない。

## 調査時点

- 2026-08-11
- ローカルで確認した CLI: Codex CLI `0.146.0`、Claude Code `2.1.220`
- 外部機能は変化が速いため、各ターンで必要な範囲を再確認する。

## 3ターン終了時の推奨

- native subagentを対話・計画・read-only fan-outの標準にする。
- 通常のwriteは同一devcontainer内のjob単位worktreeで高速に分離する。
- Dockerやcredentialまで強く分離するtaskはoptional isolated laneへ送る。
- 新しい共通層は会話を扱わず、job / attempt、workspace lease、resource namespace、structured resultだけを管理する。
- stable toolchainをrepoで固定し、host同期やlatestはedge opt-inにする。
- 現行`second-agent`は並行移行と観測期間を経て段階廃止する。

## 実装への昇格

2026-08-12にPhase 0–3e（job / workspace fabric、local process durability、capacity / resource lease、single-writer collection、bounded log / retention、dry-run GC inventory）とPhase 4aのisolated-runtime benchmarkを実装しました。このディレクトリは引き続き
検討ログであり、正本は次へ移しています。

- architecture decision: `docs/adr/0001-native-first-multi-agent-execution.md`
- representative scenarios: `docs/agents/representative-scenarios.md`
- legacy freeze / recovery: `docs/agents/legacy-second-agent.md`
- first baseline: `docs/agents/legacy-baseline-2026-08-12.md`
- implementation status: `docs/agents/implementation-status.md`
- job fabric CLI / safety boundary: `docs/agentctl.md`
- native project contract: `project/.agent/` / `project/.codex/` / `project/.claude/`
- failure recovery: `project/docs/agents/runbook.md`
- legacy wrapper compatibility: `docs/agents/legacy-second-agent-runbook.md`

以後の仕様差分は正本側へ入れ、この検討ログへ逆流させません。
