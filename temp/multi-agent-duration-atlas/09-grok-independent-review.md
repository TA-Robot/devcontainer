# 独立実験設計レビュー: multi-agent duration atlas

対象は `temp/multi-agent-duration-atlas/` の8文書と、`docs/agents/collaboration-observation.md`、`docs/agents/representative-scenarios.md`。live実験・ファイル編集・web参照はしていない。

---

## 1. 結論

**重大な基盤不足。** 計画の意図（global routingを出さない、S/M/Lを時間で定義しない、人間のstopwatchを要求しない、有限batch）は保たれている。しかし「十分なcoverageのduration reference」という主張は、現状の設計では識別できない。

阻んでいるのは標本数ではない。次が未定義のまま Wave 2 以降へ進むと、atlasは条件付き時間表ではなく、交絡した終端時間の束になる。

1. model identity が alias 文字列で、effort が requested/applied を区別しない。
2. T2 / T4 / T6 が、現hookに存在しない envelope に依存し、欠測時に製品の主差（first-useful vs accepted）が潰れる。
3. 利用者待ちと、study側のoffline oracle が同一の T5/T6 に乗っている。
4. 「36 cell coverage」が family×size の見かけ上の格子で、実際の検索キー（oracle、ambiguity、language/stack、effort、execution surface）を潰している。
5. 自動注入 instruction、compaction、approval待ち、direct vs `agentctl` が dimension に入っていない。
6. Wave 6 の natural descriptor は、`collaboration-observation.md` が `unknown` とせよと言っている意味を、注釈surfaceなしに埋めようとしている。

Milestone A の fake clock ですら、model/effort identity と user-wait vs offline-score の schema を直してからでないと、後から series を切り直せない。

---

## 2. 重大な欠落

影響順。

### 2.1 Model / effort / drift が series キーになっていない

- `03` §4 は `model identifier` と `reasoning/effort setting` を「記録する」。
- `04` §7 の schema は `"model": "observed-id"` と `"reasoning": "observed-setting"` の平坦な文字列。
- `05` §2 の series は「provider/model/CLIと観測期間」。alias が同じなら backend 更新後も同一 series に混ざる。
- `01` §4.4 の environment card も CLI/model まで。effort が閲覧単位にない。
- `06` Wave 5 は provider/context/cache を一括し、effort を独立waveにしていない。

同一 alias の silent backend 更新、default モデル、unsupported effort の無視は、family や collaboration 差より大きく時間を動かす。ここが未識別なら、以降の cell は解釈不能。

### 2.2 first-useful / synthesis / accepted が観測不能なのに、観測できた前提で製品定義している

- `04` §1, §3, §9: T2/T4/T5/T6 は既存 ledger に無い。runner の allowlist annotation と progress envelope を前提にする。
- `docs/agents/collaboration-observation.md` 「What is deliberately unknown」: worker成果が最終判断を変えたか、correctness、人間review時間は hook からは不明。`semantics` は欠測のまま。
- `04` §3 の fallback は「最初の valid final/worker result を T2 とし `firstUsefulResolution=final-result-only`」。これで **first-useful ≈ accepted** になり、`01` §2-3 が分けよと言った指標が provider 間で非比較になる。
- T4（synthesis decision）も envelope 依存。無い構成では synthesis tail が `not_observed`。Wave 4 はまさにそれを測るwave。

欠測を 0 にしない方針（`04` §10）は正しい。しかし atlas の主製品が「T2 と T6 の差」である以上、欠測時の公開規則が「欄を空にする」だけでは足りない。**その provider×config では first-useful を掲載しない**と先に書く必要がある。

### 2.3 利用者待ちと offline scoring が同一 clock に乗っている

- `04` §2: `time to accepted result = T6 - T0`、`validation tail = T5 - T4`。
- `07` Milestone E: evaluator 時間を validation tail に含め、agent time と分ける。
- F02/F08/F09/F12 の gold/entailment 判定は、利用者が待つ online test ではなく study の事後 score になり得る。

offline oracle を T5 に入れると、design 系は evaluator ランタイムのぶん遅く見え、implementation 系の test 待ち（本当の user-wait）と混ざる。`representative-scenarios.md` が `process ready` / `first useful` / `total` / `validation` を分けているのは、validation が operator-visible だから。study-only scoring を同じ T5 に載せてはいけない。

