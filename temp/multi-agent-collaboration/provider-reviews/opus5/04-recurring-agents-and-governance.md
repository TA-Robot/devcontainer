# 04. Recurring agentとgovernance

Reviewer: independent Claude Opus 5 review
Date: 2026-08-26
Scope: brief Q6、Q9、およびQ10のscheduled / event-driven部分

label（[結論] / [仮説] / [未解決]）とmechanism ID（M1–M7）、cost ID（C1–C8）は [`01`](01-principles-and-value-mechanisms.md)、実験ID（E1–E7）と budget単位は [`02`](02-adaptive-selection-and-experimentation.md)、termination rule（TR1–TR10）は [`03`](03-interaction-protocols-and-comparison.md) の定義を使います。この文書で定義する **guard tier H / D / F**（§2）と **recurring budget pool**（§4）は 02 §2.4・§5.3 と [`05`](05-repository-capabilities-and-roadmap.md) から参照されます。

## 0. 要約

1. **[結論] 「recurring agent」という実体を作らないことが最大のguardである。** 存在するのは (a) trigger、(b) 有限job、(c) bounded carry-over artifact、(d) 人間のowner の4つだけである。現doc setの「finite job emitterに限る」という判断（`collaboration-model.md`、`01-pattern-catalog.md` §4）は正しく、この review でも維持する。
2. **[結論] scheduleの正当な適用範囲はM7の成立条件から導かれ、非常に狭い。** in-repo eventで検出できる変化はすべてevent-drivenが優越する（01 §1 M7）。scheduleが残るのは**外部原因のdrift**と**履歴の累積に対する集計**だけである。
3. **[結論] 最も効く重複排除は「回数の制限」ではなく「入力digestによるgating」である。** 入力（base SHA、lockfile、feed cursor、fixture）が前回と同一なら、run自体を発行しない。これはdedupe、alert fatigue、quota、stale contextの4問題を同時に減らす唯一の安価な機構であり、現doc setに存在しない。
4. **[結論] guardは「H: 機械的に拒否できる不変条件」「D: 測定で更新するdefault」「F: reviewで守る運用規則」の3層へ明示的に分ける必要がある。** 現doc setの "Required controls" は3層を混在させており、機械検査できない項目（open-ended objectiveを登録しない等）がhard guardのように見える。これは 01 §5 の anti-pattern 10（prose-as-invariant）である。
5. **[結論] `enabled` に加えて `enabled_until`（有限の失効期限）を必須にすべきである。** 「忘れられて動き続けるschedule」は現doc setのどのguardにも捕まらない。失効はdisableと同義で扱う。これがこの文書で最も費用対効果が高い追加提案である。
6. **[結論] enablement stateとcircuit stateは、repository worktreeの外に置かなければならない。** repository内のfileに置くと、Lane W agentがscope内で自分のguardを書き換え得る。ADR-0001の「Runtime state lives outside the repository」と `AGENTCTL_STATE_DIR` の既存設計がそのまま使える。
7. **[結論] 現在の`agentctl` 0.7には、recurring workが interactive workを押し退ける具体的な経路が3つ既に存在する。** (a) queue aging（既定300秒ごとに1段昇格、interactiveまで）、(b) `light=4` slotの共有、(c) `AGENTCTL_QUEUE_LIMIT=128` の占有。scheduler設計時にこの3つへ明示的なadmission controlを入れない限り、budget表だけでは runaway を防げない。現doc setはこの相互作用に触れていない。
8. **[結論] 「findingが出たこと」をrun failureとして数えてはいけない。** circuit breakerは infrastructure failure のみをkeyにする。これを混同すると、問題を見つけたsentinelが自分でcircuitを開いて監視を止める（01 §5 anti-pattern 7）。
9. **[結論] merge / pushの禁止は security boundary ではない。** 同一UID・同一credentialのcontainer内では、agentは原理的に`git push`を実行できる。実効的なguardは「control planeがintegration actionを一切提供しない」という**能力の不在**と、「recurring runにbypass profileを使わない」ことだけである。残余riskは隠さず記述する（§7）。
10. **[結論] `max_runs_per_day: 1`、`backoff_seconds: [300, 1800, 7200]`、`open_circuit_after: 3`、`retention_runs: 12` は、いずれも根拠のない global fixed count である。** 「有限の上限が存在すること」はtier H、「その値」はtier Dとして分離し、値には根拠・適用範囲・更新方法を必ず添える（§9.2）。

