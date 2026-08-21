# 第1ターン: 現状分解と刷新仮説

調査日: 2026-08-11

## このターンの結論

現時点の第一仮説は、**`second-agent` をマルチエージェントの中心に据え続けるのではなく、対話的な委譲・並列実行・セッション表示は各クライアントのネイティブ機能へ戻す**、というものです。

このリポジトリが将来も所有すべきなのは、主に次の4点だと考えます。

1. 再現可能な開発環境
2. workspace と権限に関する方針
3. project に置く役割・手順・検証規約
4. ネイティブ機能で足りない無人実行だけを扱う、小さな automation layer

ただし、これはまだ推奨案ではありません。特に Codex CLI の subagent と worktree の組み合わせ、provider 横断運用の本当の必要度、無人ジョブの耐久性要件を第2ターンで反証します。

## 1. 現行方式は何をしているか

表面的には `codex exec` / `claude -p` のラッパーですが、実際の `scripts/second-agent` は小さな control plane です。

| 責務 | 現在の実装 |
|---|---|
| backend 選択 | `SA_BACKEND=codex|claude` と `case` 分岐 |
| workspace 固定 | control repo ごとの `workspace init` 設定 |
| scope 事故低減 | `--cd` / `--add-dir` の検証と worktree 側へのパス写像 |
| 並列編集の分離 | agent ごとの Git worktree と branch |
| 会話継続 | JSONL から session ID を抽出し、次回に resume |
| 記録 | provider 生イベントと独自 transcript JSONL の二重保存 |
| 排他 | agent ごとの `flock` |
| 運用 | `status`、`paths`、`doctor`、worktree cleanup、timeout、post-run git status |
| provider 差分吸収 | 固定フラグ、モデル上書き抑止、stdin、Claude の擬似 `--cd` |

関連する実装・テスト・運用文書は少なくとも約 3,065 行あります。そのうち共通エンジンだけで 1,178 行、テストスクリプトが 909 行、長い運用テンプレが 619 行です。すでに「薄いラッパー」と呼ぶには大きい一方、永続キュー、構造化されたジョブ状態、再試行、キャンセル伝播、ログローテーションまでは持っていません。

つまり現在地は、**単純な CLI wrapper と本格的な orchestrator の中間**です。この中間状態が、保守負担の割に native UX も durable execution も十分に得られない原因になっています。

## 2. 前提が変わった点

この仕組みを作った時点と違い、2026年時点では3つの主要 surface が自前で並列実行を持っています。

### Codex

- 現行 release は subagent workflow を既定で有効化している。
- CLI、IDE、desktop app から agent thread を確認・steer・interrupt できる。
- project 固有の custom agent を `.codex/agents/*.toml` で定義でき、model、reasoning、sandbox、MCP、skills を個別設定できる。
- ローカル CLI でも `multi_agent` feature は `stable / true` と確認できた。
- programmatic use には Codex SDK、深い client integration には app-server、他の orchestrator から specialist として使う場合には `codex mcp-server` が用意されている。
- 一方、Codex-managed worktree は現行ドキュメント上 desktop app 限定であり、CLI subagent ごとの自動 worktree 隔離は確認できていない。書き込みを伴う並列化では重要な穴になり得る。

### Claude Code

- custom subagent、background subagent、agent view、agent teams、worktree session が native に存在する。
- ローカル CLI `2.1.220` では `--agent`、`--agents`、`--background`、`claude agents --json`、`--worktree` が確認できた。
- custom subagent に `isolation: worktree` を指定でき、parallel write の分離を provider 自身へ委ねられる。
- Agent SDK から subagent、session、hooks、permissions、MCP を扱える。
- agent teams は強力だが experimental かつ既定無効なので、基盤の必須要素にはまだ置きにくい。

### Cursor

- このリポジトリの `second-agent` は元来「Cursor エージェントから別 CLI を呼ぶ」用途を前面に出している。
- Cursor 3 系は Agents Window、async subagent (`/multitask`)、worktree、plan の parallel build、cloud subagent を直接持つ。
- したがって、元の中心ユースケース自体が IDE の native surface と重複し始めている。
- ただし実際の利用端末に該当機能が導入済みか、local-only が必須かは未確認。

