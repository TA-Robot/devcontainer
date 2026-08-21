# Mira Companion v2: ambient world候補60案

検討日: 2026-08-12

## 今回の前提

v1の中心だった「小さなstatus iconをclickしてMira Deckを開き、なでる・ハイタッチする」は廃止する。仕事中のユーザーへ遊ぶ意思決定を要求した時点で、companionではなく別taskになるため。

v2の中心は次の一文とする。

> プログラミング活動が、bottomの小さな世界でミラの移動・仕事・休息・仲間の出入りとして自動的に翻訳される。

判定:

- `CORE`: v2の核として今回実装
- `SUPPORT`: 核を支えるため今回実装
- `NEXT`: contractだけ壊さず残し、次段階で追加
- `NO`: 意図的に実装しない

## A. 横長の世界そのもの

| # | アイデア | 意味 | 判定 |
|---:|---|---|---|
| 1 | Mira World bottom strip | Panel一本を横長の小世界にする | CORE |
| 2 | 5つの仕事zone | library / planning desk / workshop / test gate / dispatch dockを一枚のmapに置く | CORE |
| 3 | 中央の通り | zone間を歩く移動そのものを生命感にする | CORE |
| 4 | camera追従 | Miraが端へ行くとmapを少しpanする | NEXT |
| 5 | foreground / background二層 | 手前の草・柵と奥の建物を速度差で動かす | NEXT |
| 6 | panel高さreflow | 低い時はmapだけ、高い時は空と遠景も見える | SUPPORT |
| 7 | theme色の薄いoverlay | VS Code themeと衝突せず馴染ませる | SUPPORT |
| 8 | 朝昼夜の照明 | networkなしでlocal timeから空気だけ変える | CORE |
| 9 | workspace固有accent | hashから旗・植木・ランプの組み合わせを安定選択 | NEXT |
| 10 | map選択menu | ユーザーへ最初から選択を迫るため初期版では作らない | NO |

## B. Programming eventを場所へ翻訳

| # | アイデア | 意味 | 判定 |
|---:|---|---|---|
| 11 | thinking → planning desk | 考えている間は地図を広げる | CORE |
| 12 | research → library | 読み取り・検索で本棚へ移動する | CORE |
| 13 | typing → workshop | 編集中は机で組み立てる | CORE |
| 14 | terminal → forge | shell実行を小さな工房の稼働として見せる | CORE |
| 15 | testing → signal gate | test中はsignalが点滅する | CORE |
| 16 | delegating → dispatch dock | subagentを送り出し、戻りを待つ | CORE |
| 17 | approval → mailbox | 要確認を赤い通知ではなく待っている姿で表す | CORE |
| 18 | success → overlook | 完了後だけ高台へ一瞬移動し、光が流れる | CORE |
| 19 | error → repair corner | failureを責めず、道具箱を開く演出へ外在化 | CORE |
| 20 | recovery → bridge relight | fail後のpassで消えた灯りが順番に戻る | NEXT |

## C. 何も操作しない時の生命感

| # | アイデア | 意味 | 判定 |
|---:|---|---|---|
| 21 | deterministic idle walk | 立つ・2歩移動・眺めるをworkspace seedで選ぶ | CORE |
| 22 | bench休憩 | 長いidleで座るが、怠け扱いはしない | CORE |
| 23 | prop inspection | 看板・植木・lampをときどき覗く | CORE |
| 24 | tiny delivery cart | shell/testが多い時だけ背景を横切る | NEXT |
| 25 | window lights | activityに応じて建物の窓が一つずつ灯る | CORE |
| 26 | pixel dust | active時だけ少量の粒が流れる | SUPPORT |
| 27 | ambient NPC silhouettes | 内容を持たない背景住人が稀に通る | NEXT |
| 28 | subagent companion arrival | activeSubagents分だけ小さな仲間spriteを出す | CORE |
| 29 | rare discovery glint | researchが続いた時だけ遠景に光る点を出す | NEXT |
| 30 | 常時BGM | focusと音環境を奪うため作らない | NO |

## D. earnedなワンクリックだけ

| # | アイデア | 意味 | 判定 |
|---:|---|---|---|
| 31 | completion pop | 長いturn完了後だけMiraの上に小さな`!`/sparkが出る | CORE |
| 32 | clickで一拍celebrate | popを一度押すとwave / jumpし、すぐ消える | CORE |
| 33 | no menu interaction | clickしても選択肢を出さず一動作で完結する | CORE |
| 34 | auto-expire | 押さなくても消え、損失もstreakもない | CORE |
| 35 | recovery token | red→green時だけ工具のsparkを回収できる | NEXT |
| 36 | team return parcel | subagent完了後に小包popが一度出る | NEXT |
| 37 | release lantern | release / CI bridgeが入った将来だけ灯籠を点ける | NEXT |
| 38 | approval button | Miraからapproveさせるのは責務混同なので作らない | NO |
| 39 | なでる / ハイタッチ常設 | ユーザーへ遊びtaskを要求するため削除 | NO |
| 40 | missed interaction log | 押さなかったことを記録・表示しない | NO |

## E. 長期的に世界が育つ

| # | アイデア | 意味 | 判定 |
|---:|---|---|---|
| 41 | automatic decoration unlock | codingの節目でmapの小物が自然に増える | CORE |
| 42 | first test lamp | 最初のtest成功で青いlampが常設される | CORE |
| 43 | research bookshelf | 調査の節目で本が一冊増える | NEXT |
| 44 | builder tool rack | editの節目で工具が増える | NEXT |
| 45 | team bench | delegationの節目で仲間用benchが増える | NEXT |
| 46 | recovery flower | fail→passの記憶を花として残す | NEXT |
| 47 | safe memory postcards | code抜きの節目を背景の写真立てにする | NEXT |
| 48 | bond数値の常時表示 | 生産性meterに見えるためmain surfaceから外す | NO |
| 49 | currency / shop | grindingと選択taskを生むため作らない | NO |
| 50 | streak / 未達penalty | 長時間労働と不安を誘発するため作らない | NO |

## F. Codingを主役に保つsystem設計

| # | アイデア | 意味 | 判定 |
|---:|---|---|---|
| 51 | status iconをpanel toggle化 | status barは世界の開閉と接続状態だけへ縮退 | CORE |
| 52 | first attachだけworldを開く | 毎回focusを奪わず、存在には気づける | SUPPORT |
| 53 | VS Codeが覚えたpanel状態を尊重 | 閉じたら勝手に再openしない | CORE |
| 54 | responsive 64–240px | 高さを固定できないAPI制約をscene cropで吸収 | CORE |
| 55 | hidden/unfocusedでanimation停止 | CPUと視覚ノイズを抑える | CORE |
| 56 | reduced motion完全対応 | walkをfade/teleportへ、particleを止める | CORE |
| 57 | no toast / no badge spam | 通知はworld内だけで完結する | CORE |
| 58 | privacy-safe event only | prompt / code / command / transcriptを読まない | CORE |
| 59 | stale stateの安全なidle復帰 | Codex終了後に働き続ける誤表示を防ぐ | SUPPORT |
| 60 | one-switch disable | extension/world/hookを既存envで完全停止可能 | SUPPORT |

## 集計

- `CORE`: 31
- `SUPPORT`: 6
- `NEXT`: 15
- `NO`: 8

31個を別々のfeatureとして作るのではない。今回の実装単位は次の5つへ圧縮する。

1. responsive bottom webview world
2. event → destination state machine
3. ambient movement scheduler
4. earned completion pop
5. automatic decoration / passive progression
