# F07-L-MDPYBASH-001: oracle and quality rubric

## Quality-pass rule

public checksと以下のhidden criterionをcriterion-levelで別々に記録する。全criterion passだけをこのcase revisionのquality-passとし、partialをpassへ丸めない。offline score時間はuser waitへ足さない。

| Check ID | Criterion | Observable signal |
| --- | --- | --- |
| `docs-current-target-facts` | Current/target backend and compatibility facts match source. | fact-source tuple set complete |
| `docs-migration-order` | Staged rollout and validation order are safe. | phase DAG matches executable lifecycle |
| `docs-rollback-nondestructive` | Rollback export/abort preserve source state. | negative/rollback replay byte checks pass |
| `docs-ownership-consistency` | Runtime, migration, cleanup, and recovery owners agree across files. | cross-document owner matrix consistent |
| `docs-command-replay` | All declared commands work in their stated phase. | scenario replay passes |
| `docs-links-index` | Links, anchors, and manifest references resolve bidirectionally. | link/index validator passes |
| `docs-no-early-removal` | Compatibility removal is gated by stated evidence, not immediate. | required removal preconditions present |

## Negative calibration set

次のplausible-but-wrong artifactをそれぞれ少なくとも一つのcriterionがrejectしなければ、rubricは識別力不足として実装を差し戻す。

- Updating migration docs but leaving architecture default stale.
- A rollback section that mutates or deletes the only new-state copy.
- Correct commands assigned to the wrong lifecycle phase.
- Declaring compatibility removal complete without verification evidence.
- Three individually plausible documents with inconsistent cleanup owner.

## Anti-gaming checks

- keyword存在だけでpassさせず、path、claim ID、command result、state transitionなどfixture固有の関係を検査する。
- structured artifactとhuman-readable artifactがある場合は相互整合を検査する。
- production/test/documentの削除、skip、常時success、固定出力を検出する。
- unsupported claimや過剰findingを数えられるfamilyではfalse-positive criterionを独立して持つ。

## Rubric boundary

Structured facts and sandbox replay make this fixture deterministic, but cannot measure real operator usability or all production environment differences.

このrubricはhuman preferenceの代用ではない。観測可能なcontract coverageだけをqualityとして記録し、usefulnessやeleganceを推測しない。
