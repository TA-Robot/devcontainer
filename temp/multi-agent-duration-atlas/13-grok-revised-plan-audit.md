独立レビューとして、改訂後の計画だけを読んだ。live計測・ファイル編集・Web参照はしていない。

# Duration atlas 改訂計画監査

対象: `temp/multi-agent-duration-atlas/` の改訂本文と `docs/agents/collaboration-observation.md`。`09` は前回Mustの正本、`10` は統合記録としてだけ使う。製品は経験的duration referenceであり、routing recommendationではない。

## 1. 判定

**conditionally ready**

前回の基盤欠落（identity/effortの平坦化、T2 fallback、online/offline同一clock、36枠の偽完了、naturalの意味捏造、reviewProxyの誤用）は計画から落ちている。falsification pilot（`07` §13 P0–P6）へ進む方向は正しい。

ただし Milestone A が凍結する **derived duration の式** と **quality-conditioned の母集団** が、改訂本文のあいだでまだ食い違う。これは標本を回せば分かることではなく、schemaに写す前に計画側で閉じる定義矛盾である。ここを直さずに fake clock を書くと、C0 baseline の online validation と弱oracle family の quality 面が、後から series を切れない形で固まる。

## 2. 前回Mustのclosure

出典は `09` §7。役割ラベルは今回の監査判断。

