# 01. 目的と時間referenceの出力形

## 1. 目的

問いは「multi-agentは良いか」ではなく、より観測可能な形へ分解します。

> taskの構造、題材、実行構成、provider/model identity、適用されたgeneration setting、context、環境状態が既知のとき、利用者が待つ時間とagentが消費する稼働時間は、実際にはどの範囲へ分布したか。

この情報をprojectごとの計画時に参照できるよう、versionedなduration atlasとして蓄積します。atlasは過去の観測であって将来の保証ではありません。

## 2. 答えられるようにする問い

### Task自体の時間

- 小・中・大のreview、diagnosis、implementation、designはそれぞれ何分程度だったか。
- 同じsizeでもBash、Python、JavaScript、Docker、文書、cross-boundaryでどれくらい違ったか。
- direct test oracleがある仕事と、曖昧なdesign検討では、first contract-valid artifactとuser-visible resultの差がどれくらい違ったか。
- setup、dependency install、container build、integration testがcritical pathの何割を占めたか。

### Agent構成ごとの時間

- solo、delegate、consult、competing implementations、bounded dialogueのwall-clock分布はどう違ったか。
- workerを増やしたとき、開始待ち、並列区間、primary synthesis tailはどう変化したか。
- 対話の各exchangeは何分かかり、何exchange目で何の新規evidenceが出たか。
- 同一provider構成とcross-provider構成で、dispatchからartifact受領までどれくらい違ったか。

### 運用条件による時間

- fresh sessionとwarm session、cold cacheとwarm cacheの差はどれくらいか。
- interactive loadがある時間帯と空いている時間帯でqueue/dispatchはどう変わったか。
- retryやrate limitが発生したとき、完了時間のtailがどれくらい伸びたか。
- container rebuild後、初回のtool setupがどれくらい上乗せされたか。

### 不確実性

- 同じcaseを繰り返したときのrun-to-run varianceはどれくらいか。
- 同じfamily/sizeの別caseへ変えたときのcase-to-case varianceはどれくらいか。
- 観測値が少なく、まだ「具体的な目安」と呼べないcellはどれか。
- resolved model、alias、applied effort、CLI/runtime surface、観測windowの更新後に古くなったreferenceはどれか。

## 3. 時間を一つの数字にしない

最低でも次を分けます。

| 指標 | 利用者にとっての意味 |
| --- | --- |
| admission-to-dispatch | orchestration/control-planeで待った時間 |
| time-to-first-valid-artifact | family contractを満たす最初のprogress artifactまで。progress envelopeを観測できるsurfaceだけ掲載 |
| time-to-required-workers-terminal | request受付から必要workerが出揃うまで |
| worker terminal span | 最初のtracked worker開始から最後のrequired worker終了まで |
| worker active union | tracked worker intervalの和集合。並列区間を一度だけ数える |
| synthesis tail | worker出揃い後にprimaryが比較・統合した時間 |
| online validation time | 利用者へ返す前に実行したtest/build/validationの時間 |
| time-to-user-result | request受付からresult envelopeを利用者へ渡せるまでのwall-clock |
| quality-conditioned user time | 下記のcanonical quality-pass規則を満たすrunだけに絞ったuser-result分布。score実行時間は足さない |
| offline scoring time | study専用gold/evaluatorの実行時間。利用者待ちと別表示 |
| aggregate worker time | 全workerの稼働時間合計。並列化でwall-clockが短くても増え得る |
| recovery time | failure検知から代替・retryでacceptedになるまで |

会話型では、各exchangeの開始・終了・contract-valid evidence到達も別に残します。最終時間だけでは、「会話が長い」のか「最初のagentが遅い」のか判別できません。schema-validだけで人間にとってusefulとは呼びません。

online validationはsynthesisの有無と独立した開始・終了eventで測ります。solo/C0でT3/T4が存在しなくてもtest/build時間を掲載できます。

### Canonical quality-pass population

quality-conditioned user timeへ入る条件を次に固定します。

