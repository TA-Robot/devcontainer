# Milestone A implementation record

実装日: 2026-08-26

Status: schema + deterministic clock + fake runner implemented; no live provider run

## Outcome

Milestone Aの「測定器が嘘をつかない」範囲を実装しました。

- study / case / runのJSON Schema v1（capabilityはWave 0.5でv2へ更新）
- UTC wall time + monotonic nanosecond event
- missingを`not-applicable` / `not-observed` / `unknown`へ分離
- observed eventからのみdurationを導出
- canonical quality-pass rule
- worker aggregate / active union / peak concurrency
- incomplete workerとuntracked nested workerのcoverage低下
- one-run-one-fileのprivate atomic immutable write
- providerを呼ばずsleepもしないdeterministic fake runner
- schemaだけでなくderived値を再計算するsemantic validation

## Files

```text
experiments/multi-agent-duration/schemas/
  study.schema.json
  case.schema.json
  capability.schema.json
  run.schema.json

scripts/
  agent-duration-study
  agent_duration_study.py
  test-agent-duration-study.py
```

既存の`agent_contracts.py`へdependency-freeなnumeric bound validationを追加しました。runtime dependencyは増えていません。

## Clock catalog v1

| Event | Role |
| --- | --- |
| P0 / P1 | provisioning start / ready |
| T0 | run admitted |
| T1 | first dispatch |
| T2 | first contract-valid progress artifact |
| T3 | required workers terminal |
| T4 | explicit synthesis envelope |
| V0 / V1 | online validation start / terminal |
| T6 | user-visible result ready |
| TX | run terminal for every outcome |
| S0 / S1 | offline scoring start / terminal |

`TX`はtimeout/failureにも必ずterminal wall timeを残すため、実装時に追加しました。成功時はT6と同時でもよく、offline S0/S1はTX後でも構いません。

## Duration catalog v1

- provision
- dispatch delay
- first artifact latency
- required workers ready
- worker terminal span
- synthesis tail
- online validation
- post-validation tail
- user result
- terminal wall
- aggregate worker
- worker active union
- offline scoring

依存eventがobservedでないduration keyはJSONからomitします。0で埋めません。`durations_ms`を手で改変するとvalidationが再計算差分でrejectします。

## Model / effort representation

review後の計画をさらに具体化し、settingごとのrecordへしました。

```json
{
  "namespace": "grok.reasoning",
  "key": "effort",
  "requested_value": "high",
  "status": "applied | rejected | not-advertised | unknown",
  "applied_value": "high"
}
```

`status=applied`だけ`applied_value`を必須化します。同一participantでnamespace/keyが重複するrecordはsemantic validationでrejectします。requestedだけでeffort stratumを作らない計画をmachine contractへ落としたものです。

## Fake scenarios

| Scenario | 確認する契約 |
| --- | --- |
| `delegated-complete` | worker、dialogue、T2/T4、V0/V1、offline score |
| `solo-complete` | T3/T4なしでもonline validationを算出 |
| `missing-progress` | final resultからT2を補完しない |
| `timeout` | unfinished worker、TX、censored terminal、worker duration非掲載 |
| `provider-failure` | failed sampleを時間ごと残す |
| `nested-untracked` | observed worker timeをlower boundと明示 |

Example:

```bash
scripts/agent-duration-study fake-run \
  --scenario delegated-complete \
  --output-dir /tmp/duration-study-runs

scripts/agent-duration-study validate \
  --kind run \
  /tmp/duration-study-runs/fixture-delegated-complete.json
```

同じrun IDを同じdirectoryへ再出力するとoverwriteせず失敗します。file modeは`0600`です。

## Validation

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  scripts/agent_contracts.py \
  scripts/agent_duration_study.py \
  scripts/agent-duration-study

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  scripts/test-agent-duration-study.py \
  scripts/test-agent-contracts.py
```

実装時点で28 tests pass。

## Deliberately not implemented

- generationを伴うCodex / Claude / Grok live canary
- providerのresolved model / applied effort実観測adapter
- case catalog contentsとfixture repository
- `agentctl` / episode correlation injection
- persistent duration-atlas volume integration
- adaptive sampler、aggregate report、lookup skill
- schedulerまたは定期実行

Wave 0.5の非生成CLI probeは後続の`16-wave-0.5-passive-capability-probe.md`で実装しました。次のcritical pathはMilestone Bのcase catalogと、Milestone Cのexplicit live canaryです。受動広告と実適用を混ぜず、取得不能なfieldを非掲載にできることを確認します。
