# AGENTS_TEMPLATE.md（別プロジェクト開発用テンプレ）

このファイルは、**この devcontainer 基盤を使って開発する“別プロジェクト”側**に置くためのテンプレです。  
対象プロジェクトに `AGENTS.md` としてコピーし、`<<...>>` を埋めて使ってください。

---

## このプロジェクト情報（埋める）

- **project 名**: `<<project-name>>`
- **project の実体ディレクトリ**: `project/<<name>>/`（例: `project/app/`）
- **サブエージェントの作業ディレクトリ（effective cd）**: `<<workdir>>`
  - 例: `project`（親リポジトリを workspace にして `project/` 配下だけ触らせたい場合）
  - 例: `.`（`workspace init project/<<name>>` で **project 側 Git を workspace** にしている場合）
- **実行/テストコマンド**:
  - `<<test-cmd>>`（例: `python -m unittest -v` / `npm test`）
  - `<<lint-cmd>>`（任意）

---

## 役割（最小固定 + タスク派生）

このテンプレでは、役割名を「固定の数種類」に縛らず、**タスク単位で役割（= agent 名）を派生させて並列稼働**させる運用を推奨します。

- **固定（最小）**
  - **管理者（main/manager）**: 実装しない。管理・判断・統合・ドキュメント整備に徹する
- **タスク派生（並列実行の主役）**
  - **`implementer-taskXXXX`**: 実装・テスト・コミット（task ごとに分割し、同時に複数走らせる）
  - **`reviewer-taskXXXX`**: レビュー（Must/Should/Nice）・リスク洗い出し（task ごとに分割して並列レビュー可）
  - **`triage-taskXXXX`**: 調査・原因切り分け（ログ/再現/最小ケース作成）。実装に入る場合は `implementer-*` へ引き継ぐ
  - **`newbie-taskXXXX`**: 新人。**質問だけ**して前提/仕様/運用知識を掘り起こす（原則コードは触らない）

### 命名ルール（例）

- **粒度**: “1 タスク=1 agent” を基本にする（衝突や手戻りを減らし、worktree を自然に分離できる）
- **推奨フォーマット**: `<role>-<topic>-<id>`
  - 例: `implementer-auth-0123`, `triage-flakytest-045`, `reviewer-api-0123`, `newbie-onboarding-001`
- **依頼文の先頭に必ず書く**:
  - 対象タスク ID / 対象ディレクトリ / 完了条件 / 成果物（差分 or コミット）/ 相談事項

---

## タスク設計（クリティカルパスで整理して並列化する）

管理者は、プロジェクト開始から終了までを **「細かいタスク一覧」→「依存関係（DAG）」→「クリティカルパス」**の順で整理し、
並列に投げられるサブエージェント指示を洗い出します。

> ここでは **工数/日数/見積もりは書かない**（依存関係だけで順序を決める）前提です。

### 手順（管理者）

1. **ゴールを固定**（DoD を1文で）
2. **タスク一覧を分解**（最初は多めでOK。後で統合/分割する）
3. **依存関係を書く**（「Aが終わらないとBに入れない」を明示）
4. **クリティカルパスを特定**
   - 依存チェーンが最も長い経路（=止まると全体が止まる）を CP とする
5. **並列に投げるタスクを抽出**
   - 依存が無い/薄いタスクを先に `triage-*` / `reviewer-*` へ投げる
6. **段階化（実装/レビュー/テスト）**
   - 各タスクに「実装」「レビュー」「統合テスト/動作確認」を必ず付ける（漏れ防止）

### 出力フォーマット（例: plan）

管理者は `project/docs/plan.md`（新規作成でOK）に次のように整理します。

- **T-0001: 仕様確定（入力/出力）** → deps: なし → owner: `triage-*` → artifacts: `project/docs/decisions.md`
- **T-0002: テスト設計（Red）** → deps: T-0001 → owner: `implementer-*` → artifacts: `tests/...`
- **T-0003: 実装（Green）** → deps: T-0002 → owner: `implementer-*` → artifacts: `src/...`
- **T-0004: リファクタ（Refactor）** → deps: T-0003 → owner: `implementer-*`
- **T-0005: レビュー** → deps: T-0003 → owner: `reviewer-*` → output: Must/Should/Nice
- **T-0006: 指摘反映** → deps: T-0005 → owner: `implementer-*`
- **T-0007: 統合テスト/スモーク** → deps: T-0006 → owner: `implementer-*` → cmd: `<<test-cmd>>`

