# 接続検証と、遅れて作成されたコンテナの監査

**現在はlive admissionを保留している。最終sourceの7試験は通過したが、同じsourceでの
公開校正に未測定が残った。実モデル開始は0。**

この版は、同じ強い初期実装から新しい単独・協働が追加開発し、観測停止後の両成果物を
封印してから初期実装も含めて独立採点する接続である。実モデルはまだ開始していない。
最新の採否・source・原記録hashは [validation.json](validation.json) に保存する。

## 測定契約と回収判定の修正

期限停止した成果物の評価可否を、元の正常終了・品質・時計・使用量・予算適合から分ける。
未提出は保留、不正な方策はinvalid-policy、基盤の失敗は未測定として保持する。
正常終了、usage欠落、output超過、両条件の期限停止、書込み中の子、不正提出、未提出、
外側中断を実CLIと疑似providerで確認する。品質は要求期限ちょうどの成果とは呼ばない。

検証中にDocker createの15秒タイムアウトが発生した。元の回収処理は、その直後に名前が
存在しないことを確認して成功を記録していたが、後の監査で3個のコンテナが見つかった。
いずれも`Created`で、`StartedAt`は未開始。保存済みの所有記録、imageとmount sourceを
照合して削除し、原結果のhashが変わらないことも確認した。

CLI待機終了より遅れてdaemon側の作成が完了した可能性がある。ただし、元の回収処理は
daemon操作の完了を観測しておらず、正確な内部順序を証明したわけではない。
元記録の`cleanup: confirmed`と事後の残存観測を両方残す。

新しい監査は、起動済みの証拠がある場合と作成完了が不明な場合を分ける。
後者は20秒の有限な観測枠で現れた所有コンテナを削除するが、削除後もdaemon操作の完了を
証明できなければ回収はunknown。単発の不在を成功にしない。外側中断時も、実際の不在と
起動・回収完了を証明できるかを別に検査する。外側の監査も保存済みsourceを使う。

## 保存した検証経過

原記録の共通rootは `~/.local/state/devcontainer-evaluations/`。
すべて疑似providerまたは固定された非agent処理であり、live開始枠を使っていない。

| 保存先 | 観測 |
| --- | --- |
| `termination-pair-preflight-20260910-01` と `-interrupted` | 最初の5試験。Docker作成が2箇所でタイムアウトしたため不合格を保持 |
| `termination-pair-preflight-20260910-02` と `-interrupted` | 同じsource・上限の5試験が149.789秒、skipなしで通過。後から追加した回収監査の検証へ読み替えない |
| `termination-public-calibration-20260910-01` | 独立FIFOは14/24測定、15例目は作成タイムアウトで要求0・出力0、残り9例は未実行。公開FIFOは23/24測定、1例TimeoutError。初期実装の校正は未着手 |
| `termination-environment-probe-20260910-01` | 何もしないホストの`python3 -c pass`が16.053秒でタイムアウト、次は9.370秒、最後は0.070秒。先頭の失敗後はDocker作成を開始せず、後の2コンテナは削除済み |
| `termination-late-container-recovery-20260910-01` | 所有コンテナ3個の事後観測と削除。原記録は変更していない |
| `termination-pair-preflight-20260910-03` | 新監査が実CLIの小文字の不在応答を認識できず保留。修正前の記録を保持 |
| `termination-pair-preflight-20260910-04` | 正常・usage欠落・output超過・両期限停止・不正提出は通過。外側中断に回収完了を要求していた旧assertionが、新しいunknownの契約と不一致だった |
| `termination-pair-preflight-20260910-05` | 7試験が147.473秒、skipなしで通過。その後、採点側の作成完了判定をエラー文から固定transportのstartup記録へ変更 |
| `termination-public-calibration-20260910-02` | FIFO/初期実装ともに公開24例の全結果・trace・完了時刻が独立評価と一致。後続の監査修正前のsourceとして保持 |
| `termination-pair-preflight-20260910-06` | 疑似試験の8秒期限で、提出ファイルが作られる前に停止した。未提出の保留は正しく、意図した提出後停止のfixtureには到達しなかった |
| `termination-pair-preflight-20260910-07` | 最終sourceの7試験が201.654秒、skipなしで通過。疑似期限を20秒・最初のtool待機を30秒にして狙った故障点へ到達させた。実比較の40分期限・回収上限は不変 |
| `termination-public-calibration-20260910-03` | 最終source。FIFOは公開・独立とも24/24。初期実装は公開24/24、独立は8例測定後、9例目の初回応答が5秒でタイムアウト。残り15例は未実行で、live admissionは保留 |

ホストの`python3`はpyenv shim経由である。この診断だけでPython本体、Docker daemon、
WSL、ホストディスクのどれが根本原因かを断定しない。I/O待ちも観測したが因果関係は未確定。
public校正の失敗をFIFOの品質不足や単独モデルの限界に数えない。

最後の採点側監査は、固定transportがDocker createの成功後に書く`startup_seconds`を根拠にする。
特定のタイムアウト文言に一致しなかったという理由で、外側中断中の作成完了を推定しない。

最終校正で未測定だった`development-contended-burst-0`は、前の校正では同じ初期sourceと
公開入力で測定できていた。その回の最大応答は0.236425秒、373応答に対し、今回は5.000553秒で
応答0・出力0だった。時間差の原因を方策の質と断定しない。固定transportの`startup_seconds`は
Docker create完了後にstartクライアントを起動した時点の記録であり、Pythonや方策の準備完了を
観測した時計ではない。次は、起動待ちと方策の応答を区別する有限な非agent診断を優先する。

最終preflightの12 actor・15独立採点と、最終校正の33独立採点・2公開実行について、所有containerの
事後の不在を確認した。外側中断の回収unknownは維持する。56 sourceの一致、原結果315件のhash、
校正保留時に認証・campaign作成・provider開始より前でlive入口が拒否することも確認した。

新しいsourceでの全試験と公開24例ずつの一致がそろうまで、実モデル比較のadmissionは保留する。
旧liveの採点・未使用枠の再開や、時計・評価器の事後変更は行わない。
