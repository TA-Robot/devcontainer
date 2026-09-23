# プロジェクトレビュー — 2026-09-05

レビュー基準点: `5ca8a988efb74491cef0fa670d9137f85f855f82`。未追跡のEvidence Forge実験コードも現物を確認した。モデル世代・能力の評判を根拠にせず、目的、実装、再現結果から判断する。今回の成果はレビューと計画改訂であり、以下の実装不備を修正済みとは扱わない。

## 判断

基盤を全面的に作り直す根拠はない。native-first、broker所有のGit操作、有限job、失敗を成功と偽らない状態管理、内容を保存しない観測は維持する。一方、次の投資先をG3の難化やForgeRoomの長時間開発へ直結させる計画は変更する。

最優先は、評価値を候補自身から独立させ、保存済み成果を再検証できる状態にすること。その後に、実際の開発で判断を変える比較だけを行う。「協働が勝つ」「5倍難しい」は採用条件にしない。soloが十分、差が小さい、追加コストに見合わない、という結果も有効な終了条件にする。

現時点のEvidence Forgeは内側の課題と評価器の試作である。現行devcontainerを使ってG1–G3を解いた事実は、開発対象であるForgeRoomがそれらを解けた証拠でも、外側のB30/B60/B120品質曲線を測った証拠でもない。

改訂した実行順序と完了条件は[改訂計画](project-plan.md)に置く。

## 重要度と証拠の読み方

P1は次の比較実験・自動採用より先に処置する問題、P2は運用や解釈を誤らせる問題。稼働中基盤に重大事故が起きたという意味ではない。`再現`、`コード確認`、`計画上の判断`を分け、未計測の影響を断定しない。

## R1 / P1: G2の外部評価が候補の自己申告を採点する

**再現。** [g2/evaluate.py](../temp/forgeroom-benchmark-r0/proof/evidence-forge/g2/evaluate.py)の24–47行は候補側の`planner_batch_tool`を実行し、そのJSONに含まれる時間・worker消費を集計する。検査は主に件数と終端状態であり、割当て列や所要時間を外部で再構築していない。候補へ送るscenarioには`failing_jobs`も含まれる。

FIFO fixtureを一時directoryに生成し、batch CLIだけを「失敗jobの有無に応じたstatusと、全指標ゼロを返す」プログラムへ置換してcommitした。実際のplannerとpublic testは維持した。それでも評価器はexit 0、`valid/public_tests/workspace_clean`はすべてtrue、heldout 24件の全時間・消費指標はゼロとなった。

これは過去runの不正を示さない。候補がsimulatorやCLIを善意で改修した場合も、評価基準を変えてしまえる構造が問題である。

**処置:** evaluator所有の状態・時計・失敗情報で候補の割当てだけを評価する。候補との境界を入出力で分離し、public testの正本も評価側に保持する。自己申告JSONは診断材料に限定する。改訂前のhard gateを自動採用の根拠にしない。

## R2 / P1: 固定simulatorにも状態共有の抜けがある

**再現。** [g2/runtime.py](../temp/forgeroom-benchmark-r0/proof/evidence-forge/g2/runtime.py)の37–40行は`jobs`、`ready`、`idle_workers`に内部dictionaryへの参照を含めて`choose`へ渡す。candidateが`state['ready'][0]['duration']['cpu'] = 0`とすると、simulator側の実行時間も変わる。

10秒のjobを1個だけ持つscenarioで、候補からdurationをゼロにすると`completed`、`completion_time=0`、`worker_seconds=0`になった。単にsimulatorを評価側からimportするだけではR1を解消できない。

**処置:** 評価状態とcandidate入力の所有権を分離する。serialized copy等で別processへ渡し、返された割当てのみに基づいて評価側が遷移する。入力書換え、重複割当て、不正ID、非有限値、無限待機を拒否する回帰を持つ。同一process内のコピーは偶発的破壊対策であり、敵対的コードへの隔離を保証しない。

## R3 / P1: proof gateが意味的な差を保証しない

**再現。** [run_proof_matrix.py](../temp/forgeroom-benchmark-r0/proof/evidence-forge/run_proof_matrix.py)の40–55行は、G2のheldout dictionaryが3種類あると方策差を認める。そのdictionaryには`planner_ms_p95`が含まれる。