## 1. Lifecycle patternと、scheduleに値するもの

### 1.1 M7の成立条件からの再分類

`collaboration-model.md` の "Safe initial use cases" と `01-pattern-catalog.md` のF群を、01 §1 M7 の条件（変化がlocal eventを伴わないか / 早期検出が対応costを下げるか）で再分類します。

| 現doc setのuse case | 変化の原因 | この review の判定 | 理由 |
|---|---|---|---|
| frozen toolchain canary | 外部（provider CLI、Feature、base image） | **schedule 正当** | in-repo triggerを持たない。edge channelは起動時にhost CLIへ追随するため、同じfixtureが異なるCLIで走る |
| dependency / advisory drift | 外部（registry、advisory feed） | **schedule 正当**（cursor付き） | feed側の変化を検出する。cursorがあれば実質event |
| flaky-test候補の集計 | 内部履歴の累積 | **schedule 正当** | 単一eventでは判定できない。集計対象が増えたことが条件 |
| performance trend report | 内部履歴 + host noise | **schedule 正当**（fixture固定が前提） | trendは累積でしか出ない。noisy hostでは M7 が成立しない |
| `gc --dry-run` inventory | 内部状態の累積 | **event（job terminal）が優越** | 実triggerはjob終了。scheduleでも成立するが遅く冗長 |
| docs / API drift report | in-repo commit | **誤分類。event-triggeredが正しい** | public API surfaceへ触るcommitがlocal triggerになる（01 §1 M7） |

**[結論] 分類の判定規則は1行で書けます。** 「この変化を起こす原因は、このrepositoryのcommitか」。yesならevent、noならschedule。どちらでもないもの（履歴の累積）だけがschedule固有の領域です。

### 1.2 long-horizonをどう表現するか

**[結論] long-horizon agentは「常駐process」ではなく「有限runの列 + bounded carry-over + 人間が所有するgoal record」として表現します。** 現doc setの「会話sessionをrun間で暗黙resumeしない」は正しく、これを補うのは次の3点です。

| 要素 | 形 | 制約 |
|---|---|---|
| run間の記憶 | 明示的なcarry-over artifact（stable finding ID + status + 最小のevidence path） | schemaを持ち、最大年齢を持つ。transcriptを含めない |
| 長期のgoal | `decisions.md` / ADR / issue。**人間が所有する** | agentが書き換えない。scheduleのobjectiveへ埋め込まない |
| 各runの前提 | 「carry-overが空でも正しく動く」こと | 空から再baseline可能。これが stale context の唯一の根本対策 |

**[結論] `01-pattern-catalog.md` の pattern 54（backlog gardener）と 60（automation governor）は、この形では表現できません。** 前者はobjectiveがopen-endedでwrite-shaped、後者は「監視を監視するagent」が自分もrecurringになる自己言及を持ちます。governorは agent ではなく **audit ledgerに対する読み取りreport**（§8）として実装すべきです。pattern 55（decision-memory curator）と 58（longitudinal research diary）も、transcript保存を必要としない形へ制限しない限り登録できません。

## 2. Guard tier H / D / F

### 2.1 定義

| tier | 定義 | 判定方法 | 変更方法 |
|---|---|---|---|
| **H (hard invariant)** | structured dataに対する検査で機械的に拒否できる。違反にはcode変更が必要 | emitter / broker / validatorのcheck | 明示的な設計判断のみ。measurementでは変えない（02 §5） |
| **D (default)** | 有限の数値・選択肢。projectごとに override 可。理由と再検討条件を記録する | config field | episode / audit記録による測定（02 §5.2） |
| **F (practice)** | 機械検査できない運用規則。reviewとauditで守る | 人間のreview | guidance更新 |

**[結論] 「hard limitが存在すること」はH、「その値」はDです。** この分離を入れると、値の根拠が無いことを認めながら安全性を主張できます。現doc setは両者を混ぜているため、値を疑うとguard全体が緩んで見えます。

**[結論] tier Fをtier Hと呼ばないことが重要です。** 「open-ended objectiveを登録しない」は、文章から機械的に判定できません。これはFであり、Hのふりをさせるとreviewが省略されます。