### 依頼の組み立て（並列に投げる）

- **triage を先行**: 仕様/制約/既存構造の調査 → `project/docs/` を整備
- **reviewer を先行**: 変更予定箇所のリスク洗い出し、レビュー観点の作成（実装前レビュー）
- **implementer を並列**: タスク単位で worktree を分け、1タスク=1 agent で進める

### Mermaid で依存関係を図示（推奨）

クリティカルパスや並列化ポイントは、文章だけだとズレやすいので **Mermaid** で依存関係（DAG）を図示するのがおすすめです。
管理者は `project/docs/plan.md` に Mermaid を貼り、サブエージェントにはその図を前提に指示します。

例（依存関係の図）:

```mermaid
graph TD
  T0001[仕様確定] --> T0002[テスト設計 (Red)]
  T0002 --> T0003[実装 (Green)]
  T0003 --> T0004[リファクタ (Refactor)]
  T0003 --> T0005[レビュー]
  T0005 --> T0006[指摘反映]
  T0006 --> T0007[統合テスト/スモーク]

  %% 並列化例（仕様確定と並行で先行できる）
  T0001 --> R001[レビュー観点作成]
  T0001 --> X001[調査/影響範囲特定]
```

（備考）Mermaid の表示が効かない環境では、同じ内容を箇条書きでも残してください。

---

## 開発方針: t-wada 式 TDD（推奨）

このテンプレの基本スタイルは **t-wada 式 TDD** を前提にします。

- **基本サイクル**: Red → Green → Refactor
  - **Red**: まず小さな失敗テストを書く（仕様を一つだけ表現）
  - **Green**: 最小の実装で通す
  - **Refactor**: ふるまいを変えずに整理する（重複排除・命名改善・責務分離）
- **粒度**: “小さく・早く” を優先（コミットも小さく）
- **テストの責務**:
  - 仕様の表明（例: 入力 → 出力、エラー条件）
  - 変更検知（回帰防止）
- **モックの方針**:
  - 最初からモックありきにしない（まず純粋関数化/設計でテスト容易に）
  - I/O 境界（HTTP/DB/FS など）だけを最小限に切り出して必要ならモック
- **既存コード改修の入口**:
  - 仕様が曖昧なら「characterization test（現状のふるまい固定）」から入る

管理者は依頼文に **テストコマンド（<<test-cmd>>）**と **TDD 前提**を明記してください。

---

## project/docs（管理者が整備する前提）

このテンプレ運用では、管理者が `project/docs/` を継続的に整備します。

- **管理者が書く**（推奨）:
  - `project/docs/runbook.md`: 実行手順・リリース手順・よくある事故と対処
  - `project/docs/decisions.md`: 重要な設計判断（短い箇条書きで OK）
- **サブエージェントは参照 OK**だが、**更新は原則しない**（更新が必要なら管理者に提案）

### 改善ループ（新人エージェントで質問 → ドキュメント追記）

運用が安定してくるほど「暗黙知」が増えるので、定期的に **`newbie-*`** を立てて **質問させ、回答を管理者が `project/docs/` に追記**して整備します。

- **頻度（例）**: 週 1 / スプリント末 / 大きな変更の直後（どれかで OK）
- **進め方**
  - `newbie-*` に「プロジェクトを理解するための質問を _10〜20 個_ 出す」依頼をする（コード改変は禁止）
  - 管理者が回答し、**恒久情報は `project/docs/runbook.md` / `project/docs/decisions.md` に追記**する
  - 依頼テンプレや注意事項（スコープ、危険操作、標準コマンド等）は必要に応じて `AGENTS.md` に反映する

---

## 「project 配下だけを見せる」運用（推奨）

サブエージェントは、リポジトリ全体を見せるのではなく **project 配下のみ**を対象にすると安全です。

- このテンプレと合わせて、対象リポジトリに **`project/AGENTS.md`（サブ向け指示）**を置く運用を推奨します
- `codex-second-agent` は通常「起動場所の git root」を workspace として扱いますが、**サブエージェントは project 側の Git を workspace として固定**するのが安全です
  - まず `codex-second-agent workspace init <path-to-project-git>` を実行し、対象プロジェクト（git repo root）を保存します
  - 以降、サブエージェント実行はその workspace を基準に worktree/log/state を作るようになります
  - 重要: これは技術的な強制隔離ではありません（ルールで縛る運用）。ただし、親リポジトリの worktree を誤って作る事故は防げます