### 2.4 「36 cell」が coverage の偽完了を作る

- `02` §4: 12 family × S/M/L を coverage 候補とし、全組合せは回さない。
- `02` §5: ambiguity / oracle / decomposability / language 相当 / artifact は size と直交、と宣言。
- `02` §2 の本来の cell は `family -> size/profile cell`。
- `06` Wave 2 と `07` §11 は family×size の 36-cell map を成果にする。

Wave 2 が埋めるのは **profile を潰した格子**。`exact + deterministic + Python` の F03-M と `open + weak oracle + docs` の F08-M が同じ「M」として並ぶ。`01` §2 が聞きたい「同じsizeでも言語・oracleで違うか」に、このmapは答えない。未測定を `unmeasured` と出す原則（`README` 原則5）と矛盾する見かけの完了になる。

### 2.5 Task envelope の外にある duration 支配項が dimension に無い

`03` §2 は capsule / snapshot / visible docs を freeze する。freeze 対象外で時間が動くもの:

| 欠落 | なぜ交絡するか |
| --- | --- |
| CLI が自動注入する AGENTS.md / CLAUDE.md / persona / MCP / skills | fixture isolation（`02` §3, `07` B）は gold を除くが、host instruction は残る |
| context compaction / auto-summarization | mid-task で T2 以降が別プロセスになる |
| permission / approval 待ち | wall-clock に人間が混入。`collaboration-observation.md` が測れないと言っている量 |
| execution surface（direct CLI vs `agentctl` job vs 旧 wrapper） | 既存ledgerは source を分けて集計せよと明記 |
| worktree / image pull 等の pre-T0 provision | `representative-scenarios.md` は worktree-ready を別計測。本計画の T0 は harness 受理 |
| provider prompt cache（repo cache とは別） | `03` §6 の cache は dependency/repo/Docker だけ |

同じ capsule digest でも、これらが違う run は同一 series ではない。

### 2.6 Schema-valid を useful と読んでいる

- `04` §3: review は schema を満たす最初の finding envelope。
- `04` §4 は fast-but-wrong を accepted に混ぜない。T2 側の命名は「first useful」のまま。

schema 通過は usefulness の識別子ではない。誤findingが T2 を発火する。quality は別 field にあるので data 上は残せるが、`01` の閲覧単位と README 例は「first useful evidence」と人間向けに書いてしまう。製品名が因果主張になっている。

### 2.7 Sequential stop が between-case を過小評価する

- `05` §3-4: 固定nを捨て、interval が `planningResolution` より狭い、または更新幅が resolution 未満なら停止。
- `family-characterized`（`01` §6）は「事前に定めた精度目標」。**最小 distinct case 数がない。**

easy な1 case を繰り返すと、within-case が小さいだけで characterized に上がる。`05` §4 Step D は「1 case / 1 window 偏りなら続ける」と書いてあるが、stop 規則の mandatory 条件ではない。optional stopping と Wave 2 の「測りやすい read-only S から」が重なると、初期 atlas の帯は下側に偏る。

### 2.8 README の例示が自分の rounding 規則を破っている

`README` の family-provisional 例は `4m20s` / `11m50s`。`01` §5 と `05` §6-7 は少数標本で分秒を目安のように見せるな、p95 を最大値の言い換えにするな、と言っている。例が運用者の期待値を作る。

### 2.9 Natural live に machine descriptor surface が無い

- `06` Wave 6: 通常taskへ machine-observable descriptor を付与し、人間 form は求めない。
- `collaboration-observation.md`: mechanism / relation / lifecycle は annotation source が無い限り `unknown`。event 数から後付け分類しない。
- `04` §9: 既存ledgerから後付け分類しない。controlled study では runner が catalog ID を発行する。

通常運用の task には catalog ID が無い。Wave 6 が family/size/oracle を埋める方法が、人間 form を禁止したまま未設計。ここを無理に埋めると、同文書が禁じている semantic fabrication になる。

### 2.10 Nested worker / internal retry / 二重計上が分析規則まで落ちていない

