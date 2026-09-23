# F07-M-MDBASH-001: oracle and quality rubric

## Quality-pass rule

public checksと以下のhidden criterionをcriterion-levelで別々に記録する。全criterion passだけをこのcase revisionのquality-passとし、partialをpassへ丸めない。offline score時間はuser waitへ足さない。

| Check ID | Criterion | Observable signal |
| --- | --- | --- |
| `runbook-fact-accuracy` | Commands, exit codes, paths, and ownership match source. | fact manifest resolves to source symbols/help |
| `runbook-order-safety` | Diagnosis/evidence/verify precede restore/restart. | manifest dependency graph satisfies safety order |
| `runbook-corrupt-recovery` | Corrupt-state scenario recovers and proves health. | sandbox replay reaches canonical postcondition |
| `runbook-invalid-backup` | Missing/invalid backup stops without mutating evidence. | negative replay preserves byte digests |
| `runbook-owned-restart` | Only the owned service is targeted. | peer sentinel/process remains intact |
| `runbook-doc-manifest-sync` | Markdown commands and structured manifest agree. | normalized extracted commands match |

## Negative calibration set

次のplausible-but-wrong artifactをそれぞれ少なくとも一つのcriterionがrejectしなければ、rubricは識別力不足として実装を差し戻す。

- `rm state.json && restart-all` as the first recovery step.
- A runbook verifying backup after it has overwritten current state.
- Correct prose whose commands contain placeholders absent from the manifest.
- A successful restore with no post-restart health check.

## Anti-gaming checks

- keyword存在だけでpassさせず、path、claim ID、command result、state transitionなどfixture固有の関係を検査する。
- structured artifactとhuman-readable artifactがある場合は相互整合を検査する。
- production/test/documentの削除、skip、常時success、固定出力を検出する。
- unsupported claimや過剰findingを数えられるfamilyではfalse-positive criterionを独立して持つ。

## Rubric boundary

Replay validates the fixture command surface and safety ordering. It does not establish operator comprehension or external service-manager behavior.

このrubricはhuman preferenceの代用ではない。観測可能なcontract coverageだけをqualityとして記録し、usefulnessやeleganceを推測しない。
