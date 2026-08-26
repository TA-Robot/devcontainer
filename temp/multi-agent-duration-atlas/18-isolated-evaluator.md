# Isolated evaluator container

実装日: 2026-08-26

Status: S/M/L fixtureのagent artifactをhostで直接実行しないevaluator pathを実装・Docker smoke済み。後続のlive provider結合は`19-first-recorded-codex-canary.md`を参照。

## Outcome

`scripts/agent-duration-study evaluate-fixture-isolated`を追加しました。fixture manifestが要求する`network-disabled-read-only-container`を実際のDocker commandへ変換します。

```text
host harness
  ├─ workspace/             -> /case (read-only)
  ├─ control/hidden_tests.py -> /harness/hidden_tests.py (hidden checkだけread-only)
  └─ control/base.bundle     -> not mounted

evaluator container
  ├─ network: none
  ├─ root filesystem: read-only
  ├─ /tmp: 64 MiB tmpfs
  ├─ all Linux capabilities dropped
  ├─ no-new-privileges
  ├─ PID / memory / CPU / file descriptor caps
  ├─ current UID/GID, no credential mount
  └─ stdout/stderr discarded; exit code + duration only returned
```

public workspace checkのcontainerにはhidden evaluatorをmountしません。hidden check時だけmountするため、public test processからhidden filename/contentを先読みできません。hidden checkそのものではtest processがhidden testを実行するため、その時点のread accessは必要です。

## Command

```bash
scripts/agent-duration-study evaluate-fixture-isolated \
  /tmp/duration-case-s \
  --image devcontainer-frozen-smoke:latest \
  --timeout-seconds 30
```

imageは`--pull never`で実行し、開始前にexact image digestを取得します。resultへimage referenceとdigestの両方を残します。Dockerがcheck開始前に失敗するexit 125はartifact quality failへ変換せずinfrastructure errorにします。

各checkは固有container nameとduration-study labelを持ちます。timeout時はそのexact nameだけへ`docker rm --force`を発行し、broad pruneは行いません。timeoutはexit 124相当のfailed checkです。1 checkのcapは正値かつ最大300秒です。

## Environment boundary

containerへhost environmentを`--env-file`やbulk inheritanceで渡しません。明示するのは次だけです。

- HOME=/tmp
- C.UTF-8 locale
- UTC
- no bytecode
- `/case` Python path
- fixture workspace path

provider credential、Git credential、proxy、token、original workspace pathはmount/forwardしません。image自体にcredentialを焼かないことは別のimage supply-chain contractです。

## Smoke evidence

Evaluator image:

```text
devcontainer-frozen-smoke:latest
sha256:3f58b6614a86e40bd3adfa49f9a9b5711bcf24b8a28fe574dec8ea1e0872cc9d
```

実Dockerで確認した結果:

| Case/artifact | Result |
| --- | --- |
| F04-S seeded initial bad | public fail / hidden fail |
| F04-S private known-good | public pass / hidden pass |
| F04-M private known-good | public pass / hidden pass |
| F04-L private known-good | unit、Bash syntax、hidden lifecycleすべてpass |

ここで観測したcontainer startupとtest runtimeはevaluator implementation smokeであり、agent task duration atlasのsampleではありません。live studyではV0/V1またはS0/S1のどちらへ置くかをmanifestで明示します。

## Test contract

fake Docker testは生成commandを検査します。

- `--network none`
- `--read-only`
- `--cap-drop ALL`
- `no-new-privileges`
- bounded PID/memory/CPU/nofile/tmpfs
- workspace read-only
- base bundle非mount
- credential/secret/token引数なし
- public checkにhidden mountなし
- hidden checkだけhidden mountあり
- NaN timeoutをcommand実行前にreject

このmilestone時点でduration study全体は41 tests passでした。live runner追加後の現行checkは`AGENTS.md`を正本とします。

## Live-run boundaryへの引き継ぎ

この時点では次のagent側boundaryが未実装でした。

1. fixture workspaceだけを書き込みmountしたephemeral agent container
2. provider API transportは許しつつ、agent command/webのtask networkを禁止するprovider別profile
3. host credentialは必要最小のread-only sourceからsession専用HOMEへ渡し、analytic recordへ保存しない
4. capsuleをpromptとして一度だけ投入し、nested delegationを初期canaryでは無効化
5. provider event/resultをT0/TX/V0/V1/T6とrun identityへ接続

これらは後続のrun schema v2 / Codex one-shot runnerで実装しました。設計と最初のrecordは`19-first-recorded-codex-canary.md`へ続きます。