- `04` §10: parent/child 二重計上を correlation で防ぐ、とある。
- worker がさらに worker を出す場合の T3、aggregate worker time、peakConcurrent の定義が無い。
- `03` §11 の retry は harness の別 attempt。provider SDK retry、tool 再実行、agent 自己再試行は未分離。
- `collaboration-observation.md`: direct episode と `agentctl` outer は二重観測し得る。study record の `correlation.episodeIds` はあるが、集計時にどちらを user-wait の正本にするかの rule が `05` に無い。

---

## 3. Model / effort 設計

### 3.1 表現（run に必須）

平坦な `model` / `reasoning` 文字列を捨て、identity と settings を分ける。欠測は `unknown`。推測で埋めない。

```text
modelIdentity:
  requestedAlias        # ユーザー/harness が渡した名前。未指定なら null
  requestedSource       # flag | config-file | runtime-default | unknown
  resolvedId            # CLI/event が返した exact id。無ければ null
  identityConfidence    # exact | alias-only | default-unspecified | unknown
  snapshotHint          # provider が秘密なしで返す build/date/fingerprint。無ければ omit

generationSettings:
  requested[]           # {namespace, key, value} 例: codex.reasoning.effort=high
  applied[]             # 実行面が認めた値。観測不能なら空
  unsupported[]         # 明示 reject
  ignoredUnknown[]      # 受け付けたが applied が確認できない
  capabilityStatus      # supported | rejected | not-advertised | unknown

runtimeIdentity:
  provider
  cliName
  cliVersion
  cliSource             # container-image | host-sync | unknown
  imageDigest
  executionSurface      # direct-provider | agentctl-job | other
  permissionMode        # observed auto | observed-approval-gated | unknown
  authChannelClass      # 秘密なしの class。詳細は保存しない
  observedAt            # UTC
```

`namespace` は provider 固有キーを無理に共通 enum へ正規化しない。比較可能なのは **同一 namespace+key の applied 値** だけ。Codex effort と Claude thinking と Grok reasoning を一つの `high/medium/low` に畳まない。

### 3.2 Series キー（stratum）

同一 series とみなす条件:

```text
provider
+ identityConfidence ∈ {exact} なら resolvedId
+ identityConfidence ∈ {alias-only, default-unspecified} なら requestedAlias + 観測window
+ applied generationSettings の canonical encoding
+ cliVersion + cliSource + executionSurface
+ permissionMode
```

`alias-only` と `exact` を混ぜない。`requested=high` だが `applied` 不明の run を `high` セルへ入れない。`unsupported` / `ignoredUnknown` は **capability probe 結果** であり、duration cell ではない。

観測window の切り方は統計精度目標ではなく **non-stationarity 用の series 境界**。例として暦週は planning prior であり、hard な週次更新義務ではない。切る証拠は (a) resolvedId 変化、(b) CLI version 変化、(c) 同一 cell の accepted duration 分布が宣言済み `planningResolution` を超えて shift した、のいずれか。

### 3.3 Unsupported / provider-specific の実験手順

1. **capability probe**（live の duration 標本ではない）: provider × cliVersion ごとに、設定を1つずつ送り、reject / apply / silent を記録。role: coverage of the settings surface。失敗しても atlas の時間セルを埋めない。
2. **supported 設定だけ** を duration stratum にする。比較 block（`03` §8）は collaboration 比較なら model+applied effort を固定、effort 比較なら collaboration を固定。
3. silent ignore を検出できなければ、そのキーは diagnostic-only。`high が遅かった` と書かない。
4. default-unspecified は独立セル。`implicit default == ある明示値` と仮定しない。
5. cross-provider 比較は applied 設定が共通でないため、**同一effort帯の比較として出さない**。出すなら provider×model×applied-settings の並置だけ。

### 3.4 Server-side drift

CLI version は server 更新の識別子にならない。識別可能なのは:

- `resolvedId` の変化（ある場合だけ）
- 時間window を series に含めること
- 分布 shift を **stale 候補の diagnostic** にすること（自動で winner を出さない）

changelog の web 取得を正本にしない。run 時 capture と、shift detector の「この series はもう混ぜるな」フラグだけを使う。旧 series は削除せず `stale`。新旧を pool しない。

---

## 4. 追加すべき dimension

