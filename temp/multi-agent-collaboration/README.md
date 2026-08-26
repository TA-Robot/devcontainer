# マルチエージェント協働モデル 検討ログ

検討開始: 2026-08-26

このdirectoryは、既存のnative-first execution fabricへ「agent同士をどう関係づけるか」という協働設計を追加するための探索記録です。実運用の正本ではありません。

- `01-pattern-catalog.md`: マルチエージェント活用60案と、得られる価値・失敗形態
- `02-operating-model.md`: lane / role / collaboration mode / lifecycleを分離した推奨構成
- `03-provider-review-brief.md`: Grok 4.6 / Claude Opus 5へ渡した共通brief
- `provider-reviews/grok/`: 独立Grok 4.6 review 5文書
- `provider-reviews/opus5/`: 独立Claude Opus 5 review 5文書
- `04-cross-provider-synthesis.md`: primaryによる比較とゼロベース再設計
- `05-first-episode-observation.md`: 今回の運用から得たcontent-free observation

正本へ昇格した内容は次へ置きます。

- 基盤設計: `docs/agents/collaboration-model.md`
- target project向け運用: `project/docs/agents/collaboration-playbook.md`

`01`と`02`に含まれる固定人数・固定round・固定variant数は、provider review前の探索仮説です。authoritative guidanceとして使用せず、`04`と正本側を参照してください。

`04`の初期案にあったmanual episode記録の継続条件も棄却済みです。現在はprovider hook / `agentctl` eventからzero-input ledgerを生成し、人間へform保守を求めません。

## 出発点

既存基盤は、read / write / isolated lane、job単位worktree、structured result、single-writer integrationを持ちます。一方、primary agentの指針は主に「独立taskを並列化してcritical pathを短縮する」に留まり、次を体系化していませんでした。

- 独立した意見を集めて判断の質を上げる
- agent間の複数roundの対話で案を改良する
- 複数実装を同条件で競わせ、実測で選ぶ
- makerとcriticを分離して品質を上げる
- 定期・event駆動で有限jobを起動し、時間をまたいでprojectを見守る

今回の中心判断は、これらをexecution laneへ押し込まず、直交する`collaboration mode`として扱うことです。
