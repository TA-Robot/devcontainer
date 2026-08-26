# Agent execution runbook

このrunbookは通常のprompt作法ではなく、failure recoveryとsingle-writer integrationの正本です。project固有のsetup / test commandは`AGENTS.md`へ置きます。

## Operating rule

- 複数agentの関係、round、variant、scheduled workを設計する時は`collaboration-playbook.md`を使い、lane / role / mode / lifecycleを分ける。
- Lane Rはprovider-nativeのread-only subagentを使い、worktreeを作らない。
- Lane Wはimmutableなfull base SHAからjob専用branch / worktreeを作る。
- Lane Iはdisposableまたはprivate runtimeを使う。
- process終了、agentの自己申告、log停止だけで`completed`にしない。
- retry、削除、integrationは暗黙に行わず、誰が判断したかを残す。

Phase 3a–3eでは`agentctl`のjob、attempt、worktree lease、broker commit、result validationに加え、local supervisor、detach、heartbeat、process-group cancel、orphan reconciliation、capacity queue、Compose/port namespace、integration collection、bounded/redacted log view、terminal log retention、dry-run GC inventoryまで実装済みです。detach jobはclient terminal切断後もrunnerが所有しますが、container/host restartを越えてprocessが生きるとは主張しません。旧wrapperを使う必要がある場合は基盤repositoryの`docs/agents/legacy-second-agent-runbook.md`を参照します。

## Before dispatch

1. current HEADをfull SHAで取得し、taskの`base_sha`へ固定する。
2. roleとlaneを選ぶ。write不要ならLane Rを使う。
3. allowed / forbidden pathsとacceptanceをtask envelopeへ書く。
4. parent sessionのlive permissionを確認する。native childはparentの強いoverrideを継承し得るため、safe profileで不足する理由が無ければpermissionを強くしない。
5. Lane Wではjob IDに対応するbranch / worktreeを一つだけ割り当てる。
6. Lane Iではcredential、network、Docker daemon、成果回収方法を実行前に確認する。

taskの`priority`は通常省略して`normal`を使います。人が直ちに結果を待つjobだけ`interactive`、急がない保守作業だけ`background`にします。resource不足時にforeground commandをloopで再試行せず、`--detach`でdurable queueへ渡します。

task/result例は`.agent/examples/`、schemaは`.agent/schemas/`にあります。長い背景はtask JSONへ埋め込まず、`context_paths`からこのdirectory内の資料を参照します。

## Healthy completion

Lane Wの結果を成功として回収する前に、primaryが次を再計算します。

```bash
git rev-parse HEAD
git status --short
git diff --name-only <base-sha>...HEAD
git log --oneline <base-sha>..HEAD
```

確認項目:

- reported `job_id`がtaskと一致する。
- headがfull commit SHAで、期待したbaseから到達できる。
- changed pathsがallowed scope内にある。
- completedならworking treeがcleanである。
- task-level checkのcommand、status、exit codeがresultにある。
- result schemaに適合する。

agentの`changed_paths`と`head_sha`はヒントであり、Gitの再計算結果が正本です。

`agentctl` managed Lane Wではproviderがcommitせず`ready_for_commit`を返します。brokerがpre-commit HEAD、dirty paths、scopeを照合し、verified pathだけをstageしてhooks / signingなしのjob commitを作ります。`provider-result.json`は元の申告、`result.json`はbroker確定後のfinal envelopeです。

## Failure classification

| class | 例 | retry前の判断 |
|---|---|---|
| provider | rate limit、auth、model error | provider状態と同一attempt resume可否を確認 |
| process | crash、signal、terminal切断 | PIDだけでなくprocess生存とworktreeを確認 |
| validation | JSON/schema不適合、completedだがdirty | 成果を保全し、resultだけ修復可能か判断 |
| workspace | base不一致、scope逸脱、lock競合 | 新しいclean worktreeが必要か判断 |
| resource | port、Compose、disk、memory衝突 | namespace / capacityを直して新attempt |
| integration | conflict、aggregate test失敗 | worker成功と統合失敗を分け、修正job化 |

failure classを混ぜないでください。たとえばtest failureはprovider crashではなく、通常はjob resultの`failed`です。

## Logs and retained evidence

通常の確認ではraw fileを直接開かず、bounded viewを使います。

```bash
agentctl job logs <job-id>
agentctl job logs <job-id> --attempt <n> --lines 200 --json
agentctl job logs <job-id> --runner
```

viewは既定64 KiB / 80行、最大1 MiB / 1000行で、known tokenとauthorization/secret assignmentをbest-effort redactionします。これは完全なsecret検出ではありません。owner-onlyの`process.log`はrawのままで、provider終了時に最大8 MiBのtailへ制限され、同じattemptへ`log-retention.json`が残ります。実行中は一時的に上限を越え得ます。secret混入が疑われる場合は表示がredactedだったことを根拠にせず、raw evidenceのaccessを止め、credential rotationとincident判断を行います。

## Orphan recovery

agentやterminalが消えた場合:

```bash
agentctl supervisor status
agentctl supervisor reconcile --json
agentctl job show <job-id> --json
```