| 前回Must | 状態 | 根拠 |
| --- | --- | --- |
| README: 例示を `single-observation` / 帯なしrawへ。`4m20s` 型provisional例を削除 | **closed** | `README` 表示例は `observations: 1 run / 1 case / 0 censored`、`evidence grade: single-observation`。本文が band を作らないと明記。`11m50s` は単点のschema/example値であり、`05` §6 の「single-observationは丸めない」と一致 |
| README: 検索キーに resolved/alias、applied effort、executionSurface、firstUsefulResolution | **closed** | `README` 原則6、`01` §4.5。`firstUsefulResolution` は `progress artifact resolution` / `first-artifact resolution` へ改名済み（`03` §8、`04` §15） |
| 01: first-useful は progress-envelope のときだけ掲載。最終時刻へfallbackしない | **closed** | `01` §3「progress envelopeを観測できるsurfaceだけ掲載」。`04` §3 は T2 を contract-valid artifact とし、final時刻fallback禁止、欠測surfaceは非掲載 |
| 01: user-visible online と offline study score を分離。T6 を両方に使わない | **closed** | `01` §3 が online validation / user-result / quality-conditioned / offline scoring を別行。`04` §1 は T0–T6 と S0–S1。S1−S0 を user wait に足さない |
| 01: configuration card に identity / applied settings / surface | **closed** | `01` §4.3 列「Identity / applied settings / surface」 |
| 01: `critical-path-active` を `04` derived と一致させるか落とす | **partially closed** | `01` §3 は「復元不能なら非掲載」。`04` §2 は unrestorable なら critical path と呼ばず、`worker active union` を置く。名前付き derived key としては残存（§4） |
| 02: 公開単位を family×size-profile へ。candidate に ambiguity/oracle/decomposability/language/artifact | **closed** | `02` §4–5、`06` §5。36は candidate pool（coverage候補の列挙であり達成ノルマではない） |
| 02: language/toolchain を必須axisへ | **closed** | `02` §6。registry（`02` §5）にも Language/stack 列 |
| 02: isomorphic の操作的定義 | **partially closed** | `02` §2 は size descriptor vector + oracle/ambiguity/artifact + 同程度の change/context surface。language/toolchain が isomorphic 条件に入っていない（§5） |
| 02: F07/F08/F12 は online accepted 欠測を許す | **closed** | `02` §4 末段。弱いjudgeで accepted を捏造しない |
| 03: identity object へ置換。effort を独立stratum規則に | **closed** | `03` §4、`06` §3 Wave 0.5、`06` §8 Wave 5A |
| 03: 比較blockの freeze（model+applied+surface+session+permission） | **closed** | `03` §9。instruction digest も freeze |
| 03: instruction digest / compaction / prompt cache / surface / pre-T0 を役割付きで追加 | **closed** | `03` §5–8。stratum / covariate / diagnostic の分類あり |
| 03: approval-gated を automatic user-wait から除外 | **closed** | `03` §7、`06` §11 |
| 03: capability probe を duration wave の前へ | **closed** | `06` §3 Wave 0.5。capability coverage であり duration sample ではないと明記 |
| 04: flat `model`/`reasoning` 削除。identity/settings/runtime 必須 | **closed** | `04` §7, §9。欠測は推測しない |
| 04: T5_online / T_score / T6_user 分割 | **closed** | 名前は T5 / S0–S1 / T6。役割は分離済み |
| 04: T2 から useful 文言を外す。quality は別field | **closed** | `04` §3, §5。`01`/`README` も first contract-valid に置換 |
| 04: 欠測durationは key omit。0/`null` を duration にしない | **closed** | `04` §8, §15。landmark は `not_applicable` / `not_observed` / `unknown` |
| 04: T2 を最終結果へfallbackしない | **closed** | `04` §3, §14 |
| 04: `reviewProxy` を T4 代用にしない | **closed** | `04` §4、`README` 正本関係。observation 文書の proxy 定義と一致 |
| 04: pre-T0 を分離 | **closed** | `04` §1 P0/P1 |
| 05: characterized/stop に case偏り・window偏りを hard 条件 | **closed** | `05` §4。単一easy caseの反復では昇格しない。具体nは universal default にしない |
| 05: typical の母集団を accepted-only と censoring-aware の二面に固定 | **partially closed** | `05` §6, §10 と `10` §8 は二面表示を固定。typical の quantile 範囲は「report schemaで明記」のまま未凍結 |
| 05: progress-envelope と final-result-only を混ぜない | **closed** | `03` §8 primary stratum、`04` §15、`05` 禁止事項、`11` §3 |
| 05: user-wait 正本と二重計上規則 | **closed** | `04` §13、`05` §11。harness outer T0–T6 が正本。direct と `agentctl` は別series。worker は parent wall-clock に足さない |
| 06: Wave 0.5 | **closed** | `06` §3 |
| 06: Wave 2 を 36完了から profile付き C0 map + unmeasured へ | **closed** | `06` §5 |
| 06: Wave 4 入場は T2 と T4 を明示観測できる surface のみ | **closed** | `06` §7 |
| 06: Wave 6 は family/size を埋めず family band に入れない | **closed** | `06` §10。`collaboration-observation.md` の `unknown` 原則と一致 |
| 06: auto permission、primary checkout禁止、nested 方針 | **closed** | `06` §11、`03` §12 |
| 07: Milestone A に identity/settings と online/offline clock | **closed** | `07` §4 |
| 07: Milestone C は canary で取れなければ非掲載 | **closed** | `07` §6。1 canary は coverage probe であり統計精度目標ではない |
| 07: 最小releaseから複数familyの時間帯ノルマを外す / single-observation に限定 | **closed** | `07` §11 |
| 正本関係: 既存ledgerは T2/T4/T6 を持たない。study annotation は finite study 内だけ。通常episodeを family へ写さない。`reviewProxy` ≠ synthesis | **closed** | `README` 正本との関係、`04` §12 |

`09` の Should/Later（warm replay、hierarchical bootstrap 詳細、natural annotation surface、token内訳など）は未実装のままでよく、Must扱いにしない。

## 3. Model / effort

**識別可能になった。** requested / applied / unsupported は同じrunで並置できる。alias と resolved は confidence で切れる。比較blockは freeze 条件を持つ。impossible な「全providerで applied を証明せよ」は課していない。

観測:

- `03` §4 と `04` §7 の `generationSettings.requested[]` / `applied[]` / `unsupported[]` / `ignoredOrUnknown[]` で、requested を applied へ昇格できない。
- series 境界は resolved があれば resolved、なければ alias/default + 観測window。exact と alias-only を pool しない（`03` §4、`05` §2）。
- drift は resolved変化 / CLI変化 / 同一cellの分布shiftが `planningResolution`（統計精度目標。例: 2分・10分・30分は例示であり universal default ではない）を超えたとき `stale candidate`。旧series削除禁止（`03` §4、`05` §11）。
- 比較blockは collaboration 比較なら identity+applied+surface+permission+instruction digest を freeze。effort 比較ならその逆（`03` §9、`10` 「Model / effort測定の具体像」）。
- cross-provider は同一effort比較と呼ばない。namespace付き並置（`03` §4）。
- 2026-08-26 の local Grok CLI 1.0.5 は `--reasoning-effort` surface を持つが applied 証明には使えない、と本文が書いている。これは観測事実であり、Grok の effort 名つき cell を必須にしていない。

残る識別リスク（Milestone A の blocker ではない）:

- series key は **canonical applied** であり requested ではない。`applied=[]` の run は requested-high と requested-low が同一の applied-unknown series に入る。これは「requested で層別するな」と整合する。effort 名つき cell を作らず、band も出さないなら正しい。README 例は applied=unknown の **single-observation** を出してよい、という運用と読む。
- `capabilityStatus` が settings 全体の単一値なので、複数 key が混在すると粗い。schema/example の粗さであり、pilot が配列要素ごとの status に落とせる。
- cross-provider の series key が primary 単数か participant tuple かは Wave 5B まで未決。A の fake clock には不要。

impossible 要求は見当たらない。取れない applied / resolved / progress は非掲載であり、推測埋めを禁じている。

## 4. Clock / quality

大枠は coherent になった。user-visible、progress artifact、synthesis、online validation、offline score、censoring、二重計上の **役割** は分かれている。残るのは C0 で式が閉じない点と、quality 母集団の AND/OR である。

整合しているもの:

| 量 | 定義 | 欠測時 |
| --- | --- | --- |
| user-visible wait | T6−T0。harness outer 正本 | timeout は success にしない |
| first contract-valid artifact | T2−T0。progress envelope がある surface のみ | `not_observed`。final で埋めない。別 resolution と pool しない |
| synthesis | T4−T3。explicit envelope のみ | `reviewProxy` 禁止。推測禁止 |
| online validation | 利用者へ返す前の test/build（T5） | study score と別 |
| offline score | S0–S1。T6 の後でもよい | user wait に足さない。quality-conditioned は元の T6−T0 を抽出 |
| censoring | 安全 cap 到達は right-censored / timeout | accepted-only と cap までの未完了 k/n を併記 |
| 二重計上 | outer を sample 単位、component は相関、worker は aggregate のみ、nested 未追跡は lower bound | direct と `agentctl` は別series |

数の役割:

- `limits.wallClockMs: 3600000`（`04` §9）: schema/example の safety-censoring-cap
- `05` §6 の `6 / 17 / 2`: schema/example。統計精度目標ではない
- Wave 0.5 / P1 の default・explicit・supported/unsupported 各1: coverage probe
- P3 の progress あり/なし各1 surface: coverage probe
- C0/C1 の一 paired block（`07` §13）: delegation clock の coverage probe。agent 数の推奨ではない

定義矛盾:

