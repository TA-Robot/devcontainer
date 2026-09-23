# F08-L-MDJSON-001: oracle and quality rubric

## Quality-pass rule

public checksと以下のhidden criterionをcriterion-levelで別々に記録する。全criterion passだけをこのcase revisionのquality-passとし、partialをpassへ丸めない。offline score時間はuser waitへ足さない。

| Check ID | Criterion | Observable signal |
| --- | --- | --- |
| `design-requirement-coverage` | Functional/security/operations requirements are dispositioned with evidence. | requirement mapping complete and entailed |
| `design-topology-ownership` | Jobs, leases, credentials, cleanup, and UI state each have one correct owner. | topology ownership validator passes |
| `design-failure-recovery` | Crash, stale lease, provider loss, and UI disconnect preserve invariants. | hidden lifecycle simulator passes |
| `design-migration-rollback` | Partial migration, abort, resume, and rollback are non-destructive. | fault-cut scenario set passes |
| `design-security-boundaries` | Workspace, provider credential, Docker, and host boundaries have enforceable controls. | threat/control/counterexample set complete |
| `design-observability` | Signals distinguish queue, provider, worker, validation, and recovery states. | diagnostic scenario mapping complete |
| `design-alternative-counterexamples` | Rejected/selected tradeoffs cite decisive evidence and counterexamples. | claim entailment and scenario links pass |
| `design-unknown-honesty` | Unmeasured provider/backend assumptions remain explicit. | calibrated unsupported-claim set absent |

## Negative calibration set

次のplausible-but-wrong artifactをそれぞれ少なくとも一つのcriterionがrejectしなければ、rubricは識別力不足として実装を差し戻す。

- A feature-rich design with no migration/rollback path.
- A topology where UI state is the source of job truth.
- Central credential storage without rotation/least-privilege ownership.
- Recovery by unbounded daemon retry.
- A selected option justified by nominal throughput while ignoring incident evidence.
- A complete-looking record that silently closes unmeasured provider guarantees.

## Anti-gaming checks

- keyword存在だけでpassさせず、path、claim ID、command result、state transitionなどfixture固有の関係を検査する。
- structured artifactとhuman-readable artifactがある場合は相互整合を検査する。
- production/test/documentの削除、skip、常時success、固定出力を検出する。
- unsupported claimや過剰findingを数えられるfamilyではfalse-positive criterionを独立して持つ。

## Rubric boundary

The calibrated fixture tests consistency against supplied constraints/scenarios. It cannot prove production scalability, unknown provider behavior, or human preference among designs that tie on measured criteria.

このrubricはhuman preferenceの代用ではない。観測可能なcontract coverageだけをqualityとして記録し、usefulnessやeleganceを推測しない。
