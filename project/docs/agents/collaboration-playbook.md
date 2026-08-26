# Multi-agent collaboration playbook

このplaybookは、primary / managerが「複数agentをどう使うか」を選ぶための正本です。workspace、permission、process recoveryは`AGENTS.md`と`docs/agents/runbook.md`、individual write jobは`.agent/schemas/`を使います。

delegationやsubagent利用が上位instruction、tool、ユーザーによって許可されている場合だけ適用します。利用可能でない時は、同じ分析枠組みをprimary一人のsequential reviewへ縮退します。

## Start with the value, not the agent count

複数agentを使う前に、得たい価値を一つ以上選びます。

- `speed`: 独立作業を並行してwall-clockを短縮する。
- `coverage`: repository、evidence、riskの見落としを減らす。
- `diversity`: 独立した初期判断と異なる観点を得る。
- `deliberation`: critiqueと再提案で初案を強くする。
- `experiment`: 複数案を同じ条件で作り、実測で選ぶ。
- `assurance`: makerとcheckerを分ける。
- `continuity`: 時間またはeventをまたいでdriftを観測する。

soloより有利な理由を説明できない場合はagentを増やしません。

## Collaboration modes

| mode | 使う時 | 基本形 | 上限 / stop |
|---|---|---|---|
| `solo` | 小さく明確で可逆 | primaryだけで完了 | task完了 |
| `dispatch` | bounded artifactを委任できる | primary → worker → result | one-shot |
| `fanout` | 独立task / shardがある | N workers → primary synthesis | 必要shard回収 |
| `panel` | 正解が明らかでない | blind independent opinions → compare | first round 1回 |
| `critique` | 初案のriskを探したい | proposal → reviewer → revision | revision 1回 |
| `deliberation` | disagreementがevidenceで変わり得る | claim exchange → adjudication | 通常2、最大3 round |
| `variants` | 複数案を安価に実装・測定できる | isolated candidates → evaluator | 通常2 variants |
| `maker-checker` | write失敗の影響が大きい | implementer → independent reviewer | Must finding解消 |
| `red-team` | security / abuse / failureを探す | bounded adversarial probe | timebox到達 |
| `pipeline` | 成果物を順番に加工する | A artifact → B → C | finite stages |
| `sentinel` | 同じ点検を定期的に行う | schedule → finite job → report | per-run hard limits |
| `event-triggered` | commit / PR / incident等へ反応 | deduped event → finite workflow | eventごとに一回terminal |

`mode`と`lane`は別です。たとえば`panel`は通常read、`variants`のprototypeはwrite、untrusted codeのvariantはisolatedを使います。

`proposer`、`critic`、`evaluator`はcollaboration上の責任です。現在のprovider roleを無意味に増やさず、researcher、reviewer、implementerまたはprimaryへ明示的に割り当てます。

## Quick routing

1. 一人で速く正しく終わるなら`solo`。
2. 作業を独立artifactへ切れるなら`dispatch` / `fanout`。
3. 解決策が不明なら`panel`。
4. 案はあるが弱点が不明なら`critique`。security境界なら`red-team`。
5. 重要なdisagreementだけが残り、追加evidenceで変化し得るなら`deliberation`。
6. 共通acceptanceとbenchmarkがあり、prototype costが低いなら`variants`。
7. write resultを独立検証する価値が高ければ`maker-checker`。
8. 同じbounded taskが繰り返すなら`sentinel` / `event-triggered`候補。ただしruntime availabilityを先に確認する。

## Collaboration brief

複数agentを開始する前に、`docs/agents/tickets/collaboration-plan.template.md`を埋めるか、同じ内容をtask planへ持ちます。

- goal
- `why_multi_agent`
- modeとparticipants
- shared factsとagentごとのperspective
- independent first roundかsequential handoffか
- artifact flow
- lane、permission、base SHA、workspace
- evaluation criteria
- round、elapsed time、concurrency、usage budget
- stop conditions
- synthesis / integration / external side effect owner

各workerにはtask全体ではなく、担当scope、expected output、evidence requirement、stop conditionだけを渡します。

## Advice result

相談・review・議論の回答には次を求めます。

```text
recommendation
evidence
assumptions
alternatives considered
risks / failure modes
unknowns
confidence: low | medium | high
disconfirming test
```

primaryは多数決で決めず、evidenceとproject constraintを比較し、採用・不採用と理由をsynthesisします。

## Panel rules

