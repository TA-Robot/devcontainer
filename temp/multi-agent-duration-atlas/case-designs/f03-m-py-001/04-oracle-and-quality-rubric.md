# F03-M-PY-001: oracle and quality rubric

## Quality-pass rule

public checksと以下のhidden criterionをcriterion-levelで別々に記録する。全criterion passだけをこのcase revisionのquality-passとし、partialをpassへ丸めない。offline score時間はuser waitへ足さない。

| Check ID | Criterion | Observable signal |
| --- | --- | --- |
| `diagnosis-reload-contrast` | Fresh and reload behavior are both measured. | paired command observations recorded |
| `diagnosis-timezone-cause` | Deserializer timezone loss is identified. | gold symbol/field transition present |
| `diagnosis-causal-chain` | Timezone loss is connected to compatibility retention. | ordered model-store-scheduler edges match |
| `diagnosis-regression-layers` | Unit and integration regression tests are specified. | two layer-specific assertions present |
| `diagnosis-distractor-rejected` | Correct scheduler boundary is not blamed. | evidence-backed exclusion recorded |

## Negative calibration set

次のplausible-but-wrong artifactをそれぞれ少なくとも一つのcriterionがrejectしなければ、rubricは識別力不足として実装を差し戻す。

- A diagnosis changing the expiry threshold without comparing reload.
- A timezone observation that never connects to scheduler behavior.
- An integration-only regression proposal that leaves deserialization untested.

## Anti-gaming checks

- keyword存在だけでpassさせず、path、claim ID、command result、state transitionなどfixture固有の関係を検査する。
- structured artifactとhuman-readable artifactがある場合は相互整合を検査する。
- production/test/documentの削除、skip、常時success、固定出力を検出する。
- unsupported claimや過剰findingを数えられるfamilyではfalse-positive criterionを独立して持つ。

## Rubric boundary

The oracle covers this seeded reload chain. It does not judge the best timezone library or require an implementation patch.

このrubricはhuman preferenceの代用ではない。観測可能なcontract coverageだけをqualityとして記録し、usefulnessやeleganceを推測しない。
