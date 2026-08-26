# F08-M-MDJSON-001: oracle and quality rubric

## Quality-pass rule

public checksと以下のhidden criterionをcriterion-levelで別々に記録する。全criterion passだけをこのcase revisionのquality-passとし、partialをpassへ丸めない。offline score時間はuser waitへ足さない。

| Check ID | Criterion | Observable signal |
| --- | --- | --- |
| `design-invariant-coverage` | All declared invariants are represented and testable. | invariant ID/transition coverage complete |
| `design-state-ownership` | Durable and ephemeral state have non-conflicting owners. | ownership matrix has no gap/conflict |
| `design-failure-transitions` | Restart/cancel/retry/timeout traces reach valid states. | simulator hidden scenarios pass |
| `design-option-counterexamples` | Each rejected option has a reproducing failure trace. | counterexample scenario links execute |
| `design-migration-observability` | Migration ordering and required signals are actionable. | required phase/signal tuples present |
| `design-unknown-honesty` | Evidence gaps remain unknown and are decision-relevant. | no unsupported closed claims in calibrated set |

## Negative calibration set

次のplausible-but-wrong artifactをそれぞれ少なくとも一つのcriterionがrejectしなければ、rubricは識別力不足として実装を差し戻す。

- Retry owned independently by scheduler and supervisor.
- Cancellation held only in process memory.
- A component diagram with no state transitions.
- A proposal that declares exactly-once execution without idempotency evidence.
- Option rejection based only on preference words.

## Anti-gaming checks

- keyword存在だけでpassさせず、path、claim ID、command result、state transitionなどfixture固有の関係を検査する。
- structured artifactとhuman-readable artifactがある場合は相互整合を検査する。
- production/test/documentの削除、skip、常時success、固定出力を検出する。
- unsupported claimや過剰findingを数えられるfamilyではfalse-positive criterionを独立して持つ。

## Rubric boundary

The calibrated simulator/rubric measures fixture constraint coverage and failure consistency, not subjective architecture elegance or real distributed-system behavior.

このrubricはhuman preferenceの代用ではない。観測可能なcontract coverageだけをqualityとして記録し、usefulnessやeleganceを推測しない。
