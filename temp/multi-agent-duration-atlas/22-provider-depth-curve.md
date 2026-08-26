# Provider runnerと深度curve

実施日: 2026-08-27

Status: Codex / Claude / Grok共通one-shot runner、provider別sandbox、credential freshness gate、S path canaryを実装。Grok 4.6 / mediumはcriterion 5/5、Sol / mediumは4/5を観測。Claudeはhost OAuth再ログイン待ち。L caseのdepth curveは次の有限batch。

## 方針修正

`medium`と`high`だけを「普通 / 高め」として比べる設計は採りません。難しい問題へ推論量を厚く配ったときの伸び、頭打ち、時間増、品質変化を測れず、まさに判断材料が必要な領域を実験から外すためです。

active ladderは次です。

| Provider / model | Core points | Provider-native extension | Application evidence |
| --- | --- | --- | --- |
| Codex / `gpt-5.6-sol` | `medium`, `high`, `xhigh`, `max` | `ultra` | model catalogは全値を広告。run eventはapplied値を返さないため、現状はrequested / unknown |
| Claude / `opus` | `medium`, `high`, `xhigh`, `max` | なし | CLIが5段階を列挙。run eventでapplied値を独立確認できなければrequested / unknown |
| Grok / `grok-4.6` | `medium`, `high`, `xhigh`, `max` | 広告なし | CLIはflagだけを広告。ephemeral `summary.json`の値を観測できたrunだけappliedへ昇格 |

`high`は上端ではなく中間点です。Solの`ultra`も、全providerへ架空の共通尺度として押し付けず、provider-native extensionとして残します。`low`は既存の旧rubric観測を保持しますが、今回の「通常以上で難題へどう向き合うか」というcore batchには入れません。将来、速度floorが必要なprojectは別blockで追加できます。

provider間で同じ文字列のeffortが同じ計算量を意味するとは仮定しません。比較単位は常にprovider / resolved model / requested setting / applied confidence / CLI / imageを含む構成全体です。

## 実装したone-shot surface

```bash
scripts/agent-duration-study run-provider-study \
  --provider codex|claude|grok \
  --case-id <case> \
  --image <exact local image> \
  --model <provider model> \
  --effort medium|high|xhigh|max|ultra \
  --output-dir <record directory> \
  --run-id <unique id> \
  --confirm-live-provider
```

1 invocationは1 provider request、retryなしです。providerごとの許容effortをrunnerが検証するため、たとえばClaude `ultra`はprovider開始前にrejectされます。unsupported値を`high`へ丸めません。

全providerで次を共通記録します。

- provider wallと評価込みterminal wall
- requested / resolved model identity confidence
- requested / applied / rejected / unknown effort
- content-free event、item、usage counter
- workspace changed-path count
- binary acceptanceとcriterion score、failed criterion IDs
- CLI source/version、image/profile digest、sandbox assurance
- raw prompt、回答、stderr、credential pathを永続化しなかったこと

Claude/Grokのstream outputとGrok session metadataはprivate temp内で解析して削除します。Grok 1.0.5はhost-synced binaryをread-only mountし、frozen image内の1.0.3を`grok-4.6`観測へ誤用しません。

## Sandbox helper discovery

実canaryでcontainer依存不足が見つかりました。

- Claudeのfail-closed Linux sandboxには`bubblewrap`と`socat`が必要。
- Ubuntu 22.04のsystem `bwrap 0.6.1`をCodex 0.146へ見せると、old-bwrap compatibility pathでsynthetic helperを解決できない。
- distro `bwrap`をprovider専用directoryへ移し、Claude/Grok wrapperだけPATHへ追加する。
- Codex runnerからsystem helperを隠し、CLI同梱・digest検証済みbwrapへfallbackさせる。

Codexはgenerationなしpreflightでworkspace write、unrelated read denial、child command network denialを毎run実観測します。Claude/Grokは現状profile configuration evidenceで、Codexの`probed`と同じ強さを主張しません。Claudeの公式[sandbox説明](https://code.claude.com/docs/en/sandboxing)、Grokの公式[sandbox説明](https://docs.x.ai/build/features/sandbox)に沿って、model transportとagent command networkを分離しています。

Grokはauth fileをkernel denyするとGrok本体も読めず起動できません。strict profile、既知のversioned capsule、subagent/web/memory無効化、tool-level state-directory deny、shell env最小化を使い、この制約を`configured` evidenceとして保持します。

## Credential freshness gate

read-only credential sourceでtoken refreshを始めると、refresh失敗またはrotation後の保存不能が起きます。runnerはprovider開始前にaccess credentialの期限をcontent-freeに検査し、`timeout + 5分`より短い場合は拒否します。自動refresh、copy上のrefresh、effort fallbackはしません。

Claude path calibration中、期限切れOAuthをhost CLIで正規refreshしようとしたところ、OAuth permission error後にCLIがaccess/refresh tokenを空にしました。Claudeの追加runには`claude auth login`が必要です。この状態変化は隠さずblockerとして残し、再ログイン前の自動retryは行いません。

## S path canary

performance sampleとして読めるcurrent-image観測は次の2件です。

| Run | Model / effort | Provider wall | Evaluation込み | Score | Setting evidence |
| --- | --- | ---: | ---: | ---: | --- |
| `grok-f04-s-46-medium-20260827-r02` | Grok 4.6 / medium | 48,966.717 ms | 52,670.704 ms | 5/5、hidden 4/4 | applied medium |
| `codex-f04-s-sol-medium-20260827-r02` | Sol / medium | 66,833.530 ms | 70,678.478 ms | 4/5、hidden 3/4 | requested medium / applied unknown |

Solは`hidden-empty-result`だけ失敗しました。これはbinary `fail`だけでは得られなかった差で、Grokの5/5とSolの4/5を「成功 / 全滅」に潰さず比較できます。ただし両方とも1 run、1 S caseであり、provider ranking、typical time、varianceはまだ出しません。

次はinstrumentation calibrationであり、performance populationへ入れません。

- Claude r01-r03: sandbox helper未導入
- Claude r04: `socat`未導入
- Claude r05-r07: expired OAuth / refresh failureの診断段階
- Grok r01: Grok本体までauthをkernel denyしたprofile error

これらは起動失敗時間としてimmutable recordを保持しますが、task completion時間やeffort curveへpoolしません。

## 次のfinite depth batch

難題で深度差を見る本体は`F04-L-PYBASH-001`です。構造的にLである理由はcross-process persistent state、Python / Bash boundary、restart-delayed failure、unit + integration + lifecycle oracleであり、実行前の想定時間ではありません。

最初のcoverage passは直列実行します。

```text
Sol:      medium -> high -> xhigh -> max -> ultra(extension)
Grok 4.6: medium -> high -> xhigh -> max
Claude:   medium -> high -> xhigh -> max  (auth復旧後の別block)
```

これは必要run数のglobal defaultではありません。最初のcoverage passで各深度が実際に受理され、artifactとcriterion差を観測できるかを確認します。その後の反復数とorder counterbalanceは、観測variance、provider drift、rate-limit、L caseの識別力を見て次blockで決めます。

各rowで隣接表示するもの:

- provider / user-result / evaluator time
- criterion scoreとfailed IDs
- requested / applied setting status
- token usage
- terminal / timeout / refusal
- exact runtime identity

深度を上げてもscoreが変わらず時間だけ増える、深度差よりrun varianceが大きい、全深度が同じcriterionで落ちる、といった結果もそのまま判断材料です。最適値やrouting ruleを先に決めません。
