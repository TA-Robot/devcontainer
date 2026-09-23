# 実リポジトリの難題を借りる: 最初の入口

2026-09-23。主計画R1/R2の候補選定。live protocolではなく、実モデルは未開始。
課題のcode・正解・評価testをこの基盤repoへ追加しない。外部の固定snapshotと専用評価環境を使う。

## 固定した入口

- upstream: https://github.com/scaleapi/SWE-bench_Pro-os
- revision: `66f92766bba642462d4bbe5479e83f91f9211862`
- task root: `v2/tasks/`。旧v1のimage・採点器は混ぜない。
- candidate population: 同revisionの`v2/hard51_ids.txt`
- 参照: [上流手順](https://github.com/scaleapi/SWE-bench_Pro-os/blob/66f92766bba642462d4bbe5479e83f91f9211862/v2/README.md)

今回は公開instructionとtask/environment設定だけを読んだ。正解patch・隠しtest・個別のmodel得点は読んでいない。
選定理由は、異なる実repoでの互換性・複数形式・状態移行を伴う要求を扱うこと。
下記3repoを選び、それぞれHARD-51内でinstance IDを辞書順に並べた先頭を候補にした。
model結果を見て順序を交換しない。3は今回の探索費用capであり、統計的な必要標本数ではない。

| 順序 | repo / 公開要求の概要 | instance ID |
| --- | --- | --- |
| 1 | Ansible: POSIX mount情報の複数形式・情報源、絞込み・timeoutの契約 | `instance_ansible__ansible-40ade1f84b8bb10a63576b0ac320c13f57c87d34-v6382ea168a93d80a64aab1fbd8c4f02dc5ada5bf` |
| 2 | Flipt: metrics exporterの選択と既存設定の互換性 | `instance_flipt-io__flipt-2ca5dfb3513e4e786d2b037075617cccc286d5c3` |
| 3 | Teleport: event保存形式・日付検索・既存dataの扱い | `instance_gravitational__teleport-1316e6728a3ee2fc124e2ea0cc6a02044c87a144-v626ec2a48416b10a88641359a169d99e935ff037` |

公開instructionのSHA-256（上の順序）:

```text
b29415050a1a07795fb0c1440322e6c641c36176b53d339ad47578f06c3b5ebe
bb81e79521bc3cbd9271c6db7e2c8cb4617336a0193103e438f52503d2d18021
dff482a373984c9be10d26066d44e6a742affbaa259e90835680b72250ec8ebe
```

upstreamのtask設定には開発3000秒、1 CPU/4096 MiB、評価3000秒の上限がある。
これは上流条件の記録であり、こちらの総実験予算や実行許可ではない。
image tagは`ghcr.io/scaleapi/swe-bench_pro-v2:<instance_id>`。実行前に取得digestを固定する。
公開imageの取得、各verifierのローカル実行、現在CLIとの組合せはまだ検証していない。

## 最初の一件で確かめること

1. 上流revisionとSHA256SUMSを照合し、image digestとlicenseを記録する。
   依存と通常testが準備済みかを確かめる。candidate・referenceはhostで実行しない。
2. 認証のない別containerで、空patchは失敗しreferenceは成功することを確認する。
   testが公開要求へ対応するか、模範patchの内部構造だけを強制しないかも検査する。
   不整合は基盤/課題不良として保存し、oracleを都合よく直して合格にしない。
3. actorにはbase checkoutと公開instruction・公開testだけを渡す。
   solution、verifier、修正commit・履歴・評価結果は渡さない。モデル通信以外の外部lookupを遮断する。
   sandbox、network、実CLIの編集と公開test、期限停止後diff回収を疑似providerで確認する。
4. diffを封印後、未使用の評価containerへ適用して採点する。
   開発containerのcache、書き換えたtest、環境変更で得点を作れないことを確認する。
5. image取得・setup・開発可能時間・評価・回収を別々に記録し、次のlive protocolの全費用を固定する。

既存の回収・patch保全を使い、接続が足りない部分だけを追加する。
Harbor/Modalはこのrepoには未導入。上流手順があることを、ローカルで起動可能なruntimeとみなさない。
必要なら使い捨ての評価venv/imageへ固定版を導入し、通常devcontainerの依存へ増やさない。
自作adapterとの準備費を比較し、2時間の準備capを超えて基盤を作り続けない。
capのownerはprimary/integrator。最初の取得時に開始時刻と出力pathを記録する。

## 単独校正と、比較へ進む条件

現在の強い単独（初期候補Astra/high）に、十分なtool・公開検証・自己反証・複数案を許す。
モデル/effort/CLIの実適用、CPU/memory、開発・output・評価・回収の全上限を事前固定する。
最新modelが難題を容易に解いても成功例を捨てない。

固定順に調べ、最初の**基盤と評価が成立し、開発上の未達があり、協働介入の仮説を置ける課題**を
継続比較の開発用課題にする。未達でも隠れた要件やtest不良が原因なら除外理由を残す。
全3候補に適格な未達がなければ、この層での協働を追加しない。tool/予算を削って未達を作らない。
これは難度校正に基づく条件付き選定であり、全課題での平均改善率を示す設計ではない。

checkpointは事前に決めた開発終了時の一つを使い、隠し得点で途中候補を選び直さない。
双方へ同じsourceと同じ公開実験記録を渡す。追加の単独にも再設計・試作・反証を許す。
両方をfresh sessionから開始し、片側だけへ元会話や非公開の評価診断を継承させない。
介入のroot model・公開tool・総CPU/memory・clockは揃え、協働側の全参加者費用を残す。
評価で知った欠陥箇所・隠し失敗一覧を、追加開発のpromptへ渡さない。

比較の主成果は最終要求充足と既存動作の退行。途中の優れた候補は診断用に分ける。
予定した期限停止のpatchも、事前に固定した捕捉契約で採点し、会話の正常終了とは区別する。
usageが欠けても品質回収は試みるが、費用・output予算適合は不明のまま。
全提出の封印前に採点結果をdeveloperへ返さない。

## 採否を変える証拠

- 強い単独でも開発不足が残る → その失敗に対応した最小の協働を試す。
- 別model単独が同じ要求を容易に満たす → 協働よりmodel選択で十分かを検討する。
- 協働で有用な案が出るが統合されない → 人数より選択・統合手順を次の介入にする。
- 双方同じ失敗 → 共通情報/仮説/評価の不足を確認し、勝つまで追加開始しない。
- 協働の最終成果が改善 → 介入を固定し、未使用の別repo課題で確認する。

確認用課題はこの開発用3件とは別に、結果を見る前に固定する。
未使用の候補を後から都合よくconfirmationと呼ばず、同じ公開benchmarkの既知性も明記する。
この文書は候補の根拠を固定した段階で、難題認定・実行成立・協働効果の証明ではない。
