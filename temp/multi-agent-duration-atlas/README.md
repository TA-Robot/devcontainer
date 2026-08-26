# Multi-agent duration atlas 検討計画

検討開始: 2026-08-26

このdirectoryは、agentへ「どんな仕事を、どの構成でさせると、実際にどれくらい時間がかかるか」を計測し、projectが後から判断材料として参照できる時間atlasを作るための計画・実装記録です。schema/fake runner、非生成capability probe、S/M/L isolated fixture、network-disabled evaluator、Codex / Claude / Grok one-shot runner、raw sample reporter、criterion-level quality scoreまで実装済みです。12 family × S/M/Lの全36 candidateは`case-designs/`で各6文書へ具体化済みですが、fixture実装とlive観測が済んでいるのはまだF04の一部です。current rubricのS/C0ではGrok 4.6 / mediumが5/5、Sol / mediumが4/5の単一観測です。時間目安やtypical bandを出せる段階ではありません。

## 今回作るもの

最終成果は、次のような**実測値つきの参照表**です。

```text
task family / size profile: failing-test diagnosis / M-coupled-deterministic
configuration: primary + independent investigator, fresh context
model identity: requested=<alias>, resolved=<unknown>, confidence=alias-only
generation settings: requested=<provider effort>, applied=<unknown>
runtime: <CLI build> / agentctl-job / automatic permission

first contract-valid artifact: not observed
user-visible result ready:   11m50s
online acceptance:           pass
offline study score:         pass (scoring runtime is not user wait)
aggregate worker time:       13m10s
observations:                1 run / 1 case / 0 censored
evidence grade:              single-observation
```

数値は一件の表示例で、まだ測定値ではありません。`single-observation`ではrangeやtypical bandを作りません。実際のatlasでは全sample、観測条件、case revision、失敗・timeoutを併記します。

## 今回作らないもの

- 「この条件なら必ずmulti-agentにする」というglobal routing rule
- providerやmodelの単純な総合ランキング
- agent数、対話round数、反復回数の固定default
- 異種taskを一つの平均値へ潰した生産性score
- `terminalOutcome=success`だけを品質とみなす集計
- 人間による日報、rating、stopwatch入力を必要とする運用

どの時間・品質・資源のtrade-offを採るかは、projectの目的、期限、risk、変更可能性に依存します。このatlasはその判断を代行せず、同じ単位で比較可能な材料を提供します。

## 文書構成

- `01-objective-and-reference-output.md`: 目的、問い、時間atlasの表示単位
- `02-size-model-and-task-corpus.md`: S/M/Lの定義と12 family × 3 sizeの候補corpus
- `03-experimental-dimensions.md`: collaboration、provider、context、並列度などの比較軸
- `04-measurement-and-data-contract.md`: timestamp、品質oracle、machine-readable schema
- `05-sampling-and-analysis.md`: 反復、ばらつき、推定精度、timeoutの扱い
- `06-execution-waves-and-safety.md`: 段階実行、rate-window保護、停止条件
- `07-implementation-roadmap.md`: 計測開始前にrepositoryへ追加する最小機構
- `08-grok-review-brief.md`: Grok 4.6へ渡した独立review brief
- `09-grok-independent-review.md`: Grok 4.6 requested-high-effort reviewの原文（applied値は確認不能）
- `10-review-synthesis.md`: 指摘の採否と統合後の設計判断
- `11-skill-delivery-and-context-budget.md`: 詳細dataを残しつつcompactに参照するskill配布設計
- `12-grok-followup-brief.md`: 改訂版をfresh Grokへ再監査させたbrief
- `13-grok-revised-plan-audit.md`: 改訂版監査の原文
- `14-final-plan-closure.md`: 再監査で残ったblockerの解消記録
- `15-milestone-a-implementation.md`: schema、fake clock、runner、testの実装記録
- `16-wave-0.5-passive-capability-probe.md`: provider別のmodel/effort広告面とhost/container観測差
- `17-milestone-b-case-fixtures.md`: structural S/M/L catalog、disposable repo、gold/oracle isolation
- `18-isolated-evaluator.md`: live artifactをhost credential/networkから分離して検査するcontainer
- `19-first-recorded-codex-canary.md`: provider時間とhidden評価を結合した最初のCodex live record
- `20-raw-sample-reporter.md`: failureをquality-pass時間へ混ぜないbounded raw inventory
- `21-criterion-quality-scoring.md`: binary failの内訳を比較可能にするversioned rubric
- `22-provider-depth-curve.md`: 3 provider runner、sandbox/auth知見、mediumからmax/ultraまでのdepth curve
- `23-first-l-depth-coverage.md`: L caseでのGrok applied curve、Sol requested curve、max rejection、rubric飽和
- `case-designs/`: 全36 candidateのprofile、fixture、task、rubric、execution、implementation handoff（各6文書）

## 正本との関係

- `docs/agents/collaboration-observation.md`のzero-input episode ledgerは自然運用の観測に使えますが、task case、S/M/L、useful evidence、acceptance-readyなどの実験情報はまだ持ちません。
- study catalog annotationは、明示開始したfinite study内だけで有効です。通常episodeの`unknown` semanticsをfamily/sizeへ後付け変換しません。
- `reviewProxy`は人間review時間でもstudyのsynthesis tailでもないため、T4の代用にしません。
- `docs/agents/representative-scenarios.md`の「5回以上、median/p95」はlegacy control-plane比較の既存ルールです。今回のlive agent時間atlasへglobal ruleとして流用しません。小標本のp95は時間目安として誤解を生むためです。
- 実験で妥当性が確認できたschemaやrunnerだけを、後で`docs/`、`scripts/`、`project/`へ昇格します。

## 中心原則

1. S/M/Lを所要時間で定義しない。時間は測る対象だからです。
2. 同一taskの再実行によるrun varianceと、同じfamily内の別taskによるcase varianceを分けます。
3. wall-clock、first contract-valid artifact、worker総時間、synthesis/online validation、offline scoringを分けます。
4. 成功だけを残さず、failure、timeout、retry、provider refusalも時間sampleとして残します。
5. 測っていない組合せは`unmeasured`と表示し、近いcellから勝手に補間しません。
6. 参照値には必ず観測日、model identity confidence、requested/applied generation setting、CLI/runtime surface、machine、cache/context状態を付けます。
7. batchは明示起動・有限・停止可能にし、無限実行や定期消費を初期scopeへ入れません。
8. model alias、requested effort、schema-valid artifactから、resolved model、applied effort、人間にとってのusefulnessを推測しません。