### 2.2 tier H registry（recurring work向け）

以下はすべて structured data だけで判定できます。05 T8 で machine-readable な registry として保持し、tier Dのoverrideがこれらへ触った場合は機構的に拒否します（02 §5.3）。

| ID | invariant | 判定材料 |
|---|---|---|
| H1 | schedule作成時 `enabled = false`。enablement stateはrepository worktree外のowner-only stateにのみ存在する | state pathの位置 |
| H2 | `enabled_until` が存在し有限。失効したscheduleはdisabledとして扱う | 日時比較 |
| H3 | 1回のtrigger評価が発行するjobは最大1件。trigger処理はjobより長く生きるprocessを作らない | emitterのtransaction |
| H4 | 発行envelopeは既存 `.agent/schemas/task.schema.json` v1 検証を通る。bypass経路を持たない | 既存validator |
| H5 | scheduler発行jobの `permission_profile` は `safe` のみ。`trusted-fast` / `isolated-autonomous` はtemplate内容に関わらず拒否 | envelope field |
| H6 | 同一dedupe keyのrunが非terminalなら新規jobを発行しない（overlap `forbid` をemitter側transactionで担保） | run state |
| H7 | 有限の上限fieldが欠落・null・無限のscheduleは enable できない（wall time、attempts、per-day cap、budget share、alert cap） | field存在検査 |
| H8 | scheduleのdefinition path、enablement state、budget、circuit stateは、発行される全jobの `forbidden_paths` に入る（または worktree外にある） | scope検査 |
| H9 | control planeは merge / push / PR / release / destructive cleanup のactionを提供しない。`job collect` は read-only のまま | 能力の不在（回帰testで固定） |
| H10 | すべてのtrigger評価が append-only audit recordを書く。skip・suppress・budget拒否も記録する。recordはjob worktreeから書けない | audit ledger |
| H11 | circuitはemitterが開けるが、閉じるのはworktree外のowner actionのみ。scheduleは自分のcircuit・quota・budgetを変更できない | state所有者 |

### 2.3 tier D（値を持つもの）

`runs_per_day`、`backoff` 列、`open_circuit_after`、`retention_runs` / `retention_bytes`、`alerts_per_day`、carry-overの `max_staleness`、`enabled_until` の長さ、`max_concurrent_runs`（1超は idempotency 証明が前提）、recurring queue share、priority。値の根拠と更新方法は §9.2 の表にまとめます。

### 2.4 tier F（review規則。invariantと呼ばない）

- objectiveが有限でterminationを持つこと（「projectを良くし続ける」の排除）。
- 監視対象の外部textを instruction ではなく data として扱うこと（配送形式の一部だけがH。§7.3）。
- reportがactionableであること。
- scheduleごとに triage責任を持つ人間が1名いること。
- 誰もtriageしないscheduleを畳むこと。

## 3. Trigger、dedupe、duplicate work

### 3.1 入力digest gating（この文書の中心的な追加提案）

```text
trigger fires
  -> input digest = H(schedule revision, task template SHA, base SHA,
                      check固有の入力: lockfile SHA / feed cursor / fixture SHA / 集計対象件数)
  -> digest == 前回terminal runのdigest ?
        yes -> no-op run record（job発行なし、slot消費なし、通知なし）
        no  -> dedupe key = digest。以降のoverlap / budget / circuit checkへ
```

**[結論] これで解ける問題が4つあります。**

| 問題 | 効果 |
|---|---|
| duplicate work | 同じ入力に対する再実行が構造的に起きない。時刻ではなく入力が同一性を決める |
| runaway usage | 変化がない期間のquota消費がゼロになる。`runs_per_day` の値の重要度が大幅に下がる |
| alert fatigue | 「変化なし」の通知が発生源で消える。runは記録されるので silent automation にはならない |
| stale context | digestに base SHA と template SHA が入るため、古い前提での実行が検出可能になる |

**[結論] これはscheduleとeventの距離を縮めます。** 入力digest gating付きのscheduleは「pollingによるevent検出」であり、01 §1 M7 の「eventがscheduleを厳密に優越する」という主張と整合します。scheduleが本当に必要なのは、digestが変わらなくても意味がある集計（履歴の蓄積、trend）だけです。