例（project 側 Git を workspace として固定する）:

```bash
codex-second-agent workspace init project/<name>
```

以降の **チケット作成/起動/回収** は、下の「開発サイクル」「バックグラウンド実行（ログの見方を含む）」を正本として参照してください。  
（ここに同じ起動テンプレを重複して置かない）

---

## codex-second-agent の使い方（要点）

### codex-second-agent とは？どこにある？

- **何か**: `codex exec` を「セッション ID 自動保持」「agent 別 worktree」「ログ保存」付きで呼び出すラッパー
- **この基盤リポジトリでの実装**: `scripts/codex-second-agent`
- **コンテナ内の PATH**: 環境によっては `codex-second-agent` が PATH に入っていないことがあります（その場合は `scripts/codex-second-agent` を直接実行）

### 基本

```bash
codex-second-agent "READMEを要約して"
```

2 回目以降は、同じワークスペース（Git ルート）であれば自動的に前回セッションを `resume` します。

### エージェントを分ける（マルチエージェント）

```bash
codex-second-agent --agent reviewer "この差分をレビューして"
codex-second-agent --agent implementer "このissueを実装して"
```

### 状態/場所確認（迷子防止）

```bash
codex-second-agent status
codex-second-agent status --verbose
codex-second-agent paths
codex-second-agent doctor
```

### worktree の配置

- デフォルトは `<repo>/.codex-second-agent/<workspace_hash>/worktrees/<agent>/`
- ホーム配下に増えるのが気になる場合は、workspace 配下に置けます:

```bash
CODEX_SA_WORKTREES_MODE=workspace codex-second-agent paths
# または
codex-second-agent --worktrees-in-workspace paths
```

### worktree の後片付け

```bash
codex-second-agent worktree remove <agent>        # ブランチも整理（既定）
codex-second-agent worktree remove <agent> --keep-branch
```

### 未コミット滞留の検知（推奨）

```bash
codex-second-agent --agent implementer --post-git-status "..."
# または
CODEX_SA_POST_GIT_STATUS=1 codex-second-agent --agent implementer "..."
```

---

## バックグラウンド実行（推奨）

### 位置づけ

この章は「**バックグラウンドで回すときの落とし穴**」と「**ログの見方（正本）**」をまとめます。  
チケットの作り方/状態遷移/統合までの一連は「開発サイクル（管理者主導で回す）」を参照してください。

### ログの見方（重要）

- **最優先（推奨）**: `transcript.jsonl`（1 リクエスト=1 行）
- **次点**: `events.jsonl`（デバッグ向け、生イベント）
- `nohup` の標準出力ファイルは **空のまま**になることがあります（モデル出力はログに集約される前提で運用する）

- 実体パスの確認:

```bash
codex-second-agent --agent implementer paths
```

- 会話ログ（読みやすい）: `transcript.jsonl`

```bash
tail -n 5 .codex-second-agent/<workspace_hash>/agents/implementer/logs/transcript.jsonl
```

- 生イベント（デバッグ向け）: `events.jsonl`

```bash
tail -n 50 .codex-second-agent/<workspace_hash>/agents/implementer/logs/events.jsonl
```

### reviewer は timeout を付けるのが現実的

レビューは長引くことがあるので、バックグラウンド実行では `timeout` を付けて「必ず終了してログが取れる」形にするのがおすすめです。

（起動例は「開発サイクル > サブエージェントにタスクを投げる」を参照。ここでは timeout を付ける、という運用上の要点だけ覚える）

---

## 開発サイクル（管理者主導で回す：投げる→整備→回収→統合→次へ）

このテンプレの“基本の回し方”は、管理者が **サイクルを短く回し続ける**ことです。  
サブエージェントは「タスク単位の実行者」であり、管理者は「方向付け・整備・統合・次の投げ直し」を担当します。

### 0) サイクル開始前の準備（最初の1回だけ）

- `project/docs/runbook.md` に **最低限の実行/テスト手順**を書いておく
- `project/docs/decisions.md` に **重要な判断は残す**運用にする
- `codex-second-agent workspace init project/<name>` を実行して、対象プロジェクト（git repo root）を固定する

### 1) タスク設計（クリティカルパス＋並列化の再確認）

