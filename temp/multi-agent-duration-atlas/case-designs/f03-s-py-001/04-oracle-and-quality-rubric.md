# F03-S-PY-001: oracle and quality rubric

## Quality-pass rule

public checksと以下のhidden criterionをcriterion-levelで別々に記録する。全criterion passだけをこのcase revisionのquality-passとし、partialをpassへ丸めない。offline score時間はuser waitへ足さない。

| Check ID | Criterion | Observable signal |
| --- | --- | --- |
| `diagnosis-root-cause` | Exact faulty expression and semantic distinction are identified. | symbol/expression/cause tuple matches gold |
| `diagnosis-reproducer` | Minimal explicit-zero input reproduces the failure. | recorded input run yields expected wrong value |
| `diagnosis-regression` | Test proposal covers zero and missing separately. | two required scenarios/assertions present |
| `diagnosis-no-false-cause` | Correct integer conversion is not blamed. | forbidden cause absent |

## Negative calibration set

次のplausible-but-wrong artifactをそれぞれ少なくとも一つのcriterionがrejectしなければ、rubricは識別力不足として実装を差し戻す。

- A diagnosis blaming `int()` without testing explicit zero.
- A proposal that adds only another missing-value test.
- A root-cause statement with no executable reproducer.

## Anti-gaming checks

- keyword存在だけでpassさせず、path、claim ID、command result、state transitionなどfixture固有の関係を検査する。
- structured artifactとhuman-readable artifactがある場合は相互整合を検査する。
- production/test/documentの削除、skip、常時success、固定出力を検出する。
- unsupported claimや過剰findingを数えられるfamilyではfalse-positive criterionを独立して持つ。

## Rubric boundary

The case scores causal diagnosis and regression specificity, not whether the agent supplies a patch or discusses unrelated validation improvements.

このrubricはhuman preferenceの代用ではない。観測可能なcontract coverageだけをqualityとして記録し、usefulnessやeleganceを推測しない。
