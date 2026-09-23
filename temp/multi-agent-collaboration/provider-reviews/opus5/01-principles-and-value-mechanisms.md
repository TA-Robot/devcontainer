# 01. 価値のmechanismとsoloが勝つ条件

Reviewer: independent Claude Opus 5 review
Date: 2026-08-26
Scope: `temp/multi-agent-collaboration/03-provider-review-brief.md` の Q1、および Q10 の一部

## この文書の読み方

3つのlabelを全5文書で共通に使います。

- **[結論]**: 現在のrepository docと公開されている仕組みから論理的に導ける。反証されるまで設計前提にしてよい。
- **[仮説]**: もっともらしいが未測定。測定方法と反証条件を必ず併記する。設計を固定してはいけない。
- **[未解決]**: 現時点で判断材料がない。埋めるための行動だけを書く。

他文書との対応は次です。

| 文書 | 主な内容 | この文書で定義するIDの利用先 |
|---|---|---|
| [`02-adaptive-selection-and-experimentation.md`](02-adaptive-selection-and-experimentation.md) | 選択手続き、parameter導出、実験E1–E7、metrics | M1–M7、C1–C8 |
| [`03-interaction-protocols-and-comparison.md`](03-interaction-protocols-and-comparison.md) | topology、termination TR1–TR10、bias control B1–B6 | M3–M6 |
| [`04-recurring-agents-and-governance.md`](04-recurring-agents-and-governance.md) | lifecycle governance、guard tier H/D/F | M7、C7、C8 |
| [`05-repository-capabilities-and-roadmap.md`](05-repository-capabilities-and-roadmap.md) | 実装capability T1–T8、roadmap R0–R4 | 全体 |

前提として、**provider transcriptやprivate reasoningが保存される想定を一切置きません**。この文書の主張はすべて、content-freeなmetadataとGit/実行痕跡だけで検証できる形にしてあります。

## 0. 要約

1. **[結論]** multi-agentの価値は7つの独立したcausal mechanism（M1–M7）に分解できる。各mechanismには成立条件があり、条件を満たさない場合の期待利得はゼロではなく**負**になる（固定費が残るため）。
2. **[結論]** 現在のdoc setが最も過小評価しているcostは token/quota ではなく **人間のreview容量（C5）** と **brief serialization cost（C1）** である。前者は「agentを増やすほど遅くなる」構造を生み、後者は「小さいtaskは常にsoloが勝つ」理由の主項である。
3. **[結論]** 現在のdoc setが最も過大評価している価値は **同一provider / 同一modelによるpanelのepistemic diversity（M5）** である。panelが実際に買えるのは信頼度の校正ではなく **選択肢の列挙** であり、一致数はほぼ無情報である。
4. **[結論]** `variants`（M4）は verifier の質に完全に依存する best-of-N である。verifier を名指しできない時点で `variants` は theater であり、案数の議論には意味がない。
5. **[結論]** provider diversity は **生成側よりも評価側で価値が高い**。self-preference biasは同一modelが自作を評価する時に最大化されるため、cross-provider は evaluator に割り当てるのが費用対効果が高い。
6. **[仮説]** 「通常2 round / 最大3 round」「通常2 variants」「3 agentへ聞く」は、**terminationのmechanismとしては誤りだが、planning priorとしては妥当かもしれない**。両者を区別しないことが現在の最大の設計欠陥である（詳細は02）。
7. **[結論]** `agentctl` の capacity class limit（`light=4 / write=2 / integration=1 / isolated=0`）は、参加agent数の上限を**既に構造的に決めている**。この事実がmode設計へ反映されていない。

## 1. Causal mechanism（M1–M7）

各mechanismを「何が原因で改善するか」「成立条件」「反証方法」で書きます。**mechanismを名指しできないcollaborationは実行しない**、が唯一の入口条件です。

### M1. 独立latencyの重ね合わせ（throughput）

