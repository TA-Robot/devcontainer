# 02. Adaptive selectionとexperiment design

Reviewer: independent Claude Opus 5 review
Date: 2026-08-26
Scope: brief Q2、Q8、Q9 の一部

label（[結論] / [仮説] / [未解決]）とmechanism ID（M1–M7）、cost ID（C1–C8）は [`01`](01-principles-and-value-mechanisms.md) の定義を使います。guard tier H/D/F は [`04`](04-recurring-agents-and-governance.md) §2 で定義し、この文書ではtier Dの更新手続きを扱います。

## 0. 要約

1. **[結論] 中心的な設計誤りは「planning prior」と「termination mechanism」の混同である。** 「通常2 round、最大3 round」は観測分布の記述（prior）であり、停止判断の機構（mechanism）ではない。priorをmechanismとして使うと、簡単な問いに2 round払い、難しい問いを3 roundで切る。両方とも間違える。
2. **[結論] 停止は「残余情報量 vs 残余コスト」で決める。** 実装は claim status の変化数という content-free な観測量で足りる。transcript保存は不要。
3. **[結論] 人数・案数は「区別可能な役割を名指しできる数」から導く。** 名指しできない参加者は複製であり、M5の飽和とM4の相関劣化を招く。
4. **[結論] budgetは絶対値ではなく相対値・派生値で表す。** provider-neutralな単位として **slot-seconds**（`resource_class` slotの占有秒）を提案する。tokenは provider間で比較できず、quota semanticsも異なるため、共通budget単位に使えない。
5. **[結論] 事前に決めるべき固定値は3つだけである。** hard budget（時間・slot-seconds・quota）、guard tier H、blindingの有無。それ以外は導出値または事後更新可能なdefaultにする。
6. **[仮説] 現在の3つの premature assumption（2 round / 2 variants / 3 agent）は、E4 / E3 / E5 の結果を priorとして再公開できる。** ただしmechanismとしては採用しない。
7. **[結論] 小さなnで測るのだから、実験は「大きな効果しか検出できない」前提で設計する。** paired design、seeded ground truth、事前登録した判断ルールの3点で、n≈10–20でも意思決定に使える。

## 1. Dispatch前のselection手続き

### 1.1 入力（dispatch前に観測可能なものだけ）

primaryが数値化するのは次の7つです。既存の `02-operating-model.md` の decision card（8 factor、0–2評価）を置き換える提案です。理由は、既存cardの factor が mode を直接示唆する形になっており、mechanismの成立条件と対応していないためです。

| 入力 | 問い | 取り得る値 | 対応mechanism / cost |
|---|---|---|---|
| I1 objective type | 決めるのか、作るのか | `decision` / `artifact` | mode族の一次分岐 |
| I2 serialization cost | envelopeを書く時間 vs 自分でやる時間 | `>=` / `<` | C1 |
| I3 verifier | 良否を安価に自動判定できるか | `cheap-accurate` / `expensive` / `none` | M4の前提 |
| I4 outcome variance | approachが複数あり、質が実質的に違うか | `high` / `low` | M4の利得 |
| I5 late-failure cost | 誤りが後で発覚した時のコスト | `high` / `low` | M3、M6 |
| I6 binding constraint | 今の律速は何か | `agent-time` / `human-review` / `quota` / `capacity` | C3、C5、C7 |
| I7 recurrence trigger | 再発する問いか。triggerはlocalか | `none` / `local-event` / `external-drift` | M7 |

I2 と I6 は他のどの入力より優先します。I2 が `>=` なら即 solo、I6 が `human-review` なら生成を増やすmodeを選びません。

### 1.2 決定手続き

```text
step 0  I2 が ">=" なら solo。終了。
step 1  I6 を確認する。
          human-review binding -> 生成量を増やさないmodeだけを候補にする
          quota / capacity binding -> 参加者数上限を capacity class limit と rate window から先に決める
step 2  I1 で分岐する。
          decision  -> §1.3 の consult 系
          artifact  -> §1.4 の produce 系
step 3  I5 が high なら、選んだmodeの後段へ独立verifyを必ず足す。
step 4  I7 が none 以外なら、この一回を lifecycle 化する候補として 04 の手続きへ回す。
step 5  mechanism を1語で宣言できるか確認する。できなければ solo に戻す。
```

