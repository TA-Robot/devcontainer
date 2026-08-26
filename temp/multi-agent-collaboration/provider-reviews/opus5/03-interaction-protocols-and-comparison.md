# 03. Interaction protocolとcomparison

Reviewer: independent Claude Opus 5 review
Date: 2026-08-26
Scope: brief Q3、Q4、Q5

mechanism ID（M1–M7）は [`01`](01-principles-and-value-mechanisms.md)、selection手続きと実験ID（E1–E7）は [`02`](02-adaptive-selection-and-experimentation.md) の定義を使います。この文書で定義する termination rule（TR1–TR10）と bias control（B1–B6）は [`04`](04-recurring-agents-and-governance.md) と [`05`](05-repository-capabilities-and-roadmap.md) から参照します。

## 0. 要約

1. **[結論] 12 modeは過剰であり、内部矛盾がある。** `collaboration-model.md` は lifecycle を独立軸と宣言した上で、mode表に `sentinel` と `event-triggered`（どちらもlifecycle）を並べている。`panel` / `critique` / `deliberation` は同一protocolのparameter違いである。**5 mode × lifecycle軸**へ縮約する案を §1 に示す（migrationと削除可能性つき）。
2. **[結論] primary-mediated を default にする根拠は「providerが対応していないから」ではない。** 唯一 primary だけが budget と authority を持っており、**停止判断は budget の所有者が行うべき**だからである。この根拠なら、providerがpeer messagingを完全対応しても default は変わらない。
3. **[結論] direct peer exchange の正しい境界は「事実確認は可、評価判断は不可」である。** 「interfaceは何を返すか」は peer 間で解決してよい。「どちらの案が良いか」は peer 間で解決させてはいけない。理由は §2.3。
4. **[結論] mediated dialogue には固有の失敗様式がある**: primary が round 間要約で不都合なclaimを落とす（summarization bias）。現doc setに記載がない。対策 B4。
5. **[結論] termination は round cap ではなく10種の規則の論理和で決める。** そのうち最重要は TR1（情報停止）と TR4（crux到達）であり、TR4 は「事実は合意、価値判断で相違」という安価に検出できる状態である。
6. **[結論] variant比較は「評価契約を共通化し、approachを意図的に分岐させる」。** さらに **held-out check**（variantに見せない検証）を1本持たないと、acceptanceへの過適合と benchmark gaming を検出できない。
7. **[結論] staged gating と early abort により、`variants` のコストは N倍ではなく「1本 + 落選分の途中まで」に抑えられる。** 対称に完成させる必要はない。

## 1. Mode語彙の縮約案

### 1.1 現状の問題

| 問題 | 具体 |
|---|---|
| 軸の混在 | `sentinel` / `event-triggered` は lifecycle。同じ表に mode として並んでいる |
| parameter違いをmode化 | `panel`（独立・1 round）、`critique`（提案あり・1 round）、`deliberation`（提案あり・複数round）は同一protocolの3設定 |
| topology重複 | `dispatch` / `fanout` / `pipeline` は fan数と dependency 形状の違い。`agentctl` は既に `dependency_job_ids` で pipeline を表現できる |
| 選択コスト | routing listが8 step。primaryが毎回12択を検討するのはC1・C8の増加 |
| 記述の分散 | 同じmode表が `AGENTS.md` / `AGENTS_TEMPLATE.md` / `docs/agents/collaboration-model.md` / `project/AGENTS.md` / playbook / `persona.md` / temp 2文書に存在し、既にdriftがある（例: `01-pattern-catalog.md` §2 で pattern 42 が `deliberation` 系と `maker-checker` 系に二重計上、variant数の表現が3箇所で微妙に違う） |

### 1.2 提案する語彙

**mode（agent同士の関係。5つ）**