- **因果**: 実行時間 `Σt_i` を `max(t_i) + 統合時間` へ置き換える。agentの賢さは関係なく、待ち時間の構造だけで決まる。
- **成立条件**: (a) work itemが真に独立、(b) 共有bottleneck（同一file、同一DB、同一rate window、同一capacity class slot）が存在しない、(c) `max(t_i) + C4 + C5 + C6 < Σt_i`。
- **[結論] 見落とされている制約**: `write` classのcapacity既定値は2である。write jobを3本並べても2波に分かれるため、wall timeは1.5倍改善ではなく2倍近くかかる。**M1の有効agent数の上限はcapacity class limitであり、mode defaultではない。**
- **[結論] quotaの非対称性**: subscription型のrate windowとAPI credit型は挙動が違う。4 agentのburstがrate windowを使い切ると、primaryの対話自体が停止し、wall timeは悪化する。M1は「providerが並列を許すか」まで含めて条件付きである。現doc setにこの記述がない。
- **反証**: 同一task classでsolo逐次とfanoutのwall timeを対で測る（E6）。改善が `C4+C5+C6` を下回るなら、その task class では M1 は成立しない。

### M2. context分割による注意予算の回復（quality、not speed）

- **因果**: 単一agentが大きなtaskを扱うと、関連evidenceの密度が下がり、初期制約の脱落・retrieval精度低下が起きる。work itemを分けると各agentのcontextが小さく密になる。
- **[結論] これは現在のdoc setに存在しないmechanismである**。既存の7価値（throughput / coverage / diversity / deliberation / empirical selection / assurance / continuity）はすべて「複数agentが同時に動く」または「意見が複数ある」ことを前提にしている。M2は**並列性を必要としない**。逐次のsubagent呼び出しでも成立する。
- **重要な帰結**: `dispatch` の価値は「primaryの手離れ」だけではない。primaryのcontextを汚さずに深い調査を行える点が本体である。したがって delegation が許可されていない環境で `dispatch` を「primaryの逐次実行」へ縮退させると、M1は失われるが**M2も同時に失われる**。この縮退は等価ではない。現在のplaybookは「同じ分析枠組みをprimary一人のsequential reviewへ縮退します」と書いているが、失われるものを明示していない。
- **成立条件**: taskのcontextが分割可能で、境界を跨ぐ暗黙invariantが少ない。
- **反証**: 同一taskをsoloと「狭いcontextのdispatch」で実行し、**制約違反数**（allowed pathsからの逸脱、指定checkの未実行、既出決定の再議）を数える（E1）。差が出なければ、そのtask sizeでM2は成立していない。

### M3. error decorrelation（assurance）

- **因果**: makerの誤りとcheckerの誤りが独立でなければ、checkは誤りを見つけられない。decorrelationの源は3つある。
  1. **情報の非対称**: checkerはdiffとtestを見るが、makerの試行軌跡を見ない。
  2. **目的の非対称**: 「作る」と「壊す」は別の探索問題である。
  3. **commitmentの不在**: makerは自案へのsunk costを持つが、fresh instanceは持たない。
- **[結論] 実務上最重要な帰結**: 上の3つのうち2つは **同一provider / 同一model** でも成立する。makerの盲点の主因は自身の軌跡へのcommitmentであり、fresh instanceはそれを共有しない。したがって **role/objectiveの非対称化はprovider diversityより安価で確実である**。現doc setの「provider diversityは補助」という記述は方向として正しいが、なぜ正しいかの因果が書かれていないため、運用時に「別providerを足せばassuranceが上がる」と誤読される余地が残る。
- **[結論] 逆の非対称**: self-preference biasは「自分の出力を評価する」場面で最大化する。したがって **provider diversityの投資先はgeneratorではなくevaluatorである**（03のB5で扱う）。
- **反証**: seeded-defect fixtureで、self-review / same-provider fresh checker / cross-provider checker / red-team の検出率と誤検出率を比較（E2）。cross-providerがsame-provider freshを有意に上回らなければ、生成側のprovider diversity投資は不要と結論できる。

### M4. verifier付き選択（empirical selection = best-of-N）