## 3. 現行方式の価値と負債

### 残す価値があるもの

- provider に依存しない target workspace の指定
- agent ごとの write isolation
- 対象 repo 外へ誤ってパスを広げにくい規約
- role と task ticket を version control する考え方
- `doctor` のような、実行前に環境差分を発見する仕組み
- target project 内に runbook / decisions / tickets を置く方針

### 手放したいもの

- provider の private-ish な JSONL event 形式から session ID を抽出する責務
- provider 本体と重複する transcript 保存・resume・agent listing
- `nohup`、空になり得る出力、手動 `tail` を中心にした監視 UX
- 固定 model と、provider の option surface を除去・書き換える処理
- path correctness と backend adapter が同じ 1,178 行の Bash に混在していること
- provider ごとに進化する background、worktree、permissions を最低共通機能へ丸めること

## 4. 刷新案を評価する軸

第2・第3ターンでは、少なくとも以下を評価します。

1. **日常 UX**: 起動、進捗確認、steer、cancel、成果回収が自然か
2. **write isolation**: 並列 agent が同じ checkout を壊さないか
3. **scope / permission**: workspace 外アクセスと危険操作を明示的に制御できるか
4. **耐久性**: terminal や container の終了後も必要な仕事が継続・再開できるか
5. **観測性**: 状態、イベント、コスト、失敗理由を追えるか
6. **provider 選択**: Codex / Claude / Cursor を必要な粒度で交換できるか
7. **upgrade 耐性**: CLI の flag や JSON event 変更への追従量が少ないか
8. **再現性**: team と CI で同じ role / policy / validation を使えるか
9. **依存と保守**: 新規 runtime、SDK、daemon、DB を持つ価値があるか
10. **移行可能性**: 既存 project と運用を一度に壊さず移れるか

## 5. 暫定要件

ユーザーから追加条件がない限り、次の前提で比較します。

- 主用途は trusted local development である。
- 日常の対話作業が最多で、完全無人の CI orchestration は副用途である。
- Codex / Claude の選択肢は残したいが、同じ task の途中で provider を交換して同じ会話を継続する必要まではない。
- read-heavy な探索・レビューは同一 checkout でも並列化できる。
- write-heavy な実装は worktree または VM 単位で分離する。
- project 内の規約と成果物が正本であり、provider の transcript は正本にしない。
- 新しい依存を入れるなら、追加理由、影響、代替、削除方法を説明できる必要がある。

最後から2つ目が重要です。会話履歴を provider 横断で正規化しようとすると、各 provider の tool event や reasoning 表現を再実装することになります。横断すべきものは会話そのものではなく、**task contract、Git commit、検証結果、decision** と考えます。

## 6. 候補アーキテクチャ

### A. Native-only

各 surface の native orchestration をそのまま使います。

- Codex: subagents + `.codex/agents/`、desktop app worktrees
- Claude: subagents / agent view + `.claude/agents/` + worktree isolation
- Cursor: Agents Window + async subagents + worktrees / cloud agents

リポジトリは devcontainer と設定例・project template のみ提供し、共通 runtime を持ちません。

**長所**

- 最小の保守量で、各製品の UI、steering、cancel、session 表示をそのまま使える。
- provider の新機能が wrapper に遮られない。
- JSONL parser、独自 session registry、`nohup` 手順を削除できる。

**弱点**

- provider ごとに role 定義形式と操作が異なる。
- Codex CLI 単体で write-heavy subagent をどう隔離するかが未解決。
- headless / CI の統一入口がない。

### B. Native-first + thin policy layer

対話 orchestration は A と同じく native に任せ、共通層は次だけを持ちます。

- capability / version `doctor`
- workspace policy と safe defaults
- provider 別 agent definition の配置・検証
- 必要なら worktree lease の小さな helper
- automation 用の一回実行 contract

provider session、transcript、agent process の常時管理はしません。既存 command 互換が必要なら、移行期間だけ deprecated shim を置きます。

**長所**

- native UX を保ちながら、事故低減と project 規約は共通化できる。
- 現行の良い部分を残しつつ、変化しやすい JSON event 依存を減らせる。
- 段階移行しやすい。

**弱点**

