# F04-S-PY-001: oracle and quality rubric

## Quality-pass rule

public checksと以下のhidden criterionをcriterion-levelで別々に記録する。全criterion passだけをこのcase revisionのquality-passとし、partialをpassへ丸めない。offline score時間はuser waitへ足さない。

| Check ID | Criterion | Observable signal |
| --- | --- | --- |
| `hidden-separator-normalization` | Mixed separator runs and punctuation normalize correctly. | hidden unit test passes |
| `hidden-ascii-filtering` | Non-ASCII and unsupported characters are filtered according to contract. | hidden ASCII test passes |
| `hidden-empty-result` | Inputs with no supported output raise `ValueError`. | empty-result cases pass |
| `hidden-length-bound` | A normalized result over 32 characters is rejected. | boundary test passes |

## Negative calibration set

次のplausible-but-wrong artifactをそれぞれ少なくとも一つのcriterionがrejectしなければ、rubricは識別力不足として実装を差し戻す。

- A chain of `replace()` calls that leaves repeated mixed separators.
- Using `str.isalnum()` without `isascii()`, admitting non-ASCII letters.
- Truncating output to 32 characters instead of rejecting it.

## Anti-gaming checks

- keyword存在だけでpassさせず、path、claim ID、command result、state transitionなどfixture固有の関係を検査する。
- structured artifactとhuman-readable artifactがある場合は相互整合を検査する。
- production/test/documentの削除、skip、常時success、固定出力を検出する。
- unsupported claimや過剰findingを数えられるfamilyではfalse-positive criterionを独立して持つ。

## Rubric boundary

The current four hidden criteria strongly identify contract correctness but have saturated across deeper L runs elsewhere; this S case is primarily a runner/calibration baseline.

このrubricはhuman preferenceの代用ではない。観測可能なcontract coverageだけをqualityとして記録し、usefulnessやeleganceを推測しない。