- **因果**: N個の候補を生成し、verifierで選ぶ。期待利得は `P(候補の質に分散がある) × P(verifierが正しく識別する) × 改善の価値`。
- **[結論] 前提条件**: verifierが (a) 生成より安価、かつ (b) generatorの自己評価より正確、であること。この2条件のどちらかが欠けると、best-of-Nは**費用N倍でノイズを選ぶ**手続きになる。
- **[結論] 現doc setの欠落**: `variants` の項には base SHA / scope / acceptance / rubric の共通化は書かれているが、**verifierの識別能力を事前に確認する要求がない**。「事前rubricと独立evaluator」は手続きの記述であって、能力の保証ではない。subjectiveなrubric項目（maintainability、risk）をLLM評価者が読む場合、識別能力は未知である。
- **[結論] 相関の問題**: 同一briefから同一acceptanceで2案を作ると、候補は相関する。best-of-Nは候補間の分散から利得を得るため、**共有すべきは評価契約であり、approachは意図的に分岐させるべきである**。現doc setは「同じbase、scope、acceptanceから」までしか書いておらず、approachの分岐を要求していない。これが `variants` の期待利得を構造的に下げている（03の§4で契約化する）。
- **反証**: 過去の候補patch対（結果が既知のもの）に対して、rubric+evaluatorが後から正解を当てられるかを測る（E3）。retrodictできないevaluatorをprospectiveに信頼してはいけない。

### M5. 選択肢の列挙（option enumeration）

- **因果**: 独立した初期回答を集めると、primaryが想定していなかった候補approachと暗黙前提が表に出る。
- **[結論] 価値の正しい記述**: panelが買うのは **選択肢空間のcoverage** と **前提の可視化** である。**信頼度の校正ではない**。同一model複数sampleは事前分布を共有するため、一致は系統誤差を打ち消さない。「一致数をconfidenceの根拠にしない」（現playbook）は正しいが、それでもなお `panel` の価値を "epistemic diversity" と呼ぶのは強すぎる。列挙と可視化に言い換えるべきである。
- **[結論] saturation**: 列挙の利得は逓減する。panelistを追加してよいのは、**そのpanelistが担当する固有の観点、固有のevidence source、または固有の失敗様式を名指しできる場合だけ**である。名指しできない追加は複製である。これにより人数は「問題に存在する独立観点の数」から導かれ、固定値にならない。
- **[結論] anchoringの非対称**: blind first roundは、**delegationが使えるときにしか実現できない**。primary一人の逐次実行では、同一contextを持ったまま「独立に考え直す」ことはできない。したがって「blind first roundをproject contextによらないdefaultにする」ことは、mechanismとしては正しいが**実行可能性の前提を隠している**。これは brief が指摘したpremature assumptionの中で、最も明確に誤っている箇所である。
- **反証**: 1 / 2 / 3 / 4観点で、人間が material と認めた**新規**選択肢の数を数える（E5）。飽和点が観測されれば planning prior として公開できる。

### M6. 敵対的探索の非対称性（red-team）

- **因果**: 反例探索は構築とは別の探索空間を持つ。「作った人が思いつかない入力」を明示目的にすると、探索方向が変わる。
- **成立条件**: prober が実際の失敗面へ到達できること。実行可能なprobe（入力を投げる、境界を叩く）があるとき有効で、推測だけのthreat listは M6 を発火させない。現doc setの罠欄「checklist消化で終わる」は同じ問題を指しているが、成立条件として書かれていない。
- **[結論] このrepositoryでの適用範囲**: `docs/architecture.md` が明示するとおり、同一privileged container内にsecurity boundaryは存在しない。したがってred-teamの対象は「container内の権限分離」ではなく、**scope事故の起き方**、**broker検証の抜け穴**（偽head SHA、path逸脱、`ready_for_commit` の誤用）、**外部入力の扱い**である。前2つは既にdeterministic testが存在するため、red-teamの残余価値は主に3つ目にある（04で扱う）。
- **反証**: E2 に red-team armを含める。

### M7. 時間軸の観測（continuity）