- 「thin」の境界を守らないと再び orchestrator 化する。
- provider 別 config の重複または生成処理が残る。
- worktree helper を持つ場合、native worktree との所有権衝突を避ける必要がある。

### C. SDK-based local control plane

Codex SDK / app-server と Claude Agent SDK に adapter を作り、typed な job API、event store、worktree manager、TUI などを自前で提供します。

**長所**

- background job、structured result、timeout、budget、retry、cancel、trace を明確な契約にできる。
- provider 横断の task queue や CI integration を本当に必要とするなら最も拡張しやすい。
- shell で path / JSON を扱うよりテストしやすい。

**弱点**

- SDK、runtime、state migration、process lifecycle を持つ本格プロダクトになる。
- native UI と別の UX を維持する必要がある。
- local interactive が中心なら過剰設計になりやすい。
- Agents SDK や MCP は orchestration の部品であり、Git isolation や durable queue を自動では解決しない。

### D. IDE / hosted control plane へ全面委譲

Cursor Cloud Agents、Codex cloud / desktop app、Claude の agent view などへ仕事の隔離と長時間実行を委ねます。

**長所**

- local terminal より良い並列 UI、隔離環境、継続実行を得やすい。
- 自前の daemon、ログ、queue を持たずに済む。

**弱点**

- provider lock-in、課金、network、秘密情報、team policy の影響が大きい。
- local / offline を重視する現在の devcontainer の思想とは一部緊張する。
- provider 間で同じ運用にはならない。

### E. 現行 wrapper の近代化

外形を維持し、Bash を typed language に置き換え、adapter、job state、log rotation、structured output を追加します。

**長所**

- 現行利用者の移行が最小。
- provider 共通 CLI と workspace / worktree policy を完全に制御できる。

**弱点**

- native 機能と競争し続ける。
- 中途半端に進めると、現在より大きな「自前 agent runtime」になる。
- 独自 runtime を所有する明確な product requirement がない限り費用対効果が悪い。

## 7. 第1ターン時点の比較

`高` は優れている、`低` は弱いという意味です。まだ実験前の暫定評価です。

| 案 | 保守容易性 | native UX | provider 横断 | write isolation | 無人・耐久実行 | 段階移行 |
|---|---:|---:|---:|---:|---:|---:|
| A. Native-only | 高 | 高 | 低 | 中 | 中 | 中 |
| B. Native-first + thin layer | 中〜高 | 高 | 中 | 中〜高 | 中 | 高 |
| C. SDK control plane | 低 | 中 | 高 | 高※ | 高※ | 低 |
| D. IDE / hosted 委譲 | 高 | 高 | 低 | 高 | 高 | 中 |
| E. wrapper 近代化 | 低 | 低〜中 | 中〜高 | 高 | 中 | 高 |

`※` 自動的に得られるのではなく、こちらで正しく実装した場合です。

現状は B が最有力です。A は Codex CLI の write isolation と headless の共通入口で弱く、C は現時点の要求には重すぎ、E は native 機能の再実装を続けることになります。

## 8. 有力仮説の責務分割

```text
project repository
  ├─ AGENTS.md / CLAUDE.md / rules     durable policy
  ├─ provider agent definitions         role + tools + model policy
  ├─ tickets / decisions / test result  provider-neutral task contract
  └─ Git commits / branches             durable deliverables

interactive client
  ├─ spawn / wait / steer / cancel
  ├─ conversation and transcript
  └─ native progress UI

optional automation runner
  ├─ validate workspace and capabilities
  ├─ create or lease isolated checkout when required
  ├─ start one SDK/CLI job with structured output
  └─ record job metadata, not a duplicate conversation history
```

この分割なら、「誰が何の state を所有するか」が明確です。

- provider: conversation、tool event、token usage
- native client: interactive agent lifecycle
- Git: code changes と integration history
- project repo: rules、task contract、decisions、acceptance evidence
- optional runner: job ID、provider、workspace、開始・終了・exit reason

## 9. 刷新対象として隣接する問題

マルチエージェントだけを入れ替えても、次は残ります。

### dangerous-by-default

現在の通常 `codex` / `claude` wrapper は、devcontainer 内で無条件に danger / permission bypass を付けます。さらに container は privileged で host credential を mount しています。workspace 制限は security boundary ではないため、これは刷新時に分離すべきです。

