# F11-L-BASHDOCKER-001: oracle and quality rubric

## Quality-pass rule

public checksと以下のhidden criterionをcriterion-levelで別々に記録する。全criterion passだけをこのcase revisionのquality-passとし、partialをpassへ丸めない。offline score時間はuser waitへ足さない。

| Check ID | Criterion | Observable signal |
| --- | --- | --- |
| `ops-lifecycle-ownership` | Host/container/volume/extension stages and markers have correct owners/order. | lifecycle/owner graph passes |
| `ops-migration-fault-cuts` | Every migration cut preserves a recoverable valid source. | fault matrix never loses canonical v1/v2 export |
| `ops-reopen-resume` | Reopen resumes interrupted stages idempotently. | multi-reopen scenarios converge once |
| `ops-marker-verification` | Stale/mismatched host and extension markers trigger bounded repair. | marker/version matrix passes |
| `ops-rollback-export` | Rollback/export is non-destructive and replayable. | digest/round-trip checks pass |
| `ops-recovery-doc` | Diagnosis, recovery, owners, and verification commands match implementation. | doc replay/fact checks pass |
| `ops-residual-inventory` | Owned temporary resources are cleaned; peer/persistent sentinels survive. | post-scenario inventory passes |

## Negative calibration set

次のplausible-but-wrong artifactをそれぞれ少なくとも一つのcriterionがrejectしなければ、rubricは識別力不足として実装を差し戻す。

- Setting schema v2 before writing converted data.
- Deleting the persistent volume after migration failure.
- Boolean ready markers with no artifact/version binding.
- Repairing container state while stale host marker still suppresses extension install.
- A recovery doc that rebuilds everything but never exports original state.

## Anti-gaming checks

- keyword存在だけでpassさせず、path、claim ID、command result、state transitionなどfixture固有の関係を検査する。
- structured artifactとhuman-readable artifactがある場合は相互整合を検査する。
- production/test/documentの削除、skip、常時success、固定出力を検出する。
- unsupported claimや過剰findingを数えられるfamilyではfalse-positive criterionを独立して持つ。

## Rubric boundary

The harness simulates rebuild/reopen boundaries and persistence logic; it does not time a real image build, VS Code extension host, or host package manager.

このrubricはhuman preferenceの代用ではない。観測可能なcontract coverageだけをqualityとして記録し、usefulnessやeleganceを推測しない。
