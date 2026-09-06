# F04-L: 動作評価の適格性監査

2026-09-06。旧F04-L revision 1を変更せず、正当な2実装と欠陥を持つ7実装を監査した。
**旧評価のまま新しい協働品質比較へ採用しない。** 原子的な置換と引数保持の要求違反が
4/4を通ることを再現した。別の動作検査では識別でき、review後の修正を測る別版の材料にできる。

[実装](audit_f04_lifecycle.py)、[原記録](f04-lifecycle-audit.json)、
[検証証跡](f04-lifecycle-validation.json)。旧caseの実装正本は
[`agent_duration_fixtures.py`](../../../scripts/agent_duration_fixtures.py)にある。
過去validityの`agent_duration_cases/f04.py`という参照先は現treeにはない。

## 公開要求と既存検査の差

[公開課題](../../multi-agent-duration/capsules/f04-l-python-bash-restart.md)は、
version 1のqueue形式、enqueue/ack/pending、ackの冪等性、未知IDと不正JSONの保全、
引数と終了statusの保持、各commandを別processで実行できること、原子的な書込みを要求する。

既存検査はpublic 2項目（unit、Bash構文）とhidden 2項目（通常の別process実行とack、
未知ID/不正JSON保全）。**別processでの正常再実行は、書込み中のcrash/recovery検査ではない。**
旧hiddenには原子的な置換の観測も、空白を含む引数の検査もなかった。

| 校正実装 | 旧得点 | 追加の動作観測 |
| --- | --- | --- |
| 元のknown-good | 4/4 | 全4 probe合格 |
| 別の原子的writer（NamedTemporaryFile＋rename、異なるJSON表現） | 4/4 | 全4 probe合格 |
| 既存fileをtruncateして直接書込み | 4/4 | 開いたままのreaderに旧版が残らず失敗 |
| Bashで引数を再分割するwrapper | 4/4 | 空白/Unicodeを含むstore path・ID・payloadで失敗 |
| 最初の引数だけ転送 | 2/4 | CLI操作失敗 |
| ackのたびにcountを増やす | 3/4 | ackの冪等性に失敗 |
| Pythonの失敗statusを隠す | 3/4 | 未知IDのexit 4に失敗 |
| 不正JSONを空状態として上書き | 3/4 | 不正状態の保全に失敗 |
| pendingを挿入順で返す | 3/4 | lexical orderに失敗 |

最後の候補ではJSONのkey整列も外した。`pending`のsortだけを外しても、保存時のkey整列に
よって正しい順序が保たれるため、それだけを欠陥と数えてはいけない。
候補構築は旧sourceの置換箇所が一致しなければ停止する。

## 新しい観測が示すこと・示さないこと

追加probeは別processのCLIを呼び、実fileのbytesとJSONを観測する。
既存queueのack更新では、評価側で開いておいたunbuffered descriptorが完全な旧bytesを保持し、
pathから読むと新しいack状態になることを確認する。sleep、実装へのhook、source中の関数名による採点は使わない。
これにより今回の直接上書きの反例を検出できる。特定のtempfile APIやJSON整形方法には限定しない。

これは通常完了時のack更新を観測するprobeであり、全write経路の原子性の証明ではない。
**書込み途中のprocess kill、電源断後のdurability、並行writerの競合は未測定。**
旧referenceもdirectory fsyncを含む電源断耐性の根拠にはしない。
新probeを旧4点に加算したり、古いrunを再採点したりしない。

9候補全てで期待した判定が一致した。timeoutは`unknown`であり、欠陥を検出できた成功に数えない。
候補は監査scriptが固定したprovider-free sourceに限定する。hostの`evaluate_fixture`や
このCLI実行関数をlive agent成果物の評価入口として使ってはいけない。

## 既知の天井を読み直す

監査時の[atlas](../../../generated/duration-atlas/current.json)にはF04-Lの10観測があり、9件が旧4/4。
全てprimary-onlyで、成果物は`content-free-only / not-retained`。
これは旧検査での高い到達率を示すが、今回の2欠陥が過去成果にあったかは確認できない。
過去の満点を「全公開要求が満たされた」と広げず、満点runの採点を変更しない。
source hashと各run ID、旧得点、参加者構成、retentionを原記録へ保存した。

高い到達率だけを理由に協働が勝つよう難化しない。この課題は、不要なreviewの費用や、
同じ品質へ到達するまでの時間を測る対照にもなり得る。一般的な能力拡張の主課題とは区別する。

## 次の比較をどう具体化するか

次の方式は**同じ初期実装をsoloで点検・修正 vs 別agentの独立review→freshな修正担当**を
第一候補とする。期待するmechanismはerror decorrelationと、Python/Bash/保存状態にまたがる
検査coverage。これはplanning priorであり、現時点で効果を実証した方式ではない。
既存の直列advisor→fresh maker経路を再利用できるため、session継続engineの追加を前提にしない。

この比較で測るのは、review文章の上手さ・指摘件数ではなく、固定された要求違反の修正と退行。
soloにも同じ公開toolと全体予算を与える。review側の時間・全usage・受渡し・修正を合算する。
初期実装が正しい対照も含め、不要なreviewや不要な変更を有利に数えない。

次の実装単位と終了条件は以下。

1. F04の公開要求を基に別task IDで、通常再実行、引数境界、旧readerの保全を明示した課題を作る。
   学習用・確認用の入力、初期実装、公開check、固定評価の範囲を先に分ける。
2. 今回の正解/別実装/欠陥probeを校正に使い、開発側の成果を別containerで評価する。
   監査sourceや校正用の正解をdeveloperへmountせず、旧runner/oracleは差し替えない。
3. 同じ仕様の正しい初期実装を含む有限比較について、全予算・順序・停止・採否条件を固定する。
   初期実装の診断にhidden scoreを使わせず、修正前後の動作と全費用を記録する。
4. 疑似providerで両条件を確認してから、固定した範囲で実比較する。

現時点のadmissionは「別版でのreview→修正比較の校正へ進む」。live条件は未固定であり、
旧4/4の品質guardも解除しない。相談全般や複数実装の有効性を、このreview候補の選択で済ませない。

## 再現と上限

```bash
PYTHONDONTWRITEBYTECODE=1 python3 experiments/development-harness/selection/audit_f04_lifecycle.py \
  --output /tmp/new-f04-lifecycle-audit.json
PYTHONDONTWRITEBYTECODE=1 F04_AUDIT_IMAGE=sha256:c7f904a12d7e7c63a2c7e46bc6654c8304b497a2836ecb08fb5bea0118f679ea \
  python3 -m unittest scripts/test-f04-lifecycle-audit.py
```

実Dockerを含む7テストが合格。Dockerはnetworkなし・rootfs/repository read-only、認証mountなし。
一時workspaceをtmpfsへ作り、固有名の所有containerを`finally`で削除し、終了を確認する。
既存runや監査出力は上書きしない。

9候補・4probeは今回確認する欠陥と別解から導いたcoverage集合。
各command 5秒、旧各check 30秒、Docker create/start/cleanup 30/120/30秒はこのprovider-free監査のcost cap。
`unmodified_task_admitted: false`は要求と旧oracleの不一致に基づくhard guard。
範囲はこの監査、ownerはprimary/integrator。未検出の欠陥、正当な別解、環境由来のtimeout、
公開要求やsourceの変更が見直し根拠。probe合格も数値上限も運用defaultや協働の改善率にはしない。