| mode | topology | parameter | 吸収する既存mode | 主mechanism |
|---|---|---|---|---|
| `solo` | primaryのみ | — | `solo` | — |
| `delegate` | primary → N worker → artifact | `fan`（1..N）、`dependencies`（DAG） | `dispatch`、`fanout`、`pipeline` | M1、M2 |
| `consult` | 意見の収集と交換 | `seed`（none / proposal）、`independence`（blind / shared）、`rounds`（TR停止） | `panel`、`critique`、`deliberation` | M5、M3 |
| `compete` | 並列候補 → 評価 → 選択 | `n`、`approach_hypotheses`、`gates`、`held_out` | `variants` | M4 |
| `verify` | 成果物 → 独立検証 | `stance`（neutral / adversarial）、`access`（diff / executable） | `maker-checker`、`red-team` | M3、M6 |

**lifecycle（いつ・何回起動するか。独立軸）**: `one-shot` / `bounded-rounds` / `event-triggered` / `scheduled`

これで `panel` = `consult(seed=none, independence=blind, rounds=1)`、`critique` = `consult(seed=proposal, rounds=1)`、`deliberation` = `consult(seed=proposal, rounds=TR停止)`、`red-team` = `verify(stance=adversarial)` と表現できます。**parameterの一つとしてround数が現れるため、「通常2・最大3」という定数がmode定義から自然に消えます。** これが縮約の主目的です。

### 1.3 Migrationと削除可能性

**[結論] 破壊的置換は不要です。** 移行は3段階で、各段階で単独完結します。

| 段階 | 作業 | 元へ戻す方法 |
|---|---|---|
| MG1 | 既存12 modeを維持したまま、`collaboration-model.md` に「mode表から `sentinel` / `event-triggered` を lifecycle 節へ移す」だけを行う | 節を戻す（1コミット） |
| MG2 | 5 mode語彙を **別名（alias）** として追加し、12 mode ↔ 5 mode の対応表を1箇所に置く。運用はどちらの語彙でも書ける | alias表を削除 |
| MG3 | episode record（02 §5.1）で5 mode語彙の使用率が十分に高くなったら、12 mode表を対応表へ縮約 | 対応表から12 mode表を再生成できる（情報損失なし） |

**削除可能性**: この提案が失敗した場合の撤退は「対応表fileを1つ削除し、既存doc setをMG1前の状態に戻す」だけです。schema変更、code変更、state移行を伴いません。MG3まで進んだ場合でも、対応表に12 mode名が残るため復元できます。

**[仮説]** 縮約は選択コスト（C1・C8）を下げる。反証は、5 mode化した後に mode 選択の誤り（後から別modeが適切だったと判明する率）が増えることです。episode recordで追跡できます。

## 2. Topologyの使い分け

### 2.1 一次分岐（02 §1 の再掲ではなく、topology側からの整理）

```text
出力が「決定」か「成果物」か
  決定  -> consult。ただし I3==cheap-accurate なら consult より先に測定1本
  成果物 -> delegate（1本） / compete（複数本）
どちらでも、I5（late-failure cost）が高ければ後段に verify を足す
再発するなら lifecycle を event-triggered / scheduled へ（04）
```

### 2.2 重ねない規則

**[結論] 1 phaseに2 modeまで。** 現doc setは「3 mode以上を同時に積まない」としています。実質2までにすべきです。理由は、3 modeを重ねた時点で synthesis（C4）が primary の主要作業になり、collaborationの目的が入れ替わるためです。

**[結論] `verify` は artifact が完成した後に置く。** 並行reviewは、動いている対象を読むことになり、makerとcheckerの両方が無駄になります。例外は「設計だけを先にverifyする」場合で、これは対象が固定されているので並行ではありません。

**[結論] `consult` → `compete` の順は正しいが、逆は成立しない。** approachが絞れていないまま compete すると、候補が同一空間に落ちるか、比較不能な別物になります。

### 2.3 direct peer exchange と primary-mediated