completion、blocker、worker消費をすべて同値にし、処理時間だけ0.1/0.2/0.3へ変えた入力でも`g2_policy_vectors_differ=true`となった。また空のvariant/static集合に既定のprofile結果を添えると全gateがtrueとなった。通常CLIはvariantを固定生成するため、後者は現行の通常実行で欠測が起きた証拠ではないが、gate関数自体はcoverage不足を拒否できない。

**処置:** 必須case・variant・candidate・criterion集合の完全性、重複、非有限値、評価器の異常終了を先に検査する。方策差は決定的な成果指標で判定し、処理時間差は別の反復測定へ出す。G2/G3のtimeoutや壊れたJSONは構造化した評価不能として保存し、品質不足や完走と混ぜない。

## R4 / P2: worker-secondsは実消費とは限らない

**再現。** [g2/runtime.py](../temp/forgeroom-benchmark-r0/proof/evidence-forge/g2/runtime.py)はjob開始時に全durationを加算し、最初の失敗時点でreturnする。1秒で失敗するjobと100秒のjobを同時開始すると、1秒時点で`worker_seconds=101`となる。失敗時点までの稼働時間なら2である。

予約済み仕事量、cancel不能な支払対象、実稼働時間のいずれを測るかで、この値の意味は変わる。現在の結果はコードどおり再現するが、「消費資源が少ない」を一般化するには意味が未確定である。

**処置:** cancellation/drain方針を先に定義し、経過worker時間と開始済み仕事量を区別する。旧値を無言で再定義せず、metric revisionと旧結果を保持する。

## R5 / P1: 期待する協働の勝ち方を評価器の採用条件にしている

**コード確認と計画上の判断。** [v2設計](../temp/deep-development-benchmark-redesign-20260830/22-evidence-forge-v2-critical-design.md)の337–405行は、serial、fanout、maker-onlyに期待する負け方を設定し、その分離から次へ進む。一方、[G1 profile](../temp/forgeroom-benchmark-r0/proof/evidence-forge/g1/run_profiles.py)はM0へnaive patch、M2へreference patch、M3へ不整合な組合せを明示的に渡す。[G3 generator](../temp/forgeroom-benchmark-r0/proof/evidence-forge/g3/generate_fixture.py)もmaker/referenceの欠陥有無をコードで決める。

これらは評価器が既知の欠陥を検知するテストとして有効。しかし「serialよりadaptiveが良い」「fresh verifierが必要」という行動比較の証拠にはならない。既存文書にもlive未証明の留保はあるが、採用gateが望む勝敗へ向いている点は残る。

**処置:** calibrationは正しい成果と既知の不正成果を区別できるかで判定する。実agentの方式比較は同じ出発点・入力・権限・評価で行い、結果の向きをgateにしない。弱いbaselineに勝つだけでなく、強いsolo継続や同一makerの追加検証と比較する。「5倍」は基準量と用途が定まるまで開発の必須条件から外す。

## R6 / P2: G2の成果は保存するが、協働の限界効果は未確定

**今回の再計算。** 保存済みのmulti-agentとsoloの`planner.py`を評価側の同一simulator/scenarioで再実行した。候補側の`simulator.py`はreferenceとbyte一致し、両runでCLI/simulatorの変更はなかった。

| heldout指標 | Multi-agent | Solo |
| --- | ---: | ---: |
| completion p50 | 69 | 77 |
| blocker p50 | 42 | 39 |
| 旧定義worker-seconds平均 | 126.125 | 124.417 |

値は[既存報告](agents/evidence-forge-g2-live-pilot-2026-09-05.md)と一致した。したがってR1を理由に既存成果を全廃しない。ただしこのreplayもR2を持つsimulatorによる診断であり、修正済み評価器による完全な再認証ではない。

元の比較は901秒対460秒の各1runである。追加441秒をsoloへ使った場合の結果、実行順序やproviderの揺れ、課題間の再現性は未測定。verifierが実際の欠陥を修復させた証拠は残すが、最終成果の差をすべて協働へ帰属させない。

さらに現在のgeneratorは3/4/3層と最終jobという小さなDAGを基本とし、heldout 24件の内訳は成功8件・失敗16件である。この実装のp95は両群で最大値になる。未見seedの結果は有用だが、大規模graphや異なる業務分布への汎化、安定したtail性能を保証するものではない。