1. **online validation が点 T5 しかなく、式が `T5−T4` 固定**（`04` §2）。S0–S1 は区間なのに、online だけ終端点。C0 で T4 が `not_applicable` なら、`04` §8 の omit 規則により **solo の test/build 待ちが非掲載** になる。`01` §3 はそれを利用者向け指標として出す。Milestone A の「duration derivation and missing landmark handling」（`07` §4）がこの式をそのまま凍らせる。
2. **`last-worker-terminal`（`01` §3、出揃うまでの待ち）と `worker terminal span`（`04` §2、T3−first worker start）が別量**。`first worker start` は landmark 表に無い。worker interval を first-class にする意図は `07` §4 から読めるが、01 の公開名と 04 の derived key がまだ一つの catalog ではない。`critical-path-active` も同様。
3. **quality-conditioned の母集団が三文書で違う。** `01` §3 は offline pass のみ。`02` §4 も弱oracleは offline で quality-conditioned を作れるとする。`04` §2 は「online/offline acceptanceを満たしたrun」、`05` §10 は「online/offline pass run」。F07/F08/F12 で onlineAcceptance=`unavailable` のとき、AND なら quality 面が空、OR/offline-only なら残る。
4. sampling unit は attempt（`05` §2）。recovery は derived（`04` §2、`05` §10）。ここは coherent。end-to-end recovery を accepted-only typical に混ぜないことだけ、集計時に明示が要る。pilot が答える実装問で足りる。

landmark の `not_applicable` / `not_observed` / `unknown` と duration omit は、観測不能の埋め方として observation 契約と揃っている。

## 5. Corpus / sampling

S/M/L を構造で定義し、nested variance を分け、36枠を完了条件にしない、という骨格は defensible な分位帯を **後で** 出すのに足りる。Wave 2 の single-observation を typical と呼ばない限り、偽coverageは設計上防げる。

守れているもの:

- size は時間ではない（`02` §1）。観測が長いだけでは label を変えない。
- `unmeasured` profile が残る（`02` §4、`06` §5）。12 family は coverage 候補の列挙。
- within-case と between-case を mix した flat median を出さない（`05` §1, §5）。hierarchical / case-aware。
- promotion: provisional は複数 isomorphic case、characterized は両variance + 複数観測block + valid identity/settings + 必要landmark。n は study の precision/coverage 設計。hardSampleCap は runaway 防止であり推奨回数ではない（`05` §3–4）。
- `single-observation` に band なし。provisional の丸めは `planningResolution`（統計精度目標）。
- natural は opaque shadow。family band に入れない。
- p95 を「5回」から借りない。

偽coverageがまだ入り得る点:

- **isomorphic 条件に language/toolchain が無い**（`02` §2 vs §5–6）。Python の F03-S と Bash の F03-S を同一 profile の between-case として pool できる。language は covariate で、spread が `planningResolution` を超えたら split（`03` §8）だが、split 前の provisional 帯は言語差を case 差へ隠す。これは Milestone B / Wave 2 の前に閉じるべき。A の fake clock は止めない。
- Wave 2 が read-only S から入る順序バイアスは、初期atlasの明示限界としてはまだ薄い（`06` §5, §14）。Should 相当。single-observation のまま出すなら実害は小さい。
- L と弱oracleは characterized に届かず provisional / unmeasured で止まる可能性がある。それは偽coverageではなく、coverage を偽らない停止。

「具体的な分位帯」は Wave 3 以降、かつ promotion 条件を満たした cell だけ。pilot P4 は flat median への潰れを落とす coverage probe であり、分位帯の確定実験ではない（`07` §13）。この切り分けは正しい。

## 6. Skill / context

progressive disclosure は **atlas 本体を SKILL.md に載せない** 設計になっている。通常 turn が L2 の bounded query 結果だけを見る構造は、製品要件と合う。残るのは cap の具体値と discovery の未決、あと compact 応答が evidence state を無視して band 欄を常設していること。

効いているもの:

- 経路は raw → versioned aggregate → deterministic script → compact skill（`11` §1, §11）。routing score と nearest-neighbor 推定を script が持たない。
- SKILL.md は抽出と script 呼び出しだけ。field enum は `profile-fields.md`、解釈は `interpretation.md`、詳細 methodology は devcontainer docs へ link。深い chain を作らない。
- 通常は L2 のみ。`audit` 以外で全runを展開しない。「全部見せて」も index + 明示 study。
- exact miss は `unmeasured` + adjacent **identifiers only**。stale は現行値として出さない。
- cap の役割は context-safety cap であり quality default ではない、と書いてある（`11` §5）。
- 「SKILL本文は500 lines未満という上限よりかなり短く」: 500 は skill-creator 側の上限（schema/convention）であり、本計画の品質ノルマではない。