- first roundは互いの回答とprimaryの推奨案を見せない。
- 共通のfacts、scope、question、output formatだけを揃える。
- 観点を変える時はsecurity、operations、UX、performance等を明示する。
- 同じ結論が多いことをconfidenceの唯一の根拠にしない。
- reportを集めたらprimaryがconsensus、disagreement、decisive evidence、unknownを整理する。

## Deliberation rules

- proposal、claim、evidenceへstable IDを付ける。
- 次roundへ渡すのはopen disagreementと新しいquestionだけ。全文transcriptを連鎖させない。
- criticは相手の人格や文章ではなくclaimを批評する。
- proposerは変更した点、維持した点、理由を返す。
- 通常2 round、最大3 round。新しいevidenceが出なければ止める。
- final synthesisと判断はprimaryが所有する。
- peer messagingを使う場合もfacilitator、participant、topic、message上限、interrupt ownerを固定する。

## Variant rules

- full base SHA、scope、acceptance、fixture、deadline、resourceを全variantで揃える。
- variantごとに別job ID、branch、worktreeを使う。
- 途中実装を相互に見せず、探索の独立性を守る。
- correctness / safety不合格案を性能や好みで救済しない。
- evaluatorへ可能ならauthor / providerを伏せる。
- rubricは事前に固定し、少なくともcorrectness、maintainability、performance、risk、migration costを含める。
- winner、再実験、hybridの判断はprimaryが行う。
- hybridは新しいintegration taskとして検証する。

## Scheduled and event-triggered rules

定期実行はlong-running agentではなく、毎回terminalになるfinite jobとして設計します。基盤にschedulerが実装・有効化されていると確認できない限り、scheduleが存在すると仮定しません。

最低限必要なguard:

- scheduleはdisabledで作成し、人またはprimaryが明示enableする。
- default read-only、default overlap `forbid`、default concurrency 1。
- max runs / day、wall time、attempt、usage / credit / quotaをhard limitにする。
- trigger ID / event keyでdedupeする。
- failureはbackoffし、連続失敗でcircuitを開く。
- missed runを無制限にcatch upしない。
- last result、current run、next run、budget、circuit stateを表示する。
- pause / disable / kill switchをagent外へ置く。
- agent自身へschedule、quota、permission変更を許さない。
- writeを許しても専用worktreeのcandidate commitまで。merge、push、PR、releaseはsingle writerへ戻す。

登録してよいtaskは、toolchain canary、dependency drift report、flaky-test集計、docs drift report、performance trend、GC dry-run inventoryのようにscopeとterminationが明確なものです。

次は登録しません。

- 「projectを改善し続ける」
- 「問題がなくなるまでretryする」
- broad cleanup、dependency update、migration、releaseの無人実行
- 前runが終わらないまま重複するjob

## Safe composition examples

### Ambiguous architecture

```text
panel (independent options)
  -> critique (top proposal only)
  -> primary decision
```

### Competing implementation

```text
panel (choose 2 plausible approaches)
  -> variants (separate worktrees)
  -> blinded evaluator
  -> primary integration
  -> maker-checker aggregate validation
```

### Difficult bug

```text
fanout (different root-cause hypotheses)
  -> primary selects supported hypothesis
  -> dispatch one fix
  -> independent regression review
```

### Recurring maintenance

```text
sentinel (read-only finite report)
  -> primary triage
  -> explicit write job if needed
  -> normal review / integration
```

一つのphaseへ3 mode以上を同時に積まず、stageごとにentry / exitを決めます。

## Stop and synthesize

primaryは次でcollaborationを止めます。

- acceptanceに必要なartifactが揃った。
- decisive evidenceまたはtestが得られた。
- 新しいevidence、claim、findingが出ない。
- round / time / usage budgetへ達した。
- coordination / integration costが残りの期待利益を超えた。
- user preference、権限、外部状態なしには決められない。

最終報告では、agent topologyの実況ではなく次を伝えます。

- 何を決めた / 作ったか
- どのevidenceが決定的だったか
- 重要なdisagreementとどう扱ったか
- 採らなかった案と理由
- 残るrisk、validation、次のowner

agent数、message数、token量を成果として報告しません。

## Anti-patterns

- agent count theater
- first round前のanchoring
- 同一prompt複製を多様性と呼ぶこと
- evidenceの増えないdebate
- recursive delegation explosion
- shared-checkout parallel writes
- variant確認後の評価基準変更
- reportだけ集めてsynthesis ownerがいない状態
- unbounded scheduled agent
- recurring writeからauto merge / pushへの直結