**処置:** 自然終了までの効率と、同一budgetでの到達成果を別実験にする。予算はwallとprovider使用量を分け、cache込み入力tokenをそのまま金額に換算しない。completion重視・blocker重視・資源重視の用途を先に定義し、用途ごとの判断を出す。最大run数、停止理由、反復精度をrun前に固定し、都合のよい結果が出るまで追加しない。

## R7 / P2: G3の飽和を「さらに難しくする」だけで処理しない

**計画上の判断。** [最新G3報告](agents/evidence-forge-g3-live-pilot-2026-09-05.md)は7/7とmaker先行発見を正しく記録している。現在のvariantは主に名前の置換で、実際の義務・欠陥構成は共通である。

まずこのfamilyを既知の基本保証を守る回帰課題として保持する。追加reviewが不要だったことも有効な学習である。verifierが勝つまで欠陥を足すと、実際の需要から遠ざかる。

**処置:** 深いreviewで拾いたい実際のfailure classを先に選ぶ。同じmaker checkpointに対して、maker自身の再点検とfresh reviewへ比較可能な追加予算を与え、欠陥の再現・修復・誤検出・残存を評価する。実務上の価値を説明できなければG3の難化を終了する。

## R8 / P1: 評価を支えるsourceがclean cloneに存在しない

**Git確認。** `git ls-files temp/forgeroom-benchmark-r0 temp/evidence-forge-live-runs`は空だった。評価器・generator・proof matrixとraw runの所在はローカルの未追跡directoryであり、追跡済みのpilot報告だけでは再現できない。raw transcriptを公開しない方針自体は適切だが、実行に必要なsourceまで未管理なのは別問題である。

**処置:** 試験コード、入力、candidate、評価器、環境のdigestを結ぶmanifestを保存する。raw証跡はprivate artifactとして保管し、sanitized resultと取得手順をversion管理する。このrepoの「サンプルアプリ/デモを追加しない」責務に従い、ForgeRoomアプリや生成projectを一括追加しない。評価用sourceの正式な置場を限定するか、独立repo/artifactへ切り出してimmutable参照を残す。削除・移動・公開は今回実行していない。

## R9 / P2: execution contractと品質受入れの境界が読みにくい

**コード確認。** `scripts/agentctl_jobs.py:2409–2496,3220–3293`と[agentctl仕様](agentctl.md)では、`job validate`はresult schemaとGit stateを再検証する。acceptance commandについてはproviderが申告した`passed/exit_code=0`を照合し、command自体をbrokerが再実行する機能ではない。これは現行仕様だが、ForgeRoomのcontroller-owned acceptanceや「validated」という名前から意味的な品質保証まで推論してはいけない。

また`project/AGENTS.md:65`と`AGENTS_TEMPLATE.md:88`はimplementerにcommitを求め、後段とnative role定義ではbroker時はcommit禁止とする。completion節もbrokerに寄っており、native-firstで使う場合の完了条件と混在している。

**処置:** provider報告、brokerの機械的整合性、primaryが再実行した受入れ証拠を別の保証として記述する。nativeとbrokerのhandoffを入口で分岐させる。brokerに任意の申告commandを無条件で再実行させるのは解決策にしない。cleanなLane Rは維持し、snapshot reviewの需要と待ち時間が確認できてから別surfaceを検討する。

## R10 / P2: supervisor回帰テストの完了待ちに競合がある

**再現と診断。** Python 105テストの初回実行で、queue agingのtest/teardownがtimeoutし、ログ保持testは`agentd-log-retention.json`不存在で失敗した。対象2ケースの再実行ではagingは通り、ログ保持testだけ同じ失敗を再現した。agingの原因は未確定で、単に環境負荷だったとは断定しない。

`scripts/test-agentctl-supervisor.py:308–340`はlog本体の縮小を待つが、metadataの存在を待たずに読む。`scripts/agentctl_jobs.py:1284–1387`はlog縮小・fsyncの後にmetadataを書く。診断用にmetadata読取り時だけ最大5秒待つと、当初不存在だったfileが約0.0102秒後に現れ、当該testは通った。5秒はこの診断のcost capであり、runtimeの推奨待ち時間ではない。

