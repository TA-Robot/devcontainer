# Architecture Notes

## Positioning

このリポジトリは、次を提供する基盤です。

- 高権限 devcontainer
- native-first multi-agent実行方針と、新しいcontrol plane入口`agentctl`
- feature-frozenなlegacy second-agent wrapper（移行期間のみ）

目的は **trusted local development を速くすること** であり、未検証コードを隔離する sandbox を提供することではありません。

## Trust Boundary

この基盤の前提は次のとおりです。

- devcontainer はホスト資格情報をマウントする
- AI 認証情報は CLI の標準パスへ直接 bind mount して使う（Claude Code は `~/.claude` と `~/.claude.json`、Grok Buildは`~/.grok`をmountする）
- optional API key環境変数は`remoteEnv`でeditor/terminal processへ渡し、build済みimage ENVには保存しない
- AI CLI本体はホストからmountしない。stableはimage pinを使い、edgeだけ検出したhost versionをcontainer向けnpm packageまたは公式binaryとして起動時導入する
- devcontainer は `docker-in-docker` 前提の高権限設定で動く
- 通常`codex` / `claude` / `grok`はapproval / sandboxを維持し、`codex-trusted` / `claude-trusted` / `grok-trusted`だけが明示的にbypassする
- セカンドエージェントも常に権限バイパスを付ける

したがって、「安全」は **強い隔離** ではなく **信頼済み環境の中でスコープ事故を減らす** という意味に限定されます。

## Stable / Edge Toolchain

認証情報のbind mountとCLI配布は別レイヤーです。stableが既定で、起動時にhost CLIをprobeせずpackage installもしません。

```text
DEVCONTAINER_AI_CLI_CHANNEL=edge
  -> host CLI --version
  -> ~/.cache/devcontainer-ai-cli/versions.env
  -> read-only bind mount
  -> postStartCommand
  -> /opt/devcontainer-ai-cli (container OS/CPU向け npm package / Grok binary)
  -> /usr/local/bin/codex|claude|grok wrapper
```

ホストのpackage directoryやexecutableを直接共有しない理由は、hostとcontainerでOS / CPU / Node.js配置が異なり得るためです。stableの正本はDockerfileとFeature lockです。edgeはcanaryであり、`agentctl doctor --json`のcapability probeに合格したCLIだけを利用します。詳細は[`toolchain.md`](toolchain.md)を参照してください。

## Target Multi-agent Architecture

対話、planning、read-only fan-outはprovider-native subagentを使います。通常writeは同一container内のjob単位worktree、強い隔離が必要なtaskはoptional isolated runtimeへrouteします。共通層はconversationを再実装せず、job / attempt、immutable base SHA、workspace/process/resource lease、structured resultだけを所有します。

正本は[`ADR-0001`](adr/0001-native-first-multi-agent-execution.md)、比較scenarioは[`representative-scenarios.md`](agents/representative-scenarios.md)です。

### Project contract (Phase 2)

target projectのcopy sourceは`project/`です。

```text
project/
├─ AGENTS.md
├─ CLAUDE.md                  # @AGENTS.md bridge
├─ .agent/
│  ├─ config.json
│  ├─ roles/{researcher,implementer,reviewer}.md
│  ├─ schemas/{task,result}.schema.json
│  └─ examples/
├─ .codex/
│  ├─ config.toml
│  └─ agents/*.toml
├─ .claude/agents/*.md
├─ .grok/agents/*.md
└─ docs/agents/runbook.md
```

`.agent`はprovider-neutralなsource of truthです。Codex / Claude / Grok定義はnative discovery pathへ置くthin mappingで、project policyを複製しません。Claude Codeは`AGENTS.md`を直接loadしないため、`CLAUDE.md`が先頭で`@AGENTS.md`をimportします。

