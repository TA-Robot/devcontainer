# Multi-agent collaboration model

Status: guidance accepted; scheduler runtime not implemented  
Updated: 2026-08-26

## Purpose

この文書は、native-first multi-agent基盤で**なぜ複数agentを使い、どう相互作用させるか**の設計境界を定義します。

既存のread / write / isolated laneは、workspace、permission、resource isolationを決めます。roleはagentの責務を決めます。これらだけでは、独立相談、複数roundの批評、複数実装の比較、定期観測といった協働の価値を表現できません。そのため、直交する`collaboration mode`と`lifecycle`を追加します。

60候補の探索記録は[`temp/multi-agent-collaboration/01-pattern-catalog.md`](../../temp/multi-agent-collaboration/01-pattern-catalog.md)、設計過程は[`02-operating-model.md`](../../temp/multi-agent-collaboration/02-operating-model.md)、target projectで使う手順は[`project/docs/agents/collaboration-playbook.md`](../../project/docs/agents/collaboration-playbook.md)にあります。

## Model

```text
goal
  -> expected value
     speed | coverage | diversity | deliberation |
     empirical selection | assurance | continuity
  -> collaboration mode
  -> role assignment
  -> execution lane
  -> lifecycle and budgets
  -> primary-owned synthesis / integration
```

| concept | question | examples |
|---|---|---|
| value | 複数agentから何を得るか | throughput、diversity、assurance |
| mode | agent同士をどう関係づけるか | panel、critique、variants |
| role | 誰が何へ責任を持つか | researcher、implementer、reviewer |
| lane | どこでどのpermissionで走るか | read、write、isolated |
| lifecycle | いつ、何回、いつまで走るか | one-shot、2 rounds、weekly、on-event |
| authority | 誰が判断と外部変更を所有するか | primary / single writer |

たとえば`variants`はmodeです。設計案だけを比較するならLane R、小さなprototypeを比較するならLane W、untrusted dependencyを実行するならLane Iです。modeからlaneを暗黙に決めません。

`proposer`、`critic`、`evaluator`はcollaboration内の責任名であり、新しいprovider role fileを必須にするものではありません。現在のcopy sourceではresearcher、reviewer、implementerとprimaryへ割り当てます。

## Core modes

| mode | topology | value | default lifecycle |
|---|---|---|---|
| `solo` | primaryのみ | coordination costを払わない | one-shot |
| `dispatch` | primary → worker → artifact | bounded delegation、専門化 | one-shot |
| `fanout` | primary → independent workers → synthesis | wall-clock短縮、coverage | one-shot |
| `panel` | independent opinions → comparison | epistemic diversity | one blind round |
| `critique` | proposal → critic → revision | 初案の強化、risk発見 | one revision |
| `deliberation` | bounded claim exchange → adjudication | disagreementの解消 | normally 2, max 3 rounds |
| `variants` | parallel candidates → blinded evaluation | empirical selection | 2 candidates by default |
| `maker-checker` | implementation → independent verification | assurance | one review / fix cycle |
| `red-team` | defender boundary ← adversarial probe | security / failure discovery | timeboxed |
| `pipeline` | artifact A → stage B → stage C | sequential specialization | finite stages |
| `sentinel` | schedule → finite job → report | continuity、drift detection | bounded recurring runs |
| `event-triggered` | deduped event → finite workflow | early feedback、incident response | one run per event |

`solo`は失敗ではありません。multi-agentのnet valueがcoordination costを超えないtaskでは、意図的に選ぶ標準modeです。

## Routing principles

primaryは次の順で最も軽いmodeを選びます。

1. 小さく、明確で、可逆なら`solo`。
2. 独立artifactへ分割できるなら`dispatch` / `fanout`。
3. 解決案が不明なら、共有前提だけ渡した独立`panel`。
4. 初案があるなら`critique`。重大なsecurity / safety riskなら`red-team`。
5. disagreementがevidence交換で変化し得る時だけ`deliberation`。
6. 同じacceptanceで安価に作って測れるなら`variants`。
7. write誤りの影響が大きいなら`maker-checker`。
8. 同じbounded questionが時間またはeventで再発するなら`sentinel` / `event-triggered`。

一つのphaseへmodeを重ねすぎません。必要なら`panel -> variants -> maker-checker`のようにstage化し、各stageのentry / exitを明示します。

## Primary-owned collaboration plan

複数agentを起動する前に、primaryは最低限次を固定します。

- goalと、soloよりmulti-agentが有利な理由
- modeとparticipants
- shared facts、各agentへ意図的に分けるperspective
- first roundの独立性またはsequential handoff
- artifact flowとoutput format
- lane、permission、base SHA、workspace
- round / elapsed time / concurrency / usage budget
- evaluation criteria
- stop condition
- synthesis、integration、external side effectのowner

`why_multi_agent`を説明できない場合は`solo`へ戻します。

## Independent advice

`panel`の最初のroundでは他agentの回答やprimaryの推奨案を見せず、anchoringを避けます。全員の一致数ではなく、evidence、assumption、project制約、反証可能性を比較します。

