# Roadmap

現在のmilestoneと、後へ送った項目の正本です。task単位の進捗やlogは置きません。

- maintainer: primary agent。
- update trigger: milestone開始 / 完了、`scheduled`へ送る判断、ユーザーによる優先順の変更。

## Current milestone

- name: `<<M1: walking skeleton>>`
- goal: `<<user-visible outcome>>`
- definition of done: `<<objective checks: commands, demo path, evidence>>`
- must: `<<minimum work to reach the goal>>`
- not doing: `<<explicitly deferred, with destination>>`
- risks being retired: `<<assumption ids this milestone tests>>`
- exit review: milestone完了時に`$review-product-direction`を実行する。

## Deferred items

active milestone外の発見は捨てずに分類して残します。分類は`fix-now / scheduled / accepted-risk / out-of-scope`です。`fix-now`はcurrent milestoneへ入れるため、ここには置きません。

| item | origin | disposition | revisit trigger | notes |
|---|---|---|---|---|
| `<<item>>` | `<<lens, review, user, incident>>` | `<<scheduled / accepted-risk / out-of-scope>>` | `<<milestone, signal, date, never>>` | `<<pointer>>` |

## Next milestone candidates

完了済みmilestoneのevidenceとassumptionの状態から、次の候補を並べます。候補の数を固定せず、userへの価値と検証したいriskで順位付けします。

| candidate | user value | risk retired | cost / dependency | recommendation |
|---|---|---|---|---|
| `<<candidate>>` | `<<value>>` | `<<assumption ids>>` | `<<estimate or unknown>>` | `<<next / later / drop + why>>` |

## Completed milestones

| milestone | date | outcome | evidence | learned |
|---|---|---|---|---|
| `<<name>>` | `<<YYYY-MM-DD>>` | `<<shipped / partial / stopped>>` | `<<commit, demo, check>>` | `<<what changed in brief or assumptions>>` |
