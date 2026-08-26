# 02. Adaptive selection and experimentation

Reviewer: independent Grok 4.6  
Date: 2026-08-26  
Status: independent review. Not repository policy.

【結論】agent数、provider構成、round数、topology、duration、budgetにproject非依存の最適値はない。選ぶ単位は人数ではなく、得たいmechanismと先に尽きる制約である。数値を書くなら適用範囲・根拠・無効化条件・更新ownerを同じ場所に置く。書けない数値は`AGENTS.md`へ置かない。

## 適応してよいものと、してはいけないもの

適応してよい: extra agent数、追加roundの可否、経過時間とusageのcost cap、independence level、provider構成、topology、recurring頻度。

適応させない（hard guard）: shared checkout同時write、auto merge/push/PR/release、無期限session、open-ended自己改善、workerによるschedule/quota/permission変更、transcriptのcontrol plane保存、securityとaccidental-writeの混同、未実装schedulerの仮定。

## Binding constraintを先に名指す

現行operating-modelの0–2点cardは便利だが、【結論】点数合計でmodeを選ぶのは未検証である。最初に書くのは次のどれがこのrunで先に尽きるかである。

1. 人間のreview / integration分
2. wall-clock（interactive待ち）
3. provider quota
4. agentctl capacity（light/write/integration/isolated。isolated既定0はruntime未提供の事実）
5. 失敗コスト
6. context coupling
7. evaluability

人間reviewが制約ならagentを増やすほど遅くなりやすい。wall-clockが制約で独立shardがあるときだけparallelが効く。失敗コストが高く測れないなら実装を増やさずadvice/reviewに留める。capacity既定のwrite slot数はcollaboration最適人数ではない。

## Mechanism-first

1. artifactを一文で書く。
2. soloで足りるか。mechanism名でwhyが書けなければsolo。
3. 発火させたいmechanismを一つ選ぶ。二つ以上欲しいならstageを分ける。同時積載の整数上限は置かない。
4. binding constraintを名指す。
5. 最安のoperator topologyを選ぶ（solo / parallel / advice / review / variants / recurring）。現行12 modeはalias。
6. 人数はindependent unitから導く。好きな整数を先に置かない。
7. 予算はcost capであり消化目標ではない。human minutesを含める。
8. 停止はacceptance、evidence-delta、制約枯渇、user境界。予定round消化ではない。
9. 事後にmechanism_firedをcontent-freeに記録する。

人数の導出:

- parallel: 非overlapのshard数。切れないなら増やさない。
- advice: 操作可能な異なる観点または検証方法の数。同一問いの複製数ではない。「3 agentへ聞く」を典型にしない。
- review: 非対称ペアが基本。checkerを増やすのは手法/観点が違うときに限る。
- variants: 安価で非支配的、事前rubricで区別できる戦略の数。defaultは追加実装0。
- recurring: 並列人数ではなく標本頻度と人間が読む頻度。

減らす合図: 言い換えだけ、人間が読む前に次報が来る、integration待ちがcritical path、同じfindingの複製、本線jobがqueueに積まれる。

## Round / duration / budget

【結論】全球「通常2 / 最大3 round」は棄却する。critiqueは新しいevidence / test / 未解決Mustが返ったときだけ追加roundを開く。claim statusが動かず文章だけ変わったら即停止。

durationの「20m」例は未検証。interactiveの待ち許容、detachedのorphan/機会費用、acceptanceから導く。Grok writeの`--max-turns 64` はprovider defaultの沈黙変化を防ぐadapter cost capであり、品質最適でもcollaboration round上限でもない。当たったらfailure。

budgetは四層: provider usage（正規化しない）、agentctl capacity、human review minutes（現行template欠落）、milestone時間。

【仮説】多くのtargetではhuman minutesが最初に尽きる。tokenだけをcapにするとreport在庫が残る。

Provider数は多様性の代理にしない。capability、残したい非相関、cross-providerの複製コストを順に見る。同じproviderで観点を変える方が安いことがある。三provider同時をplaybookへ書かない。

## 学習とexperiment

【結論】C3 schemaはC2で使われたfieldだけを昇格する。現行のこの順序は支持する。支持しないのはC2前に人数とroundを高権限面へ固定したこと。

記録してよい（transcript / prompt / finding本文なし）: topology、N_extra実績、opened rounds、independence level、lane、provider識別、elapsed、queue wait、human minutes、採否、mechanism_fired、decisive_finding yes/no、rework、stop_reason。使われないfieldはschema化しない。

Solo baseline無しに有効性は判定できない。control-planeの決定論fixtureとlive model canaryを混ぜない。

数値を置く必須付帯:

```text
parameter / scope / role: cost cap|starting bound|hard guard
rationale / invalidation / update owner
```

この基盤のC2に限るstarting bound仮説（全球政策ではない）: extra agentは0からmechanismが書けたときだけ増やす。追加roundはevidence-deltaが無いなら開かない。variantsの追加実装defaultは0。無効化条件は「追加単位がMustも短縮も生まずhuman minutesだけ増えた」。

実装前実験（nativeと既存job fabricのみ。新runtime不要）:

- E1 小さいwriteはsoloが勝つか
- E2 観点分けadviceは同一prompt複製よりMustが増えるか
- E3 追加roundはevidence-deltaがあるときだけ効くか
- E4 variantsは事前rubricがあるときだけ安いか
- E5 maker-checkerはself-reviewよりintegration前Mustを取るか
- E6 手動定期点検に読む価値があるか

成功はmechanism発火かつhuman minutes込みで純価値が非負。失敗はコスト増だけでreworkが減らないこと。判定に使わない: agent数、message数、token合計、provider社数、合意自己申告。E6が負ならschedulerは作らない。

残す自由度: topology、independence、provider、N_extra、追加round可否、project-local cost cap。残さない: workerがN/round/scheduleを増やす、評価基準の後付け、部分成功、無人統合、未検証整数の高権限固定。

