# 相談比較用の障害診断課題 v1

状態: 課題生成・公開観測・独立評価・provider-free校正を実装・検証済み。
**相談による品質向上を測る主課題としては不採用。実行経路の校正と不要な相談を調べる対照候補として保持。**
この版は`consultation-crash-diagnosis-v1`。旧atlasのF03-L revision 1を変更しない。
協働runnerへの接続、live実行の予算固定、方式の効果測定は未完了。
[協働実験計画](../../../../docs/agents/collaboration-experiment-plan.md)のM1の成果物。

## 比較の問いと範囲

再起動障害の診断で、別agentから証拠付きの助言を得ることが、単体の追加調査より
最終診断の正しさ・到達時間・総消費を改善するかを調べるための課題。
worker側の永続offsetと外部副作用の順序を調べ、再現可能な中断位置と状態を提出する。
協働の有無で公開task・source・観測手段・評価を変えない。

公開課題は[brief.md](brief.md)。公開文、validator、模範出力に原因順序を埋め込まず、
sourceと実行観測から調べる形にした。operation名や出力形式、受入性質は公開する。
二つのvariantは副作用→ackとack→副作用で、実際に重複と取りこぼしが分かれる。
これは同じ答えを常に返す候補を校正で拒むための対照でもあり、難易度や協働の優位を保証しない。
どちらも校正用に検討済みなので、この二つだけを「未見課題での汎化確認」とは呼ばない。

### 既存案からの変更理由

| 選択肢 | 今回の判断 |
| --- | --- |
| 旧F03-Lのtask文から原因だけ削る | 公開checkや固定出力依存の評価を残すため不十分 |
| 任意のregression.shを提出し、その出力を採点 | 別processでも自己申告だけでは状態の証拠にならない。所有権・計時・観測の追加境界が必要 |
| 有限の再現計画を提出し、評価側が実行 | **採用**。任意コードの表現力を測定範囲から外し、選んだ中断と実状態を照合できる |

計画は`stop_after`と`restart_count`だけ。評価器が準備したworkerを同期eventで停止し、
実際に終了した後のfileと再起動後のfileを読む。単なる待ち時間や提出者の成功JSONは使わない。
公開観測のexit 0は観測完了を意味し、課題合格を意味しない。正常実行との対照も出力する。
動作の修正、任意の再現プログラム、文章の上手さ、一般的な分散保証は評価しない。

## 所有権と採点

- developerへcopyするのはworker、旧F03から再利用したjournal、公開observe、TASK、AGENTSだけ。
  `case.py`、`calibrate.py`、校正結果、variant名はdeveloper bundleへ入れない。
- 診断と再現計画を提出する。順序・隣接するcrash境界・状態・結果を構造化して照合し、
  自由記述の説明にkeywordや特定の言い回しを要求しない。
- 評価器はsourceを自分の生成した入力と照合し、candidateのPython、shell、公開toolを実行しない。
  信頼する別workspaceを生成してplanだけを渡す。candidate自身のmanifestを正本にしない。
- source変更、余分なartifact、symlink/FIFO、過大JSON、重複key、非有限数、不正型を拒否。
  `.git`はcontroller metadataとして無視し、読み込みも実行もしない。
- 正常実行、同じplanの反復、event名と開始offsetを変えた実行を使い、状態の固定出力を採点に代用しない。
  evaluatorの実行異常は`unknown`で返し、candidateの品質不足へ混ぜない。
- 採点に渡すのは全writer停止を確認したprivate snapshot。評価前後のhashも比較するが、
  それだけで実行中workspaceのatomic snapshotを保証しない。

## コマンド

すべてprovider-free。生成先と校正出力は未使用pathを指定する。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 experiments/development-harness/consultation/v1/case.py \
  create --workspace /tmp/new-consultation-workspace --variant effect-first

# developerが提出した停止済みsnapshotに対して実行する
PYTHONDONTWRITEBYTECODE=1 python3 experiments/development-harness/consultation/v1/case.py \
  evaluate --workspace /tmp/new-consultation-workspace --variant effect-first

PYTHONDONTWRITEBYTECODE=1 python3 experiments/development-harness/consultation/v1/calibrate.py \
  --output /tmp/new-consultation-calibration.json

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest scripts/test-consultation-diagnosis.py
```

`CONSULTATION_DIAGNOSIS_IMAGE`に検証済みimage IDを指定して同じsuiteを実行すると、
networkなし・read-only image・認証mountなしの実Docker校正も行う。
評価CLIはpass=0、quality fail=1、observer unknown=2。未知variantは開始前に拒否する。
入力のhashは校正結果へ残す。校正referenceは効果比較のcandidateにしない。

## この版の有限上限

ownerはprimary/integrator。以下はこの課題の局所contractであり、一般の人数・回数の推奨ではない。

| 値 | 分類・範囲 | 根拠・見直し条件 |
| --- | --- | --- |
| 3つのoperation、再起動1回 | hard guard: この単一中断課題 | 有限な計画と検証可能な状態遷移。複数中断が実要求になれば別版 |
| process待ち3秒 | cost cap: ローカルの小さなworker | 外部通信がなく、短いfile操作と起動だけ。正常実行でtimeoutなら実測を残して比較開始前に改訂 |
| plan/診断16 KiB、inventory対象file64 KiB | cost cap: この小さな構造化提出 | 巨大入力や特殊fileを評価入口で拒む。有効な成果が収まらなければ別版 |
| 同条件2回＋異なるevent/offset1回 | planning prior: 再現性の校正 | 最小の反復と固定payload依存の検出。統計的な信頼性やlive repeat数を意味しない |
| 2 variant × 10校正candidate | cost cap: 固定された校正集合 | 正解・別表現・公開toolだけの非agent解法・7種の負例を両順序で確認。新しいfailure modeが見つかれば版付きで追加 |

### 校正結果と題材の採否

[校正と検証記録](calibration.json): 固定20候補の期待判定が20/20一致。
11テストが合格し、検証済みimageのnetworkなし・read-only・認証mountなしの校正も含む。
旧atlasやその過去の得点は変更していない。

さらに`calibrate.public_tool_baseline(workspace)`はvariantや正解を入力に取らず、
公開された3つの中断点を公開CLIで試すだけで、両variantの9評価項目をすべて満たした。
原因を先に教える問題は解消したが、最終成果は小さな有限探索で構築できる。
したがって、このままモデル間の相談効果を調べる主題としてlive費用を使わない。
校正の合格と、協働比較の題材としての採用を別々に判断した。

この結果は全診断課題で相談が不要だと示したものではない。実行経路の回帰試験と、
AIが非agent手段で足りる課題に不要な相談を増やさないかを調べる対照候補として残す。
その対照用途も実際のAIによる選択は未測定。相談を勝たせるための難化や情報の片側削除はしない。

## 次の接続作業

既存terminal経路へこの独立評価を接続し、疑似providerでsoloと相談条件の受渡しを確かめる。
advisorへの情報境界、maker継続、全participant停止、全usage・待ち・統合費を
疑似providerで検証してから、model/effort/実行順/全体予算/停止方針をmanifestへ固定する。
主比較の課題は別に適格性を確認する。次の候補はF12-L revision 3の証拠統合で、
既存の選択肢・制約・複数の根拠からの判断を測る範囲に限り、情報の重なりと異なる観点の寄与を監査する。
現在の校正成功を、協働実行経路や効果の検証済み表示に使わない。
