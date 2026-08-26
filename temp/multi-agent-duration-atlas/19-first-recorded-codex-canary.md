# First recorded isolated Codex canary

実施日: 2026-08-26

Status: run schema v2、workspace-only Codex runner、hidden evaluatorのone-shot結合を実装し、S caseの有限canaryを3件記録済み。全task outcomeがquality failのため、quality-pass時間母集団には未採用。

## Outcome

最初のimmutable recordは次です。

- Run: `codex-f04-s-terra-low-20260826-r02`
- Case: `F04-S-PY-001` / bounded implementation / structural size S
- Configuration: C0 primary-only、nested delegation disabled
- Requested model: `gpt-5.6-terra`、identity confidence `alias-only`
- Requested effort: `low`、applied status `unknown`
- CLI: Codex `0.146.0`
- Frozen image: `sha256:3f58b6614a86e40bd3adfa49f9a9b5711bcf24b8a28fe574dec8ea1e0872cc9d`
- Provider terminal: 39,858.591 ms
- Online evaluator: 1,065.493 ms
- T0–T6 user-result wall: 40,936.281 ms
- T0–TX terminal wall: 40,936.286 ms
- Public workspace check: pass
- Hidden check: fail
- Canonical quality: fail (`online-fail`)
- Retry: none

これは「Sなら約41秒」という推定値ではありません。1 case、1 run、quality failの単一観測であり、range、typical band、model差、effort差を主張できません。失敗までの時間を含むraw observationとしてだけ保持します。

Machine-readable evidence:

- `evidence/wave-1/codex-f04-s-terra-low-20260826-r02.json`

## Finite canary batch

instrumentation確認後、同一case/image/CLIでrequested effortまたはmodel aliasを一軸だけ変えた2件を追加しました。いずれもretryはありません。

| Run | Requested model | Requested effort | Provider ms | T0–T6 ms | Public | Hidden | Quality |
| --- | --- | --- | ---: | ---: | --- | --- | --- |
| r02 | gpt-5.6-terra | low | 39,858.591 | 40,936.281 | pass | fail | fail |
| r03 | gpt-5.6-terra | high | 34,463.320 | 35,339.100 | pass | fail | fail |
| r04 | gpt-5.6-sol | low | 51,896.551 | 52,766.603 | pass | fail | fail |

追加evidence:

- `evidence/wave-1/codex-f04-s-terra-high-20260826-r03.json`
- `evidence/wave-1/codex-f04-s-sol-low-20260826-r04.json`

この3行をmodel/effort rankingとして読みません。特にr02/r03はapplied effortが両方`unknown`であり、requested settingの差しか確認できません。全件quality failなので、時間差は「失敗terminalまでの観測差」です。r03がr02より短いことや、r04が長いことから速度・品質の優劣を推定しません。

## Instrumentation verdictとtask verdictを分ける

今回のinstrumentation gateはpassです。

- provider processを開始し、Codex JSONL terminal eventを観測した
- workspaceの変更を観測した
- raw prompt、agent message、stderr、credential pathをrecordへ保存していない
- provider成功後に別containerでpublic/hidden checkを実行した
- run record v2のschema/semantic validationを通過した
- provider successとhidden failureを同じrecordから切り離せない

一方、task verdictはfailです。provider exit 0やfinal messageの存在をquality passへ読み替えていません。`online_acceptance=fail`からcanonicalに`quality_pass=false`を導出するため、この39.9秒/40.9秒をsuccess latencyへ混入させません。

## Agent-side isolation

各live turnは一時fixtureと一時HOMEだけをmountしたowned containerで実行します。

```text
host harness
  ├─ generated fixture workspace -> /case (write)
  ├─ ephemeral agent HOME        -> /agent-home
  └─ Codex auth source           -> auth.json (read-only nested bind)

Codex task sandbox
  ├─ /case: write
  ├─ minimal runtime + locked CLI tree: read
  ├─ unrelated filesystem: deny
  ├─ task command network: deny
  ├─ web/apps/browser/image/multi-agent/plugins: disabled
  └─ history/memory/session persistence: disabled
```

outer containerはcapability drop、no-new-privileges、read-only rootfs、PID/memory/CPU/nofile/output/timeout capを持ちます。Codex client transportとagentが実行するcommand networkは別境界です。sandbox preflightはgenerationなしでworkspace write、unrelated read denial、command network denialを毎run前に検査します。

Docker default seccompではCodex内部sandboxのuser namespace作成が阻害されたため、outer containerだけ`seccomp=unconfined`です。これはtask processを無制限にする意味ではなく、内側のCodex permission profileを成立させるための互換設定です。capability drop、no-new-privileges、resource cap、Codex filesystem/network policyは維持します。

## Record v2

v1ではprovider summaryとevaluator resultを別々に扱えたため、fast-but-wrong runから時間だけを拾う余地がありました。v2は次をrequiredにしました。

- content-free provider event/item counters
- requested model/effortと、そのidentity/application confidence
- exact CLI versionとimage digest
- output/stderr byte count、output cap、changed path count
- raw prompt/output/stderr/credential path非永続化の固定値
- sandbox preflight evidence
- evaluator isolation、check ID、exit status、duration
- evaluator resultとonline acceptanceのsemantic consistency

event typeはschema-safeな名前だけを平文で残し、それ以外は名前をdigest化します。thread IDも原文ではなくSHA-256 digestだけです。

## Earlier calibration attempts

record v2以前の試行はatlas sampleに昇格しません。

1. 3回の即時終了はDocker stdin未接続による`No prompt provided`で、generation requestではなかった。
2. stdin修正後の最初の実generationはprovider約27.7秒、public pass、hidden failだった。
3. そのrunはprovider/evaluator/landmarkを一つのimmutable recordへ結合していなかったため、参考diagnosticに留めた。

今回のr02/r03/r04でもhidden failが再現しました。ただしraw artifactは意図的に破棄するため、recordだけから具体的な誤実装内容を再構成しません。case capsuleは「normalized resultがemptyならValueError」と明示しており、private known-good artifactは同じisolated evaluatorをpass済みです。

## Command surface

recordを残す正式なlive entrypointは次です。

```bash
scripts/agent-duration-study run-codex-study \
  --case-id F04-S-PY-001 \
  --output-dir <private-record-directory> \
  --image <locked-image-tag> \
  --model <requested-model> \
  --effort <requested-effort> \
  --run-id <unique-run-id> \
  --confirm-live-provider
```

1 invocationは1 generation request、retryなしです。同じrun IDが既に存在すればprovider開始前に拒否します。quality failはrecordを書いたうえでCLI exit 1、contract/input errorはexit 2です。

## Next controlled step

同じcaseのlive run追加はここで止めます。次はraw sampleを条件・品質・欠測と一緒に表示するreporterを実装し、この3件がquality-pass bandへ混入しないことをend-to-endで検証します。その後、次の有限batchを宣言してからcase variantまたは別sizeへ進みます。

run varianceを得る反復、別caseによるcase variance、model contrast、M/L拡張はそれぞれ別の有限batchとして宣言します。今回のrequested-effort contrastはapplied settingを確認できないため、Wave 5Aのapplied-effort seriesへ昇格しません。
