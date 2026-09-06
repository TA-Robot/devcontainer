# 同じ相談能力への情報介入

`queue-conditional-review-v1`は、両条件が同じ有限な相談経路を持つ比較入口。
[固定protocol](protocol.md)・[live config](live-config.json)・[検証証跡](validation.json)を使う。
旧v1の常時reviewとsoloの値を、今回のcontrolとして流用しない。

2026-09-07に[固定した1組の実比較](result.md)を完了した。両側ともsubmit・4/4。
情報ありは時間10.176%・input13.615%減だが、時間基準を約0.168秒だけ満たす1組の観測であり、
独立確認候補に留める。今回のconfirmationと初回protocolは使用済み。追加の確認には新しいprotocolを固定する。

両条件はまずdrafterを実行し、`review-request.json`のsubmit/consultで分岐する。
submitならそのまま終了。consultなら、停止・保全した現在の実装と質問をreviewerへ渡し、
同じ実装と助言をfresh final makerへ渡す。後続を呼ばないときはそのprovider/containerを作らない。
controlは[共通案内](baseline-guide.md)、informedはそれに[前回の範囲付き実測と起動案内](evidence-guide.md)を追加する。
reviewerとfinal makerのrole promptは両条件で同じ。

## 境界と観測

stageの公開contractは[stage-contract.md](stage-contract.md)。元のqueue実装・4つの動作評価は変更しない。
新しい入力にはrouting用の追加contractを明示する。requestはdrafter、adviceはreviewerだけが書ける。
引継ぎは固定入力と許可された実装/testだけを投影し、前stageのGit設定やrequestファイルをコピーしない。
controllerの新しいGit状態で開始し、source hashをactorごとに保持する。

条件時間はcontainer起動・probe・入力の受渡し・自己調査・選択・任意のreview・最終化・停止回収を含む。
後続の最低枠は開始前に予約する。未知usage、無効なrequest/advice、source違反、予算不足では後続を止める。
レビュー要求、dispatch試行、実行が記録されたreviewer、最終artifactを区別する。
自己検証の実施や質問の必要性・助言の意味上の採用は、requestの自己申告だけで保証しない。

初期状態、draft、最終成果は全員停止後の外部評価で観測する（初期状態だけはprovider開始前）。
採点を次stageへ渡さない。submit時のdraftと最終成果は同じartifactなので再採点を重ねない。
評価はv1の認証/networkなしの別containerを使い、candidate codeをhostへimport/実行しない。
環境の原記録とactor間のfingerprint照合、全停止・cleanup、input/cache/output、欠測を自動保存する。

## 検証

```bash
PYTHONDONTWRITEBYTECODE=1 CONDITIONAL_REVIEW_IMAGE=sha256:c7f904a12d7e7c63a2c7e46bc6654c8304b497a2836ecb08fb5bea0118f679ea \
  python3 -m unittest scripts/test-conditional-review.py
```

6テストが合格し、実Dockerと疑似providerでsubmit、consult、unknown-usage、invalid-request、invalid-adviceを確認。
consultでは修正途中のmarkerと質問がreviewへ届き、同じ実装と助言がfinalへ届くこと、
draftの動作不合格からfinalの合格へ変わることを検査した。
submitは1participant、consultは3participantで、両情報条件の能力と費用集計を確認した。
この人数は有限経路の内訳であり、成果や推奨人数ではない。
旧v1で校正した2正解・7欠陥のgrader sourceが不変であることもhashで確認した。

liveはconfigの完全一致と現在のsourceに一致する検証記録を要求する。
再開・上書き・fallbackは提供しない。1組の上限と追加run禁止はprotocolに従う。
別output dirをまたぐ全体実行回数の台帳は未実装なので、controllerが固定した一組だけを実行する。

集計は`conditional_report.py --run PRIVATE_RUN --output NEW_REPORT`で再現できる。
停止・usage・動作品質が不明なら品質付き時間比を出さない。分岐が同じでも観測から除外しない。
guideの一般既定化・一般的な協働効果は、1組の結果から成立した扱いにしない。
