# Lens: pre-mortem

## Purpose

このprojectやmilestoneが失敗したと仮定し、そこから原因を遡ることで、楽観的な計画では見えないriskを表に出す。

## Use when

kickoff、milestone開始、大きな設計判断の直前、計画が順調すぎて反論が出ていない時。

## Questions

- 半年後、このproductが使われていないとする。最もありそうな理由を、技術・価値・運用・人の順に挙げると何か。
- そのうち、今のassumption registerに載っていないものはどれか。
- 各失敗理由の早期signalは何か。今の計画で、そのsignalを観測できるか。
- 最も痛い失敗を防ぐ、または早く露見させる最小の手は何か。
- 「作り切ったがuserが来なかった」と「作り切れなかった」のどちらが起きやすいか。

## Return

failure story、発生の根拠、早期signal、対応するassumption（新規ならkind付き）、推奨する検証を返す。起きやすさと影響の見立てを分けて書く。

## Avoid

根拠のない悲観、全riskの羅列。current milestoneの判断を変えないものは短くまとめる。
