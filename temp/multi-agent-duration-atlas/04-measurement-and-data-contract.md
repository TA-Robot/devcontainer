# 04. Measurementとdata contract

## 1. Clockをuser wait、component、offline scoreへ分ける

全timestampはUTC wall clockとmonotonic elapsedの両方を使います。wall clockは別eventとの相関、monotonic clockはduration計算に使います。

### Provisioning landmarks

| ID | Landmark | 意味 |
| --- | --- | --- |
| P0 | provision start | worktree、image、cache restoreなど利用者request前後の準備開始 |
| P1 | execution ready | taskをdispatch可能になった |

provisioningをT0より前に行うcaseと、request後に行うcaseを区別します。`representative-scenarios.md`のworktree-ready/startup分離を引き継ぎます。

### Online/user-visible landmarks

| ID | Landmark | 意味 |
| --- | --- | --- |
| T0 | admitted | harnessがrunを受理し、条件を確定した |
| T1 | first dispatch | primaryまたは最初のworkerへ実行を渡した |
| T2 | first contract-valid artifact | family schemaを満たす最初のprogress artifactを受領した |
| T3 | required workers terminal | acceptanceに必要なtracked workerが全てterminalになった |
| T4 | synthesis envelope | primaryが採用・統合・unresolvedを明示したenvelopeを受領した |
| V0 | online validation start | 利用者へ返す前に必要なtest/build/validationを開始した |
| V1 | online validation terminal | online test/build/validationが完了した |
| T6 | user result ready | final result envelopeを利用者へ渡せる状態になった |
| TX | run terminal | success/failure/timeout/cancelを問わずrunが終了した |

### Offline study landmarks

| ID | Landmark | 意味 |
| --- | --- | --- |
| S0 | offline scoring start | gold、seeded finding、calibrated evaluatorによる事後採点開始 |
| S1 | offline scoring terminal | study scoreが確定した |

offline scoreはT6後でもよく、S1−S0をuser waitへ足しません。offline scoreでquality passしたrunのT6−T0を抽出することはできます。

landmarkの状態は次の三つを区別します。

- `not_applicable`: 構成にそのeventが存在しない
- `not_observed`: 存在するはずだがadapter/hookで取れない
- `unknown`: eventの意味自体をmachineで識別できない

いずれも0msや推定timestampで埋めません。

## 2. Derived durations

```text
provision duration       = P1 - P0
dispatch delay           = T1 - T0
first artifact latency   = T2 - T0            # T2 observed時だけ
required workers ready   = T3 - T0
worker terminal span     = T3 - first worker start
synthesis tail           = T4 - T3            # explicit T4時だけ
online validation time   = V1 - V0            # T3/T4に依存しない
post-validation tail     = T6 - V1             # online validation実行時だけ
user-result wall time    = T6 - T0
terminal wall time       = TX - T0             # 全outcome
aggregate worker time    = sum(tracked worker stop - start)
worker active union      = union(tracked worker intervals)
recovery user time       = accepted T6 - first failed attempt terminal
offline scoring time     = S1 - S0             # user wait外
```

`quality-conditioned user time`は別clockではありません。次のcanonical quality-pass規則を満たしたrunの`T6 - T0`分布です。

```text
if onlineAcceptance == fail:
  qualityPass = false
else if offlineScore in {pass, fail}:
  qualityPass = (offlineScore == pass)
else if strongOnlineOracle and onlineAcceptance == pass:
  qualityPass = true
else:
  qualityPass = unknown
```

`onlineAcceptance=unavailable`はoffline passを妨げません。`partial`はcase manifestに明示基準がない限りpassへ昇格しません。

worker critical pathをevent graphから復元できない場合、worker spanをcritical pathと呼びません。aggregate timeが全descendantを追跡できない場合はlower boundとしてcoverageを落とします。

## 3. T2はfirst usefulではない

人間のratingなしに「役に立った」を識別できません。T2はあくまで**contract-valid progress artifact**です。

例:

- review: path、location、severity、rationaleを持つfinding envelope
- diagnosis: hypothesis、evidence reference、next falsification stepの組
- implementation: immutable patch/checkpoint digestとvalidation status
- design: constraintへ紐づく比較claimと検証可能なrisk
- dialogue: claim ID、evidence reference、state transitionを持つexchange artifact

schema-validでも内容が誤りならquality scoreはfailです。provider/runtimeがprogress envelopeを出さない場合、T2は`not_observed`のままにし、final result時刻をfallbackしません。そのsurfaceのatlasにfirst-artifact latencyを掲載しません。

## 4. T4とreview proxy

T4はprimaryが明示的なsynthesis envelopeを発行した時だけ観測します。worker終了後のelapsedやevent countから「判断が変わった」と推測しません。

`docs/agents/collaboration-observation.md`の`reviewProxy`はpost-worker tailの代理値で、人間review時間でもsynthesis decision時刻でもありません。T4の代用に使いません。

## 5. Fast but wrongを時間目安へ混ぜない

各runはclockとoutcomeを別fieldに持ちます。

```text
outcome:
  infrastructure: success | failure | timeout | cancelled | invalid
  artifact: valid | invalid | missing | not-applicable
  onlineAcceptance: pass | fail | partial | unavailable
  offlineScore: pass | fail | partial | unavailable | not-run
  qualityPass: true | false | unknown
  qualityBasis: offline-score | strong-online-oracle | unavailable
  failureClass: ...
```

- 全outcomeへ`terminal wall time`を残します。
- quality-conditioned distributionは上記canonical `qualityPass=true` runだけで作ります。
- accepted-only distributionと、timeout/censoringを含むuser-wait riskを並べます。
- provider processの正常終了をartifact品質と同一視しません。
- weak oracleしかないfamilyは`onlineAcceptance=unavailable`のままにします。

failure class候補:

- `timeout-cap`
- `rate-limit`
- `provider-refusal`
- `approval-wait`
- `nested-worker-untracked`
- `gold-leak`
- `clock-anomaly`
- `fixture-invalid`
- `artifact-invalid`
- `online-validation-failed`

## 6. Task family別quality oracle

| Family | Primary oracle | 補助metric |
| --- | --- | --- |
| trace | gold node/edge coverage | unsupported edge、path accuracy |
| review | seeded finding recall | false positives、severity calibration |
| diagnosis | root cause + reproducer | regression test rejection of bad version |
| implementation | acceptance tests | mutation/negative case、changed-path contract |
| refactor | behavior equivalence | compatibility and rollback checks |
| test design | known-bad rejection | mutation kills、flakiness |
| documentation | executable fact checks | broken links、source-of-truth consistency |
| design | constraint/counterexample checklist | unsupported assumptions、unknown handling |
| security | seeded exploit/negative test | threat coverage、false alarms |
| performance | reproducible benchmark | noise interval、regression guard |
| operations | lifecycle smoke test | owned-resource residue、recovery success |
| synthesis | source entailment | contradiction resolution、decisive evidence |

LLM evaluatorを使う場合は、known-good / known-bad / ambiguous fixturesで先にcalibrationします。区別できないevaluatorのscoreはatlasへ採用しません。evaluator runtimeはS0–S1です。

## 7. Model identity、effort、runtime contract

flatな`model`/`reasoning`文字列を使いません。

```json
{
  "model_identity": {
    "requested_alias": "grok-4.6",
    "requested_source": "flag",
    "identity_confidence": "alias-only"
  },
  "generation_settings": [
    {
      "namespace": "grok.reasoning",
      "key": "effort",
      "requested_value": "high",
      "status": "unknown"
    }
  ],
  "runtime_identity": {
    "provider": "grok",
    "cli_name": "grok",
    "cli_version": "1.0.5",
    "cli_source": "host-sync",
    "execution_surface": "agentctl-job",
    "permission_mode": "automatic",
    "observed_at": "2026-08-26T00:00:00Z"
  }
}
```

v1 schemaはoptional fieldとkey単位setting statusへ統一しました。resolved IDやapplied settingをproviderが返さない場合、fieldを捏造しません。実装正本は`experiments/multi-agent-duration/schemas/run.schema.json`です。

