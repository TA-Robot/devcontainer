# F02-S-PY-001: oracle and quality rubric

## Quality-pass rule

public checksと以下のhidden criterionをcriterion-levelで別々に記録する。全criterion passだけをこのcase revisionのquality-passとし、partialをpassへ丸めない。offline score時間はuser waitへ足さない。

| Check ID | Criterion | Observable signal |
| --- | --- | --- |
| `review-seeded-recall` | Seeded containment defect is found. | finding category and changed symbol match gold |
| `review-trigger-valid` | Counterexample actually bypasses the helper. | provided paths reproduce acceptance outside root |
| `review-impact-severity` | Impact and severity are consistent with workspace escape. | severity at least high with write/read escape rationale |
| `review-evidence-line` | Finding cites the changed helper and diff hunk. | path/symbol/hunk resolve |
| `review-false-positive` | No unsupported blocking findings are added. | all additional high/medium findings map to seeded set |

## Negative calibration set

次のplausible-but-wrong artifactをそれぞれ少なくとも一つのcriterionがrejectしなければ、rubricは識別力不足として実装を差し戻す。

- A review saying only 'use pathlib' with no bypass trigger.
- A finding against an unchanged `resolve()` call that is actually safe.
- A low-severity style comment presented as the sole result.

## Anti-gaming checks

- keyword存在だけでpassさせず、path、claim ID、command result、state transitionなどfixture固有の関係を検査する。
- structured artifactとhuman-readable artifactがある場合は相互整合を検査する。
- production/test/documentの削除、skip、常時success、固定出力を検出する。
- unsupported claimや過剰findingを数えられるfamilyではfalse-positive criterionを独立して持つ。

## Rubric boundary

False positives are checked only for blocking findings. The evaluator does not score writing style or harmless low-severity suggestions.

このrubricはhuman preferenceの代用ではない。観測可能なcontract coverageだけをqualityとして記録し、usefulnessやeleganceを推測しない。
