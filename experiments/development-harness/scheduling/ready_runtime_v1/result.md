# 2026-09-10: 起動時計の修正と公開校正

**新しい時計の境界試験と公開校正は通過した。実モデル比較は未接続・開始0。**
sourceと原記録hashは[validation.json](validation.json)に固定した。
旧`termination_pair_v1`の保留を解除した結果ではない。

## 確認した境界

最終sourceの4試験が27.582秒、skipなしで通過した。
候補は実行許可前に動かず、元source・argv・ファイルパスを保持してraw stdinの2要求に応答した。
候補の6秒初期化は5秒で停止し、偽の準備完了通知でも延長できなかった。
評価器の起動遅延fixtureでは、起動待ち上限とscenario全体上限を別々に確認した。
公開/独立のsmoke一致、不正policyの分類、host実行の拒否も確認した。
物理simulationと回収処理は、それぞれ固定された旧sourceとbyte一致している。

最初の3試験の記録`ready-runtime-preflight-20260910-01-*`も保持する。
起動・全体上限の試験を加え、最終sourceで全4試験を実行した記録は`-02-*`である。
追加は欠けていた境界の検証であり、失敗した実モデルの再試行ではない。

## 公開24例ずつの照合

同じ固定FIFOと、既存の強い初期実装だけを使った。初期実装のSHA-256は
`24c82c7e2fbc98edb73a384170074da8bf0240eb5203179aa253cbe9a5055424`。
校正開始前に24 sourceを保存し、その保存版で実行した。

| 固定policy | 独立Docker評価 | 公開actor check | 全result・trace・完了時刻 |
| --- | --- | --- | --- |
| FIFO | 24/24測定 | 24/24測定 | 一致 |
| 強い初期実装 | 24/24測定 | 24/24測定 | 一致 |

独立側は1 CPU・256 MiBの固定Python image、公開側は1 CPU・2 GiBの固定actor image。
launcherと要求ループは共通だが、両環境の観測遅延が等しいとは仮定しない。
独立側の最大応答はFIFO 0.023840秒、初期実装0.041386秒。
最大準備待ちはそれぞれ0.386188秒、0.381822秒だった。
これらは今回の観測であり、将来の最大遅延の保証ではない。

以前に初回応答で停止した`development-contended-burst-0`も、初期実装で373応答を測定し、
最大応答は0.017190秒だった。旧版の成功済み公開校正`termination-public-calibration-20260910-02`
を読取りだけで照合すると、同じ入力・候補の全48結果が新しい独立結果と一致した。
旧得点を再計算したり、以前の保留を成功に変えたりしていない。

最終試験の10個、公開校正の50個の所有containerについて、回収記録と事後の不在を確認した。
校正結果・公開source・保存sourceとcheckoutの一致も確認した。
疑似providerも実モデルも要求しておらず、非公開qualificationは採点していない。

原記録のrootは`~/.local/state/devcontainer-evaluations/`。

- 最終試験: `ready-runtime-preflight-20260910-02-{activation,parity,bounds}`
- 全公開校正: `ready-runtime-public-calibration-20260910-01`
- 結果照合・container事後監査・試験log: `ready-runtime-verification-20260910-01`

## 次の判断

この時計の修正・固定非agent校正はここで閉じる。次は既存のnative actorと期限停止後の
成果物回収を使い、新しい時計を公開bundleと独立採点の両方へ接続した有限pairを固定する。
新しい単独と協働へ同じ強い初期sourceを渡し、最終品質を比較する。
接続は疑似providerで検証し、source一致の新protocolが揃うまで実モデルは開始しない。
旧pairの未使用枠を再開せず、新たな汎用runner・方式の総当たり・候補選択UIは前提にしない。

今回減らしたのは測定の曖昧さである。難題で単独を超える成果、安定した協働効果、
通常配布へ採用できる改善は、引き続き未達である。