| 観点 | primary-mediated | direct peer |
|---|---|---|
| 停止判断の所有者 | **budgetを持つprimary** | 参加者（budgetを持たない） |
| latency | 2 hop / exchange | 1 hop |
| context成長 | primaryが要約するため抑制される | transcriptが蓄積し超線形に増える |
| 監査点 | roundごとに存在 | 終了時のみ |
| provider依存 | なし | messaging対応が必要 |
| 固有の失敗様式 | **primary summarization bias**（B4） | **収束への引力**。2者を放置すれば合意する。text上の合意は evidence ではない |
| 外部からの前提の点検 | primaryが第三の視点として機能する | 共有された誤前提が誰にも疑われない |
| 主張の帰属 | roundごとに追跡可能 | 終盤で誰の主張か曖昧になる |

**[結論] defaultは primary-mediated。根拠は「providerが未対応だから」ではなく「停止判断の所有者と budget の所有者が一致すべきだから」です。** この根拠なら、将来 provider が peer messaging を完全対応しても default は変わりません。現doc setは「providerがpeer messagingを正式に支援し、delegationが許可されている場合だけ」と可用性を条件にしており、可用性が満たされた瞬間にdefaultが揺らぐ書き方になっています。

**[結論] direct peer を許す境界は内容の種類で決めます。**

| 交換内容 | direct peer | 理由 |
|---|---|---|
| 事実確認（「この関数の戻り値の形は」「そのfixtureは何を含むか」） | **可** | 検証可能で、収束は正しい。primaryを経由する意味が薄い |
| 仕様の明確化、interface整合 | **可**（低stake） | 同上 |
| 評価判断（「どちらの案が良いか」「このriskは受容できるか」） | **不可** | 収束への引力が働き、合意が evidence を偽装する。かつ budget所有者が不在 |
| 相手の成果物へのwrite、permission変更、nested spawn | **不可** | authority境界（04 tier H） |

direct peer を使う場合の最小契約: facilitator 1名、topic固定、message上限、**成果は合意文ではなく claim ledger の差分**、primary は任意時点で interrupt 可能。この4点は現doc setの記述と一致しており、維持します。

### 2.4 delegation が使えない環境での縮退

**[結論] modeごとに縮退の質が違います。** 現playbookの「同じ分析枠組みをprimary一人のsequential reviewへ縮退します」は、この差を隠しています。

| mode | 縮退の質 | 具体 |
|---|---|---|
| `verify(stance=adversarial)` | **良好** | 「今から壊す側で読む」と目的を切り替えれば、M6の探索非対称は部分的に再現する |
| `consult(seed=proposal)` | **良好** | 案を固定してから批評passを分ければ、commitment効果は残るが情報非対称は再現する |
| `delegate`（M2目的） | **不良** | context分割ができないため、M2は完全に失われる。M1も失われる |
| `consult(independence=blind)` | **不能** | 同一contextを持ったまま独立には考えられない。blindは達成できない |
| `compete` | **不能に近い** | 逐次に2案書くと、2案目が1案目に強く条件づけられ、best-of-Nの分散が消える |

## 3. Termination rules（TR1–TR10）

**[結論] 停止は次の論理和で判定します。round cap は含みません。** すべて content-free に判定できます。

| ID | rule | 判定材料 | 適用先 |
|---|---|---|---|
| **TR1** | **情報停止**: 直前roundで claim status の変化が0件 | ledgerの遷移件数 | `consult` |
| **TR2** | **claim閉鎖**: 決定に関わる `open` / `test-needed` が残っていない | ledger | `consult` |
| **TR3** | **決定的evidence**: 実行可能なtest / 測定で相違が解消した。**roundの途中でも即停止** | check結果 | 全mode |
| **TR4** | **crux到達**: 事実は合意し、相違は価値判断・優先度・user preferenceに帰着した | ledgerの `accepted` evidence + 未合意の重み付け | `consult` |
| **TR5** | **budget到達**: elapsed / slot-seconds / provider quota | 実測（02 §2.4） | 全mode |
| **TR6** | **反復検出**: 同一claimが新evidenceなしに2回以上再提示された | claimごとの再提示カウンタ | `consult`、direct peer |
| **TR7** | **cost-to-go**: 残る相違が可逆かつ低コストな選択にしか影響しない | primary判断 | 全mode |
| **TR8** | **発散検出**: open claim 数が round を追って増加している | ledgerの件数推移 | `consult` |
| **TR9** | **人間attention超過**: 結果を説明するのに必要な分量が、reviewerが読む量を超えた | primary判断（C5） | 全mode |
| **TR10** | **authority到達**: 参加者が escalation を要する行為（merge、permission昇格、外部送信、destructive操作）を提案した | 提案内容の分類 | 全mode |