**処置:** テストが必要とする保持記録のpublicationを待ってassertする。runtimeにもlogとmetadataの同時可視性が必要なconsumerがあるか確認する。今回確認したのはtestの待合せ問題であり、productionで記録が永続的に失われる証拠ではない。診断用に待ちを加えた成功を、未変更テストのgreenへ置き換えない。

## プロジェクト全体の見直し

| 領域 | 判断 | 次の扱い |
| --- | --- | --- |
| devcontainer / toolchain | pin、明示的edge、safe既定を維持 | 実際の更新・起動回帰を先に守る |
| agentctl | Git所有権、cancel/orphan、有限capacityは再利用価値あり | 保証境界を明示し、実運用の阻害要因から改修 |
| native template | 方針は維持、説明重複とhandoff混在を整理 | 全面的framework置換は不要 |
| Mira / observation | fail-open、content-free、unknown維持 | 観測の欠測を品質不足と混同しない。完全なtelemetryを全作業の前提にしない |
| duration atlas | 139観測、36 caseという履歴は保存 | revision/identity/applied設定の制約があり、自動routingへ昇格させない |
| Evidence Forge | 評価器試作として継続価値あり | R1–R4、R8を処置してから比較を再開 |
| ForgeRoom製品 | 現行基盤に対する追加価値が未実証 | UIや永続化の全面開発前に、既存CLI＋Miraで満たせない利用上の不足を特定 |
| Lane I / scheduler / GC | 未実装であることは明示済み | 信頼境界・定期job・ディスク圧の実需要が生じた時に優先順位を上げる |

実装状況の正本は8月26日で止まり、最新の判断はpilot文書へ分散していた。複数の探索計画をそのまま実行待ちbacklogと解釈しない。現行計画への入口を一本にし、過去の計画と結果は履歴として保存する。

repo内に共通CI workflow/統一check入口は確認できなかった。外部CIの不存在は断定しない。今回の確認でも多数のテストは存在するため、「テストを増やす」より、既存checkの実行環境・実行結果・release判定を再現可能にすることを優先する。巨大moduleを行数だけで分割することも優先しない。

## 今回の検証と限界

- R1–R4の局所probeを一時directoryで実行。既存fixtureやrun成果は改変していない。
- G2保存成果の3指標をreference simulatorで再計算し、既存報告と一致。
- Mira extensionのNode test: 20/20 pass。
- Pythonのcontract / agentctl / supervisor / benchmark / observation / hook: 105テスト実行、2ケースで計3エラー。対象2ケースの再実行は1 pass・1 error。上記R10の診断ではmetadata publication待ちを加えると当該testが通った。未変更suite全体はgreenではない。
- Docker image build、live provider実験、36-case corpus全件監査は今回のレビューでは実行しない。既存build成功記録を今回の再検証成功と読み替えない。
- 一人のagentによるコード・計画レビューであり、全コードの安全監査、独立reviewerによる追試、外部利用者調査ではない。

レビュー時sourceのdigestとprobe結果は[証拠要約](project-review-2026-09-05-evidence.json)に残す。未追跡sourceはcommit SHAだけでは固定できないため、再現時はdigestも照合する。

検査コマンド:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  scripts/test-agent-contracts.py scripts/test-agentctl.py \
  scripts/test-agentctl-jobs.py scripts/test-agentctl-supervisor.py \
  scripts/test-benchmark-devcontainer.py scripts/test-collaboration-evidence.py \
  scripts/test-mira-codex-hook.py
node --test extensions/mira-companion/test/*.test.js
git diff --check
```

R1の再現では`g2/generate_fixture.py --output <一時candidate> --solution fifo`で生成し、`planner_batch_tool`の本文だけを次へ置換して実行属性を保ち、一時candidate内でcommitしてから`g2/evaluate.py --candidate <一時candidate>`を実行した。

```python
#!/usr/bin/env python3
import json, sys
scenarios = json.load(sys.stdin)
print(json.dumps([
    {"status": "blocked" if s["failing_jobs"] else "completed",
     "completion_time": 0, "time_to_blocker": 0,
     "worker_seconds": 0, "planner_ms": 0}
    for s in scenarios
]))
```