役割の定義:

- **primary stratum**: atlas の検索キーを分割する。違う値なら別 card。
- **blocking factor / covariate**: 記録し、比較 block で固定または解析で層別する。格子は埋めない。
- **diagnostic-only**: 解釈・欠測説明・汚染検出。時間帯の見出しにしない。

### Primary stratum

| Dimension | 理由 |
| --- | --- |
| task family | 既にある。oracle と T2 定義が family 依存 |
| size **profile**（S/M/L + oracle class + coupling/validation の組） | `02` §2 の本来の cell。S/M/L 単独は不十分 |
| collaboration relation class（C0/C1/CP/CC/CV/CD/CS） | 既にある |
| model identity confidence + resolved/alias キー | §3 |
| applied generation settings | §3 |
| execution surface（direct / agentctl） | 既存観測契約が別集計を要求 |
| session class（fresh / warm-task / warm-repo） | `03` §5。生成過程が違う |
| source series（fixture / historical / natural） | 既にある。昇格禁止も既にある |
| online vs 欠測の first-useful resolution | `final-result-only` の T2 を progress-envelope の T2 と並べない |

幅（CP の worker 数）と対話 depth（CD の exchange）は **stratum を掛け算しない**。既存の curve（`06` Wave 4）のまま、config card の内部表示にする。

### Blocking factor / covariate

| Dimension | 扱い |
| --- | --- |
| language / toolchain（Bash, Python, JS, Docker, 文書） | `01` §2 が問いとして持つが `02` §5 に無い。family が stack を決めないなら表示必須。spread がその study の `planningResolution` を超えたら post-hoc split（格子の事前埋めではない） |
| ambiguity | duration と T2–T6 gap を動かす。可能なら profile に入れる。入れられない natural は covariate |
| decomposability | collaboration 割り当ての **適格条件**。不適格なら `mismatched-decomposition`（`06` §6 既存） |
| artifact type / lane | 既出。family と完全相関なら重複表示だけ |
| knowledge locality（repo-only / docs / current-info） | 外部取得時間が reasoning に混ざる |
| CLI version, image digest, machine class, cliSource | series 境界または表示 covariate |
| cache: dependency / repo / Docker | `03` §6。基準 cell で一軸。全 family には掛けない |
| provider-side prompt cache | repo cache と別 field |
| time window, competing load, timezone | 既出。pool 時は blocking factor |
| risk | 時間より stop/cap/lane を変える。時間セルの主キーにしない |
| expected failure mode | F03/F10/F11 の支配項。family 内 covariate |
| repo size / index state | historical replay の隠れた規模 |
| permissionMode | auto 以外は user-wait 汚染。層別または invalid |

### Diagnostic-only

| Dimension | 使う理由 / 使わない理由 |
| --- | --- |
| token / 出力長 / tool-call count | 遅さの媒介。productivity KPI にしない（`05` §12, observation 分析規則） |
| thinking-token time vs tool-wait vs queue | 分解できるときだけ。無い provider は `unknown` |
| compaction / context-window occupancy | mid-run 過程変化の検出 |
| auto-injected instruction digest（path ではなく digest） | host leakage の再現条件。本文は保存しない |
| approval-wait intervals | 人間混入の汚染フラグ |
| harness overhead（Wave 0） | instrumentation bias（`05` §11） |
| evaluator calibration score / evaluator runtime | oracle 品質。offline score なら user-wait に入れない |
| event/category counts | 既存 ledger の範囲。意味推定に使わない |
| nested-worker detected | T3/aggregate の信頼度 |
| clock anomaly / suspend | `04` §10 既存 |
| residual Docker/disk | `06` §9, representative-scenarios 既存 |

**格子にしないもの（再掲）**: provider × family × size × config × width × effort × cache × load。`03` §9 の逐次 coverage は維持。ただし Wave 2 の完了定義を family×size から **family × profile × (C0, 1 model identity, 1 applied effort, fresh, 1 surface)** に替える。

---

## 5. 時間 reference の統計

### 5.1 公開の粒度は evidence state に連動させる