- 「タスク設計（クリティカルパスで整理して並列化する）」の手順どおりに、`project/docs/plan.md` を更新する:
  - タスク一覧（ID付き） / 依存関係（DAG、Mermaid 推奨） / クリティカルパス（CP） / Ready

ポイント:
- **Ready 条件が曖昧なタスクは投げない**（triage を先に投げて情報を揃える）
- **同じファイルを複数 implementer に触らせない**（衝突・手戻りの原因）

### 2) チケット化（必須：タスク→チケット→実行）

この運用では、**サブエージェントへの依頼=チケットファイル**です。  
管理者は「plan を更新して終わり」ではなく、Ready なタスクを **必ずチケット化**してから投げます。

- チケット置き場: `.codex-second-agent/tickets/`
- 推奨する状態遷移（ディレクトリで管理）:
  - `tickets/ready/` → `tickets/running/` → `tickets/done/`

```bash
mkdir -p .codex-second-agent/tickets/{ready,running,done} .codex-second-agent/nohup

# テンプレからチケットを起こす（“ちゃんと編集”する）
ticket=.codex-second-agent/tickets/ready/task-0001.md
cp project/docs/tickets/task-ticket.template.md "$ticket"
# ${EDITOR:-vi} "$ticket"
```

ポイント:
- チケットには **スコープ/成果物/完了条件/相談事項** を必ず入れる（口頭依頼禁止）
- チケットに **agent名（例: implementer-task0001）**を固定で書く（ログ/branch/作業単位が一致する）
- `project/docs/plan.md` から **チケットへの参照（ファイルパス）**を貼る（行き来しやすくする）

### 3) サブエージェントにタスクを投げる（チケット起点・バックグラウンド）

- **triage**（先行）: 調査・影響範囲・仕様の穴を `project/docs/` に提案
- **implementer**（並列）: タスク単位で実装・テスト・コミット
- **reviewer**（先行 or 後追い）: レビュー観点の作成 / 差分レビュー

ポイント:
- 依頼文（チケット）には必ず **スコープ/成果物/完了条件/相談事項** を含める
- reviewer は **timeout** 付き推奨（必ず終わって回収できるようにする）

チケットから起動する例:

```bash
agent=implementer-task0001
ticket=.codex-second-agent/tickets/ready/task-0001.md
out=.codex-second-agent/nohup/${agent}.out

mv "$ticket" .codex-second-agent/tickets/running/
ticket=.codex-second-agent/tickets/running/task-0001.md

cat "$ticket" | nohup codex-second-agent --agent "$agent" --post-git-status - -- --cd <<workdir>> > "$out" 2>&1 &
echo "pid=$!"
```

reviewer（timeout 付き）の例:

```bash
agent=reviewer-task0001
ticket=.codex-second-agent/tickets/ready/review-0001.md
out=.codex-second-agent/nohup/${agent}.out

mv "$ticket" .codex-second-agent/tickets/running/
ticket=.codex-second-agent/tickets/running/review-0001.md

# チケット内の related.commits / Review focus / Output format を必ず埋める
cat "$ticket" | nohup timeout 120s codex-second-agent --agent "$agent" - -- --cd <<workdir>> > "$out" 2>&1 &
echo "pid=$!"
```

### 4) TDD マイクロサイクル（各チケットで必ず回す）

チケット中心運用でも、品質の核は **t-wada 式TDD（Red→Green→Refactor）**です。  
各 implementer チケットは、原則として以下のマイクロサイクルを回して完了させます。

- **Red**: “仕様を1つだけ表現する”小さな失敗テストを書く（まず落ちることを確認）
- **Green**: 最小の実装で通す（きれいさは後回しでよい）
- **Refactor**: ふるまいを変えずに整理（重複排除、命名、責務分離）

ポイント（運用に落とす）:
- **Red が見えない差分は危険**: テスト追加が無い/薄い場合、まず Red を作るチケットに分割してよい
- **チケット分割の指針**:
  - `task-XXXX-red`（テスト追加/characterization）
  - `task-XXXX-green`（最小実装）
  - `task-XXXX-refactor`（整理だけ。ふるまいは変えない）
- **既存改修の入口**: 仕様が曖昧なら characterization test から入る（現状固定→変更）

### 5) 進捗の回収（ログ駆動＋チケット更新）

管理者は待たない。ログで回収して次の判断に進む。

