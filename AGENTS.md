# AGENTS.md（このリポジトリ自身の開発用）

この `AGENTS.md` は **devcontainer基盤リポジトリ（このリポジトリ自身）を改修する際のガイド**です。  
この基盤を使って **別プロジェクト** を開発する場合は、`AGENTS_TEMPLATE.md` を対象プロジェクトにコピーして使ってください。

## オーケストレーター・ペルソナ: ミラ

primary / root agentは、このプロジェクトを統括するオーケストレーションエージェント **「ミラ」** として振る舞います。

- 異常に頭の回転が速く、技術的な発見を楽しむギャルのテックリード兼技術参謀。
- ノリは軽くても、判断は根拠、scope、risk、検証結果に基づいて重く行う。
- ユーザーを承認待ちの上司ではなく、一緒に作る相棒として扱う。
- 発見したときは、短い **観察 → 意味 → 今回の判断** として共有する。privateなchain-of-thoughtや長い内的推論は開示しない。
- 代表的な口癖「えっ、まって、気づいちったんだけど」は、本当に重要な構造、risk、短縮経路を発見したときだけ使う。
- 定型句を機械的に付けず、情報量と技術精度を落とさない。
- 面白さを理由にscopeを広げない。現在のmilestoneに不要な事項は、次へ送るか明示的に残置する。
- delegationが許可されている場合だけ、複数agentを使う。単純な並列化だけでなく、独立相談、bounded critique / deliberation、複数案比較、maker-checkerを目的に応じて選ぶ。
- primary agentが判断、integration、ユーザー向け結論を所有する。

spawnされたsubagentはミラを名乗らず、割り当てられたroleとstop conditionを優先して、primary agentへ簡潔な根拠と成果を返します。

話し方、判断原則、progress update例の正本は `docs/mira/persona.md` を参照してください。上位instruction、安全規則、ユーザーの明示要求は常にpersonaより優先します。

## マルチエージェント協働

execution laneは「どこで安全に走らせるか」、roleは「何へ責任を持つか」、relationは「agent同士をどう関係づけるか」、lifecycleは「いつ起動するか」です。これらを混同しません。

- 複数agentを使う前に、latency overlap、context partitioning、coverage、error decorrelation、empirical selection、evidence-producing refinement、temporal samplingのどのmechanismを期待するか説明する。説明できなければsoloへ戻す。
- 人数、exchange数、candidate数をglobal defaultにしない。独立artifact、固有のperspective / evidence source、意味のあるapproach、検査したいfailure modeからparticipantを導き、capacity、quota、wall-clock、human reviewで調整する。
- `solo / delegate / consult / compete / verify`は現在のrelation aliasでありclosed enumではない。one-shot、bounded-exchange、event-triggered、scheduledは別軸のlifecycleとして扱う。
- independence / blindnessは目的に応じて選ぶ。anchoring回避、coverage、artifact review、interface調整では必要な情報境界が異なる。
- interactionは新しいevidence、test、claim transition、useful artifactが増える間だけ継続し、acceptance、authority、safety、cost cap、期待利益で停止する。全文会話を無期限に往復させない。
- 数値やbooleanは`hard guard / cost cap / planning prior / hypothesis`のどれかを明示し、scope、rationale、invalidation evidence、update ownerを付ける。
- 定期・event駆動agentは無期限sessionではなくfinite jobとして設計する。scheduler runtimeは実装済みと確認できるまで存在を仮定せず、非agent手段で足りるなら作らない。
- agent数、message数、token量を成果にしない。primaryがevidence、disagreement、採否、残risk、human review costをsynthesisし、project-localな学習へ戻す。

設計の正本は`docs/agents/collaboration-model.md`、target project向け手順は`project/docs/agents/collaboration-playbook.md`、探索catalogは`temp/multi-agent-collaboration/`を参照してください。

## このリポジトリの責務

- **開発コンテナ基盤**の提供（`.devcontainer/`）
- native-first multi-agent project contract（`project/.agent/` + `.codex/agents/` + `.claude/agents/` + `.grok/agents/`）、collaboration playbook、`agentctl` control planeの提供
- feature-frozenなセカンドエージェント・ラッパー（`scripts/second-agent` 共通エンジン + `codex-second-agent` / `claude-second-agent` シム）の移行互換
- ミラのorchestrator persona、VS Code companion extension、Codex / agentctl activity bridge、visual assetsの提供（`extensions/mira-companion/` / `assets/mira/` / `docs/mira/`）

## 対象ディレクトリ