### 1.3 decision型（何かを決める）

| I3 verifier | I4 variance | 選ぶもの | mechanism |
|---|---|---|---|
| any | low | solo（+必要なら1回のcritique） | M3 |
| none / expensive | high | **独立意見の列挙**（`panel`） → primary判断 | M5 |
| any | high、かつ意見が対立した | **bounded claim exchange**（`deliberation`） | M5 + M3 |
| cheap-accurate | high | **小さな実験を1本**（案を作らず測る） | M4 |

**[結論] 4行目が現doc setに存在しない選択肢です。** 「決定のために安価な測定が可能」なとき、panelやdeliberationよりも「spikeを1本書いて測る」方が速く、確実で、reviewable surfaceも小さい。現在のrouting listは `panel` → `critique` → `deliberation` → `variants` の順で、**測定を最後に置いています**。measurableなら測定を先に置くべきです。

### 1.4 artifact型（何かを作る）

| I3 verifier | I4 variance | I5 late-failure | 選ぶもの | mechanism |
|---|---|---|---|---|
| any | low | low | solo または `dispatch`（M2目的） | M2 |
| any | low | high | `dispatch` + 独立verify（maker-checker） | M2 + M3 |
| cheap-accurate | high | any | `variants`（staged gating必須、§2.3） | M4 |
| expensive / none | high | any | **`panel` でapproachを絞ってから1本作る** | M5 |
| any | any | 極めて高い（security境界、data loss） | `dispatch` + maker-checker + red-team | M3 + M6 |

**[結論] 3行目と4行目の分岐が `variants` の適用条件です。** verifierが無いなら複数実装しても選べません。approachの選択をpanelで済ませ、実装は1本にするのが安価です。現doc setの「Competing implementation」例（`panel` → `variants` → blinded evaluator）は、verifierが cheap-accurate な場合にだけ正しい構成です。

## 2. 固定値を作らない導出

### 2.1 round数

**mechanism（採用する停止規則）**: 「直前のroundで claim status が1件も変化しなかったら停止」。TR1として [`03`](03-interaction-protocols-and-comparison.md) §3 に定義します。

- 観測量: claim ledger 上の `open / accepted / rejected / test-needed` の遷移件数。**内容は保存せず、件数だけを記録します。**
- 帰結: 簡単な問いは1 roundで終わり、真に対立している問いは4 roundまで進み得ます。round数は出力であって入力ではありません。
- hard stop は round数ではなく **budget**（§2.4）です。budget到達時は failure ではなく「partial + 未解決claim一覧」を返します。

**prior（計画のために公開してよい値）**: 実測後に mode 別の p50 / p90 を公開します。E4 の結果として「p50=2, p90=3」が出れば、それは「2 roundぶんのbudgetを確保しておけ」という**計画上の目安**であり、2 round目で打ち切る**指示ではありません**。

**更新方法**: episode ledger（[`05`](05-repository-capabilities-and-roadmap.md) T1）から四半期ごとに再計算し、p90が変化したらpriorだけを書き換えます。mechanismは書き換えません。

### 2.2 参加者数（panel / fanout）

導出規則: **参加者を1人追加してよいのは、その参加者に固有の (観点 | evidence source | 担当する失敗様式) を名指しできる場合だけ。**

```text
participants = |{名指しできた独立観点}|  ただし ≤ min(capacity_limit[class], quota_headroom)
```

- capacity上限: `light=4 / write=2 / integration=1 / isolated=0`（`docs/agentctl.md`）。read-only panelは `light` classなので同時4が構造上の天井です。
- quota headroom: **[未解決]** provider別のrate windowが不明。判明するまでは、burst後にprimaryの応答が遅くなったら参加者を減らす、という運用的backoffで代替します。
- 「3 agentへ聞く」は、独立観点が3つ名指しできた結果として3になることはあっても、**典型値ではありません**。

### 2.3 variant数

導出規則: `variants` は「もう一度やり直すコスト」との比較で決めます。

