# 証拠統合の事前相談: 実比較と採否

2026-09-06。[固定protocol](synthesis-protocol.md)、[機械記録](synthesis-result.json)。
新しいterminal接続で実モデルの相談→makerとsoloを一組実行し、停止・保全・独立評価まで完了した。

**常に事前相談する方式は採用しない。品質改善の判断は評価器の誤判定により保留する。**
相談側は提出までの時間とinput消費が増えた。品質を揃えた速度比は成立しておらず、出さない。

| 観測 | Solo | 事前相談＋maker |
| --- | ---: | ---: |
| 固定した元の得点 | 10/12 | 10/12 |
| condition実行時間 | 282.256秒 | 336.729秒 |
| input tokens（cacheを含む） | 157,339 | 227,802 |
| cached input tokens | 136,192 | 180,352 |
| output tokens | 8,391 | 8,938 |
| 提出・予算・usage・停止 | 確認 | 確認 |

相談側のcondition時間は19.3%増、inputは44.8%増、outputは6.5%増。
advisorの開発時間は102.596秒、makerは229.899秒。condition時間には初期化・受渡し・停止・回収も含む。
準備は15.564秒、外部評価などを含む全体は637.581秒。単一実行の値で、典型時間ではない。
要求modelはgpt-6-astra、effortはhigh、CLIは0.153.0。resolved model/applied effortは確認できずnull。
金額換算や一般的なmodel優劣は出さない。advisorを含むusageを計上し、maker区間だけで速度を比べない。

## 原得点と品質解釈の分離

両条件は公開3項目をすべて通り、hiddenのうち次の2項目で落ちた。

- `synthesis-claim-provenance`: `universal`の存在だけを拒否する。
  実成果の`No universal ...` / `not universal ...`という一般化を否定する記述にも一致した。
- `synthesis-unknown-honesty`: 復旧根拠を参照するunknownと、providerに言及するunknownをそれぞれ1件ちょうどに制限する。
  同じ根拠が複数の未確認事項に関係すると落ちる。公開仕様にはこの上限がない。
  実成果では復旧groupが両方2件、provider groupは相談側2件・solo側1件だった。

原成果を変更せず、校正用known-goodから反例を別に作り、旧評価器で自動再現した。

| 校正用成果 | 得点 | 落ちた項目 |
| --- | ---: | --- |
| known-good | 12/12 | なし |
| warm比較へ「This comparison is not universal.」と追記 | 11/12 | claim-provenance |
| 同じ復旧事故に関係する追加の未確認事項を記録 | 11/12 | unknown-honesty |

[再現コード](../selection/audit_synthesis_false_negatives.py)と機械記録内の`validity`が根拠。
JSONとMarkdownを同じ内容へ揃え、どちらの反例も公開3項目は通る。
失点条件の問題を示したが、元の成果を12/12へ採点し直したことにはしない。
元の10/12、成果、oracle、run IDは保持する。全体的な設計品質が正しいとも推定しない。

## ハーネスへ戻した変更

1. 実Codexのsandbox probe、環境同等性、prompt境界、全participant停止・usage回収を持つ比較接続を追加。
2. [集計のvalidity gate](synthesis_report.py)を追加。対応するoracleの有効な校正用別表現が落ちていれば、
   元の得点を保持したまま`quality_comparison_eligible=false`、品質付き速度比nullとする。
   case/revision/source hashが異なる校正を混ぜず、欠測や不正値から改善率を生成しない。
3. [協働の実測ガイド](../../../docs/agents/collaboration-evidence.md)へ、この条件で常時事前相談を既定化する根拠がないことと、
   効果を主張できる範囲を追記した。

この1組で「相談は一般に無効」とは言えない。advisorは事故・隔離・移行の根拠を提出したが、
到着・受渡しと、最終品質への限界効果を区別する。意味上の採用は集計上unknownのまま。

## 次の比較へ進む条件

同じ旧oracleでrun数を増やさない。新しい課題/評価版で、否定表現・複数の関連unknown・
妥当な別表現を受理し、実際の誤った一般化・根拠の欠落を拒否する校正を先に通す。
自由記述のkeyword検査から、公開された構造化scopeと根拠関係の検査へ移す。
その後に、今回の常時事前相談か、明確な不足が生じた後の相談か、次に比較する介入を固定する。
確認課題での改良前後の再評価は未実施で、プロジェクト全体の改善循環を完了扱いしない。

実行用3containerは停止を確認して削除し、認証のprivate copyも削除済み。
原記録は機械記録に示したprivate evidence directoryへ保持している。