同じprovider / model / promptの複製は完全な独立性を保証しません。多様性が必要なら、security / operations / UXのように観点を変え、異なるevidence sourceまたは検証方法を割り当てます。provider diversityは補助であり、品質の代理指標にはしません。

## Bounded deliberation

stable defaultはprimary-mediated roundです。primaryがopen claimと質問だけを次roundへ渡し、全文transcriptをagent間で増幅しません。

各提案はstable claim IDを持ち、`open / accepted / rejected / test-needed`のいずれかへ更新します。通常2 round、例外的に3 roundで止めます。次のいずれかで終了します。

- decisive evidenceまたはtestが得られた。
- primaryがtrade-offを判断できる。
- 新しいclaim、evidence、反証が出ない。
- time / usage / round budgetへ到達した。
- user preferenceなしには決められない境界へ到達した。

providerがpeer messagingを正式に支援し、delegationが許可されている場合だけbounded peer exchangeを選べます。facilitator、participant、topic、message / round上限、interrupt ownerを事前に固定し、nested spawnとwriteを許しません。

## Variant comparison

複数実装は次を共有します。

- immutable full base SHA
- allowed / forbidden paths
- acceptance checksとbenchmark fixture
- resource classとdeadline
- comparison rubric

各variantは別job ID、branch、worktreeを使います。correctness / safety gateを先に通し、その後にmaintainability、performance、risk、migration costを比較します。可能ならevaluatorへauthor / providerを伏せます。

winner selectionはprimaryの判断です。複数variantの一部を混ぜる場合、それ自体を新しいintegration taskとして検証します。`agentctl collect`はartifactと競合情報を集めますが、winnerを決めたり自動統合したりしません。

## Scheduled and event-driven agents

### Boundary

定期実行は、会話sessionやagent processを無期限に存続させる機能ではありません。schedulerがtriggerごとに既存contractの**finite job**を一つ発行する機能です。

```text
schedule / event
  -> trigger record + dedupe
  -> overlap / budget / circuit check
  -> immutable finite job
  -> existing lane, permission, result validation
  -> report or candidate commit
  -> primary / human integration gate
```

`agentctl` 0.7はcapacity queueを持ちますが、schedule definitionやcron / event triggerはまだ実装していません。この文書からruntime availabilityを推測してはいけません。

### Required controls

- disabled-by-default schedule creationと明示enable
- timezoneを含むtrigger definitionとnext-run preview
- immutable trigger ID、event dedupe key、overlap policy
- default `max_concurrent_runs = 1`、default overlap `forbid`
- max runs / day、max wall time、max attempts、usage / quota budget
- exponential backoffとconsecutive-failure circuit breaker
- missed-run catch-up上限
- owner-visible status、last result、next eligible run
- pause / disable / kill switch
- schedule definition revisionとaudit evidence
- schedule自身によるquota、permission、schedule変更の禁止

scheduled taskの既定はLane Rのreportです。Lane Wを明示許可してもcandidate commitまでとし、merge、push、PR、release、dependency update、migration、destructive cleanup、外部messageは別のhuman / primary gateへ残します。

### Safe initial use cases

- frozen toolchain canary
- dependency / advisory drift report
- flaky-test候補の集計
- docs / API drift report
- performance trend report
- `gc --dry-run` inventory report

「projectを良くし続ける」のようなopen-ended objectiveはscheduleへ登録しません。

## Ownership boundary

| owner | responsibility |
|---|---|
| primary / native orchestrator | mode selection、task graph、rounds、synthesis、winner、stop |
| provider-native agents | interactive research、advice、critique、native message exchange |
| `agentctl` | finite job / attempt、worktree、process、resource、structured result |
| future scheduler | trigger、dedupe、budget、circuit、finite job emission |
| primary / integrator | merge、push、PR、release、schedule enable、permission escalation |
| Mira Companion | sanitized activity visualization only |

会話の意味、debate transcript、provider sessionを`agentctl`の共通event modelへ入れません。control planeが所有するのは実行可能性と有限jobの状態です。

## Failure modes to prevent

- agent数やmessage数を成果指標にする。
- first round前に他案を見せてpremature consensusを作る。
- 同じpromptの複製をepistemic diversityと呼ぶ。
- 新しいevidenceのないdebateを継続する。
- 複数agentへ同じcheckoutをwriteさせる。
- variantを見てから評価基準を変更する。
- workerがrecursiveにagentを増やす。
- synthesis / integration ownerを置かない。
- recurring runを重ね、quotaとfailureを無制限に消費する。
- scheduled reportを無人のmerge / pushへ直結する。

## Delivery phases

| phase | deliverable | status |
|---|---|---|
| C0 | catalog、core mode、routing、playbook | implemented in documentation |
| C1 | reusable collaboration briefとrepresentative examples | first template implemented; examples pending |
| C2 | content-free mode / elapsed / rework observation | not implemented |
| C3 | observed fieldsだけのseparate collaboration plan schema | not implemented |
| C4 | disabled-by-default read-only scheduler pilot | not implemented |
| C5 | scheduled Lane W candidateとMira表示 | not implemented |

runtimeを実装する前に、native collaborationで`solo` baselineに対するwall time、decisive finding、rework、integration costを測ります。agent count、token量、message数はsuccess metricにしません。