```text
variants を選ぶ条件:
  I3 == cheap-accurate                       … verifierが存在する（M4の前提）
  かつ N * variant単価 <= 失敗時のrework単価  … best-of-N が保険として成立する
  かつ N <= capacity_limit[write]             … 並列だと思って直列にならない
  かつ 各variantへ異なるapproach仮説を割り当てられる … 候補間に分散がある
```

- **[結論] `write=2` との相互作用**: 3本目のvariantはwall timeをほぼ倍にします（2波に分割されるため）。「安価で明確な理由がある時だけ3」（現 `02-operating-model.md`）は、この構造を考慮していません。3本目を出すなら capacity を上げるか、3本目を `light` classの設計案比較に落とすべきです。
- **[結論] 同一approachの2本は最弱形**です。approach仮説を割り当てられないなら、N=1（solo/dispatch）にします。
- **更新方法**: E3 で verifier の retrodiction 精度を測り、精度が閾値未満なら `variants` 自体を封印します（案数の議論より前に来る判断です）。

### 2.4 duration と budget

**[結論] 絶対値の定数を置かず、相対値・派生値で表します。** 理由は、絶対値はproject規模・model速度・quota契約が変わると即座に陳腐化し、更新されないまま残るためです。

| budget | 表し方 | 根拠 | 更新 |
|---|---|---|---|
| elapsed | 「人間が部分回答を求めるまでの待ち時間」を primary が宣言 | C5 の実体は人間の待ち時間である | episodeごとに宣言、集計してprior化 |
| 計算資源 | **slot-seconds**（class別 slot占有秒の合計） | provider-neutral、既存 capacity lease の acquire/release から算出可能 | T2で自動計測 |
| provider quota | 「今日の interactive 用headroomの一定割合以下」 | 相対budgetは契約変更に自動追随する | headroom観測後に割合を調整 |
| human review | 「このcollaborationの成果をreviewする分」を先に確保 | 確保できないならdispatchしない | 実測bucketで校正 |
| recurring全体 | 「observed interactive slot-secondsの一定割合以下」 | schedule数の増加で総消費が勝手に増えない | 04 §4 |

**[結論] tokenを共通budget単位にしない**理由: (a) providerが返す単位が非対称（cached/reasoning/outputの扱いが異なる）、(b) subscription型はtokenよりrate windowが律速、(c) transcript保存を前提にせずtokenを正確に集計する手段がない。slot-secondsは `agentctl` が既に持つ lease timestamp から計算でき、この3つの問題を全部回避します。

### 2.5 provider構成

| 目的 | 割り当て | 根拠 |
|---|---|---|
| generation の多様性 | **role/objectiveの非対称化を先に使う。** provider差は E2 が有意差を示すまで投資しない | M3（commitment不在が主因） |
| evaluation | **cross-providerを優先する。** self-preference biasの回避価値が最も高い | M3の逆非対称（01 §1のM3） |
| capability依存 | providerのnative機能（sandbox mode、structured output、subagent discovery）が要件を満たすかで選ぶ | `agentctl doctor` の capability probe |
| 可用性 | rate window が枯れているproviderを避ける | C7 |

**[結論] providerを増やすことは diversity ではありません。** 増やしてよいのは、上表のいずれかの理由を名指しできる時だけです。

### 2.6 blindingの有無（context依存であることを明示する）

**[結論] blind first roundは「delegationが利用可能なとき」の default であり、無条件のdefaultではありません。**

| 状況 | blinding | 理由 |
|---|---|---|
| delegation可、独立agentを起動できる | blind | anchoring回避が実際に成立する |
| delegation不可、primary逐次 | **blind不能**。sequential critiqueへ切り替える | 同一contextを持ったまま独立には考えられない |
| 既に案が1つある（critique） | 案は見せる。ただしprimaryの**選好**は見せない | 批評対象は必要、誘導は不要 |
| 評価段階 | authorを伏せる。ただし完全な匿名化は困難（§3、B3） | self-preferenceと権威biasの低減 |

現doc set（`collaboration-model.md`、playbook、`AGENTS_TEMPLATE.md`）は blind first round を無条件defaultとして書いています。**delegation不可の縮退経路が同時に定義されているため、内部矛盾しています。** 上表を採用すれば解消します。

