# codex-second-agent 改善メモ（模擬開発から得たフィードバック）

このドキュメントは、`codex-second-agent` を使って「別プロジェクトを載せて模擬開発」を回した結果から、運用上の改善点を整理したものです。

## 目的

- **迷子になりがちな情報（worktreeの場所、ログ、state）を一発で確認できる**ようにする
- **sub-agent運用で起きがちな事故（未コミットの滞留、キャッシュ混入）を減らす**

## 模擬開発で観測したこと（課題）

- **成果物が未コミットで worktree に滞留しやすい**
  - sub-agentが「作った」と言っていても、`agent/<name>` ブランチが進まず、`git status` すると untracked のまま、というケースが起こり得る
- **worktreeの場所が分かりづらい**
  - 既定では `~/.codex/.../worktrees/<agent>/` に作られるため、ホーム配下で見失いやすい
- **Python系はキャッシュ混入が起きやすい**
  - `.pyc` / `__pycache__` などがコミットに混入し、履歴が汚れやすい
- **テスト実行は `pytest` 直叩きが失敗し得る**
  - PATHに `pytest` が無い環境があり、`python -m pytest` の方が堅い

## 取り込んだ改善（今回）

- **`paths` コマンド追加**
  - state/log/worktree の実体パスと、実行時に使われる `effective_cd` を表示
- **`status --verbose`**
  - session_idに加えて、関連パスもまとめて表示
- **`doctor` コマンド**
  - `codex` の存在/バージョン、git判定、paths要約を一括で表示（トラブル切り分け用）
- **worktreeをworkspace配下に置けるモード**
  - `CODEX_SA_WORKTREES_MODE=workspace` または `--worktrees-in-workspace` で、`<repo>/.codex-worktrees/` に作成できる
- **`worktree remove <agent>`**
  - worktreeを安全に削除（`--keep-branch` を付けない限り `agent/<agent>` ブランチも削除）
- **実行後に `git status` の要約を出す（任意）**
  - `--post-git-status` または `CODEX_SA_POST_GIT_STATUS=1` で有効化

## 運用の推奨手順（最低限）

- **場所確認**
  - `codex-second-agent paths`
  - `codex-second-agent status --verbose`
  - 困ったら `codex-second-agent doctor`
- **レビュー前の確認（sub-agent側でやるべき）**
  - `git status -sb` で untracked/modified が残っていないか
  - 必要なら `git add -A && git commit` してブランチ先端を進める
  - 未コミット滞留が心配なら `--post-git-status` を付けて実行する
- **テストの実行方法**
  - Python: `python -m pytest`（PATH依存を避ける）

## 次の改善候補（未実装）

- **`doctor --verbose`**: state/log/worktreeの詳細や、代表的なトラブル（認証未設定など）の推測を表示
- **`worktree remove <agent>` の拡張**: `--dry-run` / `--force` / `--keep-session` 等（運用ポリシーに応じて）
- **未コミット滞留の自動検知強化**: `--post-git-status` を非defaultでデフォルトONにする等（ノイズとのトレードオフ）


