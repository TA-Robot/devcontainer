# 04. Recurring agents and governance

Reviewer: independent Grok 4.6  
Date: 2026-08-26  
Status: independent review. Not repository policy.

【結論】定期・event駆動agentは常駐人格ではない。schedule/event serviceが既存task contractから毎回terminalなfinite jobを発行するだけである。`agentctl` 0.7 にcron/event triggerは無い。guidanceからruntimeを推測しない。runaway、重複、stale context、alert fatigue、unauthorized writeは別失敗であり、一つの整数defaultでは防げない。数値は安全側starting parameterになり得るが、品質最適でも全球最適でもない。

`sentinel` / `event-triggered` はtopologyではなくtriggerである。中身は有限read、たまにbounded write candidate。

採らない: sessionの暗黙resume、open-ended「改善し続けて」、active runへの重ね起動（default）、agent自身によるschedule/quota/permission/circuit変更、無制限retry、write→merge→push→dependency update→外部messageの無人連結、missed runの全件catch-up、schedulerをagent processの宿主にすること。

```text
trigger -> dedupe -> overlap/budget/circuit/usefulness
       -> immutable snapshot (base SHA, template revision)
       -> existing lane/permission/result validation
       -> bounded report or candidate commit
       -> human/primary gate
       -> delta対前回
```

継続記憶はsessionではなくbounded artifact。transcriptとprivate reasoningは保存しない。

## Hard guard と adaptive parameter

Hard（人の明示操作が要る）: disabled-by-default、agent外のkill/pause、agentはschedule/quota/permissionを変えられない、merge/push/PR/release/外部messageをscheduleから行わない、open-ended objective登録不可、secretをDB/report/commitへ書かない、transcriptをcontrol planeへ入れない、untrusted定期実行をLane I未提供のまま行わない。

Adaptive（rationaleとinvalidation必須）: cron/event filter、max runs/day、wall time、attempts、backoff間隔、circuit閾値、overlap例外、usage、retention、provider/role/template、人間が読む頻度、Lane W candidateのallowed paths。付帯の無い整数をexample YAMLから政策へ昇格させない。

## 失敗モード別

**Runaway.** 毎run finite。max wall time / attempts / usage / capacity。即retryせずbackoff。連続失敗でcircuit open。closeとquota増加とenableは人。eventはfilterとdedupe必須。Grok writeのnested disableとmax-turnsはownership guardであり、recurring品質の最適回数ではない。【仮説】連続失敗回数の具体整数は失敗コストと見逃しコストの比で変わる。全球の「3回」は根拠不足。circuitが誤開するなら閾値よりjobのノイズを先に直す。

**Duplicate.** immutable trigger ID、event dedupe、default overlap forbid、default同一schedule concurrent 1、catch-upは最新一件をstartingにする。同一template+同一snapshotならskip。【結論】concurrent 1 と forbid は品質値ではなく二重実行事故を防ぐ安全側default。shardが証明されcapacityとhuman minutesが余るときだけscheduleを分割するか明示allowする。黙って並列化しない。

**Stale context.** run間resume禁止。毎回full base SHAを取り直す。template revisionを混ぜて学習しない。前回reportはdelta入力だけ。全文をprompt連結しない。staleを「もっと思い出させる」とsecretと古い前提が入る。解は新しいsnapshot。

**Alert fatigue.** attention budget（ownerが実際に読む頻度）を必須fieldにし、token capより先に置く。原則delta。変化なしは短いno-changeでterminal。新規finding無しまたは未ackが続いたらfailureでなくてもusefulness circuit相当でenableを落とす。閾値はproject-local。登録してよいのはtoolchain canary、dependency/advisory drift、flaky集計、docs/API drift、performance trend、GC dry-run inventory。backlog close、broad cleanup、文脈なしdocs書換えは登録しない。【仮説】attentionを超える頻度はcheapなreadでも純価値を負にする。手動反復（E6）で読む価値が無い題材にschedulerを実装しない。

**Unauthorized write.** 混同しない。security boundaryはuntrusted/credential/外側ネットワークの隔離で、Lane I未提供・privileged DinD不採用。accidental-writeは信頼済み環境のscope事故低減（worktree、allowed paths、broker commit、single-writer）。workspace制限とrole fileとsafe profileは事故低減であり、資格情報mountedなdevcontainerではisolationと呼ばない。

Write defaultはLane R report。Lane Wを許しても専用worktreeのcandidate commitまで。dependency/lockfile/migration/secret/外部messageは個別opt-inとhuman gate。auto merge/push/PR/release/destructive cleanupはscheduleから行わない。`gc --dry-run` を削除権限と誤読しない。trusted bypassを暗黙に付けない。credentialはDBへ恒久保存せず、現行のmemory-only dispatch + resubmitを支持する。

## State / audit / event

必須stateに consecutive no-change、last ack / unread、enable actorを足す。last resultはowner-only pathだけで本文をDBに入れない。provider outageとtest failureとschema failureを同じretryに載せない。circuit open中はtriggerを溜め込まず最新のnext eligibleだけ残す。

event-triggeredはburstする。path/class/actor filter必須。incidentでもagentは外部変更をせず調査とscribeに閉じる。auto approve/auto mergeするPR botはこのrepoの目標外。C4 pilotはread-only sentinel一件とfault injection（rebuild、clock jump、outage、duplicate trigger）に限定。Lane W candidateは報告が読まれたあと。

operating-modelの900秒、1日1回、backoff配列、circuit 3、retention 12は例であり政策にしない。max attempts starting 1は定期点検では「再試行より次標本」として支持し得るが、outageは別policyにしてよい。agentctl capacityはcollaboration人数ではない。定期jobにinteractive優先を付けず本線をstarveしない。

反対: usefulness circuitが稀で高価なadvisoryを見逃すなら、no-changeでも短報を残しunreadだけをcircuit対象にするなど題材別にparameter化する。手動週次で足りるteamにschedulerは不要。E6が負ならC4は削除可能にしておく。成功は毎回動いたことではなく、読める頻度で新しいdriftだけ出し、書込みは候補に留まり、止まれること。頻度も人数も成功指標にしない。