## 3. Experiment design（E1–E7）

### 3.1 統計的な誠実さ（先に書く）

**[結論]** このrepositoryで得られるnは、task種別ごとに10–30程度が現実的な上限です。この規模で検出できるのは大きな効果だけです。したがって:

- **効果量を報告し、p値を主張しない。** 「有意」という語を使わない。
- **paired design を優先する。** 同一task、同一fixture、同一baseで条件だけ変える。
- **ground truth を人工的に作る。** seeded defect / 既知結果の履歴を使い、判定の主観性を除く。
- **判断ルールを事前登録する。** 「効果量がXを超えたら実装する」を先に書く。事後に基準を動かせば moving evaluation になる。
- **失敗する実験を歓迎する。** 「差が出なかった」は、機能を作らない判断を正当化する最も安い結果である。

### 3.2 実験一覧

| ID | 検証するmechanism / assumption | 設計 | ground truth | 事前登録した判断ルール | 概算コスト |
|---|---|---|---|---|---|
| **E1** | M2（context分割） | 同一task pairを solo と narrow-context dispatch で実行 | **制約違反数**（scope逸脱、指定check未実行、既決事項の再議） | dispatch側の違反数が半減しなければ、そのtask sizeでM2を主張しない | 低。既存taskで並走可 |
| **E2** | M3（decorrelation）、A5（provider diversity） | 4 arm: self-review / same-provider fresh checker / cross-provider checker / red-team。seeded defect corpusへ適用 | **注入した既知defect** | cross-providerが same-provider fresh を検出率で明確に上回らなければ、生成側のprovider diversity投資を却下する | 中。corpus作成が初期費用 |
| **E3** | M4（verifier強度）、A2（variants=2） | 結果が既知の候補patch対をevaluatorへ提示し、retrodictionさせる | **後から判明した実際の優劣** | retrodiction精度が偶然を明確に上回らなければ `variants` harness（T3）を作らない | 低。履歴を使う |
| **E4** | A1（2 round / 3 round） | `deliberation` を round cap 無しで budget まで走らせ、status変化が止まる位置を記録 | なし（分布そのものが結果） | 観測分布を prior として公開。mechanismはTR1のまま | 低 |
| **E5** | A3（3 agent）、M5の飽和 | 1/2/3/4観点で panel を実行し、人間が material と認めた**新規**選択肢を数える | 人間判定（事前に material の定義を固定） | 飽和点を prior として公開。上限は capacity limit | 中 |
| **E6** | C5 が binding か | 同一task classで solo と fanout の **accept までの総時間**（人間review時間を含む）を対で測る | 実際のaccept時刻 | fanoutが総時間を短縮しないなら、routing順を書き換え、fanout推奨を下げる | 中。最も重要 |
| **E7** | M7（event vs schedule） | 同一checkを schedule版 と event版 で並走。read-only、disabled-by-default | 検出遅延、重複run数、no-change run率 | eventが遅延・重複で優越すれば、in-repo trigger checkはschedule登録を禁止する | 中。schedulerの最小実装が前提 |

### 3.3 実行順序と依存

```text
E6 ─┬─> routing順の確定（最優先。結果次第で他の実験の優先度が変わる）
E1 ─┘
E2 ───> maker-checker / red-team の標準構成と provider割り当て
E3 ───> variants harness (T3) を作るか作らないかの gate
E4 ─┬─> deliberation の prior 公開（mechanismは先に採用してよい）
E5 ─┘
E7 ───> R3 の scheduler pilot の前提（04）
```

**[結論] E6 と E1 を先に置く理由**: この2つは既存のtaskへ寄生できて追加コストがほぼゼロであり、かつ結果が routing 全体の向きを決めます。E3 は `variants` 実装の gate なので、T3 の前に必ず通します。

### 3.4 各実験の失敗条件