| State | 人間向け | 機械向け |
| --- | --- | --- |
| `unmeasured` | 欠測 | 欠測 |
| `single-observation` | 観測1件とその条件。帯を出さない | 生 duration |
| `same-case-repeat` | その case の観測範囲。family typical を出さない | case 内の全 sample |
| `family-provisional` | 丸めた帯 + n_cases/n_runs/n_accepted/n_censored + window | 生秒、case 別 median |
| `family-characterized` | 宣言した typical quantile 帯 + 不確実性 + censoring 注記 | hierarchical 推定量 |
| `stale` | 旧帯を残す。現行と pool しない。「superseded by series … on …」 | 旧 series 凍結 |

README 例の `4m20s` は `family-provisional` に使わない。display rounding は raw を変えない（`05` §6）。丸め単位はその study の `planningResolution` に合わせる。`planningResolution` の役割は **統計精度目標** であり、agent の停止規則でも universal default でもない。

### 5.2 Censoring と failure を typical から外へ出さない

公開は常に二枚:

1. **accepted-only typical** — 条件付き分布。ユーザーが「通ったとき」を見る。
2. **user-wait with censoring** — timeout / cancel / rate-limit を成功にしない。安全 cap までの restricted mean、または「cap までに未完了が k/n」。role: 計画時の待ちリスク。Kaplan–Meier 等を使うなら method/seed/tool version を aggregate に残す（`05` §5 の延長）。

`05` §6 の `12–18 min` 例は、accepted-only なのか全 outcome なのか書いていない。schema で固定する。provider incident / rate-limit は通常 variance と別 tag（`05` §7 既存）を維持。

p95 は adequacy を満たすまで出さない（既存）。adequacy を「5回」（`representative-scenarios.md`）から借りない（`README` 正本関係、`05` §7 既存）。何回なら p95 を出すかは study の tail 精度目標であり、本レビューは universal n を置かない。

### 5.3 Nested 構造を崩さない

表示の最小セット:

- n_runs, n_distinct_cases, n_accepted, n_timeout, n_invalid
- within-case spread と between-case spread を別行
- 観測期間（first/last）
- model identity confidence と applied settings
- first-useful resolution

family 推定は case-aware のまま（`05` §5）。run が多い1 case が全体を支配しない。stop 規則に **最低 distinct case 多様性** を入れる。具体数は universal にしない。役割は between-case 識別可能性。例: 「family-provisional にするなら複数 isomorphic case が要る」は規則、「3 variants」は仮の planning prior にすぎない。

### 5.4 標本が増えるとき

- 生 observations を捨てない。
- interval が狭まったら帯を更新し、evidence state だけ上げる。
- 新 sample が resolution 未満しか動かなくても、case 偏りまたは window 偏りがあれば state を上げない（`05` §4 Step D を promotion の hard 条件にする）。
- model/CLI/applied-settings が変わったら新 series。旧帯は historical。

### 5.5 偽精度を抑える rounding 規則（display policy）

役割は **表示**。推定値を変えない。

- `single-observation`: 丸めない。条件付きの1点。
- provisional: 上限・下限を `planningResolution` の粒度へ丸める。中央の秒は JSON にだけ置く。
- characterized: typical の端点も resolution 未満の桁を出さない。

---

## 6. 計測不能・識別不能なもの

harness は次を推定せず `unknown` / `not_observed` / 非掲載にする。`collaboration-observation.md` の原則と一致させる。