## 8. Provenance

各fieldは次のprovenance classを持ちます。

- `observed`: hook、process、filesystem、testから直接得た
- `declared-by-harness`: case manifestやrun configで固定した
- `derived`: observed timestamp/counterから算出した
- `evaluated`: versioned evaluatorがartifactへ適用した
- `unknown`: 観測不能または意味未定義

agentの自己申告時間はclock sourceとして使いません。agentが「完了」と書いたことと、harnessがenvelopeを受領した時刻を分けます。欠けたlandmarkに依存するduration keyはrecordからomitし、0や`null`をdurationとして入れません。

## 9. Run record案

以下は検討時の読みやすい概念表示です。実装済みv1のfield名、enum、required条件はsnake_caseの`experiments/multi-agent-duration/schemas/run.schema.json`を正本とします。

```json
{
  "schemaVersion": 1,
  "studyId": "duration-atlas-2026q3",
  "runId": "opaque",
  "blockId": "opaque",
  "case": {
    "id": "F03-M-004",
    "revision": 2,
    "capsuleDigest": "sha256:...",
    "sourceType": "historical-replay",
    "family": "diagnosis",
    "size": "M",
    "profileId": "M-coupled-deterministic-python",
    "descriptors": {
      "contextSurface": "multi-module",
      "coupling": "coupled",
      "validationDepth": ["unit", "integration"],
      "failureDistance": "cross-module",
      "languageToolchain": ["python"]
    },
    "ambiguity": "bounded-open",
    "oracleStrength": "deterministic",
    "decomposability": "partial"
  },
  "snapshot": {
    "baseSha": "...",
    "bundleDigest": "sha256:...",
    "fixtureRevision": "...",
    "instructionSetDigest": "sha256:..."
  },
  "configuration": {
    "id": "C1",
    "relation": "bounded-delegation",
    "participantPlan": "one-root-cause-investigation-shard",
    "participantsActual": 2,
    "workersActual": 1,
    "peakConcurrent": 1,
    "nestedDelegation": "disabled",
    "independencePolicy": "fresh-worker-context",
    "lane": "read"
  },
  "participants": [
    {
      "role": "primary",
      "modelIdentity": {
        "requestedAlias": "...",
        "requestedSource": "flag",
        "identityConfidence": "alias-only"
      },
      "generationSettings": [],
      "runtimeIdentity": {
        "provider": "codex",
        "cliVersion": "...",
        "cliSource": "container-image",
        "executionSurface": "agentctl-job",
        "permissionMode": "automatic"
      }
    }
  ],
  "environment": {
    "imageDigest": "sha256:...",
    "machineClass": "...",
    "sessionContext": "fresh",
    "repoCache": "warm",
    "dependencyCache": "warm",
    "dockerCache": "not-used",
    "providerPromptCache": "unknown",
    "compactionObserved": "unknown",
    "competingLoad": "none-observed",
    "timezone": "Asia/Tokyo"
  },
  "limits": {
    "wallClockMs": 3600000,
    "role": "safety-censoring-cap",
    "retryPolicy": "none"
  },
  "landmarks": {
    "T0": {"status": "observed", "wallTime": "...", "monotonicMs": 0},
    "T1": {"status": "observed", "wallTime": "...", "monotonicMs": 1},
    "T2": {"status": "not_observed"},
    "T3": {"status": "observed", "wallTime": "...", "monotonicMs": 2},
    "T4": {"status": "observed", "wallTime": "...", "monotonicMs": 3},
    "V0": {"status": "observed", "wallTime": "...", "monotonicMs": 4},
    "V1": {"status": "observed", "wallTime": "...", "monotonicMs": 5},
    "T6": {"status": "observed", "wallTime": "...", "monotonicMs": 6},
    "TX": {"status": "observed", "wallTime": "...", "monotonicMs": 6},
    "S0": {"status": "observed", "wallTime": "...", "monotonicMs": 7},
    "S1": {"status": "observed", "wallTime": "...", "monotonicMs": 8}
  },
  "durationsMs": {
    "dispatchDelay": 1,
    "userResult": 6,
    "aggregateWorker": 1,
    "synthesisTail": 1,
    "onlineValidation": 1,
    "offlineScoring": 1
  },
  "correlation": {
    "episodeIds": [],
    "agentctlJobIds": [],
    "attemptIds": []
  },
  "outcome": {
    "infrastructure": "success",
    "artifact": "valid",
    "onlineAcceptance": "pass",
    "offlineScore": "pass",
    "qualityPass": true,
    "qualityBasis": "offline-score",
    "failureClass": null,
    "stopReason": "result-ready"
  },
  "quality": {
    "evaluatorId": "diagnosis-oracle@1",
    "metrics": {}
  },
  "coverage": {
    "firstArtifactResolution": "not-observed",
    "synthesisResolution": "explicit-envelope",
    "workerTree": "root-and-direct-workers"
  }
}
```

