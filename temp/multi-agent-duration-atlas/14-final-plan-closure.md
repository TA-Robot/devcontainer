# Revised audit closure

日付: 2026-08-26

## Audit result

fresh Grok 4.6 sessionによる改訂版監査は`conditionally ready`でした。前回Mustの大半はclosedで、Milestone A前の計画blockerは二つに絞られました。原文は`13-grok-revised-plan-audit.md`です。

review実行は再び`--reasoning-effort high`をrequestedしましたが、applied確認はできないため`requested-high / applied-unknown`として扱います。

## Closed after the revised audit

### Derived duration catalog

- online validationをT4依存の`T5−T4`から、独立区間`V1−V0`へ変更
- C0/soloでT3/T4がnot-applicableでもtest/build時間を測定可能
- public worker metricsを次へ統一
  - requestからrequired workers終了まで
  - first tracked worker startからterminalまでのspan
  - tracked worker active interval union
  - aggregate worker time
- 真のcritical pathを復元できないときはcritical pathと呼ばない

### Quality-conditioned population

canonical規則を`01`、`04`、`05`へ統一しました。

1. online failは除外
2. offline pass/failがあればそれをquality判定へ使用
3. online unavailableでもoffline passは採用可能
4. offlineなしのstrong online oracleではonline passを使用可能
5. 判定不能はunknown、partialは明示基準なしにpassへしない

offline scoring runtimeはuser waitへ足しません。

### Corpus profile

isomorphic variantの必須一致条件へlanguage/toolchain profileを追加し、PythonとBashなどの差をbetween-case varianceへ隠さないようにしました。

### Skill context boundary

- `maxRows` / `maxOutputBytes`をrequired context-safety configにする
- 未設定時にunbounded fallbackしない
- single observationはraw point、same-caseはrange、family stateだけband
- aggregate pathを`generated/duration-atlas/current.json` + `manifest.json`へ統一
- discovery conflictではsource/manifestを表示し、silentに古いsnapshotを選ばない

## Plan status

計画上のschema contradictionは解消しました。次に進む場合は`07-implementation-roadmap.md`のMilestone AとP0から開始できます。

pilotで初めて答える事項は未確定のまま残します。

- providerがresolved model / applied effort / progressを実際に返すか
- optional fieldとstatus objectの最終schema表現
- setting statusをkey単位にする必要性
- exact context cap値（skill forward-testで決めるsafety cap）
- skillのcanonical distribution location
- cross-provider participant tupleのseries key
- full worker interval graphをどこまで取得できるか

これらは測る前に推測で埋めず、capability probeまたはforward-testの結果で決めます。
