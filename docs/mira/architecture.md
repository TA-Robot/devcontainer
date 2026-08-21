# Mira Companion v2 architecture

## Outcome

Mira Companion v2は、devcontainer内で動くCodexと、`agentctl`が管理するCodex / Claude / Grok jobの状態を、VS Code下部の**短い横長pixel-art world**へ変換するworkspace extensionです。

```text
container-managed Codex lifecycle hooks ─┐
  (/etc/codex/requirements.toml)          │
agentctl durable job transitions ─────────┤ provider / role / outcome only
                                         v
  mira-codex-hook compatibility entrypoint
  (sanitize + aggregate + bounded event ring, fail-open)
  -> ~/.local/state/mira-companion/state.json
  -> Mira Companion workspace extension
  -> bottom-panel Mira World
       event -> destination -> walk -> work animation
       idle -> occasional ambient walk
       milestone -> scenery growth
       earned breakpoint -> expiring one-click pop
  -> tiny status-bar reopen toggle
```

product contractは「worldを始めて遊ぶ」のではなく、**普段のcodingが自然にworldの出来事になる**ことです。会話と承認は各provider、job ownershipは`agentctl`、orchestration判断はprimary agentが所有し、extensionはsanitized activityの表示とlocalな進行だけを担当します。

60候補と採否は[`temp/mira-companion-v2/01-ambient-world-60.md`](../../temp/mira-companion-v2/01-ambient-world-60.md)、surface試行は[`02-experience-trials.md`](../../temp/mira-companion-v2/02-experience-trials.md)、実装sliceは[`03-build-plan.md`](../../temp/mira-companion-v2/03-build-plan.md)に残しています。0.2のstatus-bar-only案は`temp/mira-companion-refresh/`にhistoryとして残しますが、v2の仕様ではありません。

## Surface decision

`viewsContainers.panel`に1 container、そこへ`type: webview`の1 viewをcontributeし、`WebviewViewProvider`で描画します。

- Activity Barとsidebarは増やさない。
- bottom panelを横一杯使うが、内容は64px程度から240px以上までresponsiveにする。
- workspace初回、またはremote runtime rebuild後の初回だけ`miraCompanion.world.focus`で開く。remote側global storageのmarkerが残る通常reloadでは、VS Codeが記憶するcollapse / visibilityを尊重する。
- status barはicon-onlyのreopen toggle 1個だけにする。
- editor DOMへのCSS injection、floating overlay、notification toastは使わない。