- **因果**: 人が見ていない時刻に起きる変化を検出する。
- **成立条件**: (a) 変化が**local eventを伴わずに**起きる、(b) 早期検出が対応costを下げる。
- **[結論] event が schedule を支配する**: repository内のcommitが原因の変化には必ずlocal triggerが存在する。この場合、event-driven は schedule より新鮮・安価・自然にdedupeされるため、**厳密に優越する**。scheduleが正当化されるのは、**外部原因のdrift**（provider CLI更新、advisory公開、依存の新versionなど）に限られる。
- **[結論] 現doc setの誤分類**: `collaboration-model.md` の "Safe initial use cases" のうち、`docs / API drift report` は in-repo trigger（public API surfaceに触るcommit）を持つため sentinel ではなく event-triggered が正しい。`flaky-test候補の集計` は蓄積されたtest履歴に対する集計なのでschedule向きであり、これは妥当。`frozen toolchain canary` と `dependency / advisory drift` は外部原因なのでscheduleが正しい。`gc --dry-run inventory` は内部状態の累積なのでどちらでも成立するが、実際のtriggerはjob終了eventである。
- **反証**: 同一checkをschedule版とevent版で並走させ、検出遅延と重複runを比較（E7）。

## 2. Net valueの不等式とcost項

```text
NetValue = Σ_m Gain(M_m | 成立条件) − (C1 + C2 + C3 + C4 + C5 + C6 + C7 + C8)
```

| ID | cost | 主な決定要因 | 現doc setでの扱い |
|---|---|---|---|
| C1 | brief serialization cost | primaryの暗黙contextをtask envelopeへ書き出す労力 | 「coordination cost」に埋没。主項として書かれていない |
| C2 | context duplication cost | 同じ背景を各agentへ読み直させる入力コスト | 触れていない |
| C3 | latency skew / straggler | 最遅agent待ち、capacity queue待ち | 触れていない（capacity queueは実装済みなのに） |
| C4 | synthesis cost | primaryが結果を比較・統合する労力 | metricとして言及あり |
| C5 | **human review cost** | 生成された**reviewable surface**の量 | 成功指標に含まれるが、**制約としては扱われていない** |
| C6 | integration / conflict cost | 意味的競合、aggregate test失敗、rework | runbookに手順はあるが、mode選択の入力になっていない |
| C7 | quota opportunity cost | 使ったquotaで他に何ができたか、rate window枯渇 | token量として言及。rate windowの構造は未記述 |
| C8 | governance / maintenance cost | mode定義、template、schema、schedulerの維持 | 触れていない |

### C5 を制約として扱う（この review の中心的主張）

**[結論]** 人間のreview容量は固定である。agentの生成速度は容量ではない。したがって次が成立する。

```text
review容量 R (accept可能なdiff量/時間) が binding constraint のとき、
  生成量を増やすmodeは throughput を下げる。
  生成量を減らして決定量を増やすmodeは throughput を上げ得る。
```

この視点でmodeを再分類すると、既存のmode tableとは違う序列が出ます。

| mode | reviewable surfaceへの影響 | C5 が binding な時の評価 |
|---|---|---|
| `panel` / `critique` / `deliberation` | 出力は decision + evidence。surfaceを増やさない | **有利** |
| `maker-checker` / `red-team` | surfaceは増やさず、review対象の質を上げる | **有利**（reviewの一部を代替する） |
| `dispatch`（M2目的） | surfaceは同じ、primary contextを節約 | 中立〜有利 |
| `fanout`（M1目的） | surfaceをN倍にする | **不利**。C5がbindingなら negative |
| `variants` | surfaceをN倍作って1つだけ採用する | **staged gatingで機械的に落とさない限り不利** |

**[仮説]** 実務では C5 が binding constraint である場合が多数派である。反証はE6。もしこれが真なら、doc setが最も推奨すべきmodeは `fanout` ではなく `critique` / `maker-checker` 側であり、現在のrouting順（`solo` → `dispatch`/`fanout` → `panel` → ...）は逆向きに並んでいる。

### C1 が小taskでsoloを勝たせる