## 10. Dialogue sub-events

対話型ではexchangeごとに次を記録します。

- admitted / dispatched / artifact returned
- role、recipient、parent exchange
- claim/evidence/test reference count
- versioned family contractで定義したclaim state transition
- unresolved crux count
- stop reason

「decisive evidence」はfamily contractがallowlistしたtest/source/counterexample eventからのみ算出します。transcript本文やprivate reasoningはanalytic datasetへ保存しません。

## 11. Case catalogとraw evidenceの分離

- committed case catalog: category、descriptor、digest、oracle type
- local/private capsule: 実prompt、fixture bundle、gold patch、raw artifact
- content-free run record: ID、timing、status、count、digest
- generated aggregate: Markdown/JSON duration atlas

gold、prompt、response、private reasoning、credential、raw environment dumpをcontent-free ledgerへ入れません。再現用artifactのretentionは別policyで管理します。

## 12. 既存観測とのcorrelation gap

現在のzero-input collaboration ledgerはT0相当、terminal、worker start/stop、worker active、test outcome、post-worker tailの一部を取れます。一方、study ID、case/profile、model identity、applied setting、T2/T4/V0/V1/T6、offline score、quality oracleを持ちません。

runnerが明示したfinite studyでだけallowlist annotationとcorrelation IDを発行します。通常episodeのevent数からfamily、size、relation、synthesisを後付け推測しません。

## 13. Aggregation source of truth

- harness outer runのT0–T6（途中に独立V0/V1）をuser-waitの正本にする
- direct provider episodeと`agentctl` job/attemptはcomponent evidenceとして相関する
- 同一runのouter jobとprovider episodeを別sampleとして数えない
- direct executionと`agentctl` executionは異なるsurface seriesにする
- worker eventはaggregate worker timeへだけ使い、parent wall-clockへ加算しない
- offline evaluator processはS0–S1へだけ使う

## 14. 計測不能として残すもの

- aliasしか返らないserver側model snapshot
- silent ignoreされたeffortのapplied value
- contract-valid artifactが人間にとってusefulか
- worker成果が最終判断を変えたか
- 人間のreview/画面注視時間
- progress envelopeがないsurfaceのfirst artifact time
- annotationのないnatural taskのfamily/size/oracle
- providerが出さないthinking/tool/queue内訳
- prompt cache hitが報告されない場合のcache state
- untracked nested workerを含む真のaggregate worker time
- 測っていないconfigurationのcounterfactual duration

推測値で欄を埋めるより、`unknown`/`not_observed`/非掲載を選びます。

## 15. Coverage rules

- timestampが欠けたduration keyはomitする
- `not_applicable`、`not_observed`、`unknown`、0を区別する
- direct provider episodeと`agentctl` outer jobを二重計上しない
- child worker active timeをparent wall-clockへ足し込まない
- nested workerを追跡できないrunはaggregateをlower boundと明示する
- validationとoffline scoringの開始/終了を分ける
- machine suspend、clock jump、harness restartをanomalyとして残す
- raw sampleからaggregateへ至るtransform versionを記録する
- first-artifact resolutionが異なるrunを同じdistributionへpoolしない
