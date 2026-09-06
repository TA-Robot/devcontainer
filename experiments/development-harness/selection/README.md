# P2: 大規模候補の不足監査

対象は現行計画の第一候補「既存の依存jobを独立検証・中断復旧・収集reportまで進める利用経路」。
**この候補は大規模比較へ採用しない。P2全体は未完了で、live比較も開始しない。**
中核の利用は既存コマンドの合成で成立した。残る検証権限の不足だけでは、継続した大規模変更を
必要とする実需要と変更系列を立証できない。課題を大きく見せるための新API・状態機械は作らない。

## 再現したこと

`audit_agentctl.py`は既存の疑似provider fixtureを使い、一時的なrepo/stateだけを操作する。
新しい3つの利用probeと、既存の中断・復旧・旧状態・supervisor試験8件を明示的に選ぶ。
実CLIの別processから状態を読み、結果を確認する。model要求、認証、merge/pushは不要。

| 当初の要求候補 | 実装・再現経路 | 判断 |
| --- | --- | --- |
| 依存の順序と検証済み成果の解放 | `run → check → validate --require-checks`を親から順に実行。未検証の親を持つ子は未起動 | nominal経路は既存CLIで足りる |
| providerの自己申告が誤っている | providerが成功を主張しても実checkのexit 7でstrict validateを拒否。子attemptは0 | 独立検査は既存機能 |
| clientを作り直して継続 | 各CLIは別process。`show`で状態を読み、validated jobの再dispatchは拒否 | 新しい永続campaign状態が必須とは立証できない |
| 重複した収集要求 | 既存reportを保持し、別のimmutable reportを作る | report作成の副作用はある。無変更・exactly-onceとは呼ばない |
| 依存成果の引継ぎ | 親子のcommitと順序、path重複をcollectが報告。元checkout HEADは不変 | single-writerのレビュー境界を維持できる |
| dirty/stale、新しいattempt | 既存のsource同一性検査とclean retryで旧証拠を再利用しない | 既存の明示的操作を再確認 |
| checker喪失 | SIGKILL後の子process停止を確認してから`--recover-incomplete`で新しい検査 | 無人復旧ではない。既存の所有権・明示的復旧で扱う |
| dispatch client喪失、supervisor再起動 | detached runner、orphan reconciliation、queue再登録の既存試験 | 無期限に生存する実行を仮定せず、旧状態の意味を保つ |
| 旧形式のDB・検査証拠 | 実際の旧sourceが作るDB・phase 2 evidenceを現行CLIで検査 | 既存の移行経路を再確認 |
| 配布済みのchecker | `test-agentctl-check-container.sh IMAGE`。host runtimeを渡さずimage内のCLI/libraryを使用 | 配布側の既存検査能力も別に確認 |

既存componentのテストが通ったことを、全ての組合せ・競合・無人復旧の保証へ広げない。
今回の3つの結合probeは正常経路、検証前の失敗、検証後の失敗の境界を対象にする。

## 再現した不足とscope判断

親jobを独立検査してstrict validateした後、元のacceptanceが参照する外部条件を変え、再検査を
失敗させた。`checks`は最新の失敗を返す一方、親のjob状態は`validated`のまま。
その後も子のdispatchとcollectは許可された。

`_dependencies_ready`はjob状態を確認する。`collect_job`は成果・Git整合を再確認するが、
最新の独立検査の合否を継続的に要求しない。現在の`validated`は過去の明示的な確定であり、
最新チェックの合格を常時表すものではない。legacy validateがprovider申告を扱う既存互換性とも区別する。

これは「現在の独立検査が合格した依存だけを常に解放したい」という厳格な運用では残る不足。
単純な順次scriptでも、最新検査が失敗したら後続を呼ばない運用はできる。競合する別clientまで
拘束するには、権限の適用範囲・lock・証拠の参照時点を新しい要求として決める必要がある。
その要求を勝手に付け足して大規模課題へ膨らませない。今回は再現を保存し、runtime仕様は変更しない。

| 判断項目 | 結果 |
| --- | --- |
| 中核が未実装である | 否定。既存の明示的な操作で利用できた |
| 不足が一つもない | 未証明。検証後の失敗とdispatchの境界を確認した |
| この不足だけで大規模の継続変更を代表できる | 未立証 |
| 既存の小課題で代用する | しない。小規模選定も大規模候補の成立後に進める |
| 次の分岐 | 実際に進めたいprojectと変更要求から別の系列を選ぶ |

ForgeRoom/Evidence Forge/DevRelayの既存実験を新しい未見の実案件へ読み替えない。
外部projectはソースの存在だけでは選べない。実利用の要求、現状の不足、前段階が作るデータを
後続変更で引き継ぐ必要を確認してから、課題・公開check・oracle・予算・順序を固定する。

## 実行と証跡

```bash
PYTHONDONTWRITEBYTECODE=1 python3 experiments/development-harness/selection/audit_agentctl.py \
  --output /tmp/new-agentctl-candidate-audit.json
scripts/test-agentctl-check-container.sh sha256:検証済みimageのID
```

出力済みのauditは上書きしない。`audit-2026-09-06.json`が観測の原結果、`validation.json`が実行証跡。
同じfixtureが将来のruntimeで違う結果になったら新しい監査として保存する。過去の観測を書き換えない。

commandごとの60秒は、この疑似provider監査のcost cap。checkの3秒、job数2はそれぞれ検査用の
cost capと依存辺を通す最小fixtureで、運用defaultや大規模の判定値ではない。
scopeは今回の監査、ownerはprimary/integrator。CLI・fixture・環境が変われば新しい監査で見直す。
`large_task_admitted/live_comparison_admitted: false`は現行計画の大規模選定条件によるhard guard。
この監査はlive実行の入口ではなく、P2の課題seal・全予算・実行順の代わりにはならない。
