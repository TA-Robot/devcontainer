# Assumptions and open questions

product判断が依存している前提と、ユーザーに確認する価値がある問いの正本です。ユーザーが明示しなかった視点は、ここで仮説として可視化してから扱います。

- maintainer: primary agent。advisor / reviewerの指摘は、primaryが採否を判断してから反映する。
- update trigger: kickoff、milestone境界、検証結果の取得、ユーザー回答。

## Assumption register

前提は、外れた時の影響が大きく確度が低いものから検証します。検証は会話より測定、prototype、既存データを優先します。

| id | assumption | kind | confidence | 外れた時の影響 | 最も安い検証 | status | evidence |
|---|---|---|---|---|---|---|---|
| A-001 | `<<statement>>` | `<<value / usability / feasibility / viability / risk>>` | `<<low / medium / high + why>>` | `<<what breaks>>` | `<<experiment, spike, question, data>>` | `<<untested>>` | `<<pointer or none>>` |

- kind: `value`（欲しいか）、`usability`（使えるか）、`feasibility`（作れるか）、`viability`（続けられるか：cost、運用、法務）、`risk`（害や失敗の仕方）。
- status: `untested`、`testing`、`supported`、`refuted`、`accepted-risk`。
- `refuted`は消さずに残し、brief / roadmapの何を変えたかを書く。

## Questions for the user

答えによって方向、scope、優先順が変わる問いだけを置きます。codeや調査で解ける問いはここへ置かず、primaryが自分で解きます。

| id | question | なぜ重要か（答えで何が変わるか） | 聞かない場合の既定 | status |
|---|---|---|---|---|
| Q-001 | `<<question>>` | `<<decision it unblocks>>` | `<<safe default and its risk>>` | `<<open / answered: summary>>` |

ユーザーへはまとめて短く聞きます。一度に全部を聞かず、現在のmilestoneをblockしているものを先にします。

## Perspective findings

advisorのlens reviewやprimaryの気付きのうち、採用・保留したものを残します。

| date | lens / source | finding | disposition | destination |
|---|---|---|---|---|
| `<<YYYY-MM-DD>>` | `<<lens>>` | `<<finding>>` | `<<fix-now / scheduled / accepted-risk / out-of-scope>>` | `<<roadmap, assumption id, task, none>>` |
