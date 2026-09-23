# F02-M-PY-001: oracle and quality rubric

## Quality-pass rule

public checksと以下のhidden criterionをcriterion-levelで別々に記録する。全criterion passだけをこのcase revisionのquality-passとし、partialをpassへ丸めない。offline score時間はuser waitへ足さない。

| Check ID | Criterion | Observable signal |
| --- | --- | --- |
| `review-symlink-recall` | Post-validation symlink escape is identified. | exploit path reproduces outside-root resolution |
| `review-ownership-recall` | Caller-label cleanup collision is identified. | two job IDs reproduce cross-job deletion target |
| `review-interaction` | Combined impact is explicitly reasoned. | finding relation links escaped path and wrong owner |
| `review-ranking` | Severity/order match reachable data loss and isolation impact. | both blocking findings rank above distractors |
| `review-evidence` | Changed symbols and callers are cited accurately. | reference resolver passes |
| `review-false-positive` | Safe logging hunk is not a blocking defect. | forbidden finding absent |

## Negative calibration set

次のplausible-but-wrong artifactをそれぞれ少なくとも一つのcriterionがrejectしなければ、rubricは識別力不足として実装を差し戻す。

- A review that finds symlink escape but misses cleanup ownership.
- Two findings with no explanation of their interaction.
- A review that labels the safe structured logging change as credential leakage without evidence.

## Anti-gaming checks

- keyword存在だけでpassさせず、path、claim ID、command result、state transitionなどfixture固有の関係を検査する。
- structured artifactとhuman-readable artifactがある場合は相互整合を検査する。
- production/test/documentの削除、skip、常時success、固定出力を検出する。
- unsupported claimや過剰findingを数えられるfamilyではfalse-positive criterionを独立して持つ。

## Rubric boundary

The seeded set is exhaustive only for medium-or-higher correctness/security findings in this fixture diff. Minor maintainability comments are ignored.

このrubricはhuman preferenceの代用ではない。観測可能なcontract coverageだけをqualityとして記録し、usefulnessやeleganceを推測しない。