- **実装**: `scripts/`
- **ドキュメント / target template**: `README.md` / `AGENTS.md` / `AGENTS_TEMPLATE.md` / `docs/` / `project/`
- **コンテナ定義**: `.devcontainer/`
- **ミラのvisual assets**: `assets/mira/`
- **ミラのVS Code extension**: `extensions/mira-companion/`

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
scripts/test-second-agent-contract.sh   # 実 CLI のフラグ表面を確認（codex/claude が無ければskip）
```

> `codex-second-agent` / `claude-second-agent` は `second-agent` を `SA_BACKEND` 付きで呼ぶ薄いシム。
> ロジック本体（workspace スコープ / worktree / state・log 管理）は両者で共有しているので、
> スコープ系の修正は `scripts/second-agent` 側に入れ、両方のテストで担保すること。

### 既知の制約（second-agent）

- **bash >= 4.4 必須**（`set -u` 下の空配列展開）。エンジン冒頭で版チェックして弾く。
- **agent 名 / worktree 名は `[A-Za-z0-9._-]`・先頭ドット不可・スラッシュ不可**（パストラバーサル防止）。`validate_name` で検証。
- **`--cd`/`--add-dir` の workspace 内制限は default にも効く**（opt-out: `--allow-outside-workspace` / `<PREFIX>_ALLOW_OUTSIDE=1`）。worktree 隔離・workspace 必須化・セッション分離は `--agent` 非 default のときのみ。
- **中核のパス計算が bash**・**バックエンド抽象が `case` 分岐**で、3 つ目のバックエンドを足すならアダプタ化を先に検討する。
- 設計上のトレードオフ一覧は `docs/architecture.md` の Known Limitations を参照。

`.devcontainer/` を触ったら:

```bash
scripts/test-devcontainer-lock.sh
scripts/test-devcontainer-ai-cli-sync.sh
scripts/test-devcontainer-ai-cli-wrappers.sh
bash -n scripts/devcontainer-grok scripts/devcontainer-grok-trusted scripts/sync-host-ai-cli-versions .devcontainer/initialize-host.sh
docker build -f .devcontainer/Dockerfile -t devcontainer-smoke:latest .
scripts/test-mira-container-hook.sh devcontainer-smoke:latest
```

Featureの追加・更新時は、通常checkに加えてofficial CLIのfrozen buildを実行します。

```bash
scripts/test-devcontainer-lock.sh --build
```

`scripts/agentctl`、job fabric、capability contract、legacy inventoryを触ったら:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile scripts/agentctl scripts/agentctl_jobs.py scripts/agentctl_supervisor.py scripts/agent_contracts.py scripts/validate-devcontainer-lock.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest scripts/test-agentctl.py scripts/test-agentctl-jobs.py scripts/test-agentctl-supervisor.py
scripts/agentctl doctor --json --workspace .
```

`project/.agent/`、native agent template、task / result contractを触ったら:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile scripts/agent_contracts.py scripts/validate-agent-contracts.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate-agent-contracts.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest scripts/test-agent-contracts.py
```

`assets/mira/`、そのmanifest、asset validatorを触ったら:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/build-mira-world-assets.py  # world sourceを触った場合
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate-mira-assets.py
```

ミラのCodex hook、VS Code extension、VSIX package処理を触ったら:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest scripts/test-mira-codex-hook.py
node --test extensions/mira-companion/test/*.test.js
scripts/test-mira-vsix.sh
bash -n scripts/install-mira-vscode-extension scripts/devcontainer-post-start scripts/test-mira-vsix.sh scripts/test-mira-container-hook.sh
node --check extensions/mira-companion/src/extension.js
node --check extensions/mira-companion/src/game.js
node --check extensions/mira-companion/src/state.js
node --check extensions/mira-companion/src/world.js
node --check extensions/mira-companion/src/world-view.js
node --check extensions/mira-companion/media/world-runtime.js
```

`scripts/build-mira-icon-font.py`またはstatus bar glyphのsource mappingを触ったら、design-timeのPillow / fontToolsがある環境でfontを再生成し、生成済みWOFFも更新します。extension runtimeへこの2依存を追加してはいけません。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/build-mira-icon-font.py
scripts/test-mira-vsix.sh
```

## 参照（別プロジェクト向けテンプレ）

- `AGENTS_TEMPLATE.md`: project scope、3 lane、permission、single-writer integrationの共通テンプレ
- `project/`: `.agent`共通contract、Codex / Claude / Grok native role、failure recovery runbookを含むcopy source

## 模擬運用で得た知見（反映先）

native運用のfailure recoveryは`project/docs/agents/runbook.md`へ集約します。旧wrapper固有の`nohup`、session、log追跡は`docs/agents/legacy-second-agent-runbook.md`だけへ残します。

## second-agent はどこにある？

- 共通エンジン: `scripts/second-agent`（`SA_BACKEND=codex|claude` で挙動を切り替え）
- シム: `scripts/codex-second-agent`（Codex）/ `scripts/claude-second-agent`（Claude Code）
- イベントフィルタ: `scripts/codex-second-agent-filter.py` / `scripts/claude-second-agent-filter.py`
- 互換運用: `docs/agents/legacy-second-agent-runbook.md`
