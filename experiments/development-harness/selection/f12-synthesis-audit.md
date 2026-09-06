# F12-L証拠統合課題の適格性監査

更新: 2026-09-06。[実行記録](f12-synthesis-audit.json)。旧case revision 3、oracle、得点は変更しない。
結論は**数値・参照・明示制約の組立てを測る条件付き候補**。対策の実効性や一般的な案の創造性は未測定。

## 何を相談の対象にできるか

公開入力には、warm/coldの性能と打ち切り、無効なpooled観測、cleanup事故、隔離、
未確認の復旧、移行・所有権・rollbackの制約がある。
例えばmakerが性能値を整理し、advisorが事故・隔離・移行の根拠と矛盾を点検するという
観点分割を組める。これは作用の仮説であり、その分担が有効と観測済みではない。

一方、公開`decision-contract.json`はDを移行bridge、A/Bを最終候補、Cを採用禁止とし、
必要なclaim/evidence/dependencyの集合まで示す。自由な製品案やarchitectureの発明は測っていない。
公開情報を隠して多agentだけ有利にする変更はしない。

## 実行した反例

既存known-goodを基に、提出物だけを変更し、JSONとMarkdownを同じ内容へ揃えて固定評価した。
校正用正解は監査専用で、developerへ渡して比較するものではない。

| 提出物 | 結果 | 読めること |
| --- | --- | --- |
| 既存known-good | 12/12 | 既存の正常経路が成立 |
| controlを「事故が再発しても強制しない」、gateを`printf success`、rollbackを「失敗しても続行」へ変更 | **12/12** | 根拠IDと必須fieldが残れば、対策が有効でなくても満点になる |
| BM-A-WARMのmedianを40から0へ変更 | 10/12 | 数値の再計算と対応するcriterionは誤りを検出 |

二番目では出力文を変更しただけで、そのshell文字列を監査側が実行したわけではない。
評価器の`test_incident_security`、`test_migration_operations`、`check_entailment.py`は、
主にIDの集合、非空のfield、依存辺を確認し、提出したgateやrollbackを実行していない。
この反例は過去runの不正や、過去の全観測の無価値を意味しない。

## ハーネス比較への反映

1. このcaseでの改善を「実効的な事故対策が良くなった」と表現しない。
2. 使うなら、数値・打ち切り・参照・明示制約の組立てに評価範囲を限定する。
   旧12点の総得点から、測っていない設計品質へ一般化しない。
3. 実効的な対策を比較したい場合は、後続の実装・故障注入・rollbackまで自動検査する別contractが必要。
   自由記述をLLM採点で上書きして既存runを再認証しない。
4. 独立した助言の寄与は、その根拠を使った最終成果と全費用で比較する。
   advisorの人数、助言の長さ、参照ID数だけで有効としない。

次の判断は、この限定された問いでもハーネスの相談起動・context分割・証拠引継ぎの採否を
変えられるか。変えられる比較を先に固定し、汎用的な設計品質を測る別基盤の完成を前提にしない。

再実行は未使用output pathで、providerを呼ばずに行える。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 experiments/development-harness/selection/audit_f12_synthesis.py \
  --output /tmp/new-f12-suitability-audit.json
```

上限は固定の3候補で、この対照監査のcost cap。ownerはprimary/integrator。
課題・oracle変更または新しいfailure modeで、新しい記録を作って見直す。