- 進捗確認の基本:
  - `transcript.jsonl`（最優先）
  - `events.jsonl`（詰まった時だけ）
  - `nohup` は空のことがある（前提にしない）

詳細（どこを見ればいいか・パスの確認・tail の例）は「バックグラウンド実行 > ログの見方（重要）」を正本にしてください。

ポイント:
- **「終わった」宣言だけで判断しない**。必ず成果物（コミット/差分/パッチ）を確認する
- `--post-git-status` で **未コミット滞留**が出たら、次の指示は「コミットしてから報告」に寄せる
- 回収したら、チケットに **結果（commit hash / 変更概要 / 実行したテスト / 残課題）**を追記する（次の人が見て分かる状態にする）

### 6) ドキュメント整備（管理者の仕事）

サブの成果を受けて、管理者が `project/docs/` を更新して“次が速くなる状態”にする。

- `runbook.md`: 実行/テスト/デバッグの手順を追記（手戻り防止）
- `decisions.md`: 重要判断（採用/却下した代替案）を追記（ブレ防止）

ポイント:
- 「この判断は次も使う」ものは必ず残す（口頭/チャットで消える知識を減らす）

### 7) 統合（タスクが終わったら取り込む＝チケットを閉じる）

統合の基本は **小さく・頻繁に**。

- 取り込み前チェック:
  - テスト: `<<test-cmd>>`
  - reviewer の **Must が解消**されている
  - スコープ逸脱（project 外の変更）が無い

ポイント:
- implementer が「パッチ」しか出せない場合もある（環境/権限/制約）。その時は管理者が取り込む
- worktree の後片付け（不要なら `worktree remove`）
- 取り込みが終わったらチケットを `tickets/done/` に移動し、内容が十分なら最後に削除してよい（削除は“回収・統合が完了してから”）

### 8) 次のタスクへ（plan 更新→新チケット化→再投入）

統合したら `project/docs/plan.md` の Ready/CP を更新して、次のタスク群を投げる。

ポイント:
- “やり残し”は plan に戻す（チャットの記憶に頼らない）
- 仕様が揺れたら decisions に残す（揺れの履歴が次の判断を助ける）

---

## 管理者のチェックリスト（短縮版）

- **依頼前**:
  - `project/docs/runbook.md` に「実行/テスト/確認方法」が書かれている
  - `workspace init` が対象プロジェクトを指している
  - **TDD 前提**（Red/Green/Refactor、最小ステップ、テストを先に）を依頼文に明記
  - Ready なタスクが **チケット化**されている（`.codex-second-agent/tickets/ready/`）
- **依頼後**:
  - `transcript.jsonl` で進捗確認（`nohup` が空でも慌てない）
  - 必要なら `--post-git-status` で未コミット滞留を早期検知
  - 回収結果（commit/test/残課題）が **チケットに追記**されている
- **取り込み前**:
  - `<<test-cmd>>` を実行して OK
  - reviewer の Must が潰れている
- **後片付け**:
  - 統合済みチケットを `tickets/done/` に移動 → 必要なら削除（回収・統合が完了してから）

---

## サイクルの要約（チートシート）

上の「開発サイクル」の **最短版**です。迷ったらまず開発サイクルに戻り、ここは“手元の確認用”として使ってください。

### 1) 管理者: plan 更新 → チケット作成 → 起動（バックグラウンド）

- **チケットテンプレ（`project/docs/tickets/task-ticket.template.md`）を埋める**:
  - 特に: **Scope / Acceptance Criteria / Commands / Deliverables / TDD Plan** を空にしない
  - “短さ”より **誤解の余地を潰す**（並列化しても衝突しない依頼にする）

### 2) implementer: 実装 → テスト → コミット

- `--post-git-status` を付けると未コミット滞留が早期に見つかります

### 3) 管理者: reviewer にレビュー依頼（バックグラウンド）

- commit hash / ブランチ名 / 変更範囲 を明示
- 指摘は Must/Should/Nice に分けてもらう
 - （推奨）timeout 付きで起動して、回収できる形にする（理由は「バックグラウンド実行」を参照）

### 4) implementer: 指摘反映 → 再テスト → 追加コミット

### 5) 管理者: 取り込み判断・統合・後片付け

- 不要になった worktree は削除（上記 `worktree remove`）
- 統合済みチケットは `tickets/done/` に移動（必要なら削除）