### 3.1 特に価値の高い2つ

- **TR4（crux到達）**: 「両者が同じ事実を認め、重み付けだけが違う」状態は、追加roundで解決しません。これは **user へ返すべき状態** であり、agentに決めさせてはいけない境界です。検出は安価で（ledgerで evidence が `accepted` かつ結論が不一致）、現doc setの停止条件「user preferenceなしには決められない境界へ到達した」を**判定可能な形にした**ものです。
- **TR8（発散検出）**: open claim が増え続けるのは、議論が悪いのではなく **問いの立て方が悪い** signalです。停止して再scopeするのが正解で、round capでは「時間切れ」と区別できません。

### 3.2 budget到達時の扱い

**[結論] TR5 での停止は failure ではありません。** 返すのは `partial` + open claim一覧 + 「あと何が分かれば決まるか」です。これを failure として記録すると、budgetを上げる圧力が生まれます（silent budget creep）。

## 4. Synthesis

### 4.1 primaryが返すもの

現playbookの最終報告要件（何を決めたか / 決定的evidence / 重要なdisagreementの扱い / 採らなかった案と理由 / 残risk）は妥当です。**追加すべきものが1つあります。**

- **「何が分かれば判断が変わったか」（decision-flip condition）**。これを書くと、(a) 後から評価の妥当性を検証でき、(b) episode recordの `decisive_evidence_kind` が意味を持ち、(c) 次に同じ判断をする時の測定対象が決まります。1–2行で足ります。

### 4.2 多数決を使わない代替手続き

```text
1. 各参加者の recommendation を、結論ではなく evidence と assumption で並べる
2. assumption を project制約（AGENTS.md / .agent/config.json / 実測値）と照合する
3. 照合で落ちた assumption に依存する recommendation を除外する
4. 残った相違が TR3 で解ける（測定可能）なら測る。TR4 なら user へ返す
5. 採否と理由、decision-flip condition を記録する
```

**[結論] 一致数を confidence の根拠にしない**（現doc setと同意）。ただし理由を明示しておきます。同一model複数sampleは事前分布を共有するため、一致は系統誤差を打ち消しません（01 §1 M5）。**異なるproviderの一致は弱い証拠にはなり得ます**が、学習データの重複により独立性は保証されません。

## 5. Variant比較（compete）の契約

### 5.1 共通化するもの / 分岐させるもの

**[結論] 「評価契約を共通化し、approachを分岐させる」。** これが現doc setとの最大の差です。

| 項目 | 扱い | 理由 |
|---|---|---|
| immutable full base SHA | **共通** | 比較の前提 |
| allowed / forbidden paths | **共通** | scope差は比較を無効にする |
| acceptance（可視のcheck command） | **共通** | correctness gateは同一でなければならない |
| **held-out check（variantに見せない）** | **共通だが非開示** | acceptanceへの過適合を検出する唯一の手段 |
| resource class、wall-clock deadline、slot-seconds budget | **共通** | 3倍のbudgetで勝った案は勝っていない |
| result contract、出力形式 | **共通** | 比較の機械化 |
| rubricの**次元** | **共通・開示** | 同じ目標を最適化させる |
| rubricの**重み** | **非開示** | 重みを知らせるとrubric gamingが起きる |
| **approach仮説** | **分岐・明示割当** | 候補間の分散がbest-of-Nの利得源（M4） |
| provider / model | 分岐してよい | 分散の追加源。ただし主要因ではない |
| 途中実装の相互参照 | **禁止** | 独立性 |
| diff sizeの上限 | **共通** | spike scopeの強制。production品質化の浪費を防ぐ |

