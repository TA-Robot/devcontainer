# Mira Companion v2: experience trial

## Trial A — Workshop Strip（採用）

```text
┌─ MIRA WORLD · 実装中 ─────────────────────────────┐
│  本棚        計画机       工房            test門       dock  │
│   ▤           ⌑           ⚒  ミラ→→       ◉           ⚑   │
│▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒│
└─ 今回: read 4 · edit 7 · test 1                         ┘
```

- 固定された一枚のmapなので、状態と場所の対応を覚えられる。
- Miraはteleportせず、短いwalk transitionで移動する。
- HUDは一行以下。codeやpromptは出さない。
- panelが低い時は空とHUDを隠し、地面とMiraを優先する。

## Trial B — Endless Journey

作業eventのたびに道が右へ伸びる横scroll型。見栄えは良いが、同じstateの居場所が毎回変わって状態把握が弱い。長時間作業を距離として可視化すると生産性scoreにも見えやすい。

判定: `NEXT`。release単位の特別sceneには使えるが、通常loopには使わない。

## Trial C — Desk Diorama

一つの机の中でMiraと道具だけが動く。省面積で安定するが、ユーザーが求める「mapの中で動く」感とsubagentの出入りを表現しづらい。

判定: 不採用。狭幅reflow時のfallback compositionとして一部利用する。

## 採用するinteraction grammar

### 通常時

- hover不要、click不要。
- activityに合うzoneへ移動し、そこでanimationする。
- idleは低頻度で歩く、座る、小物を見る。

### 区切りが生まれた時

```text
       ✦          ← 45–90秒で自動消失
      [!]
     Mira
```

- 長いturn完了、初test成功、recoveryなど「earned event」の時だけpopが出る。
- popをclickすると一回だけ専用animation。menu、Quick Pick、toastは出さない。
- clickしなくても結果・bond・unlockに差を付けない。

### panelを閉じた時

- status barは小さなMira iconと接続状態だけを残す。
- status item clickはMira Worldを開く。
- 勝手に再openしない。

## 廃止するv1 interaction

- `ミラ: ハイタッチ`
- `ミラ: なでる`
- `ミラ: ひとこと`
- reaction wheel
- 常設Mira Deck Quick Pick
- interaction XP / interaction daily cap

recap、badge、momentは消去せず、world内の受動的なscene decorationと短いHUDへ再配置する。