- E1/E6: task heterogeneityが大きすぎて対にならない → task classを粗く定義し直す（例: 「単一fileのbug fix」「複数moduleの機能追加」「調査のみ」）。それでも対にならなければ、その task class での測定を諦め、guidanceのみとする。
- E2: seeded defectが現実のdefect分布を代表しない → corpusを実際のrevert / follow-up commitから作る。それでも代表性が疑わしければ、検出率の**相対比較**にのみ使い、絶対値を主張しない。
- E3: 履歴上の候補patch対が足りない → E3 を保留し、`variants` も保留する（作らないのが安全側）。
- E4: budgetが小さすぎて自然停止が観測されない前に打ち切られる → budgetを一時的に緩めた探索runを少数だけ実施する。
- E5: 「material な新規選択肢」の判定が主観的 → 事前に定義（「この選択肢が採用され得ると primary が判断した」）を固定し、判定を1人に固定する。
- E7: schedulerが未実装 → E7 は R3 と同時にしか実施できない。それまで M7 の event優越は論理的主張のまま置く。

## 4. Metrics

### 4.1 使う（primary metrics）

すべて content-free で、transcript保存を必要としません。

| metric | 定義 | 何を守るか |
|---|---|---|
| **time-to-accepted-decision** | dispatch開始から、人間/primaryが成果をacceptするまでの実時間 | C4 + C5 + C6 を含む唯一の総合指標 |
| **material findings per human review minute** | 人間が material と認めた finding 数 ÷ review 実時間 | review surface のinflationを penalize する |
| **rework rate** | 同一objectiveに対する後続修正jobの発生率 | 「速く終わった」の見かけ倒しを検出 |
| **escaped-defect rate** | integration後に発覚した defect / integration件数 | maker-checker を省いた時の代償を可視化 |
| **integration conflict rate** | `job collect` の overlap / blocker 発生率 | C6 の実測 |
| **budget breach count** | elapsed / slot-seconds / quota の超過回数 | 制御が効いているか |
| **claim status change per round** | round別の遷移件数 | TR1 が機能しているか、debate theater の検出 |
| **decisive-evidence rate** | 決定を変えた evidence が「実行可能な test / 測定」だった割合 | 議論より測定を選べているか |

### 4.2 使わない（explicitly rejected）

agent数、message数、token量、round数そのもの、議論時間、参加provider数、consensus率、行数、生成file数。理由は 01 §5 の anti-pattern 1・3・6 と同じで、いずれも「多いほど良い」方向へ運用を歪めます。

**[結論] round数は metric ではなく観測される出力**です。E4 では round数の分布を測りますが、それは prior を作るためであり、round数の増減を成果として評価するためではありません。

## 5. Learning loop

```text
episode（1回のcollaboration）
  -> content-free episode record を1件書く（T1）
  -> 四半期ごとに mode/task class 別に集計
  -> 更新するのは tier D の default と prior だけ
  -> tier H（hard guard）は集計では変えない。変更は明示的な設計判断とする
  -> 更新履歴を残し、いつ何を根拠に変えたかを追跡可能にする
```

### 5.1 episode record（content-free、最小案）

```yaml
episode_id: <ULID>
task_class: <粗い分類>           # 例: single-file-fix | multi-module-feature | investigation
objective_type: decision | artifact
declared_mechanism: [M1, M3]     # 01のID。1語で宣言できたか
binding_constraint: agent-time | human-review | quota | capacity
mode: <選んだmode>
participants: {count: N, roles: [...], providers: [...]}   # promptもtextも保存しない
rounds: N
claim_status_changes_per_round: [3, 1, 0]
blinding: first-round-blind | shared-context | sequential | none
rubric_preregistered: true | false
budget: {elapsed_s: N, slot_seconds: {light: N, write: N}, breaches: 0}
human_review_minutes_bucket: <5 | 5-15 | 15-60 | >60
outcome: accepted | partial | rejected | escalated
decisive_evidence_kind: test | measurement | argument | none
rework_job_ids: [...]
integration: clean | conflict | reverted | not-applicable
```

**[結論] これは task/result schema v1 とは別contractにします。** 現doc setのC3方針（「観測で価値が確認できたfieldだけschema化」「native session IDやtranscriptを共通schemaへ固定しない」）に同意します。加えて、**最初からschemaにせず、Markdown表かJSON Linesの追記で始めるべきです**。schema化はfieldが安定してからで十分で、早すぎるschemaはC8を増やします。