**[結論]** 小さいtaskでmulti-agentが負ける主因はtoken costではありません。primaryが持っている暗黙のcontext（今の設計意図、直前の判断、触ってよくないfile、まだcommitしていない前提）をtask envelopeへ serialize する労力が、taskそのものの実行時間を上回るためです。`.agent/schemas/task.schema.json` は `objective` 最大4096文字、`acceptance` 必須1件以上、`scope.allowed_paths` 必須1件以上を要求します。これは正しい厳格さですが、同時に **C1 の下限を構造的に決めています**。

帰結: **task envelopeを書く時間 > 自分でやる時間** なら solo。これは測定不要の、その場で判断できる基準です。

## 3. soloが勝つ条件

**[結論]** 次のいずれかが成立するとき、solo が期待値で勝ちます。

1. **C1 支配**: envelope作成時間がtask実行時間と同程度以上。
2. **結合edit**: 一つの意味的変更が複数fileへ跨り、境界にinvariantがある。分割はC6を増やし、各agentのinvariant理解を不完全にする。
3. **verifier不在**: 良否を安価に判定できない。M4は成立せず、`variants` は費用倍増のみ。
4. **C5 binding**: 人間のreview容量が律速。生成を増やすmodeはqueueを深くするだけ。
5. **tacit constraintが serialize 不能**: 「なぜこうなっているか」がcodeにもdocにもなく、primaryの中にしかない。
6. **quota binding**: rate windowやcredit上限が律速。agentを増やしても消費者が変わるだけ。
7. **capacity binding**: 必要な resource class の slot が既に埋まっている（`integration=1`、`isolated=0` は特にそう）。
8. **可逆かつ低コストな失敗**: 間違えてもすぐ戻せるなら、assurance mechanismの期待利得が小さい。

**[結論]** `solo` を12 modeの一つとして明示している現doc setの判断は正しく、維持すべきです。ただし上記1・4・6・7は現在のrouting基準に入っていません。

## 4. 現doc setのassumption棚卸し

load-bearing（これが偽なら設計が変わる）なassumptionだけを挙げます。

| # | assumption | 出典 | 判定 | 反証実験 |
|---|---|---|---|---|
| A1 | deliberation は通常2・最大3 round | `collaboration-model.md`、playbook、persona、template | **[仮説]** planning priorとしては妥当かもしれないが、terminationのmechanismとしては誤り | E4 |
| A2 | variants は通常2案 | 同上 | **[仮説]** verifier強度・分散・単価から導くべきで、定数ではない。かつ `write=2` と相互作用する | E3 + 容量モデル |
| A3 | 「3 agentへ聞く」が典型 | 説明例 | **[仮説]** 列挙の飽和点は未測定。観点数から導くべき | E5 |
| A4 | blind first round が context 非依存の default | `collaboration-model.md`、playbook、`AGENTS_TEMPLATE.md` | **[結論] 誤り**。delegationが使えないと実現不能。適用条件を明示すべき | 不要（論理で決まる） |
| A5 | provider diversity は品質の補助指標 | `collaboration-model.md` | **[結論] 方向は正しいが不完全**。評価側では主要指標になり得る | E2 |
| A6 | mode と lane は直交 | `collaboration-model.md`、`02-operating-model.md` | **[結論] 正しい**。この review でも維持する | — |
| A7 | `agentctl` は会話を所有しない | ADR-0001、`architecture.md` | **[結論] 正しい**。維持し、強化する | — |
| A8 | scheduled work は finite job emitter に限る | 両doc | **[結論] 正しい**。ただし enablement の権限分離が欠けている（04） | — |
| A9 | agent数・token量・message数を成功指標にしない | 全doc | **[結論] 正しい**。metricsの正の定義が不足（02で補う） | — |
| A10 | 12 mode が first-class の適切な粒度 | `01-pattern-catalog.md` §2 | **[仮説] 過剰**。5 mode + lifecycle軸へ縮約可能（05で移行案） | 運用observation |

## 5. Anti-pattern（既存listへの追加分）

既存の anti-pattern list（agent count theater、premature consensus、debate theater、same-model monoculture、unowned synthesis、shared-write swarm、moving evaluation、recursive delegation explosion、scheduled infinity、silent automation）は妥当です。重複を避け、**追加すべきもの**だけを挙げます。

