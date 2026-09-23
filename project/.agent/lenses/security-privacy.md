# Lens: security and privacy

## Purpose

悪意あるuser、誤操作、漏えいが起きた時に、誰が何を失うかを問う。

## Use when

認証・認可、user入力、file / network境界、個人情報、決済、外部integration、secretを扱う変更。

## Questions

- 信頼境界はどこか。境界を越える入力はすべて検証されているか。
- 認可は操作ごとに確認されているか。他人のdataへ到達できる経路はないか。
- どの個人情報・機微情報を、なぜ、どこに、どれだけの期間保存するか。削除できるか。
- secretはcode、log、error message、client側へ漏れていないか。
- abuse（spam、scraping、大量request、権限昇格）への耐性はあるか。
- 適用される法令・規約・license上の義務はあるか（不明なら`unknown`として問いにする）。

## Return

threat、到達経路、影響、根拠（file / symbol / 再現手順）、最小の緩和策、残るriskを返す。確認済みの脆弱性と、設計上の懸念を分ける。

## Avoid

projectのthreat modelに無関係な一般checklist、exploit手順の詳細化。
