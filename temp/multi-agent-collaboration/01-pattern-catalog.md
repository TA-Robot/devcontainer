# マルチエージェント活用60パターン

検討日: 2026-08-26

## 0. 先に結論

複数agentの価値は「同時にたくさん働かせる」だけではありません。主な価値は次の7種類です。

1. **throughput**: 独立作業を同時に進め、wall-clock timeを短縮する。
2. **coverage**: 一人では見落とすfile、観点、仮説、riskを広く拾う。
3. **epistemic diversity**: 独立した初期判断を集め、anchoringと単一仮説への過適合を減らす。
4. **deliberation**: critique、反証、再提案を重ね、最初の案より強い案へ更新する。
5. **empirical selection**: 複数案を実際に作り、同じacceptanceやbenchmarkで比較する。
6. **assurance**: makerとchecker、redとblueを分離し、誤りを発見しやすくする。
7. **continuity**: 定期・event駆動の有限jobで、driftやregressionを時間をまたいで観測する。

逆に、複数agentにはcontext複製、token / quota消費、待ち時間、重複調査、groupthink、write conflict、review負荷、統合失敗という固定費があります。**複数agentであること自体を成功条件にしません。**

## 1. 60候補

### A. Throughput / task decomposition

| # | pattern | topology | 主な恩恵 | 向く状況 | 主な罠 |
|---:|---|---|---|---|---|
| 1 | bounded dispatch | primary → worker → artifact | primaryの手離れと専門化 | taskと完了条件が明確 | 丸投げ、scope膨張 |
| 2 | parallel fan-out / fan-in | primary → N worker → synthesis | 独立taskのwall-clock短縮 | dependencyがなく成果が併合可能 | integrationがcritical path化 |
| 3 | map-reduce research | shard調査 → evidence統合 | 大きいrepositoryや資料のcoverage | 調査対象を重複なく分割可能 | shard境界の見落とし |
| 4 | specialist routing | domain別expertへdispatch | security、DB、UI等の深さ | 必要能力が明確に異なる | role labelだけで専門性を仮定 |
| 5 | dependency pipeline | Aのartifact → B → C | 変換工程を明確化 | contractが安定した逐次作業 | 前段誤りの増幅 |
| 6 | critical-path sidecar | primaryが本線、workerが先回り | 待ち時間の隠蔽 | build中の調査や次step準備 | 本線と前提がずれる |
| 7 | blocker swarm | 複数agentが別仮説を検証 | 難しいfailureの解除速度 | 仮説を独立検証できる | 全員が同じlogを読むだけ |
| 8 | background prefetch | 次に必要な情報を先行収集 | context switch削減 | 次の入力が高確率で予測可能 | 無駄調査と古い結果 |
| 9 | batch shard execution | file / case / target単位に分割 | 大量の均質作業を並列化 | lint修正や互換性確認 | mechanical変更の衝突 |

### B. Independent advice / decision quality

| # | pattern | topology | 主な恩恵 | 向く状況 | 主な罠 |
|---:|---|---|---|---|---|
| 10 | independent consultation | 同じ問いを独立にN回答 | anchoring低減、選択肢拡張 | 正解が一意でない設計判断 | 似たmodel/contextで擬似多様性 |
| 11 | perspective panel | security / UX / ops等の観点分担 | 多面的なtrade-off | 横断的architecture | 観点の羅列で結論がない |
| 12 | evidence triangulation | 同じclaimを別source / methodで確認 | confidence向上 | 不確かな仕様、外部情報 | 同じ二次情報の引用循環 |
| 13 | assumption audit | 提案の暗黙前提だけを抽出 | 早いrisk発見 | migration、性能見積り | 批判だけで代案なし |
| 14 | uncertainty decomposition | unknownを分類しowner割当 | 調査順序の最適化 | 問題が曖昧で広い | 全unknownを潰そうとする |
| 15 | hypothesis tournament | 複数原因仮説を独立検証 | debuggingの収束 | 観測可能なfailure | 勝敗基準が後付け |
| 16 | estimation ensemble | 工数・riskを独立見積り | 過小評価の検知 | roadmap、migration | 数字の平均が真実になる錯覚 |
| 17 | counterfactual explorer | 「逆を選んだら」を検討 | irreversible decisionの盲点発見 | architecture / vendor選定 | 非現実的な反実仮想 |
| 18 | user-impact panel | user種別ごとに影響評価 | 技術最適化の局所解を防ぐ | UX、breaking change | 架空personaの断定 |

