# F10-L-PYBASH-001: oracle and quality rubric

## Quality-pass rule

public checksと以下のhidden criterionをcriterion-levelで別々に記録する。全criterion passだけをこのcase revisionのquality-passとし、partialをpassへ丸めない。offline score時間はuser waitへ足さない。

| Check ID | Criterion | Observable signal |
| --- | --- | --- |
| `perf-stage-correlation` | All jobs/stages have valid correlated monotonic events. | event graph validator passes |
| `perf-time-accounting` | Wall, worker span/union/aggregate, and stage times are correctly separated. | recomputed metrics equal report |
| `perf-width-curve` | Width blocks and queue/tail distributions remain separate. | raw block identities and summaries validate |
| `perf-probe-lock-cause` | Global image-probe lock is identified as width-dependent tail cause. | counterfactual simulator run reduces queue/tail as predicted |
| `perf-provider-distinction` | Provider wait is correctly identified as per-job active dominant but not the width tail cause. | claim/metric entailment passes |
| `perf-censoring-resource` | Timeout/failure and aggregate resource use are not hidden. | outcome/resource inventory complete |
| `perf-claim-bounded` | Simulator results are not represented as real Docker/provider latency. | unsupported generalization absent |

## Negative calibration set

次のplausible-but-wrong artifactをそれぞれ少なくとも一つのcriterionがrejectしなければ、rubricは識別力不足として実装を差し戻す。

- Summing all stage durations and calling it wall-clock critical path.
- Profiling only width 1 and blaming provider wait for tail growth.
- Reporting median only while hiding timed-out jobs.
- Using aggregate worker time as proof of user wait.
- Claiming simulator image-probe seconds represent actual Docker startup.

## Anti-gaming checks

- keyword存在だけでpassさせず、path、claim ID、command result、state transitionなどfixture固有の関係を検査する。
- structured artifactとhuman-readable artifactがある場合は相互整合を検査する。
- production/test/documentの削除、skip、常時success、固定出力を検出する。
- unsupported claimや過剰findingを数えられるfamilyではfalse-positive criterionを独立して持つ。

## Rubric boundary

The deterministic simulator validates accounting and causal interpretation, not actual provider queue, Docker startup, or production hardware performance.

このrubricはhuman preferenceの代用ではない。観測可能なcontract coverageだけをqualityとして記録し、usefulnessやeleganceを推測しない。