1. **verifier-less tournament**: 識別能力を確認していないevaluatorで `variants` を回す。M4の前提を欠いた best-of-N。
2. **correlated variants**: 同一briefから同一approachの案を並べ、分散のない best-of-N を実行する。
3. **review-surface inflation**: C5がbindingな状況でfanoutし、review queueを深くして体感を遅くする。
4. **degenerate fallback**: delegation不可時に「primaryの逐次実行」へ縮退させ、M1とM2の喪失を同一視する。
5. **capacity-blind fan**: capacity class limitを超える参加者数を計画し、並列だと思って直列実行する。
6. **primary summarization bias**: primaryがround間要約で、自分の推したくないclaimを落とす。mediated dialogueに固有の失敗で、既存listにない（03のB4で対策）。
7. **finding counted as failure**: sentinelが問題を検出したことを run failure として数え、circuit breakerで監視を止める（04）。
8. **repo-writable enablement**: schedule の `enabled` flag を repository 内のfileに置き、Lane W agentが書き換えられる状態にする（04）。
9. **instruction-bearing external input**: 監視対象の外部text（advisory、release note、issue本文）に含まれる指示をagentが実行文脈として扱う（04）。
10. **prose-as-invariant**: 文章にしか存在しないruleをhard guardと呼ぶ。機械的に検査できないruleは default であって invariant ではない（04のtier定義）。

## 6. 重要な反対意見、unknown、失敗条件

### この review 自身への反対意見

- **反対1: mechanism分解は運用時に重い。** 妥当な批判です。primaryが毎回7 mechanismを検討するのは C1 を増やします。緩和策は、mechanism名をbriefに1語書くだけの要求へ縮めること（02の§2）。それ以上の形式化は C8 を増やすだけで、価値がありません。
- **反対2: C5 bindingという主張は、review体制次第で成立しない。** 正しい。人間が review をagentへ委譲する（maker-checker）ほど C5 は緩みます。ただしその場合、最終責任者が読む量は減っても、**escaped defect risk** が増えます。C5 は消えるのではなく別のcostへ移動します。E6 と E2 を対で測る必要があるのはこのためです。
- **反対3: M2（context分割）は model の context window拡大で消える。** 部分的に正しい。window長は伸びますが、長いcontext内での retrieval 精度と制約保持は window 長と別問題です。ただし **[未解決]**: このrepositoryが使うmodel世代でM2がどの程度残るかの測定値はありません。E1 が最初に確認すべき点です。

### Unknown

- **[未解決]** 各 mechanism の効果量。この review は方向と条件しか主張できません。
- **[未解決]** provider間の rate window / credit 挙動の実測値。C7 の見積りができません。
- **[未解決]** このrepositoryのtask分布。C1 支配のtaskが何割かによって、推奨modeの重心が変わります。
- **[未解決]** 人間reviewerの実効throughput。C5 の binding 判定に必要です。

### 失敗条件（この review の枠組みを捨てるべき兆候）

1. mechanism宣言が形式化し、briefが長くなっただけで判断が変わらない → 枠組みを捨てて `solo` / `delegate` / `verify` の3択へ落とす。
2. episode ledger（T1）が3ヶ月で意思決定を一度も変えなかった → 測定を捨て、guidanceだけに戻す。
3. mode選択のC8が、observed net gainを上回った → mode語彙を縮約する（05の移行案）。
4. 実測でC5がbindingでなかった → §2の序列を撤回し、fanout優先へ戻す。この文書のうち§2後半と§3の項目4を削除すればよく、他は独立に成立します。

## 7. 次の文書へ

- 各mechanismの成立条件をdispatch前に判定する手続きと、agent数・round数・durationを固定しない導出方法 → [`02`](02-adaptive-selection-and-experimentation.md)
- M3–M6 を実現する具体protocol、termination rule、bias control → [`03`](03-interaction-protocols-and-comparison.md)
- M7 と C7/C8 の governance、guard tier → [`04`](04-recurring-agents-and-governance.md)
- 上記を支えるためにこのrepositoryが用意すべきtooling → [`05`](05-repository-capabilities-and-roadmap.md)