| 対象 | なぜ識別できないか | 誤った埋め方 |
| --- | --- | --- |
| alias だけの server 側 weight | CLI version と alias は backend を一意にしない | changelog や「同じ名前」で series 継続 |
| silent ignore された effort | applied が取れない | requested 値で層別 |
| schema-valid だが人間にとって useful か | 人間入力を禁止している | T2 を usefulness と呼ぶ |
| worker が最終判断を変えたか | 既存 hook の unknown | event 列から T4 を推測 |
| 人間の review / 画面注視時間 | observation 契約が明示 | reviewProxy を synthesis tail にする |
| progress envelope の無い first-useful | fallback で T2=final | provider 間の first-useful 比較 |
| natural task の family/size/oracle | catalog ID も form も無い | episode から後付け分類 |
| 対実構成の因果効果（unpaired live） | `05` §11, `06` Wave 6 既存 | natural を config 差の根拠にする |
| 未来の同一 task の時間 | atlas は過去観測（`01` §1） | stale を現行目安として出す |
| thinking vs tool-wait vs queue | provider が出さない | 終端時間から内訳を按分 |
| prompt cache hit | 報告されないことが多い | repo warm と同一視 |
| auto-instruction の因果効果 | digest は記録できても効果は実験無しでは不明 | 「同じ capsule だから同じ」 |
| within-case 差の原因（生成 vs 混雑 vs 経路） | 一つの duration に畳まれている | 分散を「モデルのばらつき」と書く |
| ネスト worker を含む真の aggregate | 未観測なら合計は下限 | peakConcurrent から推定 |
| 課金・残 quota の絶対量 | 秘密・subscription 詳細を保存しない（`06` §9） | 時間の安さ＝コストゼロ（`05` §12） |
| 弱oracle family の accepted-result | 機械 acceptance が無い | LLM judge の満足を T6 にする |
| counterfactual（測っていない config の時間） | 原則5 | 近傍 cell の補間 |

`not_applicable`（構成にその landmark が無い）と `not_observed`（取るべきなのに hook が無い）と `unknown`（意味が定義不能）を混ぜない。`04` §1 の前二者に、意味定義不能の第三を足す。

---

## 7. 修正提案

Must / Should / Later。実装コードではなく計画文書の変更。

### README

| 優先度 | 変更 |
| --- | --- |
| Must | 例示を `single-observation` か、帯なしの raw に替える。`4m20s` 型の provisional 例を削除 |
| Must | 成果物の検索キーに `resolved/alias identity`、`applied effort`、`executionSurface`、`firstUsefulResolution` を書く |
| Should | 「36 cell」を coverage 完了条件として出さない。候補 family 数である旨を明示。役割は **coverage 候補の列挙** であり達成ノルマではない |

### 01-objective-and-reference-output.md

| 優先度 | 変更 |
| --- | --- |
| Must | first-useful の公開条件: `firstUsefulResolution=progress-envelope` かつ schema+family contract を満たす場合のみ。それ以外は欄を出さない |
| Must | 指標表に (a) user-visible online acceptance、(b) offline study score を分離。T6 を両方に使わない |
| Must | Configuration card の列に model identity / applied settings / surface を追加。collaboration だけ横並びしない |
| Must | `critical-path-active` を `04` の derived と一致させるか、01 から落とす。今は 01 にあって 04 に無い |
| Should | Family card の typical に n_cases, n_censored, identityConfidence, 観測window を必須化 |
| Later | Exchange curve の人間向け要約。計測契約が通ってから |

### 02-size-model-and-task-corpus.md

| 優先度 | 変更 |
| --- | --- |
| Must | Wave 2 用の公開単位を family×size から **family × size-profile** に戻す。各 candidate に ambiguity, oracleStrength, decomposability, language/stack, artifact の設計値を書く |
| Must | language/toolchain を §5 の必須 axis に入れる |
| Must | isomorphic の操作的定義。同じ descriptor ベクトル + 同じ oracle class + 同程度の change surface。主観の「似たバグ」は不可 |
| Must | F08/F07/F12 は accepted-result を欠測にし得る、と family ごとに書く。無理に T6 を作らない |
| Should | このリポジトリ stack（Python/Bash/JS/Docker/agentctl）への偏りを generalization 限界として family card に出す |
| Should | historical replay の leakage チェックリスト（future commit だけでなく blame, tag, 修正済みコメント, gold path） |
| Later | 他 stack の fixture generator。今の repo に sample app を足さない制約は維持 |

### 03-experimental-dimensions.md

| 優先度 | 変更 |
| --- | --- |
| Must | §4 を §3.1 の identity object に置換。effort を Wave 5 の「ついで」から独立した stratum 規則にする |
| Must | 比較 block の固定条件: collaboration 比較なら model identity + applied settings + surface + session class + permissionMode を freeze |
| Must | auto-injected instruction digest、compaction 発生、provider prompt cache、execution surface、pre-T0 provision を dimension に追加し、stratum/covariate/diagnostic を明記 |
| Must | approval-gated run を user-wait 標本から除外または `contaminated`。study は auto で回す |
| Must | 設定 capability probe を duration wave の前に置く |
| Should | CP width と CD depth は stratum 非乗算と明文化（本文に既にある方針を coverage 順から除外する） |
| Should | nested delegation を in-scope にするか、検出したら invalid/diagnostic にするかを決める |
| Later | warm context の replay 可能 history digest の作り方。初期は fresh のみを因果比較に使う |

