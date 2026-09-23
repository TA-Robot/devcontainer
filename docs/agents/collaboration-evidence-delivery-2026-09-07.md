# 通常のproject入口へ実測を届ける

2026-09-07。配布変更commitは`753407c`。
**基盤の限定実測をtemplateへ同梱し、通常入口からagentが観測と限界を取り出せることを一件確認した。**
開発性能の比較は行っておらず、改良前後の再評価までの改善循環を完了したとは扱わない。

## 変更と配布の確認

[既存orchestration skill](../../project/.codex/skills/orchestrate-agent-collaboration/SKILL.md)と
[playbook](../../project/docs/agents/collaboration-playbook.md)に、
[範囲付きの実測](../../project/docs/agents/collaboration-study-evidence.md)への入口を追加した。
queue review、条件付き相談の情報介入、F12事前相談の公開集計を原fileと同じbytesで同梱した。
原集計を読むために基盤repositoryのcheckoutやnetworkへ依存せず、必要な記録だけを辿れる。
copy元・SHA-256を保持し、過去の得点と限界は変更していない。新しいskill・runtime依存は追加していない。

新image: `sha256:760ecc736134756d8bb8d03312c01e97e1b865b58e12d40f7ca7328a6586e7f7`。
通常Dockerfileでbuildし、networkなし・host mountなしのcontainerで`manage-agent-project`を実行した。
生成されたprojectをexportし、公開template 51 file全てがcheckoutと同じbytesであることを確認した。
既存の利用projectへの更新適用は、この配布物の作成・導入確認とは別である。

## 初見のagentによる利用確認

上記で導入したprojectだけを調査対象にし、これまでの会話を渡さないgpt-6-astra/lowの
`evidence_entry_reader`へ、`AGENTS.md`から通常の案内を辿るよう依頼した。
依頼は「公開checkのある小さなPython/Bash CLI修正の協働を検討し、使える手順・実測・限界と、
将来の複数実装選択へ適用できるかを説明する」。期待する答えや実測file名は渡していない。

agentの回答で確認した内容:

- 通常入口、orchestration skill、playbook、実測snapshotを参照先として挙げた。
- queueの両条件4/4と、review付きの時間増を引用した。
- 似た小課題では公開checkと自己修正から始め、具体的な不足があれば別の観点の相談・検証を検討すると提案した。
- maker自身のcheckpointへのreviewとは違うこと、中断・並行writer・継続開発等は未測定であることを説明した。
- reviewの実測から複数実装の効果は推定できず、必要なreviewを省く根拠にもしないとした。
- templateのproject/test placeholderと、このproject自身のepisode実測が未確認であることを残した。

これは回答内容の定性的な利用確認で、数値の品質得点や性能比較ではない。
native advisoryのread-onlyと調査範囲は行動上の指定で、強制隔離の証明ではない。
通常入口からの独立確認だが、広い課題や全providerで同じ行動を保証しない。
実projectでの導入、発動・採否の改善、最終成果の改善、全利用費用は未測定。

## 検証

- template lifecycleとnative contract: 92テスト合格、contract validator合格。
- 更新skill: `skill-creator`のquick validation合格。
- devcontainer lock、isolation、CLI同期、wrapper、指定shell構文確認: 合格。
- 新imageの導入・merge・crash recovery・rollback・contract確認: 合格。
- 新imageのMira hookと観測永続化: 合格。
- 新imageのagentctl外部check: 42テスト合格。
- 同梱3集計の原fileとのbyte一致とSHA一致、導入51 fileの一致を確認。

private記録は `/home/asakura/.local/state/devcontainer-evaluations/collaboration-entry-20260907-01/`。
`installation.json`はimageと導入fileのhash、`installed-project.tar`は実際の導入成果を保存する。
過去のlive比較を再実行せず、モデルを使った作業は上記の有限な利用確認と保存資産のread-only相談だけ。

次の比較対象の選定は[保存済みlifecycle成果の監査](../../experiments/development-harness/selection/lifecycle-reuse-audit-2026-09-07.md)へ分けた。
同じ校正の再実行を避け、複数実装の新規生成は保留し、公開証拠による受入判断を記録するadapterを次の限定対象にする。
