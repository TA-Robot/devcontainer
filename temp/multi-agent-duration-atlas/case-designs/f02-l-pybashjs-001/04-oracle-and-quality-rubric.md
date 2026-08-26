# F02-L-PYBASHJS-001: oracle and quality rubric

## Quality-pass rule

public checksと以下のhidden criterionをcriterion-levelで別々に記録する。全criterion passだけをこのcase revisionのquality-passとし、partialをpassへ丸めない。offline score時間はuser waitへ足さない。

| Check ID | Criterion | Observable signal |
| --- | --- | --- |
| `review-redaction-order` | Multiline payload bypass from wrapper through pre-normalization redaction is found. | provided payload reaches persisted sensitive fragment |
| `review-stale-restart` | Restart resurrection of transient working state is found. | restart harness reproduces stale active render |
| `review-cleanup-owner` | Prefix-only cleanup cross-resource deletion is found. | peer resource trigger reproduces deletion target |
| `review-lifecycle-model` | Findings cover input, persistence, restart, and cleanup ownership. | required lifecycle relation set present |
| `review-ranking-impact` | Severity and impact reflect credential/data/resource risks. | gold rank constraints satisfied |
| `review-evidence-integrity` | Cross-language citations and reproductions resolve. | reference/command validator passes |
| `review-false-positive` | CSS/comment distractors are not blocking findings. | forbidden categories absent |

## Negative calibration set

次のplausible-but-wrong artifactをそれぞれ少なくとも一つのcriterionがrejectしなければ、rubricは識別力不足として実装を差し戻す。

- A Python-only review that misses wrapper input constraints.
- A review finding stale state but not the restart condition.
- A cleanup warning with no peer-prefix reproduction.
- A long review that flags CSS positioning as a lifecycle blocker.

## Anti-gaming checks

- keyword存在だけでpassさせず、path、claim ID、command result、state transitionなどfixture固有の関係を検査する。
- structured artifactとhuman-readable artifactがある場合は相互整合を検査する。
- production/test/documentの削除、skip、常時success、固定出力を検出する。
- unsupported claimや過剰findingを数えられるfamilyではfalse-positive criterionを独立して持つ。

## Rubric boundary

The oracle scores the three seeded lifecycle defects and unsupported blocking findings. It does not claim an exhaustive audit of Bash, Python, JS, or container security.

このrubricはhuman preferenceの代用ではない。観測可能なcontract coverageだけをqualityとして記録し、usefulnessやeleganceを推測しない。
