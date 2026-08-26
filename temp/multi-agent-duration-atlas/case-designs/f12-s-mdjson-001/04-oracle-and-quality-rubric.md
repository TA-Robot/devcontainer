# F12-S-MDJSON-001: oracle and quality rubric

## Quality-pass rule

public checksと以下のhidden criterionをcriterion-levelで別々に記録する。全criterion passだけをこのcase revisionのquality-passとし、partialをpassへ丸めない。offline score時間はuser waitへ足さない。

| Check ID | Criterion | Observable signal |
| --- | --- | --- |
| `synthesis-claim-coverage` | All claims from both analyses are dispositioned. | claim ID set complete |
| `synthesis-agreement` | Argv-forwarding agreement is retained with evidence. | gold agreement/evidence tuple present |
| `synthesis-conflict-adjudication` | Override conflict resolves to explicit conditional semantics. | corrected claim entailed by source branch |
| `synthesis-unsupported` | Logging claim remains unsupported. | unsupported disposition and missing-evidence note present |
| `synthesis-doc-json-sync` | Human and structured artifacts agree. | normalized disposition sets match |

## Negative calibration set

次のplausible-but-wrong artifactをそれぞれ少なくとも一つのcriterionがrejectしなければ、rubricは識別力不足として実装を差し戻す。

- Choosing analysis A wholesale due to more citations.
- Averaging conflict into vague 'may be active' without condition.
- Repeating the logging claim as an agreed fact.
- Adding a migration recommendation absent from all sources.

## Anti-gaming checks

- keyword存在だけでpassさせず、path、claim ID、command result、state transitionなどfixture固有の関係を検査する。
- structured artifactとhuman-readable artifactがある場合は相互整合を検査する。
- production/test/documentの削除、skip、常時success、固定出力を検出する。
- unsupported claimや過剰findingを数えられるfamilyではfalse-positive criterionを独立して持つ。

## Rubric boundary

Entailment is calibrated to supplied sources. It does not judge broader project truth or prose persuasiveness.

このrubricはhuman preferenceの代用ではない。観測可能なcontract coverageだけをqualityとして記録し、usefulnessやeleganceを推測しない。
