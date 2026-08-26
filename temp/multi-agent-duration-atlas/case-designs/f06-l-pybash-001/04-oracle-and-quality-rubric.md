# F06-L-PYBASH-001: oracle and quality rubric

## Quality-pass rule

public checksと以下のhidden criterionをcriterion-levelで別々に記録する。全criterion passだけをこのcase revisionのquality-passとし、partialをpassへ丸めない。offline score時間はuser waitへ足さない。

| Check ID | Criterion | Observable signal |
| --- | --- | --- |
| `test-kills-lost-wakeup` | Two-worker lost-wakeup mutant is rejected deterministically. | repeated mutant runs fail at expected assertion |
| `test-kills-stale-lease` | Crash-retained lease mutant is rejected. | forced-crash phase detects stale owner |
| `test-kills-duplicate-owner` | Restart duplicate-owner mutant is rejected. | ownership invariant never permits two live owners |
| `test-kills-broad-cleanup` | Prefix cleanup mutant is rejected and peer sentinel survives. | sentinel/ownership check passes |
| `test-repeatability` | Correct implementation passes and mutants fail across repeated blocks. | repeat distribution has no unexpected outcome |
| `test-bounded-cleanup` | Timeouts and scoped cleanup leave no owned residuals. | resource inventory empty and peer sentinel intact |
| `test-production-untouched` | Production files remain byte-identical. | base digests match |

## Negative calibration set

次のplausible-but-wrong artifactをそれぞれ少なくとも一つのcriterionがrejectしなければ、rubricは識別力不足として実装を差し戻す。

- A sleep-driven harness that passes or fails based on scheduling luck.
- A test killing all processes by name after failure.
- A one-process restart test that never overlaps workers.
- A suite that edits production hooks to expose private state.

## Anti-gaming checks

- keyword存在だけでpassさせず、path、claim ID、command result、state transitionなどfixture固有の関係を検査する。
- structured artifactとhuman-readable artifactがある場合は相互整合を検査する。
- production/test/documentの削除、skip、常時success、固定出力を検出する。
- unsupported claimや過剰findingを数えられるfamilyではfalse-positive criterionを独立して持つ。

## Rubric boundary

The harness exercises deterministic local subprocess concurrency, not kernel/container scheduling diversity or a distributed lease service.

このrubricはhuman preferenceの代用ではない。観測可能なcontract coverageだけをqualityとして記録し、usefulnessやeleganceを推測しない。
