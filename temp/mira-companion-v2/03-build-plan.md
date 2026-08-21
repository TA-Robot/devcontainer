# Mira Companion v2: build plan

## Product statement

> Mira Worldはゲームを始める場所ではない。開発しているだけで、仕事の流れが小さな世界の営みとして見える場所である。

## Surface

- `viewsContainers.panel`に`Mira World`を一つだけcontributeする。
- contentは`WebviewViewProvider`で描画する。
- Panelは横幅が必要なsupporting contentという今回の用途に合う。
- VS Code APIではpanel高さをextensionが固定できないため、64pxから240px以上までCSSでreflowする。
- 初回attachで一度だけ開く。その後はVS Codeが保存したvisibilityを尊重する。
- status itemは`iconOnly`相当へ縮め、clickでworldを開くfallbackにする。

## Scene contract

logical mapは横1536、縦192を基準にする。

| state | destination x | zone | main motion |
|---|---:|---|---|
| idle / ready | 48–82%内を巡回 | street / bench | idle / walk |
| thinking | 28% | planning desk | thinking |
| research | 12% | library | research |
| typing | 48% | workshop | typing |
| terminal | 61% | forge | terminal |
| testing | 76% | signal gate | testing |
| delegating | 90% | dispatch dock | delegating |
| approval | 84% | mailbox | approval |
| success | 68% | overlook | success |
| error | 39% | repair corner | error / retry |

spriteは既存256x256 RGBAをwebview内で48–64px表示する。walk transitionでは既存walk-left / walk-rightを使い、到着後にstate animationへ切り替える。

## Event model

extension hostは既存sanitized stateをconsumeし、webviewへ次だけを送る。

- normalized status / label / category
- activeSubagents
- safe counters
- unlocked decoration IDs
- earned pop `{id, kind, expiresAt}`
- motion / theme / focus state

webviewへprompt、tool input、command、tool output、workspace absolute pathは送らない。

## Earned pop v2

今回実装するtrigger:

1. `Stop`か`SessionEnd`で、そのsessionにread/edit/shell/testが合計6event以上
2. test success
3. badge unlock

同じevent IDからは一度だけ生成する。45秒後に消える。click時は`acknowledgePop`だけをextension hostへ返し、専用animationを一回再生する。報酬差は付けない。

## Automatic decoration v2

- first completed turn → desk lamp
- first passed test → blue signal lamp
- first delegation → dock flag
- first recovery → flower pot（既存profile dataがある場合だけ）

decorationはCSS overlayと小さなpixel primitiveから始め、map sourceを破壊せず追加できるlayerにする。

## Asset plan

1. Mira referenceの黄色・水色・濃紫を拾った、人物なしの横長pixel-art workshop mapを生成。
2. open street laneと5 zoneのsilhouetteが48px Miraを邪魔しないか確認。
3. project用backgroundへcopyし、nearest-neighborでruntime sizeを作る。
4. manifestへ`worlds.workshop`を追加し、validatorでdimensions / RGBA / pathを検証。
5. mapが読みにくい場合だけ、建物のcontrastとground laneを一回targeted regenerateする。

## Implementation slices

1. `world.js`: pure destination / pop / decoration modelとtest。
2. `world-view.js`: WebviewViewProvider、CSP、URI変換、state message bridge。
3. `world.css` / `world-runtime.js`: responsive scene、movement、click、reduced motion。
4. `extension.js`: v1 Deck commandを外し、status itemをworld toggleへ変更。
5. `package.json`: panel container / webview view / command / settings / v0.3.0。
6. VSIX packagerへwebview runtimeとworld assetsを追加。
7. mock VS Code API test、pure model test、package contract test。

## Definition of Done

- Activity Bar itemは復活しない。
- bottom Panelに一つの横長Mira Worldだけがある。
- idleでも低頻度にMiraがmap内を動く。
- Codex stateごとに対応zoneへ歩いてから作業poseへ変わる。
- active subagentがmapへ現れる。
- 長い作業完了時だけone-click popが出て、menuなしで反応する。
- ハイタッチ・なでる・ひとこと・reaction wheelがUIとcommandsから消える。
- closed / unfocused / reduce motion時にanimation負荷が抑制される。
- prompt / code / commandをwebviewへ渡さないtestが通る。
- VSIX install、Docker managed hook、asset validatorが通る。
