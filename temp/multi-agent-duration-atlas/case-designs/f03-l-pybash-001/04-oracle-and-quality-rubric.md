# F03-L-PYBASH-001: oracle and quality rubric

## Quality-pass rule

public checksと以下のhidden criterionをcriterion-levelで別々に記録する。全criterion passだけをこのcase revisionのquality-passとし、partialをpassへ丸めない。offline score時間はuser waitへ足さない。

| Check ID | Criterion | Observable signal |
| --- | --- | --- |
| `diagnosis-deterministic-barrier` | Crash window is forced by a synchronization barrier. | reproducer uses barrier event and succeeds repeatedly |
| `diagnosis-ordering-cause` | External effect and durable ack ordering is exact. | gold event-order tuple present |
| `diagnosis-restart-state` | Retained offset explains replay after fresh process start. | journal before/after evidence matches |
| `diagnosis-regression-reliable` | Regression fails seeded code and avoids timing flakiness. | repeated evaluator runs have stable expected result |
| `diagnosis-cleanup-bounded` | Harness timeout and ownership-scoped cleanup are present. | static and runtime cleanup checks pass |
| `diagnosis-semantics-honest` | No unsupported exactly-once guarantee is claimed. | contract language and mitigation scope validate |

## Negative calibration set

次のplausible-but-wrong artifactをそれぞれ少なくとも一つのcriterionがrejectしなければ、rubricは識別力不足として実装を差し戻す。

- A reproducer based on `sleep 0.01` and repeated luck.
- A diagnosis blaming JSON corruption without journal evidence.
- A script using broad process kill or temporary-directory cleanup.
- A proposed exactly-once guarantee with no idempotency boundary.

## Anti-gaming checks

- keyword存在だけでpassさせず、path、claim ID、command result、state transitionなどfixture固有の関係を検査する。
- structured artifactとhuman-readable artifactがある場合は相互整合を検査する。
- production/test/documentの削除、skip、常時success、固定出力を検出する。
- unsupported claimや過剰findingを数えられるfamilyではfalse-positive criterionを独立して持つ。

## Rubric boundary

The fixture proves one crash window and at-least-once replay. It does not establish real distributed-system exactly-once behavior or measure external provider latency.

このrubricはhuman preferenceの代用ではない。観測可能なcontract coverageだけをqualityとして記録し、usefulnessやeleganceを推測しない。
