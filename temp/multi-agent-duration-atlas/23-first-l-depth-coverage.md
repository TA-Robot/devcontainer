# First L-case depth coverage

実施日: 2026-08-27

Status: `F04-L-PYBASH-001`でGrok 4.6のmedium/high/xhigh/max候補、Solのmedium/high/xhigh/max/ultra候補を1回ずつ直列観測。accepted 8 runは全てcriterion 4/4。Grok maxは明示reject。Claude blockはOAuth再ログイン待ち。

## Case

`F04-L-PYBASH-001`はpersistent queueをPython storage、Python CLI、Bash entrypointにまたがって完成させるdeterministic fixtureです。

- cross-process persistent state
- Python / Bash boundary
- idempotent ack、unknown ID byte preservation、malformed JSON preservation
- fresh-process lifecycle
- public unit + lifecycle checks、hidden atomicity + wrapper checks

Lは実行時間ではなく、この構造で事前分類しています。

## Canonical observations

各rowは1 runだけです。provider timeはagent process terminalまで、user-result timeはisolated evaluator完了までです。

| Provider | Requested effort | Applied evidence | Provider time | User-result time | Output / reasoning tokens | Score |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| Grok 4.6 | medium | applied medium | 81,665.238 ms | 86,564.216 ms | 5,888 / unavailable | 4/4 |
| Grok 4.6 | high | applied high | 94,792.704 ms | 100,239.970 ms | 6,570 / unavailable | 4/4 |
| Grok 4.6 | xhigh | applied xhigh | 176,225.981 ms | 181,362.993 ms | 12,486 / unavailable | 4/4 |
| Grok 4.6 | max | rejected | 2,287.907 ms | result unavailable | 0 / 0 | unavailable |
| Sol | medium | requested / unknown | 92,203.593 ms | 96,938.053 ms | 3,888 / 1,266 | 4/4 |
| Sol | high | requested / unknown | 130,193.781 ms | 134,933.673 ms | 4,587 / 1,583 | 4/4 |
| Sol | xhigh | requested / unknown | 131,816.021 ms | 136,639.170 ms | 5,609 / 2,299 | 4/4 |
| Sol | max | requested / unknown | 230,175.920 ms | 235,214.495 ms | 7,780 / 3,834 | 4/4 |
| Sol | ultra | requested / unknown | 563,592.865 ms | 568,271.833 ms | 11,565 / 6,102 | 4/4 |

Grokのinput / cached inputは順にmedium `21,952 / 15,232`、high `15,755 / 32,384`、xhigh `49,302 / 102,656`。Solはmedium `68,775 / 40,960`、high `72,080 / 50,944`、xhigh `85,963 / 65,024`、max `98,354 / 74,240`、ultra `531,423 / 463,872`でした。token taxonomyはprovider固有なのでcross-provider合算や単純比較をしません。

## What this does and does not show

このcoverage passでは、accepted settingの品質は全て4/4で飽和しました。したがって、このcase/rubricから「xhigh/max/ultraの方が高品質」とは言えません。

同時に、深度候補を外してよいわけでもありません。実際に含めたことで次が判明しました。

- Grok 4.6はmedium/high/xhighを受理し、session metadataでも同値を確認できた。
- Grok 4.6のmaxはCLI help上では事前判別できず、実runで初めてunsupportedと確定した。
- Solはmaxだけでなくprovider-native extensionのultra requestもterminalまで進んだ。
- Solのhighとxhighは単発時間が近く、effort labelから時間倍率を決め打ちできない。
- Sol ultraはこのrunでmediumの約6.1倍のprovider時間になり、input/cached inputも大きく増えた。

ただし、実行順は浅い方から深い方への1 blockで、provider load、時刻、cache driftとeffortが交絡しています。比率を一般化しません。全て同一qualityだったため、速かったmediumをglobal defaultやwinnerにも昇格しません。

このL fixtureは「全要件を満たせるか」の比較には使えましたが、accepted depth間の品質差を識別するoracleとしては飽和しています。次のquality studyでは、仕様曖昧化ではなく、より長いfailure distance、複数の妥当な実装trade-off、adversarial edge、review/architecture evidenceなど、深い検討が観測可能な別case familyを追加する必要があります。

## Rejected-setting instrumentation correction

最初のGrok max attempt `grok-f04-l-46-max-20260827-r01`はproviderがrejectした一方、pre-run `summary.json`に残った`high`を初版parserがappliedと誤認しました。このrecordは**instrumentation-invalid**で、canonical rowへ入れません。

修正内容:

- provider rejectionをsession metadataより優先
- `generation-setting-rejected`をoutcome failure classへ追加
- generation settingを`requested=max / status=rejected`として記録
- pre-run/default metadataをsilent coercion evidenceへ使わない

r02はprovider rejection後に旧schemaが新failure classを受理できず、record finalizeに失敗したunrecorded calibration attemptです。schema修正後のcanonical rejectionは`grok-f04-l-46-max-20260827-r03`です。retryによるtask成功を作る目的ではなく、instrumentation contract修正の有限calibrationとして区別します。

## Evidence files

Canonical accepted/rejected rows:

- `evidence/wave-3/grok-f04-l-46-medium-20260827-r01.json`
- `evidence/wave-3/grok-f04-l-46-high-20260827-r01.json`
- `evidence/wave-3/grok-f04-l-46-xhigh-20260827-r01.json`
- `evidence/wave-3/grok-f04-l-46-max-20260827-r03.json`
- `evidence/wave-3/codex-f04-l-sol-medium-20260827-r01.json`
- `evidence/wave-3/codex-f04-l-sol-high-20260827-r01.json`
- `evidence/wave-3/codex-f04-l-sol-xhigh-20260827-r01.json`
- `evidence/wave-3/codex-f04-l-sol-max-20260827-r01.json`
- `evidence/wave-3/codex-f04-l-sol-ultra-20260827-r01.json`

Calibration-invalid evidenceは`evidence/wave-3/README.md`に説明し、machine-readableなcanonical/exclusion setは`wave-3-disposition.json`に固定します。raw reporterは自動集計を行わないため、将来の集計/skill層がこのdispositionを適用します。

## Next block

1. Claudeを`claude auth login`後に別blockでmedium/high/xhigh/max coverageする。
2. 同じL caseを反復するならeffort orderをcounterbalanceし、provider/time driftと深度効果を分離する。
3. 現rubricが飽和したため、反復数を機械的に増やす前にdepth-sensitiveな別case/rubricを設計する。
4. M caseはsize curve用に保持し、L depth差を埋めるための代理にはしない。
5. raw rowsはsample inventoryとして提示し、project-local utilityやdeadlineなしにrouting ruleへ変換しない。

反復回数や終了回数は固定defaultにしません。coverage、variance、oracle discrimination、runtime costの観測から次blockごとに決めます。
