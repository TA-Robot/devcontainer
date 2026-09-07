# 次候補Bの入口監査

2026-09-08。schedulingのH2実行中に、次候補の既存sourceをread-onlyで確認した。
これは難度校正でもlive比較でもない。既存のサッカー実験の得点・sourceは変更していない。

## 再利用できるもの

Rust simulatorが状態・物理時計・成功判定を所有し、controllerは公開観測とcommand APIを使う。
[開発runner](../../scripts/develop-robot-soccer-controller)にはcontrollerのsnapshot、複数seedでの実行、
trace回収がある。[公開契約](../../experiments/robot-soccer-control/PUBLIC-SPEC.md)も存在する。
戦術・制御・状態推定を試作して比べる入口はある。

## 主評価へそのまま使えない点

| sourceで確認した事実 | 主評価への意味 |
| --- | --- |
| `sim.rs`の初期ball・味方・相手配置は定数。seedは物理係数と観測等の乱数へ入る | seed数を増やしても別の初期配置・別の相手戦術への一般化とは呼べない |
| `main.rs`の`POST /v1/start`はcontrollerがseedを指定でき、呼出しごとにsimulatorを作り直す | 評価対象のepisode・seed・再試行回数をcontrollerから独立させる必要がある |
| 旧gateはseedをcontrollerの引数へ渡し、実行後に`GET /v1/result`を読む | controllerが指定seedで一度だけ実行したことを、その読み出しだけでは保証しない |
| 旧gateと開発runnerはcontrollerをhostの`subprocess.run`で実行する | 未信頼のlive提出物を独立評価する隔離境界としては未成立 |
| 旧gateは異なるseedをちょうど3個要求する | 小さい開発受入れであり、広い頑健性の到達水準を裏付けない |

参照: [sim.rs](../../experiments/robot-soccer-control/src/sim.rs)、
[main.rs](../../experiments/robot-soccer-control/src/main.rs)、
[旧gate](../../scripts/evaluate-robot-soccer-controller)。
以上はsource上の経路の確認であり、既存controllerが抜け道を利用したという主張ではない。

## 次の判断に必要な最小成果

既存の[8月29日記録](robot-soccer-orchestration-benchmark-2026-08-29.md)は、約86分で中断、
開発上の最高4/8、同じdigestの再実行3/8と2/8、未使用受入れ未完了を報告している。
当時は別modelで、後半には独立候補探索もあり、現在のstrong-solo基準とは比較できない。
raw worktree・artifactは削除済みと明記されているため、この要約から候補の再採点や因果確認はできない。
探索の停滞と実時間制御のばらつきを疑う材料はあるが、到達可能な頑健性水準の校正には不足する。

次は残るcontroller資産の所在と再利用可否を確認し、未使用条件で求める成功水準と、その価値を固定する。
単独を失敗させる目的で条件を後付けしない。
既に広く達成できているなら、Bの独立評価接続を作る前に採用を見送る。
未達という過去の要約だけでも採用せず、その水準へ届く有効な戦術・制御の根拠を求める。
再利用可能な候補があれば、事前に有限枠を決めて、同じartifactの再実行変動と異なる戦術間の差を確認する。
seed数の増加で実時間制御のnoiseが解消するとは仮定しない。

採用の見込みがある場合に限り、評価側がseedと一回のepisodeを所有し、候補には観測・commandだけを許す
別版の隔離adapterを作る。seed無視・再開始・自己申告成功を拒否する校正を含める。
旧APIや旧得点を変更して過去の実行を新版へ読み替えない。
未知の配置・相手を測るなら、それは現runtimeに存在しない新しい課題版として別途設計する。

現在はBのlive予算を予約していない。上記の不足と保存成果を確認してから、必要な有限準備枠を決める。
サッカーへ移ること自体を難題選定の成功に数えない。
