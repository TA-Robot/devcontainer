# 05. Repository capabilityとroadmap

Reviewer: independent Claude Opus 5 review
Date: 2026-08-26
Scope: brief Q7、Q9、Q10 の実装面

mechanism ID（M1–M7）と cost ID（C1–C8）は [`01`](01-principles-and-value-mechanisms.md)、実験ID（E1–E7）とbudget単位は [`02`](02-adaptive-selection-and-experimentation.md)、termination rule（TR1–TR10）・bias control（B1–B6）・mode縮約（MG1–MG3）は [`03`](03-interaction-protocols-and-comparison.md)、guard tier H/D/F と tier H registry（H1–H11）は [`04`](04-recurring-agents-and-governance.md) の定義を使います。

## 0. 要約

1. **[結論] このreviewが推奨する最初の作業はcodeではなくdocの訂正である。** 内部矛盾（blind first roundを無条件defaultとしながらdelegation不可の縮退経路を併記、lifecycleをmode表へ混在、根拠なきglobal定数）は、tool 0本で今日直せる。逆に、docを直さないままtoolを作ると誤った既定値が実装へ固定される。
2. **[結論] 事前に作るべきものは「content-freeな観測」と「機械的に拒否できるguard」の2種類だけである。** 対話の形、要約、説得、role演技はprovider-nativeへ残す。`agentctl` が会話を所有しない（ADR-0001）という境界は維持し、強化する。
3. **[結論] schema v1（`.agent/schemas/task.schema.json`、`additionalProperties: false`）を変更しない。** held-out check、episode record、schedule定義はすべて **sidecar**（brokerまたはcontrol planeだけが読む別contract）として持つ。sidecarはfile削除でrollbackできる。
4. **[結論] `variants`（`compete`）harnessはE3の gate を通るまで作らない。** verifierの識別能力が未確認のままbest-of-N harnessを作ると、費用N倍でノイズを選ぶ機構を実装することになる。
5. **[結論] schedulerは最後で、かつ「非agentの定期実行で足りない」ことを示した後にしか作らない**（04 §10 反対5）。R3の入口条件として明文化する。
6. **[結論] 人間のreview容量（C5）とslot-secondsをcostの一級市民として計測する。** token量は共通budget単位に使わない（02 §2.4）。
7. **[結論] 全stageは単独完結し、rollbackはfile削除かconfig field削除で済む。** state移行やschema migrationを要するstageを置かない。

## 1. 判定基準（何を作り、何を作らないか）

capabilityを追加してよいのは次の3つを同時に満たす場合だけです。

- **決定を変える**: そのtoolが無いと下せない判断が具体的に名指しできる。
- **provider非依存**: 全providerで同じ意味を持ち、transcriptやprivate reasoningの保存を前提にしない。
- **削除可能**: 使われなければfile 1つの削除で撤退でき、他機能が壊れない。

作らないもの: 会話orchestrator、prompt template engine、agent間message bus、consensus計算、transcript store、universal evaluator、agent registry。いずれも C8（maintenance cost）を確実に増やし、価値は未実証です。

## 2. Capability T1–T8

| ID | capability | 目的 | 依存 | 削除可能性 |
|---|---|---|---|---|
| **T1** | content-free episode ledger（JSON Lines追記） | E1/E3–E6の観測、prior更新（02 §5.1） | なし | fileを消す |
| **T2** | slot-seconds計測（既存capacity leaseのacquire/releaseから算出） | provider-neutral budget、C3/C7の実測 | agentctl内の既存lease | 出力fieldを止める |
| **T3** | compete harness（共通base/scope/acceptance/deadline、提示順random化、staged gating） | M4の公正比較、B2 | **E3 gate**、T4 | harness削除。task schema無変更 |
| **T4** | verification sidecar（held-out check定義。brokerのみ読む） | acceptanceへの過適合検出（03 §5.1） | agentctl state | sidecar削除 |
| **T5** | claim ledger（3列: ID / 1行claim / status）+ 遷移件数カウンタ | TR1・TR6・TR8の判定、debate theater検出 | なし | markdown表を廃止 |
| **T6** | seeded-defect corpus（実revert / follow-up commit由来） | E2、maker-checker/red-team構成の決定 | なし | corpus削除 |
| **T7** | trigger emitter（入力digest gating + audit record + tier H検査） | M7、04 §3.1・§8 | T1、T2、T8、E7 | emitter削除、schedule定義削除 |
| **T8** | machine-readable guard registry（tier H）+ project override field（tier D） | Hをconfigで曲げられなくする、02 §5.3 | なし | registry削除でF運用へ戻る |

### 2.1 各capabilityの最小形