### 5.2 更新規則

| 対象 | 更新頻度 | 更新の根拠 | 変更してはいけないもの |
|---|---|---|---|
| round prior（p50/p90） | 四半期 | E4 + episode record | TR1（停止機構） |
| variant数 prior | E3 更新時 | verifier精度 + capacity limit | M4の前提条件 |
| panel参加者 prior | 四半期 | E5 + 観点の名指し可能性 | 「名指しできない参加者は追加しない」規則 |
| elapsed / slot-seconds default | 四半期 | breach率と待ち時間の実測 | hard budgetを持つこと自体 |
| routing順 | E6 の結果が出たとき | 総時間の実測 | tier H |
| mode語彙 | 年1回、または C8 が観測 net gain を超えたとき | 使用頻度と誤選択の実測 | lane / role / mode の直交性 |

### 5.3 project単位の自由度

**[結論] projectごとの試行錯誤は「tier D の override を記録する」形で許します。** 承認プロセスは置きません。理由は、承認を要求するとC8が増え、実験が止まるからです。代わりに次を要求します。

```yaml
# project の .agent/config.json 相当へ置く想定（05 T8）
collaboration_overrides:
  variants_max: 3
  reason: "benchmark fixtureが安定していて verifier 精度が確認済み"
  recorded_at: 2026-08-26
  revisit_after_episodes: 10
```

`reason` と `revisit_after_episodes` が空のoverrideは、レビュー時に削除候補として扱います。これで「危険な自由度」ではなく「忘れられた自由度」を回収できます。tier H に触るoverrideは機構的に拒否します（04 §2）。

## 6. 反対意見、unknown、失敗条件

### 反対意見

- **反対1: 停止規則を claim status 変化に依存させると、ledgerを書く手間（C1の一種）が増える。** 正しい。緩和は、ledgerを「ID・一行の主張・status」の3列だけに制限すること。それ以上の構造化はC8です。5行を超えるledgerが必要な議論は、そもそもdeliberationではなく測定で決めるべき問題である可能性が高い。
- **反対2: slot-secondsは provider の実消費と相関しない。** 部分的に正しい。slot-secondsは「このrepositoryの実行資源の占有」を測る単位で、providerの課金とは別物です。ただし共通budgetとして必要なのは前者であり、後者は provider 側のdashboardで見るべきものです。**[未解決]** 両者の相関は測っていません。
- **反対3: 相対budget（interactive headroomの割合）は、headroomが観測できないと機能しない。** 正しい。**[未解決]** 現在headroomの観測手段がありません。それまでは絶対値の暫定defaultを置き、根拠を「暫定」と明記して、observation後に相対値へ移す必要があります。これは 05 の R1 に含めます。
- **反対4: 実験を7本並べるのは重すぎる。** 妥当。E6 と E1 の2本だけで routing の向きは決まり、E3 は `variants` を作らない限り不要です。最小構成は **E6 + E1** です。残りは対応する機能を作る直前のgateとして実施すれば足ります。

### Unknown

- **[未解決]** provider別 rate window / credit の観測手段。§2.4 の相対budgetの前提。
- **[未解決]** human review throughput の実測値。C5 binding判定の前提。
- **[未解決]** seeded defect corpus が現実のdefect分布を代表するか。
- **[未解決]** task class の適切な粒度。粗すぎれば対にならず、細かすぎればnが足りない。
- **[未解決]** episode record を誰が書くか。primaryが自動で書けなければ記録は続きません。T1の設計課題です。

### 失敗条件

1. episode record の記入率が半分を切った → 記録項目を3つ（mode / outcome / human review bucket）まで削る。それでも続かなければ測定を諦め、guidanceのみに戻す。
2. E6 で fanout が総時間を短縮しなかった → 01 §2 の序列を正式採用し、routing の `fanout` 優先度を下げる。この文書の §1.3–1.4 はそのまま使える。
3. tier D override が理由なしで増殖した → override機構を撤去し、defaultを固定する。撤去はconfig fieldの削除だけで済むよう、05 T8 で分離しておく。
4. prior の更新が一度も判断を変えなかった → prior の公開をやめ、budgetのみで運用する。
