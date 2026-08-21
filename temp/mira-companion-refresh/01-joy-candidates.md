# Mira Companion刷新: joy候補60案

検討日: 2026-08-11

## 評価原則

通常のcodingが100%、ミラはその上へ足す数%の楽しさです。候補は次の順で評価します。

1. **joy per pixel**: 専有面積に対して感情的な反応や意味があるか。
2. **zero interruption**: focus、keyboard、terminal、editor widthを奪わないか。
3. **earned response**: 状態を単に絵へ置換せず、interactionやsessionの記憶へ繋がるか。
4. **privacy by construction**: prompt、code、command、transcriptを保存せず成立するか。
5. **graceful absence**: 無効化してもcodingとCodexが一切壊れないか。

判定は`NOW`（今回実装）、`NEXT`（拡張点を用意）、`LATER`（素材・event不足）、`NO`（思想またはAPIに不適合）です。

## A. 1秒ごとの存在感

| # | 候補 | joyの核 | 判定 |
|---:|---|---|---|
| 1 | 16px custom Mira glyph | status barに本当にミラの輪郭がいる | NOW |
| 2 | glyph animation | 4 frameを静かに切り替え、状態だけでなく生命感を出す | NOW |
| 3 | 状態別silhouette | 調査、typing、test、委譲で姿勢が変わる | NOW |
| 4 | 1行の短い台詞 | 状態名の読み替えではなく、ミラらしい反応を返す | NOW |
| 5 | color sprite hover | 常時16px、見たい時だけ64px相当の本絵を見せる | NOW |
| 6 | transition reaction | 状態遷移時だけ一瞬違う表情を挟む | NEXT |
| 7 | rare idle line | 低確率の小ネタで機械的loop感を消す | NOW |
| 8 | completion pose | 完了時だけ専用silhouetteへ切り替える | NOW |
| 9 | approval tug | 承認待ちを小さな専用iconと台詞で知らせる | NOW |
| 10 | party count | subagent数を`+3`のように1 fragmentで伝える | NOW |

## B. 触る楽しさ

| # | 候補 | joyの核 | 判定 |
|---:|---|---|---|
| 11 | clickでMira Deck | 大画面を常設せず、遊ぶ時だけQuick Pickを開く | NOW |
| 12 | ハイタッチ | 完了や任意のタイミングで短い相互反応 | NOW |
| 13 | 頭をなでる | 小さな反応とbond、連打を要求しない | NOW |
| 14 | reaction wheel | `応援して / 落ち着こ / 祝お`を選べる | NOW |
| 15 | 「ひとこと」 | 現在状態に合う台詞を任意に引く | NOW |
| 16 | icon-only切替 | 最小1 glyphまで縮められる | NOW |
| 17 | motion切替 | auto / subtle / full / off | NOW |
| 18 | banter切替 | 台詞を消し、純粋な状態iconにもできる | NOW |
| 19 | session recap | 内容を読まず、回数と節目だけを短く振り返る | NOW |
| 20 | おやつを渡す | 日1回程度の小さなreaction、収集強制なし | NEXT |

## C. 長く一緒にいる意味

| # | 候補 | joyの核 | 判定 |
|---:|---|---|---|
| 21 | bond XP | 完了、test、委譲、interactionで少しずつ関係が育つ | NOW |
| 22 | bond level / title | 数字だけでなく関係性の呼び名が変わる | NOW |
| 23 | session rhythm | 多様な作業が繋がると一時的なsparkが育つ | NOW |
| 24 | daily cap | 連打や長時間労働を報酬最適化させない | NOW |
| 25 | badge collection | coding上の初めてを小さく記念する | NOW |
| 26 | 初green test badge | `はじめての青信号` | NOW |
| 27 | delegation badge | subagentとの協働を記念する | NOW |
| 28 | recovery badge | test fail後にpassした回復を記念する | NOW |
| 29 | long project badge | 日数やproject identityの安定化が必要 | LATER |
| 30 | costume unlock | color sprite素材の追加が必要 | LATER |

## D. Coding eventを遊びへ変換

| # | 候補 | joyの核 | 判定 |
|---:|---|---|---|
| 31 | session greeting | 毎回ではなくsession最初だけ挨拶 | NOW |
| 32 | green test celebration | test成功を短い喜びへ変える | NOW |
| 33 | red test response | 失敗を責めず「原因見えたね」に変える | NOW |
| 34 | red-to-green redemption | fail→passを特別なmomentとして扱う | NOW |
| 35 | edit craft metaphor | typing中を「組み立て中」など数種の台詞で表す | NOW |
| 36 | research detective lines | 調査を探偵モードとして演出 | NOW |
| 37 | terminal forge lines | command実行を工房モードとして演出 | NOW |
| 38 | subagent role parade | agent typeの安全なtaxonomyが必要 | LATER |
| 39 | turn completion capsule | 1 turnを小さな「完了moment」にする | NOW |
| 40 | safe activity summary | 調査・編集・testなどcategory回数だけ表示 | NOW |

## E. 小さな世界観

| # | 候補 | joyの核 | 判定 |
|---:|---|---|---|
| 41 | time-of-day greeting | 朝・昼・夜で空気を少し変える | NOW |
| 42 | deterministic daily line | 同じ日は同じ一言、毎reloadでガチャにしない | NOW |
| 43 | theme-native appearance | custom colorを押し付けずVS Code themeに溶ける | NOW |
| 44 | seasonal micro-event | 少量の追加台詞とbadgeで季節を感じる | NEXT |
| 45 | weekday desk mood | 月曜煽り等を避けた丁寧なcontent設計が必要 | LATER |
| 46 | workspace seed | projectごとにrare lineの出方が少し違う | NOW |
| 47 | rare easter egg | 低確率かつ1日上限で小ネタを出す | NOW |
| 48 | real weather | network、location、privacyに対し価値が低い | NO |
| 49 | ambient BGM | codingと音環境を奪う。標準機能にはしない | NO |
| 50 | sound effects | default offでも驚かせるriskが高い | LATER |

## F. ゲーム会社的な奥行き

| # | 候補 | joyの核 | 判定 |
|---:|---|---|---|
| 51 | 今日のテーマ | 達成ノルマでなく「丁寧にいこ」等のtoneを選ぶ | NOW |
| 52 | branching micro story | event categoryだけで進む短編 | NEXT |
| 53 | bug monster encounters | failureを敵に見立て、責めずに外在化する | NEXT |
| 54 | test boss battle | suite単位の安定IDと専用素材が必要 | LATER |
| 55 | subagent party personalities | role taxonomyとcompanion glyph素材が必要 | NEXT |
| 56 | release festival | Git / CI event bridgeが必要 | LATER |
| 57 | sticker album | badge一覧をQuick Pick内で見る | NOW |
| 58 | local moment log | code抜きで直近の節目だけを保存する | NOW |
| 59 | shareable result card | code、project名、privacyのreviewが必要 | LATER |
| 60 | content pack API | 台詞・badge・glyphを将来差し替え可能にする | NEXT |

## 集計

- `NOW`: 43案
- `NEXT`: 7案
- `LATER`: 8案
- `NO`: 2案

`NOW`は39個の別々な大機能を意味しません。1つのcompact core（glyph animation、event engine、local profile、Quick Pick deck）にまとめて実現できる小さな振る舞いです。