### 04-measurement-and-data-contract.md

| 優先度 | 変更 |
| --- | --- |
| Must | schema から `providers[].model/reasoning` を削除し、`modelIdentity` / `generationSettings` / `runtimeIdentity` を必須化 |
| Must | landmark を分割: `T5_online`（user-visible test/build）、`T_score`（offline oracle、user-wait 外）、`T6_user`（結果が利用者に渡った時刻） |
| Must | T2 の定義を「schema-valid first artifact」とし、製品文言の useful を外す。quality は別 field のまま |
| Must | provenance に `unknown` に加え、landmark 欠測時は derived duration を key ごと omit（0 も `null` も入れない） |
| Must | first-useful を最終結果へ fallback しない。`not_observed` のまま |
| Must | `reviewProxy` を T4 の代用にしない、と observation 契約への明示参照 |
| Must | pre-T0（worktree ready, image pull, cache restore）を任意 landmark として分離。`representative-scenarios.md` の worktree-ready と整合 |
| Should | failureClass enum: timeout-cap, rate-limit, provider-refusal, approval-wait, nested-worker-untracked, gold-leak, clock-anomaly |
| Should | dialogue の「decisive evidence」を allowlist count に限定する契約を、CD を測る前に family ごとに書く |
| Later | token/tool 内訳。provider が出す範囲だけ |

### 05-sampling-and-analysis.md

| 優先度 | 変更 |
| --- | --- |
| Must | `family-characterized` / stop 規則に distinct-case 偏りと window 偏りを hard 条件として入れる。resolution 未満の更新幅だけでは上げない |
| Must | typical 帯の母集団（accepted-only vs censoring-aware user-wait）を schema で固定し、両方出す |
| Must | 同一 cell に `final-result-only` と progress-envelope を混ぜない |
| Must | direct episode と `agentctl` outer のどちらを user-wait 正本にするか。二重計上の分析規則 |
| Should | 分布 shift detector を stale 候補 diagnostic にする。自動 routing には使わない |
| Should | Wave 順序バイアス（read-only S が先）を初期 atlas の明示限界にする |
| Later | hierarchical bootstrap の実装詳細。今は method 記録義務だけでよい |

### 06-execution-waves-and-safety.md

| 優先度 | 変更 |
| --- | --- |
| Must | Wave 0 の後に **Wave 0.5 capability/identity probe** を入れる。model resolve、unsupported settings、approval mode、progress envelope の有無 |
| Must | Wave 2 の成果を 36-cell 完了から「profile 付き C0 map、未測定 profile は unmeasured」へ変更 |
| Must | Wave 4 の入場条件: T2/T4 が `not_observed` でない execution surface 上だけで collaboration を測る |
| Must | Wave 6 は descriptor を埋めない。timing/outcome と opaque correlation だけ。family 集計に入れない |
| Must | 実験は permission auto、primary checkout 禁止、nested worker 方針を safety に書く |
| Should | write/Docker は per-run disposable。layer cache の持ち越しを paired block の交絡として扱う |
| Should | interactive 優先の検出方法が未定義。未検出なら competingLoad=`unknown` |
| Later | natural へ catalog を後付けする machine annotation。observation 文書の Later と同じゲート |

### 07-implementation-roadmap.md

| 優先度 | 変更 |
| --- | --- |
| Must | Milestone A の schema に identity/settings/online vs offline clock を含める。後付け migration を前提にしない |
| Must | Milestone C の成功条件: resolved vs alias、applied vs requested、progress envelope 有無、execution surface を **1 canary で証明**。取れなければその指標は非掲載 |
| Must | 最小 useful release（§11）から「複数 family の具体的時間帯」を外すか、`single-observation` に限定。provisional 以上を初期ノルマにしない |
| Should | Milestone B の isolation test に host instruction digest と gold/future leakage を追加 |
| Should | evaluator を online path に置かない API。score は artifact 後段 |
| Later | sampler の adaptive 配分。clock と identity が通るまで作らない（§12 の方針は維持） |