**[仮説]** digest計算のcostは、check本体より2桁小さい。反証条件は、digest計算のために provider を起動する必要が生じた場合で、その場合gatingは成立しません（例: 「外部docsが更新されたか」をLLMに判断させる設計）。digestは**決定論的なlocal command**で計算できなければなりません。

### 3.2 3種類の重複

| 重複の型 | 現doc setの扱い | この review の対策 |
|---|---|---|
| 同一scheduleの重複run | `overlap: forbid`、`max_concurrent_runs = 1` | 維持（H6）。加えて入力digestで時刻由来の重複を消す |
| 複数scheduleが同じcheckを持つ | **記述なし** | `check_identity` を必須にし、同一identityの有効scheduleを複数enableできない（H相当の追加候補） |
| recurring work と interactive work の重複 | **記述なし** | 発行前に「同じ問いが現在のinteractive workで進行中でないか」を確認する。機械判定は困難なので **tier F** とし、代わりに §4 の admission control で被害を限定する |

### 3.3 missed-run catch-up

**[結論] 「最新1回だけ」は state-snapshot checkに対しては mechanism から導けます。** 現在の状態を見るcheckは、逃したrunを遡って実行しても同じ結論になるため、各occurrenceに独立の価値がありません。

**[結論] しかし event-derived checkでは同じ規則は成立しません。** feed cursorやevent queueを消費するcheckでは、逃した区間の入力を落とすとデータが欠落します。この場合の正しい設計は「runを繰り返す」ではなく「**1回のrunで cursor 区間をまとめて処理する**」です。現doc setの「既定は最新一回だけ」（`02-operating-model.md` §8）は前者にしか当てはまらず、区別が書かれていません。

## 4. Budget、quota、runaway防止

### 4.1 3階層のbudget

```text
per-run       : wall time、max attempts、slot-seconds
per-schedule  : 1日のrun数（digest gating後）、1日のslot-seconds、alert数
recurring pool: 全recurring workの合計 <= 観測された interactive slot-seconds の一定割合
```

**[結論] hard guardとして必要なのは3階層目です。** per-scheduleの上限だけでは、scheduleが増えるほど総消費が線形に増えます（silent budget creep）。pool を先に固定すれば、schedule数の増加は互いのshareを削り合うだけになり、**scheduleを増やすことが自動的に高くならない**構造になります。02 §2.4 の相対budgetの実体はこれです。

**[未解決]** poolの割合の初期値には根拠がありません。provider別のrate window headroomが観測できないためです（02 §6 反対3）。当面は slot-seconds の絶対値で暫定運用し、「暫定」と明記して headroom 観測後に相対値へ移します。

### 4.2 `agentctl` 0.7 との具体的な相互作用（現doc setに欠けている部分）

| 経路 | 現状の挙動 | recurring workで起きること | 対策 |
|---|---|---|---|
| queue aging | `AGENTCTL_QUEUE_AGING_SECONDS`（既定300）ごとに1段昇格、interactiveまで | `background` で投入したsentinelが、待つほど昇格して interactive workの前へ出る | scheduler発行jobは **aging対象外**にする。recurring workにstarvationは許容できる（skipのほうが安い） |
| `light=4` capacity | read jobは全て `light` slotを共有 | scheduled reportが `consult` の参加者slotを奪う（02 §2.2の天井を下げる） | recurring workが同時に占有できる `light` slotに上限を設ける（pool派生のD値） |
| `AGENTCTL_QUEUE_LIMIT=128` | queue全体の上限 | 暴走したemitterがqueueを埋め、interactiveのdetach dispatchが失敗する | recurring由来のwaiterが占有できるqueue枠の割合を制限する |
| `awaiting_resubmit` | supervisor再起動後、同じdetach commandの再送が必要（環境はmemory-onlyのため） | schedulerが自動resubmitするには provider credentialを保持し続ける必要がある | **[結論] 自動resubmitしない。** recurring runは droppable と定義する。次のtriggerで入力digestが同じなら再実行され、違えば新しいrunになる。長命daemonへcredentialを預ける設計を避ける |

**[結論] 最後の行が重要です。** recurring runの droppability は、単なる簡略化ではなく **credential露出面を増やさないための設計判断**です。「落ちたら次回」で正しく動くことは、§1.2の「carry-overが空でも動く」要件と同じ性質です。

