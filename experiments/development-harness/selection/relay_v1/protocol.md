# 保存候補の受入点検に固定事前助言を加える探索 v1

対象は既存lifecycle候補の採用条件・パス境界の分類。標準2候補の受入保留と
異なる欠陥範囲を区別できるかを測る。実装の新規生成・改修・一般的な最良候補選択は測らない。

## 比較と公開情報

1組、solo→consultの固定順序。候補順はimproved→controlを中立IDへ投影し、両条件で同じ。
両方の保存判定でパス境界が不合格。integratedは渡さない。これは既知課題の再利用で、未使用課題ではない。

- solo: 自己点検、独自の公開probe、最終判断。
- consult: 同じ公開入力を独立advisorが1回コード・仕様読解→助言を受けたmakerが自己点検・probe・最終判断。
- makerは最大3回のfresh Codex呼出しと最大2回のprobe。advisorは1回、probeなし。
- 各呼出しへ公開file全文を同じ形式で再提示する。makerには自身の過去の要求・公開stdout・終了codeを全て返す。
  任意の切詰め・private reasoningの受渡し・同一session再開はしない。consultだけがadvisorの最終助言を追加で受け取る。
- 通常のCLI toolsを使わず、JSONのprobe/submit要求をcontrollerへ返す。内蔵toolが空になる固定モデル定義と設定を使う。

追加の生成機会、独立context、情報履歴がまとめて変わる有限ワークフローの比較。
同じ締切で追加総消費を含め使う価値があるかを調べ、独立性だけの因果効果を分離したとは主張しない。
advisorは独立した実験を行う役割ではなく、今回AIが相談の必要性を選ぶ比較でもない。

## 全体予算と停止

各条件600秒・全actor output合計12000。各actor最大240秒、advisor最大120秒/output3000。
advisor後にmakerへ180秒/output4000を予約する。actor開始最低30秒、各cleanup予約30秒。
probeは各30秒、最終判定のprint-only probeは10秒とcleanup30秒を予約する。
候補投影は共通準備、条件時計はprompt生成・actor起動・検証・助言受渡し・提出・停止回収を含む。
input/cache/outputを全呼出しで記録し、金額に換算しない。output上限はturn終了観測で、厳密なin-turn上限ではない。

数値はこの探索のcost cap/予約prior。3回はprobe→feedback→再probe→feedback→提出の最小上限、
advisor1回は今回の固定介入、人数の一般既定ではない。ownerはprimary/integrator。
環境・校正不成立、予算不足、識別力不足なら新版で見直す。

不明usage、tool利用、schema不正、source不一致、timeout、回収未確認、未知actionで停止し、残り条件へ進まない。
新しい出力pathだけを使い、失敗・差なしを保存し、成功までの再試行はしない。
liveはこの1組だけ。設定・全source・能力校正を固定してから開始する。

## 情報境界と評価

actor imageは固定したPython基盤へCodex native binaryとCA証明書だけを追加したもの。
候補・過去の評価・完成CLI・template・host workspace・Docker socketをmountしない。
公開入力はpromptのデータだけ。検証は別の認証/networkなしprobe imageで行う。
固定binary、モデル定義、設定、argvについてfake Responses serverで実際の要求のtools=[]を確認する。
code-mode host無効化の既知startup通知は記録して許容し、それ以外の未知error/toolは保留する。

最終判断はactor原response→抽出content→print-only probe→stdoutのhashで結び、内容を修復・正規化しない。
旧adapterで保存された2群の判定との分類一致だけを評価し、自由文の根拠の真偽はunknown。
評価をactorへ返さず、得点を見た再選択もしない。旧oracle・得点は保持する。

## 採否

主に候補別の分類の不一致・未確認と誤採用を比較し、全時間・全消費を併記する。
consultのみが全分類一致かつ誤採用なしなら別条件の確認候補。1組で一般既定にしない。
両側完全一致なら成果上積みは未確認。僅かな時間差を理由に同課題の追加確認を自動的に優先しない。
欠測・無効なら効果判断を保留。nullだけの提出や、根拠fileの実在を良い選択の証拠にしない。
この比較は配布案内の使い分け改善、継続開発、単体には絶対不可能な成果の証明ではない。
