# F06-S-PY-001: oracle and quality rubric

## Quality-pass rule

public checksと以下のhidden criterionをcriterion-levelで別々に記録する。全criterion passだけをこのcase revisionのquality-passとし、partialをpassへ丸めない。offline score時間はuser waitへ足さない。

| Check ID | Criterion | Observable signal |
| --- | --- | --- |
| `test-kills-upper-bound` | Suite rejects a mutant accepting 65536. | mutant run fails for the intended assertion |
| `test-kills-bool` | Suite rejects bool-as-int acceptance. | boolean mutant is killed |
| `test-kills-whitespace` | Suite rejects whitespace-only coercion. | whitespace mutant is killed |
| `test-kills-float` | Suite rejects silent float coercion. | float mutant is killed |
| `test-production-untouched` | Production source remains byte-identical. | base digest matches |

## Negative calibration set

次のplausible-but-wrong artifactをそれぞれ少なくとも一つのcriterionがrejectしなければ、rubricは識別力不足として実装を差し戻す。

- A test suite covering only 0 and 65535 but not adjacent invalid values.
- Editing `ports.py` to special-case the public tests.
- Tests that inspect function source for constants instead of behavior.

## Anti-gaming checks

- keyword存在だけでpassさせず、path、claim ID、command result、state transitionなどfixture固有の関係を検査する。
- structured artifactとhuman-readable artifactがある場合は相互整合を検査する。
- production/test/documentの削除、skip、常時success、固定出力を検出する。
- unsupported claimや過剰findingを数えられるfamilyではfalse-positive criterionを独立して持つ。

## Rubric boundary

Mutation kills measure specified contract sensitivity, not general test maintainability or unseen production defects.

このrubricはhuman preferenceの代用ではない。観測可能なcontract coverageだけをqualityとして記録し、usefulnessやeleganceを推測しない。