1. supervisorにreconcileさせる。recorded PIDだけでなくLinux process start timeとheartbeatを照合する。
2. provider/runnerが正しいidentityで生き、heartbeatが新しければ二重起動しない。
3. ownership deadlineを越えたprocessは対象process groupだけを止め、attemptを`orphaned`として扱う。成功へ推測遷移しない。
4. worktreeで`git status --short`、`git log`、untracked fileを確認する。
5. 回収価値のある差分をpatchまたはcommitとして保全する。agentの代わりに勝手な完了commitを作る場合はprimaryの判断として記録する。
6. resumeかclean retryを選ぶ。どちらを選んだか、旧attemptのpath / commitを残す。
7. dirty worktreeを削除する前に、人が対象pathと回収済み成果を確認する。

## Resume versus clean retry

provider-native resumeは同じattemptの会話継続です。次の場合だけ選びます。

- workspaceとbaseが変わっていない。
- 途中contextが再利用価値を持つ。
- failureがprompt / state corruptionではない。

clean retryは同じjobの新attemptです。

- immutable `base_sha`から新しいworkspaceを作る。
- 古いlog、result、worktreeを上書きしない。
- 前attemptのcommitを使う場合は明示的なinputとして扱う。
- retry回数で原因を隠さず、同じfailureが続けば停止してprimaryへ返す。

## Schema failure

providerが有用な成果を出していてもresult JSONが不正な場合、jobを`completed`にしません。

1. raw final messageとworkspaceを保全する。
2. schema pathと最初のvalidation errorを記録する。
3. head SHA、changed paths、dirty stateをGitから取得する。
4. providerへresultだけ再出力させるか、primaryが検証済みresultを作るかを選ぶ。
5. codeを再実行する必要が無ければ、同じattemptのvalidation repairとして扱う。

## Docker and port collision

Lane Wでshared Docker daemonを使う場合、jobごとのnamespaceを必須にします。

- `COMPOSE_PROJECT_NAME`へjob ID由来の一意名を設定する。
- integration jobはbrokerが渡す`AGENTCTL_PORT`を使う。host portを固定共有せず、可能なら内部networkを使う。
- temp directory、container、network、volumeへjob IDを付ける。
- `docker compose down -v`の対象projectを実行前に表示・確認する。
- 他jobのresourceを止める必要があるならLane Iへrouteする。

collision解消のために全container / volumeを一括削除しません。

`agentctl supervisor status --json`でclass別limit / used / waitingを確認できます。`waiting_capacity`にはまだattemptもworktreeもありません。supervisor再起動後に`awaiting_resubmit`へ載ったjobは、credentialをDBから復元したふりをせず、元と同じ`job run ... --detach`を再送します。

## Single-writer integration

workerはmain / integrationへmerge、pushしません。primary / integratorがdependency順に一件ずつ取り込みます。

まずread-only reportを作ります。

```bash
agentctl job collect <job-id> --onto <integration-branch-or-sha> --json
```

reportの`candidate_commits`はdependency順ですが、自動適用命令ではありません。`target_path_overlaps`、`inter_job_path_overlaps`、`blockers`、各memberのchecks / risks / followupsをreviewし、reportの`target_sha`が今もintegration対象と一致することを適用直前に再確認します。`clean_candidate`も意味的な互換性を保証しません。

1. task / result schemaとbase / headを照合する。
2. scope外変更、dirty state、secret混入を確認する。
3. commit差分をreviewし、Must findingを解消する。
4. cherry-pick / merge / rebaseの方法をprimaryが選ぶ。
5. conflictは自動解決せず、原因とownerを特定して修正jobへ戻す。
6. aggregate test / lint / buildをintegration workspaceで実行する。
7. push / PR作成後にjobをintegratedとして記録する。

worker checkが通っていても、integration先のschema、generated file、lockfile、migrationとの論理競合は別に検査します。

## Aggregate test failure after integration

- worker resultを遡って失敗へ書き換えない。
- integration failureとして対象commit群と再現commandを記録する。
- 最小の原因commitを切り分ける。
- revert / follow-up job / dependency順変更のどれを選ぶかprimaryが判断する。
- 未検証のforce pushや複数workerへの同時修正依頼で隠さない。

## Cleanup and GC

削除判断の前に必ずagentctlのread-only inventoryを作ります。

```bash
agentctl gc --dry-run --job <job-id> --json
agentctl gc --dry-run --json
```

- `eligible: true`でも削除は実行されていない。`candidate_actions`はprimary向けの提案にすぎない。
- validated / terminal state、live process、runtime leaseを確認する。
- worktree path、generated branch、Git common directory、recorded HEAD、dirty/untracked stateを再確認する。
- raw log、result、log retention、validation / collection evidenceをcanonical attempt pathで確認する。
- no-changeまたはcollection reportによるintegration proofが、現在のregistered HEADでも成立することを確認する。
- integration classは正確なCompose project labelのcontainer / network / volumeが0件であることを確認する。Dockerを照合できない場合はblock扱いにする。

version 0.6にdestructive GCはありません。worktree/branch削除やCompose teardownを行う場合は、inventory後も対象を個別に再照合し、primaryが明示commandとrollback/evidence方針を所有します。broad `docker system prune`やrepository-wide cleanupへ読み替えません。legacy session / worktreeは新contractへ自動変換せず、commit SHAまたはpatchを回収してから別途整理します。

## Escalate instead of guessing

次はprimaryまたは人へ返します。

- base SHA、allowed scope、acceptanceのいずれかが不明。
- secretやhost credentialをworkerへ渡す必要がある。
- protected path、dependency、lockfile、migration変更が必要。
- destructive cleanupの正確な対象を特定できない。
- 同じfailureがclean retryでも再現する。
- integration conflictの意味的な正解が複数ある。
