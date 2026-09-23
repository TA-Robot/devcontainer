# Product brief

このfileは「何を、誰のために、なぜ作るか」の正本です。code、task envelope、reviewが迷った時に戻る場所であり、仕様書やbacklogではありません。

- maintainer: primary agent。通常作業中に更新し、ユーザーへ記入を求めない。
- update trigger: kickoff、milestone境界、assumptionの確定 / 棄却、ユーザーが方向を変えた時。
- status: `<<draft | agreed | revising>>`
- last reviewed: `<<YYYY-MM-DD>>`

不明な箇所は推測で埋めず、`unknown`と書いて`assumptions.md`へ仮説として移します。ユーザーの発言、code、観測に由来する記述と、primaryの推論は区別します。

## Problem

- 解く問題: `<<one or two sentences>>`
- 今それが起きている証拠: `<<observation, user statement, metric; or unknown>>`
- なぜ今か: `<<trigger, deadline, dependency>>`
- 解かなかった場合: `<<cost of inaction>>`

## Users and context

| user | 状況 / 制約 | 片付けたい用事 | 今の代替手段 |
|---|---|---|---|
| `<<primary user>>` | `<<environment, skill, frequency>>` | `<<job to be done>>` | `<<workaround, competitor, nothing>>` |

- 意図的に対象外にするuser: `<<non-users and why>>`
- 影響を受けるが操作しない人（運用者、第三者、data subject）: `<<stakeholders>>`

## Outcome and quality bar

- userにとっての成功: `<<observable change in the user's world>>`
- product principles（trade-off時の優先順）: `<<e.g. correctness over speed of release>>`
- 体験の質として守るもの: `<<first-run, latency, clarity, accessibility, trust>>`

## Success signals

各signalは`hard guard / cost cap / planning prior / hypothesis`のどれかとして扱い、根拠のない目標値を既定にしません。

| signal | 測り方 | 現在値 | 期待 | role | 見直す条件 |
|---|---|---|---|---|---|
| `<<signal>>` | `<<command, event, manual check>>` | `<<value or unmeasured>>` | `<<direction or value>>` | `<<role>>` | `<<invalidation evidence>>` |

## Scope

- in scope: `<<capabilities>>`
- non-goals: `<<explicitly not doing, with reason>>`
- constraints: `<<technical, legal, budget, timeline, platform>>`

## Directions considered

kickoffや大きな方向転換で比較した案を残します。選んだ理由と、捨てた案が再浮上する条件を書きます。

| direction | 核となる考え | 強み | 弱み / risk | 判定 |
|---|---|---|---|---|
| `<<name>>` | `<<core idea>>` | `<<why it could win>>` | `<<why it could fail>>` | `<<chosen / rejected: reason / revisit when ...>>` |

## Links

- 前提と検証: `docs/product/assumptions.md`
- milestoneと送った項目: `docs/product/roadmap.md`
- 長く有効な判断: `docs/agents/decisions.md`