1. 明示的な`onlineAcceptance=fail`は除外する。
2. offline scoreが`pass/fail`なら、その結果をquality判定に使う。onlineが`unavailable`でもoffline passは採用できる。
3. offline scoreがないstrong-online-oracle profileでは`onlineAcceptance=pass`をquality passにできる。
4. 両方で判定できなければ`quality=unknown`で、quality-conditioned bandへ入れない。
5. `partial`をpassへ暗黙変換せず、case manifestで別の明示基準がある場合だけ独立stratumにする。

## 4. Atlasの閲覧単位

### 4.1 Case card

exact task instance単位です。再現性とrun varianceを見るために使います。

```text
case: REVIEW-M-004@r2
task capsule digest: sha256:...
base snapshot: <immutable digest>
observations: all raw durations
same-case median/range: ...
```

### 4.2 Family card

同じtask family、structural size、configurationの複数caseを束ねます。新しいprojectの概算はこちらを主に参照します。

```text
family: review / M / seeded multi-file defects
case variants: <count>
run samples: <count>
first-valid-artifact distribution: ...
user-result distribution: ...
quality-conditioned user-result distribution: ...
between-case spread: ...
n_cases / n_runs / n_censored: ...
model identity confidence / applied settings / observation window: ...
```

### 4.3 Configuration card

同じcaseに対する実行構成別の実測を横並びにします。ただし優劣を自動判定しません。

| Configuration | Identity / applied settings / surface | first valid artifact | user result | worker minutes | outcome | Evidence state |
| --- | --- | ---: | ---: | ---: | --- | --- |
| solo | TBD | TBD | TBD | TBD | TBD | unmeasured |
| primary + delegate | TBD | TBD | TBD | TBD | TBD | unmeasured |
| two independent candidates | TBD | TBD | TBD | TBD | TBD | unmeasured |
| bounded dialogue | TBD | TBD | TBD | TBD | TBD | unmeasured |

### 4.4 Environment card

referenceの移植可能性を判断するため、machine/container、CPU/memory、requested alias、resolved identity、identity confidence、requested/applied setting、CLI/runtime surface、permission mode、base image、network/cache/context状態、観測期間をまとめます。

### 4.5 Primary search key

最低限、`task family + size profile + collaboration relation + model identity series + applied generation settings + execution surface + session class + source series + progress resolution`でcardを分けます。worker widthとdialogue depthは無限に格子を増やさず、該当configuration card内のcurveとして表示します。

## 5. 表示する数値

初期sampleでは、もっとも正直な情報は全observationsです。標本が増えたら次を追加します。

- sample countとdistinct case count
- median、minimum、maximum
- quartileまたはcentral prediction band
- failure/timeout/rate-limit count
- same-case spreadとbetween-case spread
- 観測期間と最終観測日
- evidence state

`p95`は十分なtail sampleがあるcellだけに表示します。少数sampleの最大値をp95と呼び換えません。

## 6. Evidence state

固定回数ではなく、何を観測できたかでreferenceの成熟度を示します。

| State | 意味 |
| --- | --- |
| `unmeasured` | 実runなし |
| `single-observation` | 一件の実測。例示には使えるが目安とは呼ばない |
| `same-case-repeat` | 同一caseのrun varianceを観測済み |
| `family-provisional` | 複数caseでbetween-case spreadを観測した暫定目安 |
| `family-characterized` | 複数caseと複数観測blockの多様性を満たし、事前に定めた精度目標の時間帯を推定できる |
| `stale` | model/CLI/environment更新で直接適用しにくい |

stateは品質rankingではありません。たとえば`family-characterized`でも、その構成が良いとは限りません。

## 7. Project側へ渡す材料

atlasは次を渡します。

- 具体的な時間帯とばらつき
- progress envelopeを観測できる場合のfirst valid artifactまでの待ち時間
- user-visible resultまでのtailと、quality-conditioned distribution
- online validationとoffline study scoreの分離
- 並列worker総稼働時間
- failure/recoveryの頻度と所要時間
- どの条件で測ったか
- どこが未測定か

projectはこれを期限、risk、利用可能provider、変更内容、review capacityと組み合わせて自分の計画を作ります。このrepository側からdecision policyを埋め込みません。