候補は、通常コマンドを provider の安全な既定へ戻し、明示的な `*-trusted` profile だけが bypass を使う二層化です。最終判断は第3ターンに回します。

### model pin と CLI surface の横取り

`second-agent` はモデルをコード内既定値へ固定し、provider が持つ model option を除去します。native custom agent / project config に任せれば、役割単位の model と reasoning を明示でき、wrapper の陳腐化を減らせます。

### 文書量と運用の複雑さ

`AGENTS_TEMPLATE.md` は約500行あり、かなりの部分が `nohup`、ログ tail、manual ticket movement、wrapper-specific path に費やされています。刷新後は「タスク分割原則」と「provider 別の短い recipe」を分離できそうです。

## 10. まだ捨ててはいけない反論

- native feature は provider ごとの差が大きく、CLI update で挙動も変わる。
- native transcript は横断検索・監査しづらい。
- Codex desktop app worktree は CLI では使えず、terminal-first 利用者には足りない可能性がある。
- Claude の agent teams は実験的で、標準運用には早い。
- Cursor native orchestration へ寄せると、この repo を VS Code / terminal から使う価値が下がる。
- 現行 wrapper の「同じコマンドで Codex / Claude を交換できる」性質が、実利用でどれだけ重要か未計測である。
- provider-native session と独自 Git worktree を混在させると、cleanup と branch ownership がかえって不明確になる可能性がある。

## 11. 第2ターンで行う反証

次は候補を増やさず、以下の代表シナリオへ当てます。

1. **並列 read-only review**
   - security / correctness / tests の3 agent が同時に読み、親が統合する。
2. **並列 implementation**
   - 2 agent が別ファイル群を編集し、衝突検出、テスト、統合、cleanup まで行う。
3. **長時間 background task**
   - terminal / parent session から離れても状態確認、steer、cancel、再開ができる。
4. **provider fallback**
   - Codex が使えないとき Claude へ task contract を渡し直せる。会話互換ではなく成果物互換で評価する。
5. **scope failure**
   - workspace 外パス、untracked secret、stale worktree、同名 agent、container restart をどう扱うか。

そのうえで、A・B・Cを主対象に、次を明らかにします。

- native-only で失う安全性と運用性は本当に許容できないか。
- thin layer に残す最小責務は何か。
- SDK control plane が必要になる明確な閾値は何か。
- 現行 command をどの期間、どの互換度で残すべきか。

## 12. 参照した根拠

### リポジトリ内

- `scripts/second-agent`
- `scripts/codex-second-agent-filter.py`
- `scripts/claude-second-agent-filter.py`
- `README.md`
- `docs/architecture.md`
- `AGENTS_TEMPLATE.md`
- `project/AGENTS.md`
- `.devcontainer/Dockerfile`
- `.devcontainer/devcontainer.json`

### 公式資料

- [Codex: Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents.md)
- [Codex: Worktrees](https://learn.chatgpt.com/docs/environments/git-worktrees.md)
- [Codex SDK](https://learn.chatgpt.com/docs/codex-sdk.md)
- [Use Codex with the Agents SDK](https://learn.chatgpt.com/docs/mcp-server.md)
- [Claude Code: Run agents in parallel](https://code.claude.com/docs/en/agents)
- [Claude Code: Custom subagents](https://code.claude.com/docs/en/sub-agents)
- [Claude Code: Worktrees](https://code.claude.com/docs/en/worktrees)
- [Claude Code: Agent SDK subagents](https://code.claude.com/docs/en/agent-sdk/subagents)
- [Cursor 3.0: Agents Window](https://cursor.com/changelog/3-0)
- [Cursor 3.2: Multitask and worktrees](https://forum.cursor.com/t/multitask-worktrees-and-multi-root-workspaces/158954)
- [Cursor 3.3: Build Plan in Parallel](https://cursor.com/changelog/05-07-26)

## 第1ターン終了時の一文

**独自 runtime を育てる前に、native orchestration を標準経路にし、provider をまたいで本当に共有すべきものを「会話」ではなく「task contract・policy・Git成果物」に狭められるかを検証する。**
