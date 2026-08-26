# Milestone B: case catalog and isolated fixture builder

実装日: 2026-08-26

Status: bounded implementationのS/M/L calibration case、disposable Git builder、hidden oracle calibrationを実装。live agent runはまだ0件。

## Outcome

時間を測る前にtask自体をversioned inputへ固定しました。

| Case | Structural size | Boundary | Strong oracle |
| --- | --- | --- | --- |
| `F04-S-PY-001` | S / local | 一つのpure function | public + hidden unit tests |
| `F04-M-PY-001` | M / coupled | Python storage、CLI、exit contract、atomic file state | unit + subprocess contract tests |
| `F04-L-PYBASH-001` | L / cross-boundary | Python storage/CLI、Bash entrypoint、fresh-process restart state | unit + lifecycle/restart tests |

このsizeは実行時間ではなく、context surface、artifact surface、coupling、validation depth、failure distance、statefulnessで定義しています。3件の実時間はまだ測っていません。

## Case schema v2

計画ではsizeと直交するとしていたのにv1 schemaへ不足していたaxisを、live data前にv2へ追加しました。

- `variant_group_id`
- `risk`
- `task_lane`
- `environment_dependence`
- `knowledge_locality`
- `expected_failure_modes`

たとえば今回のL caseはcross-boundaryですがriskはlow、task laneはwrite、execution isolationは別contractでisolatedです。「Lだからhigh risk」「writeだから同じworkspaceで実行可能」とは推測しません。

## Repository shape

```text
experiments/multi-agent-duration/
  catalog/cases.json                 # case v2 + fixture execution contract
  capsules/*.md                      # agentへ渡せるtask。goldなし
  schemas/case-catalog.schema.json
  schemas/fixture.schema.json

scripts/agent_duration_fixtures.py   # temporary repo recipe / builder / oracle calibration

<generated fixture root>/
  fixture.json                       # content-free immutable manifest
  workspace/                         # agent containerへmountしてよい唯一のtree
    .git/                             # base commit一つだけ
    AGENTS.md
    source + public tests
  control/                           # agent containerへmount禁止
    base.bundle
    hidden_tests.py
```

fixture sourceをsample appとしてrepositoryへ追加せず、builderがtemporary pathへ生成します。task capsuleとrecipe revisionを変えた場合はcase revision/digestも変わります。

## Snapshot identity

Catalog revision 1 digest at implementation:

```text
sha256:5e1f6f6f3d29ab4e9d0e73bacb870d2bec32d05d6edabcebe784a15e445f6c79
```

fixture manifestは次を自動記録します。

- catalog ID / revision / canonical digest
- case ID / revision / capsule digest
- recipe ID / revision
- deterministic base commit SHA
- Git bundle digest
- path + executable mode + contentから作るworkspace tree digest
- generated `AGENTS.md`のinstruction set digest
- initial public/hidden oracleのcontent-free outcomeとruntime

同じcaseを同じrecipeで二回生成したtestでは、base SHA、bundle digest、workspace tree digest、instruction digestが一致します。output pathやfixture IDをsnapshot identityへ混ぜません。

## Gold and history isolation

生成workspaceは次の状態です。

- branchは`main`だけ
- reachable commitはbase commit 1件だけ
- remote、tagなし
- capsule、hidden evaluator、base bundle、known-good artifactなし
- Git template hooksなし
- validation後もbase workspaceはclean

agent実行contractは`workspace-only-container-mount`です。同じVS Code devcontainerで単に`--cd`するだけでは、元repositoryのrecipe/known-good codeを読める可能性があるため入場不可です。

frozen imageへ`workspace`だけをbind mountしたsmokeでは、case source/public testsだけが見え、`control/hidden_tests.py`は存在しませんでした。

## Network boundary

`task_network_policy=disabled`はagent tool/taskから外部sourceへ接続させない意味です。Codex / Claude / Grok CLI自身のprovider control-plane通信まで無効にする意味ではありません。この二つを同じ`network disabled`へ潰しません。

agent変更後のcodeを評価するprocessはcredential environmentを継承してはいけません。local calibration evaluatorはPATH、locale、UTC、workspace pathだけのallowlist environmentを使います。live artifactはさらに`network-disabled-read-only-container`で評価するcontractです。

`evaluate-fixture`は安全な既定としてhost実行を拒否します。checked-in bad/good fixture calibrationだけは明示的な`--trusted-calibration`で実行できます。live artifact用のisolated evaluator runnerは後続の`18-isolated-evaluator.md`で実装しました。

## Oracle calibration

各caseで次を自動確認しました。

1. generated initial fixtureはpublic/hidden oracleの少なくとも一方でfail
2. harness sourceにだけあるknown-good variantは全public/hidden checkでpass
3. hidden evaluator pathを`workspace/...`へ改変したmanifestはsemantic validationでreject
4. check statusとexit codeを改変したmanifestはreject

これはoracleが最低限known-badとknown-goodを識別できる証拠です。agentが速く終了しただけのartifactをquality-passへ入れません。

## Usage

```bash
scripts/agent-duration-study validate \
  --kind case-catalog \
  experiments/multi-agent-duration/catalog/cases.json

scripts/agent-duration-study build-fixture \
  --case-id F04-S-PY-001 \
  --output-dir /tmp/duration-case-s

# checked-in fixture calibration専用。live agent artifactには使わない
scripts/agent-duration-study evaluate-fixture \
  /tmp/duration-case-s \
  --trusted-calibration
```

既存output directoryは上書きしません。build failure時にもbroad cleanupを行わず、ownerがexact pathを確認して処理できるようpartial directoryを残します。

## Validation

40 testsで次を確認しました。

- catalog/case/capsule digest validation
- capsule traversal、duplicate case/recipe、oracle leakのreject
- S/M/L全fixtureのbuildとbad/good oracle calibration
- one-commit Git、remote/tagなし、bundle verification
- deterministic snapshot identity
- private manifest/control mode
- CLI build/validate/refuse-overwrite
- host evaluator safe-default refusal

## Next gate

live provider canary前の残りを次へ絞りました。

1. agent container: workspaceだけをwrite mountし、task networkをprovider別sandboxで禁止
2. evaluator container: workspace read-only、hidden evaluator read-only、network none、credential mountなし — implemented
3. task capsuleをCLI promptへ渡し、prompt自体はanalytic recordへ保存しない
4. T0/TX/V0/V1/T6とcase/catalog/fixture snapshotをrun recordへ接続

このgateを通った最初のS primary-only runから、初めてtask durationの`single-observation`を公開できます。
