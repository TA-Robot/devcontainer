# ミラ visual asset contract

## 現在のscope

このdirectoryは、VS Code companion extensionで使うミラのidentity anchorとpixel-art framesを提供します。extension本体は`extensions/mira-companion/`、Codex / agentctl activity bridgeの互換entrypointは`scripts/mira-codex-hook.py`、連携contractは`docs/mira/architecture.md`を正本とします。

## Inventory

| 種類 | path | 内容 |
|---|---|---|
| original reference | `assets/mira/reference/mira-original-reference.png` | ユーザー提供のdesign reference |
| character sheet | `assets/mira/character-sheet/mira-character-sheet.png` | front / 3/4 / back / face / expressions |
| chroma sheets | `assets/mira/spritesheets/*-chroma.png` | image generationのsource、各4×4 |
| alpha sheets | `assets/mira/spritesheets/*-alpha.png` | 背景除去済みのsource sheet |
| runtime frames | `assets/mira/sprites/<set>/*.png` | 256×256 RGBA、合計80枚 |
| animation previews | `assets/mira/previews/*.gif` | idle、walk、typing、delegationの目視確認用 |
| world source | `assets/mira/worlds/workshop-source.png` | image generationで保持する再構築source |
| world runtime | `assets/mira/worlds/workshop.png` | 1536×192 RGBAのbottom-panel backdrop |
| manifest | `assets/mira/manifest.json` | animation、pose、companion、world topologyの正本 |

生成sheetは1254×1254で、4では割り切れないうえ、生成された各poseの中心も等間隔ではありません。runtimeでatlasを直接4等分せず、行・列の透明ガターを境界として各poseを分離し、nearest-neighborで共通scaleへ縮小した`sprites/`以下を使用します。

animation frameは、最大連結成分（ミラ本体と机など）の水平中心を`x = 128`、接地線を`y = 248`へ揃えています。単純な等分cropへ戻すと、frameごとの横流れや隣接poseの切れ端が再発するため、再生成時もこのanchorを維持してください。anchor値は`manifest.json`の`frame.anchor`が正本です。

## Sets

| set | frames | 用途 |
|---|---:|---|
| `core-motion` | 16 | idle、左右walk、wave |
| `work-actions` | 16 | typing、terminal、research、testing |
| `status-emotions` | 16 | thinking、approval、success、errorなど |
| `orchestration` | 16 | planning、delegation、report、integration |
| `companions` | 16 | researcher、implementer、reviewer、tester |

## Suggested Codex hook mapping

| event / state | visual |
|---|---|
| no active session | `core-motion/idle-*` |
| `SessionStart` | `status-emotions/ready.png` |
| `UserPromptSubmit` | `status-emotions/thinking.png` |
| `PreToolUse` for edit | `work-actions/typing-*` |
| `PreToolUse` for shell | `work-actions/terminal-*` |
| read / search tool | `work-actions/research-*` |
| test command | `work-actions/testing-*` |
| `PermissionRequest` | `status-emotions/approval.png` |
| `SubagentStart` | `orchestration/delegate-*` + role companion |
| `SubagentStop` | `orchestration/report-receive.png` |
| validation | `orchestration/validate.png` |
| successful `Stop` | `status-emotions/success-jump.png` or `orchestration/complete.png` |
| failed tool / run | `status-emotions/error.png` then `retry.png` |
| `SessionEnd` | idleへfade |

hook payloadからprompt、tool arguments、transcript本文、private reasoningをvisual layerへ渡しません。event name、session ID、agent type、sanitized tool category、timestamp程度に制限します。

## Rendering guidance

現在の主rendererはbottom panelのWebview Viewです。1536×192のworld backdrop上で256×256 RGBA frameを38–68pxへ縮小し、manifestの共通anchorを基準に移動させます。`scripts/build-mira-icon-font.py`が作る29 glyphのWOFFは、worldを再表示するstatus-bar toggleだけに残します。

- worldとspriteの両方へ`image-rendering: pixelated`を指定する。
- backdropは`object-position: center bottom`とし、短いpanelでも歩行線を優先する。
- `subtle`は最大3fps、idleは最大0.75fps。`full`も最大6fpsに抑える。
- `workbench.reduceMotion=on`、motion off、window非focus、hidden webviewでは停止する。
- frameは全面差し替えし、前frameの透明pixelを残さない。
- 16px status glyphは上半身72%のmonochrome line artで、独自色を付けない。
- hook bridgeが落ちてもCodexを止めない。visual integrationは常にfail-openにする。
- 台詞はsanitized stateと固定contentから選び、hidden reasoningを表示しない。

## Packaging guidance

extension packageには`manifest.json`、`sprites/`以下、`worlds/workshop.png`、生成済み`mira-icons.woff`を含めます。character sheet、chroma source、alpha source、`workshop-source.png`、design-time Python packageはregeneration artifactなのでVSIXから除外します。

`previews/`のGIFは目視確認用です。各frameは全面破棄（GIF disposal method 2）で保存しています。runtimeではGIFを直接state machineにせず、manifestで指定したPNG frameを切り替えます。

original referenceと生成物を外部配布する前に、reference imageの利用権を確認してください。他projectのassetをそのままコピーせず、今回生成したオリジナルassetを使用します。

## Validation

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate-mira-assets.py
```

validatorはmanifest、全runtime path、80 frame、1536×192 world、PNG dimensions、RGBA color typeを検査します。worldを再構築するときは先に次を実行します。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/build-mira-world-assets.py
```

## Regeneration record

生成にはbuilt-in image generation toolを使用しました。Image 1をoriginal identity reference、生成したcharacter sheetをImage 2のidentity / costume anchorとして、各sheetを独立promptで生成しています。背景はflat green chroma keyとして生成し、imagegen skillの`remove_chroma_key.py`でalpha化しました。

characterの最終prompt setは`docs/mira/image-generation-prompts.md`、worldの生成・composition edit記録は`assets/mira/worlds/README.md`に保存しています。