**[結論] `held_out` の実装は task schema を変えずに済みます。** 可視の `acceptance` は現行 `.agent/schemas/task.schema.json` のまま使い、非開示の検証は **job envelopeとは別の sidecar**（brokerだけが読むverification定義）として `agentctl` state 側へ置きます。schema v1 は `additionalProperties: false` なので、field追加は破壊的変更になります。sidecarならschema変更なし・削除も容易です（05 T4）。

### 5.2 staged gating（コストをN倍にしない）

```text
stage 0  存在確認: buildが通るか。落ちたら即終了、以降のstageへ進めない
stage 1  可視 acceptance の全command。落選確定なら**その時点で他variantの残作業を止める**
stage 2  held-out check。ここで落ちる案は acceptance へ過適合している
stage 3  差分の質的評価（maintainability、risk、migration cost）。
         **生存した候補のdiffだけ**を見る。試行軌跡は見ない
stage 4  primaryの採否判断 + decision-flip condition の記録
```

- **early abort**: stage 1 で1本が全通過、他が失敗したなら、失敗側を完成させる必要はありません。**対称完成は不要**です。
- **人間reviewの投入点は stage 3 だけ**にします。これで C5 の消費は「生存候補数 × diff量」に抑えられ、N に比例しません。
- **budget消費の報告**: 各variantの実消費 slot-seconds を比較reportへ載せます。載せないと「勝った案が実は高かった」が見えません。

### 5.3 「存在するか」を問う場合はcompeteを使わない

**[結論] 目的が「acceptableな解が1つあればよい」なら、best-of-Nではなく early-exit の逐次実行が安価です。** compete は「どれが最良か」を問うときだけ使います。現doc setはこの区別をしていません。

### 5.4 hybrid（複数案の混合）

現doc setの「hybridは新しいintegration taskとして検証する」に同意します。追加すべき点: **hybridは held-out check を再度通す必要があります**。混合によってacceptanceは通るがheld-outが落ちる、という状態が起こり得ます。

## 6. Bias control（B1–B6）

| ID | bias | 発生箇所 | 対策 | コスト |
|---|---|---|---|---|
| **B1** | anchoring | consult の first round | blind（delegation可能時のみ。02 §2.6）。primaryの選好は最後まで出さない | 低 |
| **B2** | position / order bias | 評価者が複数候補を順に読む | **提示順をランダム化**し、順序を記録する。LLM評価者の位置選好は無視できない | 低 |
| **B3** | 匿名化の失敗 | evaluatorへauthorを伏せたつもりが、code styleやcommit messageから漏れる | **伏せる努力はするが、成立を仮定しない。** 匿名性に依存する結論を出さない。実務上は「provider名を出さない」程度が上限 | 低 |
| **B4** | **primary summarization bias** | mediated dialogue の round 間要約 | open claim は **要約せず原文の主張文をそのまま持ち越す**。rejected claim は理由つきで残す。要約は「背景」にだけ適用する | 低。現doc setに欠落 |
| **B5** | self-preference | 同一modelが自作を評価 | evaluatorへ **cross-provider** を優先割当（02 §2.5）。同一providerしか無い場合は、makerの試行軌跡を見せない形で情報非対称だけ確保する | 中 |
| **B6** | verbosity bias | 長い回答が良く見える | rubricに分量項目を入れない。回答形式の上限を先に固定する（recommendation / evidence / assumptions / alternatives / risks / unknowns / confidence / disconfirming test） | 低 |

**[結論] B2 と B4 は現doc setに存在せず、どちらも実装コストがほぼゼロです。** 先に入れるべき対策です。

