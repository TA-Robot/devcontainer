# 01. Principles and value mechanisms

Reviewer: independent Grok 4.6  
Date: 2026-08-26  
Status: independent review. Not repository policy.

`【結論】` は現行architectureと文書から正当化できる判断。`【仮説】` は未測定の作業仮定。現行の「通常2 round / 最大3」「通常2 variants」「3 agent典型」「panelは常にblind first round」は品質の最適値ではない。

## 価値は人数ではない

【結論】複数agentがsoloより価値を生むのは、人数が増えたからではない。次のmechanismが実際に発火したときだけである。

1. **wall-clock parallelism** — 独立作業がprimaryの待ちと重なり、longest pathが短くなる。
2. **coverage** — 分割または観点分担で、一人の逐次探索が見ない領域を拾う。
3. **error-correlation reduction** — 失敗モードが独立なら、一人の盲点を他が検出する。本体は人数ではなく残差相関。
4. **role-separated detection** — makerとchecker（またはred-team）の注意と誘因を分ける。
5. **empirical selection** — 同じacceptance / fixtureで実装を測り、言語化した優劣を検証する。
6. **evidence-producing iteration** — 次のやり取りが新しいclaim / evidence / testを生む。言い換えと合意したふりはmechanismではない。
7. **temporal sampling** — 有限jobの反復標本で、一回のsnapshotでは見えないdriftを見る。

【結論】このrepositoryのlane、job worktree、structured result、single-writerは 1, 4, 5 の一部を支える。2, 3, 6, 7 はguidanceに書かれているが観測されていない。`agentctl` 0.7 にschedulerは無く、7 を提供しているとは言えない。

【仮説】純価値の一次近似:

```text
Net = E[品質改善 or wall-clock短縮]
    - agent実行コスト - 調整/synthesis
    - 人間のreview/integration分
    - 機会費用（capacity, quota, primaryの注意）
```

品質改善の観測可能な形は、soloでは出なかったdecisive evidence / Must、事前rubricで区別できる実装差、rework削減、失敗の早期停止である。token量・message数・議論時間は成功指標にしない。現行modelもそう書いており支持する。支持しないのは、同じ文書が未検証の人数とroundをmodelの性質として固定している点である。

## 成立条件と壊れ方

- Parallelismはshardが切れ、統合がcritical pathを再導入しないときだけ速くなる。shared checkoutへの同時writeは事故になる。Lane W worktreeは **accidental-write boundary** であり、security boundaryではない。Lane Iは未提供。
- Coverageは重複少なく分割できるか、観点が本当に別のevidenceを見るときに限る。観点ラベルだけ与えて同じREADMEを読ませるのは偽多様性。
- 相関低下は、視点・証拠源・検証方法・modelの少なくとも一つが違う必要がある。同じpromptの複製は多様性ではない。【結論】blind first roundはanchoringを減らす手法であり、panelの普遍defaultではない。共有文脈が高価なら盲は調査をN倍する。
- Assuranceはcheckerが追認せず、Mustの修正後に独立再検証があるときに効く。role fileをsecurity isolationと呼ばない。現行researcher / implementer / reviewerで足り、collaboration内のproposer/criticは責任名にすぎない。
- Empirical selectionは事前rubric、安いprototype、correctness-first gateが揃うときだけ安い。「通常2案」は比較の最小人数とdefaultを混同している。defaultは今の最良案を一つ実装すること。
- Iterationの価値はevidence-deltaがあるときに限る。「通常2 / 最大3 round」は未検証のcost cap候補であり、最適round数ではない。【仮説】第一回の反証で価値の大半が出て、追加roundは証拠が無い限り修辞的再話になりやすい。未測定なので政策にしない。
- Temporal samplingは毎回immutable snapshot、delta報告、必ずterminal、人間が読む頻度を超えないことが条件。常駐sessionと無人mergeは禁止。

## Soloが勝つ条件

【結論】taskが小さく明確で可逆、context couplingが高い、評価が主観で結局primaryが決める、人間のreview枠が飽和、統合がcritical path、失敗が強く相関、quota/capacityが逼迫、書く場所が一つ、user preference待ち、のいずれかが強いなら追加agentの期待純価値は負になりやすい。`solo` は失敗ではなく標準である。`why_multi_agent` をmechanism名で書けない、またはbinding constraint（多くは人間のreview分かwall-clock）を書けないなら起動しない。

【仮説】この基盤repoの日常の小さいscript/docs/test修正はsolo側に入ることが多い。ritual fan-outは「面白さでscopeを広げない」とも矛盾する。

## Anti-pattern

agent count theater、round theater（予定回数の消化）、blind cargo cult、premature consensus、same-model monoculture、unowned synthesis、shared-write swarm、moving evaluation、recursive spawn、scheduled infinity、human-review denial、transcriptを共通stateにすること、open-ended自己改善とauto merge。現行ADRがtranscriptをcontrol planeへ入れない点は支持する。Grok durable writeはnested subagent無効・memory無効で、peer dialogueは使えない。

反対: 固定roundはteamの予測可能性にはなる。それはgovernance comfortであり品質効果と取り違えない。unknown: provider混合がこのrepoで相関を下げるか、claim ledgerの情報損失、human minutesの測り方。