### 4.3 failureとcircuit

```text
run_status  : infrastructure的な成否（provider起動失敗、schema不正、timeout、broker検証失敗）
findings    : checkの内容的な結果（driftあり、advisoryあり、flaky候補あり）
```

**[結論] circuit breakerとbackoffは `run_status` だけをkeyにします。** `findings` が非空であることは success です。これを分離しないと、監視が機能した瞬間に監視が止まります（01 §5 anti-pattern 7）。

- backoffは failure class 別にする。provider outage（外部）とschema不正（自分のtemplateのbug）は、同じ待ち時間で扱う理由がありません。後者はbackoffではなく即disableが正しい。
- circuit openは **1回だけ通知する**。通知しないとsilent automation、毎回通知するとalert fatigueです。
- circuitの自動closeを持つ場合、cooldown後の **single probe（half-open）** に限り、budgetを自動で増やしません。closeの完全自動化は避け、H11のとおり閉じる権限はownerへ残します。
- retryはbudgetを消費します。`max_attempts` の既定は read-only reportでは1で十分です（再実行しても入力が同じなら結論が同じ）。

## 5. Stale context

| 型 | 症状 | 対策 |
|---|---|---|
| base drift | scheduleが古い固定SHAで走り続ける | `base_policy` を明示（`registered_head` = drift検出向け / 固定SHA = canary fixture向け）。**どちらを選ぶかはcheckが何を比較しているかで決まる**: 固定base + 変動toolchain = canary、変動base + 固定期待値 = drift report |
| template drift | task templateがrepositoryの現実と乖離（消えたpath、消えたcommand） | 各runでtemplateを既存validatorへ通す。失敗は run failure として大きく落とす。黙って適応させない |
| carry-over rot | 古いfinding IDが現在のcodeと対応しない | carry-overに `max_staleness` を持たせ、超えたら破棄して再baseline。§1.2の「空でも動く」要件で安全 |
| definition drift | scheduleが誰の同意も経ずに意味を変える | definition revisionをaudit recordへ含める（H10）。revisionが変わったら `enabled_until` を短縮するか再enableを要求する |
| toolchain drift | edge channelで起動ごとにCLIが変わる | canaryにとっては検出対象そのもの。他のscheduleでは、run recordへ provider CLI version を残して混同を防ぐ |

**[結論] 「carry-overが空でも正しく動く」という一つの要件が、stale contextの大半を無効化します。** carry-overは高速化と差分通知のためのcacheであり、正しさの前提にしません。

## 6. Alert fatigue

**[結論] 通知の単位はrunではなく「finding stateの遷移」です。**

```text
finding ID（安定keyで生成: check identity + 対象 + 分類）
  new       -> 通知
  changed   -> 通知
  resolved  -> 通知（1回）
  unchanged -> 通知しない。ただしrun recordには残す
```

追加の制御:

- **suppression（snooze）は必ず失効させる。** 恒久muteを作らない。suppress中のfindingもaudit recordには出る。無期限muteは「見えないまま壊れている」状態を作ります。
- **alert上限を持ち、超過分はdigestへ落とす。** 上限値はD、上限の存在はH（H7）。
- **owner 1名を必須にする（F）。** triageされないscheduleは、`enabled_until` の失効で自然に止まります。これが `enabled_until` の第二の効能です。
- **表示は権限ではない。** Mira Companionは sanitized 表示専用（`collaboration-model.md` の ownership boundary）です。通知経路を増やしても、enable / disable / circuit close の権限をUI側へ渡しません。

**[未解決]** 何件/日でfatigueが起きるかは測定していません。initial値はD扱いにし、`notified` と `triaged` の比（audit recordから計算可能）で更新します。

## 7. Permissionとwrite境界

### 7.1 2つの境界を混ぜない

`docs/architecture.md` と `docs/agentctl.md` が明示するとおり、同一privileged container・同一UID・同一credentialの中に **security boundaryは存在しません**。したがって:

| 境界 | 何を防げるか | 何を防げないか |
|---|---|---|
| accidental-write boundary（broker検証、allowed / forbidden paths、job専用worktree、Lane R = 変更禁止） | scope事故、意図しないfile変更、偽head SHA、path逸脱 | 意図的な逸脱、shell経由の任意操作 |
| 能力の不在（control planeがmerge / push / PR / releaseを提供しない。H9） | 自動integrationの連鎖、`collect` の誤読による無人merge | agentが自分で`git push`すること |
| provider sandbox / permission profile | 既定の危険操作、approval無しの破壊的command | bypass profile（`trusted-fast`）を使った場合の全部 |

**[結論] recurring workに対する実効的なguardは、「Lane Rを既定にする」「bypass profileを構造的に拒否する（H5）」「control planeにintegration能力を持たせない（H9）」の3点です。** これ以上の主張はしません。remote側のbranch protectionはこのrepositoryの外にあり、必要ならそこで担保すべきです。

### 7.2 write許可の設計

- 既定は Lane R の report（現doc setと同じ）。
- Lane W を許すschedule は **schedule単位の別opt-in**とし、`enabled_until` をさらに短くします。理由: 無人write の risk は時間に比例して蓄積し、忘却の代償が read-only より大きい。
- 生成できるのは job branch上の candidate commit まで。merge / push / PR / release / dependency update / migration / destructive cleanup は human / primary gate（現doc setと同じ。維持）。
- **[結論] recurring Lane W は roadmap上で最後（05 R4）に置き、「作らない」選択を正当な結果として残します。** read-only recurringの triage 実績がない状態でwriteを足すのは、C5（人間のreview容量）を最も浪費する順序です。

### 7.3 外部入力の扱い

**[結論] recurring workのmechanismのうち、最も検査が弱いのはここです。** advisory本文、release note、issue本文、外部docsは、agentが読むtextに指示文を含み得ます。01 §5 anti-pattern 9（instruction-bearing external input）です。

機械的に担保できる部分（H寄り）:

- 外部contentは **fileとして** worktree内の指定pathへ落とし、prompt本文へ展開しない。
- acceptanceは command-based にする（外部textの内容が成否判定を動かせない）。
- 外部contentを取得するrunは Lane R とし、書き込みpathを取得先ディレクトリに限定する。
- 結論の形式を固定する（finding IDと分類のみ）。自由文の中の要求を実行させない。

担保できない部分（F）:

- 「textに書かれた指示に従わない」ことそのもの。これはprompt側の規律であり、structured dataからは判定できません。**[未解決]** このrepositoryのproviderでどの程度成立するかは未測定です。red-team（M6）の残余価値の主要部分はここにあります（01 §1 M6）。

## 8. Audit

**[結論] audit recordはtrigger評価単位で、content-freeに、append-onlyで書きます。** `agentctl` の既存 validations ledger と同じ性質（broker観測の事実のみ、prompt / transcript / credentialを含めない）で設計できます。

```yaml
schedule_id: <stable id>
definition_revision: <rev>
template_sha: <sha>
evaluated_at: <ts>
decision: fired | skipped_no_input_change | skipped_overlap
        | skipped_budget | skipped_circuit_open | skipped_disabled | skipped_expired
dedupe_key: <input digest>
job_id: <ULID or null>
run_status: succeeded | failed | cancelled | orphaned | not-started
failure_class: provider | template | timeout | broker | null
findings: {new: N, changed: N, resolved: N, unchanged: N}
notified: true | false
suppressed_until: <ts or null>
budget: {slot_seconds: {light: N, write: N}, attempts: N}
enabled_until: <ts>
provider_cli_version: <string>
```

- **skipを必ず記録します。** skipが見えないと、「静かに何も起きていない」と「静かに止まっている」が区別できません。
- enable / disable / circuit close / budget変更は、actorとともに別recordへ残します（H10、H11）。
- retentionは件数とbyteの両方で上限を持ちます（既存のlog retention evidenceと同じ方針）。件数だけでは1件が巨大な場合に効きません。
- **automation governor は agent ではなく、この ledger に対する read-only report として実装します**（§1.2）。

## 9. 現doc setへの具体的な指摘

### 9.1 過剰・欠落・誤分類