残る deterministic bound / discovery:

- row/byte/token cap の **数値例すら safety cap として無い**。「実装時に設定可能」だけ。script が守るなら LLM context は守れるが、未設定のまま compare/curve が selected cells を返し得る。
- `11` §6 の compact 応答は first artifact / quality-pass を常に `<band>` と書く。`05` §6 の「single-observation に band を出さない」が skill 契約に落ちていない。
- data path が二系統: `07` §10 `generated/duration-atlas.json` 対 `11` §4 `generated/duration-atlas/current.json` + `manifest.json`。
- location は env → project aggregate → image/shared → not found の **候補順** で、最終決定は skill 実装開始時（`11` §8）。A の後、skill milestone の入口作業。
- `profile-fields.md` に coverage map や時間帯を置くと、参照層が小型atlasになる。今の本文は enum と意味に限定している。この境界を守ることが disclosure の実体。

skill は `07` §12 の最後、aggregate 安定後。Milestone A の blocker ではない。設計としては atlas 全注入を避ける方向で正しい。

## 7. Remaining Must before code

Milestone A（schema + fake clock）の前に計画で閉じるものだけ。pilot が落とすべき計測バグは含めない。

### 計画で直す（A の schema freeze 前）

1. **Derived duration catalog を 01 と 04 で一つにする。** 特に online validation を S0–S1 と同様の **開始+終端** にする。`T5−T4` を唯一の式にしない。C0 で T3/T4 が `not_applicable` でも、solo の test/build 待ちを omit せずに出せるようにする。あわせて `last-worker-terminal` と `worker terminal span`、`critical-path-active` と `worker active union` の公開名を対応づける。欠けた landmark に依存する key は今どおり omit。
2. **quality-conditioned の母集団を一文で固定する。** 推奨される読みは `02`/`01` に合わせ、offline pass の T6−T0 を quality 面の正本とし、onlineAcceptance が `pass`/`fail` の family では online fail をその面から外す。`unavailable` を AND 条件にして F07/F08/F12 の quality 面を空にしない。accepted-only と censoring-aware の二面は維持。typical quantile 自体は study の report schema / `planningResolution` に宣言する（統計精度目標。universal 分位ではない）。

この2つは定義矛盾であり、P0 の「missing landmark を試せ」とは別物。今の式を実装すると、欠測処理testが「C0 では online validation が無い」を正解にしてしまう。

### A に進めばよく、pilot / 後続 milestone の問い

- identity field の欠測を optional omit にするか status object にするか（`04` §7 が実装時統一と既に書いている）
- `capabilityStatus` を key 単位にするか
- worker start を landmark にするか interval record にするか（fake runner が worker を再生できればよい）
- P4 の case/repeat の具体形（coverage probe。manifest の study cap 内で、flat median 潰れを落とせる最少）
- language を isomorphic 条件へ入れるか、family band の pool 禁止にするか（**Milestone B / Wave 2 前**。A は止めない）
- applied-unknown series の表示規則の文言整理
- skill の path、cap 数値（いずれも context-safety cap）、single-observation で band を出さない compact 契約（skill milestone）
- cross-provider の composite series key（Wave 5B）

### 再提案しないもの

前回Mustとして既に入っている identity object、T2 非掲載、S0–S1、Wave 0.5、36枠の非ノルマ化、natural の opaque 化、`reviewProxy` 禁止、promotion の case/window hard 条件、outer 正本、approval contamination、nested disabled。

---

**観察 → 意味 → 判断。** 改訂は「終端時間の束」になる経路を閉じた。残っているのは、C0 と弱oracleという **一番先に測る cell** で、online validation と quality 面の式がまだ T4 前提 / AND 前提のままなこと。そこだけ計画を直してから Milestone A に入れば、P0–P6 は設計の falsification として使える。