定義形式の根拠はCodex公式の[Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents.md)、Claude Code公式の[Create custom subagents](https://code.claude.com/docs/en/sub-agents)と[project memory](https://code.claude.com/docs/en/memory)、xAI公式の[Grok Build subagents](https://docs.x.ai/build/features/subagents)と[project rules](https://docs.x.ai/build/features/project-rules)です。providerのformatが変化した場合は、このthin mappingとcapability testだけを更新します。

task / resultはJSON Schema draft 2020-12、`schema_version = 1`です。taskはfull `base_sha`、lane、permission profile、relative scope、acceptanceを固定します。resultはstatus、full `head_sha`、changed paths、dirty state、checks、risks、followupsを返します。brokerはprovider申告を信頼せずGitからSHA / path / dirty stateを再計算します。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate-agent-contracts.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest scripts/test-agent-contracts.py
```

failure recoveryとsingle-writer integrationは`project/docs/agents/runbook.md`、legacy wrapper操作は`docs/agents/legacy-second-agent-runbook.md`へ分離します。

### Job / process fabric (Phase 3a–3e)

`agentctl 0.7`はproject UUID、SQLite job / attempt state、immutable base SHA、job-ID branch、private worktree lease、Codex / Claude / Grok adapter、result/Git照合、明示clean retryを実装します。foregroundに加えて、owner-only Unix socketのlocal supervisor、専用runner、detach、PID/start-time照合、heartbeat、process-group cancel、startup orphan reconciliationを持ちます。さらにresource class別capacity lease、priority + aging付きのdurable queue、job固有Compose namespace、integration port lease、validated dependencyを順に集めるread-only integration report、bounded/redacted log view、terminal log retention evidence、conservative GC inventoryを同じtransactional stateへ統合します。stateとjob worktreeはnamed volume`/var/lib/agentctl`へ置き、repository runtime fileとcontainer rebuildから分離します。

queue metadataは永続化しますが、provider credentialを含み得るdispatch environmentはagentdのmemoryだけに保持します。agentd再起動後のqueued jobは`awaiting_resubmit`として可視化し、同じdetach commandの再送で起動情報を補充します。secretをDBへ保存して完全自動resumeしたふりはしません。

`job collect`はmerge/pushを行いません。target SHAに対するcommit候補、dependency order、path overlap、checks/risksとstructural blockerをimmutable reportへ固定し、integration方法と意味的競合の判断はsingle writerへ残します。

`job logs`はcanonical attempt pathから最大1 MiB / 1000行までのtailだけを読み、known token、authorization header、secret名付きassignment、現在processが保持するsecret値をbest-effortでredactします。raw log自体をredactしたとは主張しません。正常にproviderが閉じた時点でraw logを最大8 MiB、detached runner終了後は1 MiBのtailへ原子的に制限し、別々のretention evidenceへ元サイズと保持結果を記録します。supervisor logはstdout/stderrのinodeを維持したまま2 MiBのlive tailへ回します。未解決なのは実行中provider logの一時的な増加です。

`gc --dry-run`は削除commandではありません。validated state、terminal attempt、process/lease不在、canonical worktree/branch/Git common-dir identity、clean tree、canonical evidence、明示的なcollection integration proof、Compose project labelの残存resource不在を全て満たしたjobだけへ候補actionを返します。registered workspaceが移動済み、Dockerを照合できない、pathやDB evidenceが矛盾する場合はjob単位でblockし、global inventory自体は継続します。

### Isolated runtime pilot (Phase 4a)

Lane Iはstable adapter未選定で、capacity既定値を0のまま維持します。`benchmark-isolated-runtime-pilot.py`はstandalone `sbx`とDocker Agent pluginをread-only probeし、未導入を成功扱いしません。比較可能なlocal fixtureとして、committed Git bundleだけを入力し、outer network/credential/workspace/host socketを渡さないdisposable private-DinD containerからresult bundleを回収します。5 sampleはp95約4.3秒で完走しましたが、outer containerが`--privileged`でhost kernelを共有するためsecurity boundaryとしては不採用です。測定値と次の`sbx --clone` gateは[`isolated-runtime-pilot-2026-08-12.md`](agents/isolated-runtime-pilot-2026-08-12.md)を正本とします。

Codexのsafe sandboxではlinked worktree外のGit common metadataがread-onlyになることを実測しました。common dirをwritable rootに足す代わりに、providerは`ready_for_commit`とdirty pathを返し、brokerがscope / HEAD / pathを再計算してverified pathだけをcommitします。詳細は[`agentctl.md`](agentctl.md)です。

## Legacy Scope Model (feature-frozen compatibility)

セカンドエージェント（`codex-second-agent` / `claude-second-agent`）の sub-agent (`--agent` が `default` 以外) は、configured workspace を基準に動かします。スコープ制御は共通エンジン `second-agent` に実装され、両バックエンドで共有されます。

- `workspace init <path-to-project-git>` を必須にする
- runtime state (session / logs / worktrees) は target workspace 側へ置く
- `workspace init` の設定は control repo 側へ置く
- sub-agent の `--cd` / `--add-dir` は workspace 内だけを許可する
- workspace 内の相対パスは agent worktree 側へ写像する
- backend ごとに state / worktree を分離する（codex: `.codex-second-agent` + `agent/<name>` ブランチ / claude: `.claude-second-agent` + `claude-agent/<name>` ブランチ）
- claude には `--cd` が無いため、wrapper が effective_cd へ `cd` して実行ディレクトリを合わせる

これは wrapper レベルの **運用境界** です。OS-level isolation ではありません。

## Legacy Target-Project Layout (do not copy for new projects)

target project 側では、sub-agent が読む運用情報を **workspace 内** に置きます。

```text
<target-project-git>/
  AGENTS.md
  docs/
    agents/
      runbook.md
      decisions.md
      plan.md
      tickets/
        task-ticket.template.md
        ready/
        running/
        done/
```

理由:

- `workspace init <path-to-project-git>` 後も runbook / tickets / decisions をそのまま参照できる
- runtime state が target workspace 側へまとまり、別 control repo からでも resume できる
- `--add-dir` で workspace 外を追加する必要がない
- manager と sub-agent で参照する正本がズレにくい

## Legacy Operating Modes

以下は既存stateの互換説明です。通常手順の正本は[`legacy-second-agent-runbook.md`](agents/legacy-second-agent-runbook.md)であり、新規projectは上のPhase 2 contractを使います。

どちらの例も `codex-second-agent` を `claude-second-agent` に置き換えれば Claude バックエンドで同じように動きます（CLI 表面は共通）。

### 1. Recommended: target project git root as workspace

```bash
codex-second-agent workspace init <path-to-project-git>
codex-second-agent --agent implementer "..."
```

- 通常 `--cd` は不要
- docs / tickets も workspace 内に置く
- `.gitignore` には `.codex-second-agent/` `.codex-worktrees/` `.claude-second-agent/` `.claude-worktrees/` を入れる

### 2. Allowed: parent repo as workspace, subdir via `--cd`

```bash
codex-second-agent workspace init .
codex-second-agent --agent implementer "..." -- --cd packages/api
```

> claude バックエンドでも `-- --cd packages/api` は同じ意味で使えます。claude 自体に `--cd`
> フラグは無いので、wrapper が指定サブディレクトリ（worktree 内へ写像済み）へ `cd` して実行します。

- monorepo の一部だけを触らせたいときに使う
- `--cd` / `--add-dir` は workspace 内のみ許可

## Non-Goals

この基盤の非目標:

- untrusted code execution の隔離
- host secrets を渡さない実行環境
- policy enforcement を越えたセキュアコンテナ境界の提供

それが必要なら、credential mount を外した別 devcontainer / VM / remote sandbox を使うべきです。

## Known Limitations（既知の限界・設計上のトレードオフ）

これらは「trusted local development を速くする」目的のために受け入れているトレードオフです。

- **スコープ ≠ 隔離**: workspace 制限は accident-reduction であり security boundary ではない。実行は常にホスト権限フル。
- **default エージェントのスコープ**: `--cd`/`--add-dir` は default でも既定で実行対象 repo 内に制限する（`--allow-outside-workspace` / `<PREFIX>_ALLOW_OUTSIDE=1` で opt-out）。ただし worktree 隔離・workspace 必須化・セッション分離は `--agent` 非 default のときだけ効く。
- **状態は対象 repo の作業ツリー内に同居させる（意図的な設計）**: `.<be>-second-agent/` 等を target workspace 配下に置く。これは「その repo の開発に必要なデータを、その repo に同居させる」という方針であり、中央集約（例: `~/.local/state`）にしない。集約は際限なく貯まって管理不能になりやすく、どのデータがどの repo のものか追えなくなるため。誤コミットは `workspace init` の `.gitignore` 自動補完で防ぐ。
- **セッション同一性はパスの sha256**: repo を移動/rename すると key が変わり既存セッションが孤立する。シンボリックリンク経由など別パスで同一 repo を指すと resume 共有が壊れ得る。
- **固定モデルはコード直書きの既定**: 陳腐化し得る（`<PREFIX>_MODEL` で上書き可）。
- **edge CLI version同期は起動時**: edge実行中のcontainerはhost CLI updateを即時検知しない。stableは起動時同期を行わない。
- **legacy wrapperのログは無制限・機微を含み得る**: ローテーションなし。prompt/response 全文を保存。`umask 077` で所有者限定にはする。`agentctl`側の別contractは上記Phase 3eと`docs/agentctl.md`を参照する。
- **バックエンド抽象はアドホック**: 変数群 + `case` 分岐。3 つ目を足す前にアダプタ化を検討する余地がある。
- **中核ロジックが bash**: パス正規化・スコープ判定など間違えてはいけない処理を bash で実装している。将来はパス計算を別言語ヘルパへ切り出す候補。
- **並行性**: 同一 agent の同時実行は `flock` で直列化（flock が無い環境はベストエフォート）。