**T1 episode ledger**: 最初からschemaにしません。JSON Lines 1行/episode、fieldは02 §5.1のとおりでprompt・text・transcriptを含めません。**記入率が半分を切ったら3 field（mode / outcome / human review bucket）へ削る**（02 §6 失敗条件1）。誰が書くかは未解決で、primaryが自動で書けない形にすると続きません。

**T2 slot-seconds**: 新規計測基盤を作りません。既存のcapacity lease timestampの差分をclass別に合計するだけです。これが `light=4 / write=2 / integration=1 / isolated=0` という**既に存在する構造的な参加者上限**を、mode設計へ初めて接続します（01 §0-7、02 §2.2）。

**T3/T4 compete**: `held_out` をtask envelopeへ入れません。可視 `acceptance` は既存v1のまま使い、非開示検証はsidecarへ置きます。rubricの**次元は開示・重みは非開示**、diff size上限とdeadlineは共通、**approach仮説だけを分岐**させます。staged gating（stage 0 build → 1 可視acceptance → 2 held-out → 3 生存候補のdiff質評価 → 4 採否+decision-flip condition）で、人間reviewの投入点をstage 3だけに限定します。early abortにより cost は N倍ではなく「1本 + 落選分の途中まで」になります。

**T5 claim ledger**: evidence本文は別artifactへ置き、pathで参照します。**transcriptは保存しません。** 実装が必要なのは遷移件数のカウントだけで、TR2/TR4/TR7/TR9はprimaryの判断規則です。

**T7 emitter**: 「recurring agent」という実体を作らず、trigger・有限job・bounded carry-over・人間ownerの4つだけを持ちます。`enabled=false` at creation（H1）、`enabled_until` 必須（H2）、1 trigger評価あたり最大1 job（H3）、`permission_profile=safe` のみ（H5）、enablement / circuit stateはworktree外（H1・H8）、skipを含むaudit record（H10）。入力digestが前回と同一ならjobを発行しません。`run_status`（infrastructure）と `findings`（内容）を分離し、circuit breakerは前者だけをkeyにします。

**T8 registry**: tier Hを1箇所へ集め、project overrideがHへ触った場合は機構的に拒否します。overrideには `reason` と `revisit_after_episodes` を要求し、空のものは削除候補として扱います。

## 3. provider-nativeへ残すもの

| 領域 | 理由 |
|---|---|
| 会話state、session、resume、要約 | ADR-0001の境界。`agentctl` が所有すると全provider分の実装と維持が発生する（C8） |
| subagent / delegation | provider機能。有無は `agentctl doctor` のcapability probeで検出し、無い場合の縮退はmode別に質が違うと明記する（03 §2.4） |
| private reasoning、試行軌跡 | 保存を前提にしない。M3の情報非対称はむしろ「見せない」ことで成立する |
| sandbox / approval / permission profile | provider実装を使う。control plane側で再実装しない |
| direct peer messaging | 現時点で実装を推奨しない。許すとしても事実確認に限り、評価判断は不可（03 §2.3） |
| role演技、tone、persona | prompt側。structured dataで検査できない（tier F） |

**[結論] primary-mediated をdefaultにする根拠は「providerが未対応だから」ではなく「停止判断はbudget所有者が行うべきだから」です。** この根拠なら、providerがpeer messagingへ完全対応してもdefaultは変わりません。現doc setの可用性ベースの記述は書き換えるべきです。

## 4. Roadmap R0–R4

各stageは単独完結し、次へ進まなくても価値が残ります。

### R0. docs-first correction（tool 0本、最優先）

1. mode表から `sentinel` / `event-triggered` をlifecycle節へ移す（MG1）。
2. blind first roundを「delegationが利用可能なときのdefault」へ限定し、縮退表（03 §2.4）を併記する。**現在の内部矛盾はこれで解消します。**
3. 「2 round / 2 variants / 3 agent」を **planning prior** と明記し、terminationはTR1（情報停止）へ移す。**根拠なきglobal agent/round定数を新設しない。**
4. `variants` に「verifierが cheap-accurate であること」「approach仮説を分岐させること」を適用条件として追加する。
5. docs / API driftをevent-triggeredへ再分類する。
6. "Required controls" をtier H / D / F へ分ける。機械検査できない項目をhard guardと呼ばない。
7. C1（brief serialization）とC5（human review）をrouting判定の入力へ入れる。B2（提示順random化）とB4（open claimを要約せず原文で持ち越す）を追記する。

Rollback: 各項目1コミットで戻せます。

### R1. 観測（T1 + T2）+ E1/E6

既存taskへ寄生させ、追加費用をほぼゼロにします。E6（solo vs fanoutのaccept到達総時間）とE1（制約違反数）の結果で **routing順の向き** が決まります。C5がbindingなら、推奨の重心は `fanout` から `verify` / `consult` 側へ移ります。

