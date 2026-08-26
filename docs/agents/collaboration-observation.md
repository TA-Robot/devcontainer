# Zero-input collaboration observation

Status: automatic content-free episode ledger implemented
Updated: 2026-08-26

## Outcome

人間がformや日報を記入することを前提にしません。container-managed Codex / Claude / Grok hookと`agentctl` activity envelopeから、solo turnとworkerを伴うturnを同じschemaで自動要約します。

```text
provider / agentctl lifecycle event
  -> allowlist normalization
  -> per-session counters and timing
  -> terminal / superseded / expired boundary
  -> bounded content-free episode ledger
```

このdevcontainer基盤は、rebuildをまたいで残るnamed volumeへ保存します。

```text
/var/lib/mira-observations/collaboration-episodes.json
```

pathは`MIRA_COMPANION_EPISODE_DIR`で変更できます。未設定時だけ`MIRA_COMPANION_STATE_DIR`、さらに未設定なら`~/.local/state/mira-companion`へfallbackします。これはbest-effort observationであり、providerやjobの成否を決めるcorrectness pathではありません。

## What is observed automatically

- opaque workspace / session / episode ID
- sourceとprovider
- start / finish / durationとterminal outcome
- content-free event / activity category count
- structured test outcome count
- worker start / stop、peak concurrency、provider / role count
- observed worker slot-milliseconds
- test failure後のeditとred-to-green recovery
- 最後のworker終了からturn terminalまでのelapsed / activity count
- start、terminal、worker-start eventが観測できたかというcoverage

`agentctl`のjob / attempt、worktree、state transition、validation evidenceは従来どおりbroker DBが正本です。episode ledgerはそれを置き換えません。

## What is deliberately unknown

hook topologyだけでは次を正しく判定できません。

- expected value mechanism
- binding constraint
- semantic relation / lifecycle
- worker成果が最終判断を変えたか
- correctness、maintainability、user value
- 実際に人間がreviewへ使った時間

そのため`semantics`はannotation sourceがない限り`unknown`、`expectedMechanisms`は空配列です。agent数やevent列から意味を捏造しません。primaryが通常作業中に持つplan / synthesisはagent-owned artifactへ残せますが、ユーザーへ記入を求めません。利用可能なmachine annotation surfaceができるまでは欠測を欠測のまま扱います。

## Human-review proxy

direct providerのparent episodeでworker start / stopが揃った場合だけ、最後のworker終了からterminalまでを`reviewProxy`として記録します。

これは次を混ぜた**代理値**です。

- primary agentのsynthesis
- testや追加編集
- userが画面を読んでいた時間
- provider / UI待ち

したがって「人間のreview時間」とは呼びません。`elapsedMs`とpost-worker event / category countを併記し、比較時も同じexecution surface内の傾向としてだけ使います。`agentctl` outer jobやworker stopが欠けたepisodeでは`available: false`です。

## Ledger contract

```json
{
  "schemaVersion": 1,
  "updatedAt": "2026-08-26T00:00:00Z",
  "retention": {
    "role": "storage-cost-cap",
    "maxEpisodes": 512
  },
  "episodes": [
    {
      "schemaVersion": 1,
      "id": "opaque",
      "session": "opaque",
      "workspace": "opaque",
      "source": "codex",
      "provider": "codex",
      "startedAt": "2026-08-26T00:00:00Z",
      "finishedAt": "2026-08-26T00:01:00Z",
      "durationMs": 60000,
      "startEvent": "UserPromptSubmit",
      "terminalEvent": "Stop",
      "terminalOutcome": "success",
      "completion": "observed-terminal",
      "topology": "delegated",
      "eventCounts": {},
      "categoryCounts": {},
      "outcomeCounts": {},
      "testOutcomes": {"success": 0, "failure": 0, "unknown": 0},
      "delegation": {
        "starts": 1,
        "stops": 1,
        "peakConcurrent": 1,
        "workerActiveMs": 10000,
        "unfinishedAtTerminal": 0,
        "providerCounts": {"codex": 1},
        "roleCounts": {"researcher": 1}
      },
      "reviewProxy": {
        "kind": "post-worker-tail",
        "available": true,
        "elapsedMs": 5000,
        "eventCounts": {},
        "categoryCounts": {}
      },
      "reworkProxy": {
        "testRecoveries": 0,
        "editEventsAfterTestFailure": 0
      },
      "semantics": {
        "expectedMechanisms": [],
        "bindingConstraint": "unknown",
        "relation": "unknown",
        "lifecycle": "unknown",
        "annotationSource": "none"
      },
      "coverage": {
        "startObserved": true,
        "terminalObserved": true,
        "workerStartsObserved": true
      }
    }
  ]
}
```

`topology`は観測形だけです。

- `solo-observed`: worker startを観測しなかったdirect turn
- `delegated`: worker startまたはconcurrent workerを観測したdirect turn
- `managed-job`: `agentctl` outer lifecycle

`solo-observed`は「内部delegationが絶対になかった」ことを証明しません。coverageとprovider hook capabilityを合わせて読みます。

## Retention and opt-out

episode数の上限は品質上の推奨値ではなく、local stateを無制限に増やさないための`storage-cost-cap`です。

- default cap: `512`
- override: `MIRA_COMPANION_EPISODE_LIMIT`
- accepted range: `1..4096`
- observation opt-out: `MIRA_COMPANION_EPISODES_ENABLED=0`
- companion全体のopt-out: `MIRA_COMPANION_ENABLED=0`

上限到達時は古いepisodeから落とします。集計や長期保存が必要になった場合も、無断でcloud送信や無制限retentionへ変えません。

### Persistent volume

- reason: container rebuildでobservation evidenceを失わないため。
- scope: named volume `devcontainer-mira-observations`を`/var/lib/mira-observations`へmountする。
- impact: project横断のlocal ledgerを一つ保持する。recordはopaque workspace keyでpartitionし、別containerからの並行更新はledger固有の`flock`で直列化する。
- alternative: `MIRA_COMPANION_EPISODE_DIR`をproject固有のpersistent pathへ変更する。未設定fallbackはcontainer lifecycleにより消える可能性がある。
- removal: 利用containerを停止し、保持が不要と確認してから`docker volume rm devcontainer-mira-observations`を明示実行する。自動削除しない。

## Privacy and failure boundary

保存しないもの:

- prompt、response、private reasoning、transcript
- command、tool input / output、error detail
- task objective、file path、workspace path
- raw session / job / attempt / agent ID
- credential、environment dump

workspace pathと各IDはprocess内でopaque hashへ変換します。state directoryは`0700`、fileは`0600`、更新は既存lock内でatomic replaceします。ledger write failureはprovider、tool、`agentctl` job、Mira UIを失敗させません。

## Analysis rules

- `terminalOutcome: success`はprovider turnの終了であり、artifact品質ではない。
- direct provider episodeと`agentctl` outer episodeは二重観測になり得るため、sourceを分けて集計する。
- coverageが異なるepisodeを同じ精度として比較しない。
- proxyから因果効果を断定しない。soloとの比較にはtask class、acceptance、risk、execution surfaceを揃えた実験が要る。
- event countやworker countをproductivity KPIにしない。
- semanticsが`unknown`のepisodeを後付けで都合よく分類しない。

episode ledgerで観測可能性は作れますが、global optimumは作れません。project-localなrouting判断を変えるだけのevidenceが得られた時だけplanning priorを更新します。
