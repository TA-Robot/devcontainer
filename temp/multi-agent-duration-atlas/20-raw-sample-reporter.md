# Raw sample reporter

実装日: 2026-08-26

Status: validated run recordを、条件・品質・欠測を保ったままbounded表示するCLIを実装。統計集約、typical band、routing ruleはまだ生成しない。

## Outcome

次のcommandでrun fileまたはrun fileだけを置いたdirectoryを照会できます。

```bash
scripts/agent-duration-study report-runs \
  temp/multi-agent-duration-atlas/evidence/wave-1 \
  --case-id F04-S-PY-001 \
  --provider codex \
  --limit 20
```

2026-08-26の3 canaryに対する要約は次です。

```text
terra low   40,936.286 ms  failed-terminal  quality-fail
terra high  35,339.102 ms  failed-terminal  quality-fail
sol low     52,766.608 ms  failed-terminal  quality-fail

matched=3 / quality-pass=0 / quality-fail=3 / quality-unknown=0
aggregation=none / evidence=single-observation per row
```

これは時間bandではなくraw inventoryです。表示値はquality fail runのT0–TXであり、quality-pass user-result populationには入りません。

## Duration role

reporterは`quality_pass`を先に判定し、表示するdurationのroleを固定します。

| Quality population | 表示duration | Role |
| --- | --- | --- |
| `quality-pass` | T0–T6 | `quality-pass-user-result` |
| `quality-fail` | T0–TX | `failed-terminal` |
| `quality-unknown` | T0–TX | `unknown-terminal` |

fast failureをfast successへ混ぜません。failure/unknownも消さず、time-to-terminalの観測として残します。

## Conditions retained per row

JSON formatでは各sampleに次を残します。

- case ID/revision/family/structural size/profile
- configuration ID/relation/actual participant・worker数
- provider、requested model、identity confidence
- requested generation settingとapplied status
- CLI version、execution surface、image digest
- provision/first artifact/validation/user/terminal/worker durationの観測済み部分だけ
- infrastructure/artifact/online/offline/canonical quality/failure class
- T2/T4 coverageとevaluator status
- `single-observation` evidence state

欠測durationは0で埋めずkey自体を出しません。たとえば現Codex direct surfaceはcontract-valid progress envelopeを返さないため、T2と`first_artifact_latency`は非掲載です。

## Bounded query

利用可能なfilter:

- `--case-id`
- `--provider codex|claude|grok|fixture`
- `--quality all|pass|fail|unknown`
- `--limit`（1..500、default 50）
- `--format table|json`

directory scanは非再帰で、discovery hard capは5,000 recordsです。duplicate run ID、schema/semantic invalid record、上限超過はfail closedです。表示limitで切れた場合は`truncated=true`とmatched/displayed countを返します。

## Explicit non-features

現段階のreportには次を入れません。

- mean/median/quantile/range
- model/provider winner
- global selection recommendation
- observedしていないcellの補間
- requested effortをapplied effortへ読み替える処理
- failureとquality passのduration pooling

JSONには`aggregation=none`と`selection_rule_generated=false`を固定表示します。skill化時にこのbounded JSONを読み込ませれば、raw evidence全件をpromptへ流さずに済みます。

## Test contract

50 testsで次を確認しています。

- pass/fail/unknown populationの分離
- passはuser-result、fail/unknownはterminal durationを表示
- `typical`、quantile、recommendationを生成しない
- filter/limit/truncation
- requested settingの`unknown`を表示
- duplicate run ID rejection
- CLI JSON/table経路

## Next

次は同一条件のrepeatとisomorphic case variantを別々に表現できるseries summary contractです。ただしquality-passが0件の現cellにはtypical bandを出さず、`insufficient-quality-pass`を明示します。その表示規則をtestしてから新しいlive batchを開始します。