| 箇所 | 判定 | 内容 |
|---|---|---|
| `collaboration-model.md` mode表の `sentinel` / `event-triggered` | **誤分類** | lifecycleをmodeとして並べている（03 §1）。MG1で解消 |
| `collaboration-model.md` "Safe initial use cases" の docs / API drift | **誤分類** | in-repo triggerを持つのでevent-triggered（§1.1、01 §1 M7） |
| `collaboration-model.md` "Required controls" | **混在** | tier H（disabled-by-default、dedupe、overlap）とtier F（open-ended objectiveを登録しない）が同じlistにある。§2の3層へ分ける |
| 全doc | **欠落** | 入力digest gating（§3.1）。dedupeが時刻とtrigger IDだけをkeyにしている |
| 全doc | **欠落** | `enabled_until`（§0-5）。「忘れられたschedule」に対するguardが無い |
| 全doc | **欠落** | enablement / circuit stateの**保存場所**の規定（§0-6、H1、H8） |
| 全doc | **欠落** | `agentctl` 0.7 の aging / `light` slot / queue limit / `awaiting_resubmit` との相互作用（§4.2） |
| 全doc | **欠落** | `run_status` と `findings` の分離（§4.3） |
| 全doc | **欠落** | finding単位の状態遷移通知、suppressionの失効、alert上限（§6） |
| 全doc | **欠落** | 外部入力の配送形式に関する規定（§7.3） |
| 全doc | **欠落** | skipを含むaudit record（§8） |
| `01-pattern-catalog.md` pattern 54 / 60 | **登録不可** | open-ended・自己言及。§1.2のとおりreportへ変える |
| `02-operating-model.md` §8 の missed-run 既定 | **不完全** | state-snapshot checkにしか当てはまらない（§3.3） |
| `02-operating-model.md` §8 の schedule YAML定数群 | **根拠なし** | §9.2で扱う |

### 9.2 提案する固定値と、しない固定値

**[結論] mechanismから導ける値だけを既定として残し、それ以外は「上限の存在（H）+ 値（D）」へ分解します。**

| 値 | 判定 | 根拠 | 適用範囲 | 更新方法 |
|---|---|---|---|---|
| `enabled = false` at creation | **維持（H）** | enableは人間の決定であり、作成の副作用にしない | 全schedule | 変更しない |
| `max_concurrent_runs = 1` | **維持（D、mechanism由来）** | checkのidempotencyが未証明で、capacity / queueの競合costが確定している | 全schedule | idempotencyの証明と pool 余裕が揃った場合のみ引き上げ |
| overlap `forbid` | **維持（H相当）** | 同一入力の並走に価値がない。§3.1のdigest gatingと整合 | 全schedule | 変更しない |
| `max_runs_per_day = 1` | **却下（global fixed count）** | 根拠なし。digest gating後は実効run数が入力変化率で決まる | — | 上限の存在はH7。値は pool share から導出し、audit recordの実測run数で校正 |
| `backoff_seconds = [300, 1800, 7200]` | **却下（値のみ）** | 単調増加・上限付きであることは正しいが、数列自体に根拠がない。failure classごとに違うべき | — | provider outageの実測復帰時間で校正。template failureはbackoffせず即disable |
| `open_circuit_after = 3` | **暫定として許容（D）** | 小さい整数は防御的に妥当（失敗runのcostは有界、検出遅延は小さくしたい）。ただし「3」に固有の根拠はない | infrastructure failureのみ | false-open率（circuit openのうち再開後すぐ成功した割合）で更新 |
| `retention_runs = 12` | **却下（値のみ）** | 件数だけでは巨大recordを制限できない | — | 「そのreportが主張するtrendの計算に必要な期間」+ byte上限で決める |
| missed-run catch-up = 最新1回 | **条件付き維持** | state-snapshot checkではmechanismから導ける。event-derived checkでは誤り | check種別ごと | §3.3のとおりcursor集約へ切り替え |
| `alerts_per_day` | **新規（H7で存在必須、値はD）** | alert fatigueは通知量に依存する | schedule単位 | `notified` / `triaged` 比で更新 |
| `enabled_until` | **新規（H2で存在必須、値はD）** | 忘却に対する唯一の自動guard | 全schedule。Lane Wはより短く | 再enable頻度と、失効による事故（見逃し）の実測で調整 |
| recurring pool share | **新規（H7で存在必須、値は暫定）** | schedule数の増加で総消費が増えない構造を作る | 全recurring合計 | **[未解決]** headroom観測後に相対値化（02 §2.4） |