### docs/agents/collaboration-observation.md との関係（計画側の追記）

atlas 側 README「正本との関係」に Must で書く:

- 既存 ledger は study の T2/T4/T6 を持たない。
- study runner の catalog annotation は **明示開始した finite study の中だけ** 有効。
- 通常運用 episode の semantics を duration atlas の family へ写さない。
- `reviewProxy` は synthesis tail ではない。

`representative-scenarios.md` からは、5回/p95 を借りない既存方針を維持し、借りるのは **worktree-ready と validation の分離、失敗を消さない、fixture と live を混ぜない、residual resource** だけ。

---

## 8. 最小 pilot

目的は coverage でも精度でもなく、**設計が壊れていることの検出**。数値の役割を括弧で書く。universal な agent 数・round 数・反復 default ではない。

### 入れないもの

- 12 family、L、Docker cold、cross-provider、width curve、natural live、p95、characterized 判定。
- T2 fallback を「とりあえず動かす」ための実装。

### 構造

**P0. Fake clock（live なし）**

既定の Wave 0。T0–T6、missing landmark、timeout、parent/child 非二重計上、content allowlist。role: instrumentation の falsification。

**P1. Identity / settings probe（時間atlasに載せない）**

1 execution surface、1 短時間 case。

条件例（coverage of capture paths、統計精度ではない）:

- alias default
- explicit alias
- supported setting 1つ
- unsupported setting 1つ
- approval-gated が観測されるなら、その run を duration から除外できること

Gate: `requested` と `applied` が区別される。unsupported が `high` セルに入らない。`identityConfidence` が欠測で exact 扱いにならない。

**P2. User-wait vs offline score**

oracle の強い family 1つ（F02 または F03。oracle が機械で閉じるための **coverage** 選択であり、family 代表値ではない）。size は S のみ（**safety/cost cap**: L で設計バグを焼くのを避ける）。

online test と gold score を別 timestamp に出せること。gold を T5_online に載せたら fail。

**P3. T2 非掲載規則**

progress envelope がある surface と、無い surface（または無いと分かっている経路）を各1。

無い側の atlas 行に first-useful が出たら fail。最終時刻で埋めない。

**P4. Nested variance の表示契約**

同一 profile、C0、fresh、1 identity、1 applied setting。

1 case × 反復（within-case 識別の **hypothesis**。回数は study cap 内で最少）と、isomorphic 2 case（between-case が式に載るかの **hypothesis**）。

atlas が全 run を平坦 median だけ出したら fail。case 偏りで characterized に上がったら fail。

**P5. Envelope / instruction leakage**

同一 case を (a) 隔離 fixture、(b) host の AGENTS.md 等が残る workspace、で1回ずつ。role: confounder 検出。時間差を「真の効果」と書かず、digest が record に残るか、gold が読めたら invalid になるかを見る。

**P6. Surface 非混合**

同じ case を direct と `agentctl` で1回ずつ。同一 cell に pool したら fail。

Collaboration は、P3 が T2/T4 を観測できた surface に限り、C0 と C1 だけを **同じ case の paired block** で1組。C1 は subtask 境界が capsule で切れる case に限る（`06` §6 の適格条件）。width≥2 や dialogue round を default にしない。1 worker は「delegation の clock 分割ができるか」の **coverage** であり、最適人数ではない。

### 停止

設計 Gate が落ちたら live を増やさない。Wave 2 へ進まない。落ちた契約（identity、T2 非掲載、offline score、平坦 median、surface 混合、leak invalidation）を文書と schema で直す。

batch の wall-clock / rate / hard sample cap は **runaway 防止の cost cap**。到達しても provisional 以上へ昇格しない（`05` §3 既存）。cap の具体値は実行時 manifest で宣言し、本レビューは universal 値を置かない。

### この pilot で十分と言わないこと

P0–P6 は「測れる製品か」を落とすためにある。language 差、L、cache、load、CD/CP、cross-provider、natural 外的妥当性は検出対象外。それらを未測定のまま、初期 atlas に typical 分位を出してはいけない。