### C. Structured dialogue / repeated deliberation

| # | pattern | topology | 主な恩恵 | 向く状況 | 主な罠 |
|---:|---|---|---|---|---|
| 19 | proposal → critique → revision | proposer、critic、proposer | 初案を具体的に強化 | 提案が既に一つある | 無限修正loop |
| 20 | dialectic pair | thesis ↔ antithesis → synthesis | 対立軸を明確化 | 2案のtrade-off | 勝つための議論になる |
| 21 | steelman exchange | 互いに相手案を最善化して返す | strawmanと感情的対立を低減 | 微妙なdesign選択 | 合意したふりで差が消える |
| 22 | cross-examination | claim IDごとに質問・回答 | 根拠と前提を検査 | 高riskな主張 | 質問量がcontextを食う |
| 23 | blind Delphi rounds | 独立回答 → 匿名要約 → 再回答 | authority biasとanchoring低減 | estimate、prioritization | roundを重ねても新情報なし |
| 24 | bounded roundtable | N agentが論点別に2 round | 複合問題の相互補完 | architecture review | 発言順依存と収束不全 |
| 25 | debate with arbiter | A対B、別agent / primaryが判定 | 明示的な選択と記録 | 排他的な2案 | judgeの基準が曖昧 |
| 26 | convergence workshop | disagreementだけを次roundへ | consensus形成の効率化 | 部分合意が多い | 少数の重要反対を潰す |
| 27 | Socratic interviewer | interviewerが前提を質問 | 問題設定そのものを改善 | user intentや要件が曖昧 | user不在で要件を創作 |

### D. Parallel implementation / empirical selection

| # | pattern | topology | 主な恩恵 | 向く状況 | 主な罠 |
|---:|---|---|---|---|---|
| 28 | parallel prototypes | 同じbriefからA/B prototype | 手触りを早く比較 | 小さく作れて評価可能 | 両方をproduction品質にする浪費 |
| 29 | N-version implementation | 独立実装を同じtestへ | robustnessと設計差の発見 | 高信頼component | 費用がほぼN倍 |
| 30 | algorithm bake-off | 複数algorithm + benchmark | 性能を実測で選択 | datasetとmetricがある | benchmark過適合 |
| 31 | UI exploration set | layout / interactionを複数実装 | 言語化しにくいUX比較 | visual prototype | subjective voteだけで決める |
| 32 | migration rehearsal variants | migration手順を別workspaceで試す | rollback / downtime risk低減 | schemaやtoolchain移行 | fixtureが本番を表さない |
| 33 | performance race | 同一correctness test下で最適化 | bottleneckへの複数戦略 | hotspotが測定済み | 読みやすさ・安全性の犠牲 |
| 34 | compatibility matrix variants | version / platform別に実装・検証 | cross-platform confidence | adapter、build、packaging | matrix爆発 |
| 35 | shadow implementation | 現行経路と新経路を並走比較 | safe migration | output比較が可能 | shadow側の保守長期化 |
| 36 | patch tournament | 複数最小patchをblind review | biasを減らし小さい修正を選択 | bug fixの候補が複数 | 差分のつまみ食いで整合性喪失 |

### E. Quality / adversarial assurance

| # | pattern | topology | 主な恩恵 | 向く状況 | 主な罠 |
|---:|---|---|---|---|---|
| 37 | maker–checker | implementer → independent reviewer | self-review blind spot低減 | 通常のwrite task | checkerが追認だけする |
| 38 | test challenger | testerが先にfailure caseを設計 | acceptanceの具体化 | parser、state machine、API | testに実装を過適合 |
| 39 | red team / blue team | attacker ↔ defender | exploitabilityと防御の実証 | auth、sandbox、input境界 | safe範囲を越えた攻撃 |
| 40 | threat-model panel | asset / trust boundary別review | security coverage | credentialや外部入力 | checklist消化で終わる |
| 41 | invariant auditor | state / concurrency invariantを検査 | raceとfalse success発見 | broker、scheduler、DB | 実装から離れた形式論だけになる |
| 42 | regression hunter | diff外の影響と過去bugを探索 | local testの穴を発見 | large refactor | 根拠の薄い懸念の大量生産 |
| 43 | integration referee | 複数artifactの意味的競合を判定 | clean diffでも起きる衝突を発見 | parallel write後 | referee自身が勝手にmerge |
| 44 | reproducibility verifier | fresh環境で手順を再現 | hidden state検知 | build、release、onboarding | 同じcacheを共有してしまう |
| 45 | release-readiness council | code / test / docs / opsを別々に判定 | go/no-goの網羅性 | release前 | 全員一致を必須にして停止 |

