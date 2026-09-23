# F10-M-PY-001: oracle and quality rubric

## Quality-pass rule

public checksと以下のhidden criterionをcriterion-levelで別々に記録する。全criterion passだけをこのcase revisionのquality-passとし、partialをpassへ丸めない。offline score時間はuser waitへ足さない。

| Check ID | Criterion | Observable signal |
| --- | --- | --- |
| `perf-instrumentation-consistency` | Open/byte/decode/cache counters reconcile with workload. | counter invariants pass |
| `perf-cold-warm-separation` | Cold and warm observations are distinct strata. | report/source IDs and order blocks validate |
| `perf-cache-diagnosis` | Mutable/identity cache key and repeated-query dominance are identified. | source/counter/effect chain matches |
| `perf-secondary-costs` | Duplicate decode and reopen costs are measured without overranking. | candidate comparison has evidence for all three |
| `perf-distribution` | Multiple raw observations and bounded summary are present. | run vector and summary recompute |
| `perf-output-equivalence` | Instrumentation does not alter summaries or ledger bytes. | behavior/digest checks pass |

## Negative calibration set

次のplausible-but-wrong artifactをそれぞれ少なくとも一つのcriterionがrejectしなければ、rubricは識別力不足として実装を差し戻す。

- One warm run reported as universal cache performance.
- Timing decorators with no call/byte/cache counters.
- Fixing duplicate decode and declaring victory while cache misses remain.
- Instrumentation that consumes the generator and changes output.
- Pooling cold and warm results into one average.

## Anti-gaming checks

- keyword存在だけでpassさせず、path、claim ID、command result、state transitionなどfixture固有の関係を検査する。
- structured artifactとhuman-readable artifactがある場合は相互整合を検査する。
- production/test/documentの削除、skip、常時success、固定出力を検出する。
- unsupported claimや過剰findingを数えられるfamilyではfalse-positive criterionを独立して持つ。

## Rubric boundary

The fixture provides deterministic counter relations and local timing distributions. It does not generalize absolute performance to other disks, Python builds, or ledger sizes.

このrubricはhuman preferenceの代用ではない。観測可能なcontract coverageだけをqualityとして記録し、usefulnessやeleganceを推測しない。