**[結論] scheduleの本数を「監視の充実度」の指標にしません。** これは 01 §5 の agent count theater と同型の誤りです。指標は「triageされたfindingの数」と「見逃しの数」です。

## 10. 反対意見、unknown、失敗条件

### 反対意見

- **反対1: guard tierを3層にすると、運用者が覚えることが増える（C8）。** 妥当です。緩和は、tier Hをmachine-readable registry 1箇所に集め（05 T8）、人間が読むdocには「Hはconfigで曲げられない」という一文だけを置くことです。tier Dの値は config に理由付きで書かれるため、docへ再掲しません。
- **反対2: 入力digest gatingは、checkが「時間経過そのもの」を見る場合に機能しない。** 正しい。証明書の期限、SLAの経過、staleness自体を見るcheckでは、入力が変わらなくても結論が変わります。この場合はdigestへ「時間bucket」を含めます（例: 日付）。ただしこれは gating を実質無効化するため、**そのcheckは本当に日次である必要があるかを先に問うべき**です。
- **反対3: `enabled_until` は、正常に動いている監視を無用に止める。** 部分的に正しい。見逃しのcostが高いschedule（security advisory等）では、失効が事故になり得ます。緩和は (a) 失効前の通知、(b) scheduleごとに期間をDとして設定可能にすること、(c) 失効を「削除」ではなく「disabled」にして再enableを1操作にすることです。それでも、**期限のない自動化を残すよりは失効のほうが安全**という判断です。
- **反対4: circuitのcloseを人間に限るのは、夜間の一時的なoutageで監視が長時間止まることを意味する。** 正しい。だから half-open single probe を許します。それでも自動でbudgetを増やすことは許しません。区別は「再試行するか」と「使える資源を増やすか」です。
- **反対5: そもそもschedulerを実装しないほうが安い。** 真面目に検討すべき選択肢です。§1.1の判定で残るuse caseは4件程度で、そのうちevent化できるものを除くと、canary / advisory drift / 履歴集計だけです。これらが既存CIやcron + 単純scriptで足りるなら、agent schedulerは不要です。**[結論] このreviewは「scheduler実装の前に、非agentの定期実行で足りないことを示す」ことを R3 の入口条件として要求します**（05 §5）。

### Unknown

- **[未解決]** provider別 rate window headroom の観測手段。recurring poolの相対値化の前提（02 §6も同じ）。
- **[未解決]** alert fatigue の閾値。`notified` / `triaged` の実測が必要。
- **[未解決]** 外部text由来のprompt injectionに対する各providerの耐性（§7.3）。
- **[未解決]** digest計算をlocal commandだけで書けるcheckの範囲。書けないcheckではgatingが成立しません。
- **[未解決]** `enabled_until` の適切な長さ。見逃しcostとの trade-off が測れていません。
- **[未解決]** 非agentの定期実行（CI、単純cron）で代替できないuse caseが実際に存在するか。E7 と R3 の入口で確認します。

### 失敗条件（この章の設計を捨てるべき兆候）

1. 6ヶ月運用して、triageされたfindingがゼロだった → recurring work全体を畳む。schedulerを実装済みなら disable のまま残し、次のcontainer rebuildで削除する。
2. skip recordばかりでfired recordがほとんど無い → そのcheckはscheduleではなくevent、または不要。`enabled_until` の失効に任せる。
3. audit recordが増えるだけで一度も判断に使われなかった → recordのfieldを `decision` / `run_status` / `findings` の3つへ削る。それでも使われなければ ledger を廃止し、report fileだけ残す。
4. guard tierの分類自体が議論の対象になり続けた → tier Fを廃止し、Hと「それ以外」の2層へ落とす（Fは元々reviewで守るものなので、名前が無くても運用は変わらない）。
5. 入力digest gatingがcheckの半分以上で書けなかった → gatingをoptionalな最適化へ格下げし、dedupeをtrigger ID + overlapに戻す。この場合 §4 の pool の重要度が上がります。

## 11. 次の文書へ

- ここで定義したtier H registry、audit ledger、digest gating、pool を**誰が実装し、どの順で、どこまでを`agentctl`が持つか** → [`05`](05-repository-capabilities-and-roadmap.md)
- schedule と event の優越関係の実測（E7）と、scheduler最小実装の依存関係 → [`05`](05-repository-capabilities-and-roadmap.md) §5 R3