### R2. assurance（T5 + T6 + E2）

`verify(stance=neutral/adversarial)` を標準構成にします。E2が cross-provider の優位を示さなければ、**生成側のprovider diversity投資を却下**し、cross-providerはevaluatorへのみ割り当てます。

### R3. compete（E3 gate → T3 + T4）

E3（過去の候補patch対に対するretrodiction精度）が偶然を明確に上回らなければ **T3を作りません**。これは「案数」の議論より前に来る判断です。held-out fixtureを維持できないtask classでは compete を成立させません。

### R4. lifecycle（T7 + T8 + E7）

入口条件（すべて必須）:

- 非agentの定期実行（CI、単純cron + script）で足りないuse caseを具体的に示す。
- R0の再分類後にscheduleとして残るuse caseが存在する（canary / advisory drift / 履歴集計）。
- 入力digestを**決定論的なlocal command**で計算できる。
- triage責任を持つ人間owner 1名が確保できる。

さらに `agentctl` 既存挙動との衝突へ明示的なadmission controlを入れます: scheduler発行jobをqueue aging対象外にする、recurringが占有できる `light` slotとqueue枠に上限を設ける、`awaiting_resubmit` を自動resubmitせず **recurring runをdroppable** と定義する（長命daemonへcredentialを預けない）。

**recurring Lane W は最後に置き、「作らない」を正当な結果として残します。** read-only recurringのtriage実績がない状態でwriteを足す順序は、C5を最も浪費します。

## 5. 最小pilot（1週間、tool追加なし）

R0の7項目を適用し、以後のcollaborationで手書きの episode 行（mode / declared mechanism / binding constraint / outcome / human review bucket）とclaim ledger 3列だけを残します。10 episodeで判定します。

- 記入が続かない → T1を作らない。measurementを諦め、guidanceのみへ戻す。
- 宣言できるmechanismが常に同じ1つ → mode語彙をその周辺へ縮約する。
- TR1で自然停止した → round定数を復活させない。
- C5がbindingと判明 → routing順を書き換える。

## 6. Risk と rollback

| risk | 兆候 | rollback |
|---|---|---|
| 観測が儀式化する（C8だけ増える） | 3ヶ月で判断が一度も変わらない | T1を3 fieldへ削り、続かなければledger廃止 |
| sidecarがschemaへ昇格を求められる | field追加要求が繰り返される | 昇格させない。v1は `additionalProperties: false` のままにし、sidecarで受ける |
| compete harnessが未検証のまま作られる | E3を飛ばす圧力 | T3の実装をE3 gateの後ろに置き、gate未通過なら着手しない |
| held-out fixtureの維持費が利得を超える | fixture更新が滞る | held-outを廃し、**competeごと封印**する（held-outなしのcompeteは過適合を検出できない） |
| schedulerがinteractive workを押し退ける | interactive dispatch失敗、応答遅延 | aging除外とslot/queue上限を先に入れる。効かなければscheduleをdisableのまま残し、次のrebuildで削除 |
| 監視が自分で止まる | findingを failure として数えている | `run_status` と `findings` の分離を回帰testで固定する |
| guard tierの分類が議論を呼ぶ | tier論争が続く | Fを廃止し、Hと「それ以外」の2層へ落とす |
| mode aliasが12 mode表と併存してdriftする | 両方が更新される | aliasを削除し、MG1の状態で固定する |

**明示する残余risk**: 同一privileged container・同一UID・同一credential内に **security boundaryは存在しません**。merge / pushの禁止は accidental-write boundary と「control planeがintegration能力を持たないこと」（H9）で担保され、意図的な逸脱は防げません。remote側のbranch protectionはこのrepositoryの外で担保すべきものです。外部text由来のprompt injectionへの耐性は **[未解決]** で、red-team（M6）の残余価値の主要部分はここにあります。

## 7. Unknown（roadmapの前提）

- **[未解決]** provider別 rate window / credit headroomの観測手段。相対budgetとrecurring poolの前提。
- **[未解決]** human review throughputの実測値。C5 binding判定の前提。
- **[未解決]** episode recordを誰が書くか。T1の成否を決める設計課題。
- **[未解決]** held-out fixtureを安定して作れるtask classの範囲。
- **[未解決]** 非agentの定期実行で代替できないuse caseが実在するか（R4の入口）。
- **[未解決]** slot-secondsとproviderの実課金の相関。

**[結論] R0だけでもこのreviewの主要な指摘は解消し、R1が最小の追加投資で routing の向きを決めます。R2以降は各gateの結果次第で「作らない」が正当な結論になり得ます。**
