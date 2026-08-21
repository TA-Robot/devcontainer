# Mira Companion刷新: product plan

## 1. Product statement

> コーディング画面の高さも幅も増やさず、status barの16pxにミラが住む。普段は静かな相棒、hoverすると表情が見え、clickすると短く遊べる。長く一緒に開発すると、codeを読ませずに二人の小さな履歴だけが育つ。

## 2. Surface decision

### 採用: status bar 1 item

- workbenchの高さを追加消費しない。
- 16px custom product icon + 8〜14文字程度の短いtextだけを常設する。
- workspace全体のagent statusというstatus bar本来の用途に合う。
- hoverはcolor sprite、現在の一言、bond、party、直近momentを表示する。
- clickはQuick Pickの`Mira Deck`を開く。閉じれば占有領域はゼロへ戻る。

### 廃止: custom Activity Bar / Sidebar Webview

- 常設の専用sidebarは面積に対する情報量とinteractionが少ない。
- 初回自動openもしない。
- VS Code公式guidelineもcustom webviewを必要最小限にし、sidebar clutterを避けるよう求めている。

### 不採用: bottom panel

- 横長ではあるがterminal / Problems / Outputと同じ席を奪う。
- panelはユーザーが頻繁に最小化するため、常時相棒のsurfaceに向かない。
- APIで高さを小さく固定できず、「薄い」を保証できない。

## 3. Visual budget

```text
status bar height: VS Code既存値（追加0px）
Mira glyph:       16px monochrome / theme foreground
text:             icon-only または「ミラ · 実装中 ✦3」程度
animation:        subtle最大3fps、idle最大1fps
expanded UI:      hover tooltip / Quick Pickのみ
```

custom icon fontは既存pixel spriteのalpha silhouetteから生成します。VS Codeの`contributes.icons`で登録し、`StatusBarItem.text`内の`$(mira-...)`を切り替えます。独自色は使いません。

## 4. Core loops

### Moment loop（秒）

Codex event → Mira glyph / 短い台詞 → 仕事へfocusを戻す。

### Session loop（分〜時間）

調査・編集・test・委譲・完了がsafe momentとして蓄積 → rhythm / recap / badgeへ繋がる。

### Relationship loop（日〜週）

節目と任意interactionでbondが少し育つ → titleと台詞のvariationが増える。作業量ランキング、連続日数、未達penaltyは作らない。

## 5. V1 systems

### Compact renderer

- custom animated Mira glyph
- `full` / `compact` / `iconOnly` / `hidden`
- `auto` / `subtle` / `full` / `off` motion
- `workbench.reduceMotion`を尊重
- state別の短いlabelとoptional banter

### Rich hover

- 64px相当のcolor sprite
- 現在の台詞
- bond level / title
- session rhythm
- active subagents
- 直近のsafe moment

### Mira Deck

- ハイタッチ
- なでる
- ひとこと
- 今日のテーマ
- session recap
- sticker album
- display / motion切替

### Local game state

- promptやcodeを含まないcategory eventだけをconsume
- bond XP、level、title
- daily interaction cap
- session rhythm
- category counters
- badge unlock
- 最大20件のsafe moment log
- VS Code `globalState`へ保存

### Hook enrichment

- state fileへ最大24件のsanitized recent eventsをring bufferで含める
- event ID、time、status、category、outcome、subagent countのみ
- Bash testの`tool_response`からexit codeが明示される場合だけpass / failを分類
- raw response、command、promptは保存しない

## 6. Initial badges

| badge | unlock |
|---|---|
| はじめまして | first completed turn |
| 探偵モード | research 10回 |
| 組み立て上手 | edit 10回 |
| 青信号 | first passed test |
| 指揮者 | delegation 3回 |
| 立て直し名人 | test fail後にpass |
| にぎやか開発部 | active subagent 3人以上 |
| 相棒 | bond level 5 |

badgeは能力や生産性の評価ではなく、二人の思い出です。通知toastは出さず、status barの短いsparkとhover / albumだけで知らせます。

## 7. Non-goals

- code品質や作業量のscore化
- streak喪失、daily未達、連打報酬
- prompt / code / transcript分析
- notification spam
- soundのdefault有効化
- editor DOMへのunsupported CSS injection
- Codexのapprove / cancel / steer操作

## 8. Implementation order

1. Activity Bar contributionsとwebview providerを削除。
2. source spriteからmonochrome glyph fontを生成し、status bar animationを実装。
3. hookへbounded recent event envelopeとtest outcome分類を追加。
4. local profile / progression / badge engineをpure moduleとして実装。
5. rich hoverとMira Deckを実装。
6. package、asset、privacy、migration、reduced motionをtest。
7. versionを`0.2.0`へ上げ、installed `0.1.0`を更新。

## 9. Definition of Done

- Activity BarにMira containerが存在しない。
- 常設面積はstatus bar 1 itemのみ。
- 16px glyphがstateに応じて動き、motion offでは完全停止する。
- click interactionとlocal progressionがprompt / codeなしで成立する。
- state / profile / eventのprivacy testが通る。
- VSIX実installとDocker smokeが通る。
