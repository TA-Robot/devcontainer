# Conditional review information comparison v1

2026-09-07。M4の最初の限定的な情報介入比較。旧queue v1の初回2組は再実行しない。
live未使用のconfirmation初期実装（ack countと終了statusの欠陥）を使う。
同じfamily内の別欠陥であり、未使用の実プロジェクト一般ではない。

## 比較するもの

両条件とも、drafterが公開check・調査・修正後にsubmitかconsultを選ぶ同じ能力を持つ。
submitならそのartifactで終了。consultなら、現在の実装と具体的質問を独立reviewerへ渡し、
その助言と同じ実装をfresh final makerへ渡す。1回だけの有限な相談で、対話の無制限往復はない。
期待する作用は不足に応じたerror decorrelation/coverageと、不要な呼出しの費用回避。

controlには共通の能力・費用・選択責任を説明するbaseline-guideを渡す。
informedにはそれに加え、旧2組の範囲付き観測と「まず自力検証し、残る具体的な不足を質問する」案内を渡す。
情報だけが介入であり、一方だけ相談を強制・禁止しない。reviewerとfinal makerには同じrole promptを使う。
guideの長さの違いも実際のinput費用に含める。情報量と内容の効果を別々に識別する実験ではない。
両側が同じ選択をしても除外しない。reviewが呼ばれなければ、review経路の実モデル効果は未測定となる。

## 固定した上限と順序

- 1組、各条件1episode。条件順はstudy IDのSHA256先頭byteの偶奇で事前決定し、configへ保存。
- Codex 0.153.0、gpt-6-astra/highを要求。imageはv1と同じsha256:c7f904a12d7e7c63a2c7e46bc6654c8304b497a2836ecb08fb5bea0118f679ea。
- 各条件600秒、全参加者output合計12000。drafter最大300秒、reviewer最大120秒。
- drafter開始最低30秒、reviewer開始最低15秒、final開始最低60秒。
  drafterからreviewerの最低15秒とfinalの120秒を予約し、reviewerからfinalへ120秒を予約。
  outputは後続stageごとに1000を予約。分岐不要でもdraftの最大枠は両条件同じ300秒。
- snapshot16 MiB、request8 KiB、advice16 KiB。stop10秒、capture30秒、window10秒。
- stage用container作成・環境照合・probe・Gitでの受渡しもcondition時間に含める。
  呼ばれないstageのprovider/containerは作らない。初期評価と最終外部評価は別計測。
- 外部評価はv1の認証/networkなしのCLI単位containerを再利用する。
  通常呼出し15秒、全評価の開始枠120秒、削除30秒。sourceとgraderは版を変えない。

数値上限はこの小課題のcost cap。最低予約はplanning prior、情報以外の能力同等性・1回の分岐・
停止/保全・source不変性はhard guard。根拠は前回の64〜185秒の作業量と、後続へ作業枠を残す必要性。
scopeはこの1組、ownerはprimary/integrator。校正失敗・CLI/image/source変更なら実行前に別の固定を行う。
outputはturn終端観測であり、in-turnの厳密なtoken/金額上限ではない。input/cache/outputと欠測を分ける。

## 品質と解釈

初期状態と最終成果にv1と同じ4つの動作検査を使う。consult時のdraftも全員停止後に採点し、
review前後の変化を残すが、採点をrouting・reviewer・makerへ返さない。
request/adviceの内容をLLMで採点しない。意味上の相談必要性・採用はunknown。
requestは共通の構造と実在file参照だけを検査し、一方だけ「十分な不確実性」を主観判定するgateは設けない。

全停止・cleanup・提出枠・完全なinput/output観測・既知の動作品質がなければ改善判断を保留する。
informedだけが全項目へ到達すれば確認候補。両方全合格なら、informedの時間がcontrol比90%以下で、
input/outputが各110%以下の場合だけ改善候補にする。これはこの探索のhypothesisで、有意差の基準ではない。
それ以外は改善未確認。1組でguideを一般既定にせず、採否と失敗/欠測をガイドへ返す。
良い結果まで追加・再試行せず、今回のconfirmationを別名で未使用扱いへ戻さない。

この比較は、常時reviewと条件付きreviewという能力の違いの直接比較ではない。
queue v1の秒数を今回のcontrolへ流用しない。普通の終了・file置換の検査であり、kill・電源断・競合は未測定。
元task/oracle/runner/結果は変更せず、新しい入口とartifact contractとして実装する。