### F. Temporal / scheduled / event-driven agents

| # | pattern | topology | 主な恩恵 | 向く状況 | 主な罠 |
|---:|---|---|---|---|---|
| 46 | scheduled scout | cron → finite read job → report | 定期的なdrift発見 | 日次・週次点検 | 無期限sessionとquota暴走 |
| 47 | event-triggered reviewer | commit / PR event → bounded review | change直後の早いfeedback | 明確なeventとscope | event storm、同一event重複 |
| 48 | toolchain canary | schedule → frozen fixture | provider / dependency破壊の早期検知 | version更新が速いtool | canary自身のdrift |
| 49 | flaky-test miner | 定期test履歴 →候補report | 不安定testの可視化 | result履歴がある | 何度もtestを回して資源浪費 |
| 50 | dependency-drift sentinel | lock / advisory差分をread-only監視 | 更新判断の先行情報 | dependencyを持つproject | 自動update・mergeの連鎖 |
| 51 | documentation gardener | code / docs差分を定期比較 | stale docs発見 | public API、runbook | 文脈なしの大量書換え |
| 52 | performance watch | benchmark schedule → trend判定 | slow regression検知 | 安定fixture / host | noisy hostで誤警報 |
| 53 | cleanup inventory reporter | GC dry-runを定期作成 | disk / stale resourceの見える化 | worktree、container、log | inventoryを自動削除へ誤読 |
| 54 | backlog gardener | issue / TODOを分類して提案 | 優先度の棚卸し | backlogが大きい | 勝手なclose、scope創作 |

### G. Organizational continuity / meta collaboration

| # | pattern | topology | 主な恩恵 | 向く状況 | 主な罠 |
|---:|---|---|---|---|---|
| 55 | decision-memory curator | artifacts → ADR候補 | 同じ議論の反復削減 | 長期project | transcriptやsecretの保存 |
| 56 | knowledge distiller | 複数report →短いrunbook | teamへの再利用 | 知見が散在 | nuanceを消した過度な要約 |
| 57 | incident command cell | commander + investigators + scribe | 緊急時の役割分離 | production incident | agentが外部変更を勝手に行う |
| 58 | longitudinal research diary | 定期snapshot →差分分析 | trendと変化点の把握 | evolving ecosystem | 古い前提の累積 |
| 59 | agent-quality evaluator | task/result履歴をsampling review | role promptとrouting改善 | 十分なevidenceがある | token量を品質と誤認 |
| 60 | automation governor | schedule / quota / failureを監査 | runaway防止と停止判断 | recurring jobs導入時 | governorも無期限agent化 |

## 2. 最初にfirst-classにする12 mode

60案を毎回選ばせるのではなく、primaryが通常使うmodeを次の12個へ畳みます。

| mode | catalog対応 | 得たい価値 |
|---|---|---|
| `solo` | baseline | coordination costを払わない |
| `dispatch` | 1, 4 | bounded artifactを専門agentへ任せる |
| `fanout` | 2, 3, 7, 9 | 独立作業を並列化する |
| `panel` | 10–18 | 独立意見と観点を集める |
| `critique` | 19, 22 | 初案を反証して一度改訂する |
| `deliberation` | 20–27 | disagreementを複数roundで解消する |
| `variants` | 28–36 | 複数実装を同じ基準で比較する |
| `maker-checker` | 37, 38, 41–44 | 実装者と検証者を分離する |
| `red-team` | 39, 40, 42 | 敵対的観点で重大riskを探す |
| `pipeline` | 5, 6 | artifactを順番に流す |
| `sentinel` | 46, 48–54, 58 | 定期的に有限jobを起動する |
| `event-triggered` | 47, 57, 60 | eventに反応し、bounded workflowを起動する |

`solo`を明示的なmodeに含めるのは重要です。複数agentが得をしない小さな作業で、儀式的にfan-outするのを防ぎます。