VS Codeのpanelは補助情報を横方向に置けてユーザーが移動・最小化できる正式surfaceです。[Panel UX guideline](https://code.visualstudio.com/api/ux-guidelines/panel)の「常に見えていると仮定しない」を守り、非表示中もcodingやhookを止めません。custom viewは公式の[`viewsContainers` / `views` contribution points](https://code.visualstudio.com/api/references/contribution-points#contributes.viewsContainers)と[`registerWebviewViewProvider`](https://code.visualstudio.com/api/references/vscode-api#window.registerWebviewViewProvider)だけで実装します。

## World topology

runtime backdropは`assets/mira/worlds/workshop.png`、logical sizeは1536 x 192です。Miraの基準線は`y = 166`です。

| destination | x% | activity |
|---|---:|---|
| research library / telescope | 31 | read、search、調査 |
| planning pavilion | 41 | thinking、planning |
| coding workshop | 52–56 | edit、typing、shell |
| test signal gate | 60–63 | test、error、success |
| dispatch dock | 68–72 | approval、delegation、subagent |

stateが変わると現在位置からdestinationまで`walk-left` / `walk-right` frameで移動し、到着後にstate固有animationへ切り替えます。idle中は11–21秒程度の間隔でwaypointを選び、focusとmotion policyが許すときだけ散歩します。

background sourceはbuilt-in image generationで作った`workshop-source.png`です。全施設を中央の浅い帯へ再構成し、`scripts/build-mira-world-assets.py`で縦横比を壊さずruntime cropへ変換します。生成記録と再構築条件は`assets/mira/worlds/README.md`を正本とします。image-generation sourceはVSIXへpackageしません。

## Experience loops

### Work feedback loop

Codexのread、edit、shell、test、delegationと、`agentctl` jobのstart / success / failure / cancel / orphanが、地理的な移動、作業animation、短いHUD、test gateの色へ自動変換されます。ユーザーの追加操作は不要です。

subagent稼働中は最大4体のrole spriteを対応zoneへ出します。researcherは資料庫、reviewerは作戦卓、implementerは工房、testerはtest門へ配置し、同roleだけ少し横へずらします。Codex / Claude / Grokは小さな色dotとHUDのprovider countで区別します。extensionへ渡すのはopaque ID、provider / role enum、aggregate count、categoryだけで、agentの発言や作業内容は渡しません。

### Ambient loop

active workがない間も、Miraは低頻度でwaypointを歩きます。panel非表示、window blur、`motion=off`、`workbench.reduceMotion=on`ではtimerを止めます。absence penalty、streak loss、放置要求はありません。

### Earned one-click loop

常設buttonやmenuは置きません。次の区切りでだけMiraの近くに小さなbuttonが現れます。

- 新しいbadgeを自動獲得したとき
- red-to-green recoveryを検出したとき
- 6 activity以上を含むturn / sessionが完了したとき
- 3 activity以上の流れでtestが成功したとき

buttonは45秒で消え、押さなくても損失や未読表示はありません。clickはすでに起きた節目を短く祝うだけで、XP、badge、進行結果を変えません。test failureではbuttonを出さず、自動のrecovery-oriented feedbackだけを出します。

### Passive progression loop

bond、badge、rhythm、safe momentは自動eventだけで育ちます。daily automatic XPは12でcapし、作業量や長時間労働を最適化目標にしません。進行に応じて次の小さな景観差分を自動表示します。

- first sticker
- turn lanterns
- green test signal
- team pennant
- comeback star
- partner banner

v1のハイタッチ、なでる、ひとこと、reaction wheel、Mira Deck、interaction XPは削除しました。

## Components

| component | responsibility |
|---|---|
| `.devcontainer/codex-requirements.toml` | lifecycle eventをbridgeへ渡すcontainer-owned managed config |
| `.devcontainer/Dockerfile` | managed configとbridgeをsystem pathへ配置 |
| `scripts/agentctl_jobs.py` | durable job transition後にprovider / role / outcomeだけのMira eventをbest-effort emit |
| `scripts/mira-codex-hook.py` | Codex互換entrypoint。Codex hookとagentctl envelopeを分類し、機微情報を捨て、stateとbounded event ringをatomic write |
| `extensions/mira-companion/src/state.js` | filesystem contractをもう一段allowlist normalize |
| `extensions/mira-companion/src/game.js` | automatic bond、daily cap、rhythm、badge、safe moment、固定台詞 |
| `extensions/mira-companion/src/world.js` | state-to-destination、passive decoration、earned pop、webview snapshot allowlist |
| `extensions/mira-companion/src/world-view.js` | Webview View lifecycle、CSP、local asset URI、message allowlist |
| `extensions/mira-companion/media/world-runtime.js` | walk / work / ambient animation、responsive DOM renderer |
| `extensions/mira-companion/media/world.css` | short-band layout、VS Code theme integration、reduced-motion behavior |
| `extensions/mira-companion/src/extension.js` | state監視、profile persistence、provider更新、status toggle |
| `assets/mira/manifest.json` | character frameとworld topologyの正本 |
| `scripts/build-mira-world-assets.py` | retained sourceから1536 x 192 runtime backdropを再構築 |
| `scripts/build-mira-icon-font.py` | tiny reopen glyph用のchecked-in WOFFを生成 |
| `scripts/build-mira-vsix` | dependency-free VSIXへruntimeだけをpackage |
| `scripts/install-mira-vscode-extension` | remote editor CLIを検出してlocal VSIXを導入 |

## State contract

bridgeが書く`state.json`はschema version 1です。追加fieldは後方互換で扱います。state fileが存在しない場合は通常idleと区別してHUDへ`activity未接続`を表示します。bridgeからstateを受け取りactive workがない場合は`待機中`です。

```json
{
  "schemaVersion": 1,
  "revision": 1,
  "updatedAt": "2026-08-12T00:00:00Z",
  "status": "typing",
  "message": "実装してるよ",
  "event": "AgentJobStart",
  "toolCategory": "edit",
  "activeSubagents": 1,
  "activeAgents": [
    {
      "id": "opaque-agent-id",
      "provider": "grok",
      "role": "implementer",
      "status": "typing"
    }
  ],
  "providerCounts": {"codex": 0, "claude": 0, "grok": 1},
  "expiresAt": null,
  "source": "agentctl",
  "recentEvents": [
    {
      "id": "opaque-event-id",
      "at": "2026-08-12T00:00:00Z",
      "event": "AgentJobStart",
      "status": "typing",
      "category": "agent",
      "outcome": "unknown",
      "activeSubagents": 1,
      "provider": "grok",
      "role": "implementer"
    }
  ]
}
```

`recentEvents`は最大24件です。`state.js`はeventの`id / at / event / status / category / outcome / activeSubagents / provider / role`と、active agentのopaque ID / provider / role / statusだけを再allowlistします。`world.js`はそこからさらに描画用のnumber、enum、bounded labelだけをsnapshotへ作ります。

`agentctl`からbridgeへ渡すenvelopeは`mira_source / hook_event_name / session_id / attempt_id / provider / role`だけです。raw job / attempt IDはbridge内でhash化され、task objective、workspace / worktree path、command、result、failure reason、provider logはenvelopeへ入りません。bridge binaryの欠損、nonzero exit、1秒timeoutはpresentation failureとして無視され、broker stateやjob resultを変更しません。

複数sessionは`approval > error > success > delegating > active work > thinking > ready > idle`の順でaggregateします。別のagent jobが稼働中なら、完了済みjobのtransient stateでactive workを隠さず、terminal eventだけをreactionとして表示します。session ID、job ID、attempt ID、subagent IDはhash化します。

PostToolUseのtest成否は、structured JSON内に`exit_code`、`isError`、明示的な`status`がある場合だけ判定します。自然言語outputを解析せず、不明なら`unknown`のままにします。

## Local profile contract

VS Code `globalState`へ保存するのは次だけです。

- automatic bond XPと当日のcap消費
- sanitized category counters
- unlocked badge IDと時刻
- 最大20件の定型safe moment
- 最大96件の処理済みevent ID
- testの直前outcome
- transient rhythm

未知field、legacy interaction field、未知badge、長すぎるtextはnormalize時に捨てます。prompt、code、project名、command、tool outputはprofile schemaに存在しません。

## Motion, focus, and accessibility

- motion: `auto`（既定）/ `subtle` / `full` / `off`
- `auto`は`workbench.reduceMotion=on`なら停止、それ以外はsubtle。
- subtleはwork animation最大3fps、idle最大0.75fps。fullも最大6fps。
- window blur、hidden webview、collapsed panelではanimation / ambient timerを止める。
- runtime backdropとspriteは`image-rendering: pixelated`で描画する。
- panel heightが105px未満では台詞とsession detailsを隠し、状態とMiraを優先する。
- earned popだけbutton semanticsとfocus ringを持ち、結果は`aria-live=polite`で伝える。
- status itemにはbutton roleと状態labelを付ける。
- sound、modal、toast、constant animation notificationは使わない。

## Privacy and failure behavior

bridgeはprompt本文、tool arguments、shell command本文、tool result、transcript、private reasoning、raw session / job / attempt / agent IDを保存しません。`Bash` commandはtestまたはsecond-agentかをprocess内で分類するためだけに読み、永続化しません。`agentctl` emitterはAPI keyを含む親environmentをbridgeへそのまま渡さず、HOME / PATH / locale / Mira state設定だけをallowlistします。

state directoryは`0700`、JSONとlockは`0600`です。temporary fileからatomic replaceし、並行するCodex / agentctl eventは`flock`で直列化します。bridge内部で例外が起きてもexit 0で終了し、表示機能の故障がCodex、tool call、agentctl jobを止めないことを優先します。extension側もstate欠損、破損、期限切れ、1時間更新されないactive stateをdisconnected / idleとして扱います。

webviewはstrict CSPを設定し、extension mediaとMira runtime assetsだけをlocal resource rootにします。messageは`ready`と現在表示中popの`ackPop`だけを受け付け、arbitrary command execution経路を持ちません。

## Install and lifecycle

devcontainerの`postStartCommand`はhostとAI CLI versionを同期します。Mira VSIXはremote editor CLIが利用可能になる`postAttachCommand`で導入します。installerはPATH上のremote `code` / `cursor` / `codium`を優先し、必要なら`code-server` / `cursor-server`を検出します。同じversionが未導入の場合だけbuildし、install後のextension一覧まで検証します。

```bash
# packageだけ作る
scripts/build-mira-vsix

# 現在のremote editorへinstall
scripts/install-mira-vscode-extension

# 同じversionを強制再install
MIRA_COMPANION_FORCE_INSTALL=1 scripts/install-mira-vscode-extension
```

Codexはhook configをprocess / session開始時に読みます。image rebuild後はeditor windowをreloadし、新しいCodex sessionを開始します。`MIRA_COMPANION_ENABLED=0`はbridgeと自動導入を止め、`MIRA_COMPANION_INSTALL=0`はextension導入だけを止めます。

v0.4.0では`agentctl`のCodex / Claude / Grok job表示を追加しました。workspace初回とremote runtime rebuild直後に一度だけMira World panelを開き、同じruntimeでの以後のpanel open / collapseはVS Codeに任せます。v0.2のstatus-only UIやv0.1のActivity Bar iconが残って見える場合はeditor windowをreloadしてください。

## Dependency and removal record

追加したextension runtime dependencyはありません。runtimeはNode.js built-in module、VS Code API、plain browser DOMだけを使い、VSIXはPython標準ライブラリの`zipfile`で作ります。

generated world sourceからruntime PNGを再構築するdesign-time taskだけPillowを使います。Pillowは既存icon-font generatorでも使うdesign dependencyで、extension runtimeとVSIX buildには追加しません。削除する場合はworld sourceとbuilderを外し、manifestのworld backgroundを別のchecked-in 1536 x 192 RGBA assetへ向けます。

Mira全体を削除する場合は`.devcontainer/codex-requirements.toml`、`extensions/mira-companion/`、`assets/mira/`、Mira scriptsを削除し、`.devcontainer/devcontainer.json`の`postAttachCommand`とDockerfileのrequirements / hook copyを外します。導入済みextensionは`code --uninstall-extension asakura.mira-companion`で削除できます。

## Known limitations

- extension APIからbottom panelの正確な高さは固定できない。rendererは64px以上で段階的に情報を減らす。
- panelはTerminal / Problems / Outputと同じ領域を共有するため、ユーザーがcollapseしたらworldも見えない。status glyphから再表示できる。
- managed hookはこのdevcontainer内で起動したCodexだけを観測する。hostや別containerのCodexとはstateを共有しない。
- image / hook更新後も既に動いているCodex processは旧configのままなので、新しいsessionが必要。
- Claude / Grokの単独interactive CLI sessionは未接続。`agentctl` managed jobは3 providerとも接続済みで、Codexからlegacy `claude-second-agent`を起動した場合はcommand categoryで委譲を表示する。
- structured exit statusがないtest outcomeは`unknown`になる。
- extensionからagentをsteer、cancel、approveしない。操作系は別milestone。

## Verification

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/build-mira-world-assets.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate-mira-assets.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest scripts/test-mira-codex-hook.py
node --test extensions/mira-companion/test/*.test.js
node --check extensions/mira-companion/src/extension.js
node --check extensions/mira-companion/src/game.js
node --check extensions/mira-companion/src/state.js
node --check extensions/mira-companion/src/world.js
node --check extensions/mira-companion/src/world-view.js
node --check extensions/mira-companion/media/world-runtime.js
scripts/test-mira-vsix.sh
scripts/test-mira-container-hook.sh devcontainer-smoke:latest
```