**[仮説] B5 の効果量は未知です。** E2 で same-provider fresh checker と cross-provider checker を比較して初めて、cross-provider evaluator への投資が正当化されます。それまでは「evaluatorに割り当てるなら generator より優先」という**順序の主張**だけに留めます。

## 7. Advice result format

現doc setの format（recommendation / evidence / assumptions / alternatives considered / risks / unknowns / confidence / disconfirming test）は良い設計です。**維持し、2点だけ変更を提案します。**

1. **`confidence` の意味を限定する。** `low/medium/high` は「この回答が正しい確率」ではなく「**この回答を覆すために必要な追加evidenceの量**」と定義します。前者は較正されておらず比較できませんが、後者は disconfirming test と整合し、primaryが次の行動を決められます。
2. **`assumptions` にproject制約への参照を要求する。** 「どのfile / config / 実測値に依拠したか」を書かせると、§4.2 step 2 の照合が機械的になります。

claim ledgerは3列で十分です。

```text
| ID | claim（1行） | status: open / accepted / rejected / test-needed |
```

evidence本文は別artifactへ置き、ledgerからはpathで参照します。**transcriptは保存しません。** ledgerに残るのは主張1行とstatusだけです。

## 8. 反対意見、unknown、失敗条件

### 反対意見

- **反対1: mode縮約は既存doc setの大規模書き換えを招く。** 妥当な懸念です。だから MG1（lifecycleを表から出すだけ）から始め、MG2 は alias 追加のみとしました。MG1 単体でも内部矛盾は解消します。ここで止めても価値があります。
- **反対2: held-out check は agent へ「隠しゴール」を課すことになり、不公平ではないか。** 逆です。held-outが無い場合、agentは可視acceptanceへ最適化する強い誘因を持ち、**それは合理的な行動です**。過適合を agent の不誠実として扱うのは誤りで、評価設計の欠陥として扱うべきです。ただし **[結論]** held-out は「可視acceptanceと同じ性質のcheck」でなければなりません。全く別の要件を隠すのは仕様の後出しであり、moving evaluationです。
- **反対3: TR群が10個は多い。** 実務上は TR1・TR3・TR5 の3つで大半が停止します。TR4・TR8 は「停止して人へ返す」判断のためにあり、残りは事故防止です。**実装が必要なのは TR1（件数カウント）と TR5（budget）だけ**で、他はprimaryの判断規則です。
- **反対4: direct peer を事実確認に限るのは、実際の設計議論では線引きが曖昧。** 正しい。運用可能な代理判定は「**その交換の結論が check command で検証できるか**」です。できるなら事実、できないなら評価です。

### Unknown

- **[未解決]** LLM評価者の position bias / verbosity bias の効果量（このrepositoryのrubricにおいて）。B2・B6の対策は安価なので効果量を待たずに入れますが、効果は主張しません。
- **[未解決]** approach仮説を分岐させた場合の候補間分散の実測値。M4の利得を決める量です。
- **[未解決]** held-out check を安定して用意できるtask classの範囲。fixtureが作れないtaskでは compete が成立しません。
- **[未解決]** direct peer exchange の provider 対応状況。現時点でこのreviewは実装を推奨しません。

### 失敗条件

1. mode alias（MG2）が使われず、12 mode表と併存したまま両方が drift した → alias を削除し、MG1 の状態で固定する。
2. held-out check の維持コスト（fixture更新）が compete の利得を超えた → held-out を廃し、**compete 自体を封印する**（held-outなしのcompeteは過適合を検出できないため、compete だけ残すのは悪い方向の妥協）。
3. TR1 の判定に必要な ledger が書かれない → `consult` の複数round運用をやめ、1 round + primary判断へ固定する。
4. B4（原文持ち越し）が context を膨らませて budget を圧迫した → 持ち越し対象を「決定に直結する open claim のみ」へ絞る。要約へ戻すのは最後の手段とする。