## 3. ユーザーが挙げた4形態の深化

### 3.1 Orchestrator dispatch

単なるtask投下ではなく、task graph、critical path、artifact boundary、integration ownerを先に決めます。速くなるのは、worker数が増えた時ではなく、primaryの本線と独立workerの待ち時間が重なった時です。

### 3.2 Independent advice

最初のroundでは他agentの答えを見せず、独立性を守ります。その後primaryが、結論の一致数ではなく、根拠、前提、反証可能性、project制約との適合を比較します。同じprovider / modelを複数回呼ぶだけなら、roleやevidence sourceを変えない限り多様性は限定的です。

### 3.3 Repeated dialogue

自由会話を無期限に続けません。`proposal -> critique -> revision -> adjudication`のように、各roundのinputとoutputを固定します。次roundへ渡すのは全文transcriptではなく、claim ID、disagreement、追加evidence、未解決質問です。通常2 round、例外的に3 roundを上限とします。

### 3.4 Parallel implementations

各variantは同じbase SHA、同じscope、同じacceptance、独立worktreeから始めます。評価者には可能ならprovider / authorを伏せ、correctnessを最初のgateにします。その後にperformance、maintainability、risk、diff sizeを比較します。「両方の良い部分を混ぜる」は新しいintegration taskであり、自動的に安全ではありません。

## 4. 定期実行agentの安全設計

### 採らない構成

- 一つの会話sessionを無期限にresumeし続ける。
- 「projectを良くし続けて」のようなopen-ended objectiveを与える。
- 前回runが動いていても次runを重ねる。
- agent自身にschedule、quota、permissionを変更させる。
- test failureやprovider failureを即retryし続ける。
- write、merge、push、dependency updateを無人で連結する。

### 推奨構成

```text
schedule / event
  -> deterministic trigger record
  -> dedupe + overlap policy
  -> finite job with immutable input snapshot
  -> existing lane / permission / result validation
  -> bounded report or candidate commit
  -> human / primary integration gate
```

scheduleはagent processを所有せず、毎回既存jobを一つ作るだけにします。最低限、次のhard limitを持ちます。

- `max_runs_per_day`
- `max_concurrent_runs`（既定1）
- `max_wall_time_per_run`
- provider固有のusage / credit / token上限、または共通のcapacity unit
- `max_attempts_per_run`
- failure時のexponential backoff
- `max_consecutive_failures`後のcircuit open
- overlap policy: `forbid`を既定、必要なら`replace` / `allow`
- event dedupe keyとretention
- userがいつでも使えるpause / disable / kill switch
- next-run previewとmanual dry-run

writeは既定禁止です。writeを許すscheduleでも、作成できるのは専用worktree上のcandidate commitまでで、merge / pushはsingle-writer gateへ残します。

## 5. 共通anti-pattern

- **agent count theater**: agent数を成果の代理指標にする。
- **premature consensus**: 独立回答前にprimary案を見せ、全員を追認者にする。
- **debate theater**: 勝敗基準も新しいevidenceもない議論を続ける。
- **same-model monoculture**: 同じpromptとcontextの複製を多様性と呼ぶ。
- **unowned synthesis**: reportを集めるだけで、誰も判断・統合しない。
- **shared-write swarm**: 同じcheckoutやfileを複数agentへ同時に書かせる。
- **moving evaluation**: variantを見てから採点基準を変える。
- **recursive delegation explosion**: workerが自由にworkerを増やす。
- **scheduled infinity**: 終了条件のない常駐agentを定期実行と呼ぶ。
- **silent automation**: quota、failure、last result、next runを人が確認できない。

## 6. 次の設計判断

1. collaboration modeはlaneと直交させ、primaryが選ぶ。
2. modeはnative providerのsubagent / messagingを使い、`agentctl`は会話を理解しない。
3. Lane Wのvariantだけは既存job fabricでbase、worktree、resultを固定する。
4. 対話はbounded roundとclaim ledgerで管理し、無期限peer chatを標準にしない。
5. scheduled / event-drivenは将来のcontrol-plane拡張候補だが、常駐agentではなくfinite job emitterに限定する。
6. まずplaybookとbrief templateを整備し、実運用の観測後にmachine-readable collaboration planやschedulerを実装する。
