# F08-S-MDJSON-001: oracle and quality rubric

## Quality-pass rule

public checksと以下のhidden criterionをcriterion-levelで別々に記録する。全criterion passだけをこのcase revisionのquality-passとし、partialをpassへ丸めない。offline score時間はuser waitへ足さない。

| Check ID | Criterion | Observable signal |
| --- | --- | --- |
| `design-constraint-coverage` | All supplied constraints receive evidence-backed disposition. | constraint ID coverage complete |
| `design-counterexamples` | Both raw options are challenged by fixture-valid counterexamples. | counterexample runners reproduce stated failure |
| `design-selected-contract` | Chosen API addresses deletion and request isolation. | required invariant/operation tuple present |
| `design-evidence-entailment` | Claims are entailed by callers/constraints. | claim-source validator passes |
| `design-doc-json-sync` | Markdown and structured decision agree. | normalized claim sets match |

## Negative calibration set

次のplausible-but-wrong artifactをそれぞれ少なくとも一つのcriterionがrejectしなければ、rubricは識別力不足として実装を差し戻す。

- Choosing the builder for extensibility while ignoring cross-request state.
- Choosing pure merge without a deletion semantic.
- A pros/cons list with no decision or counterexample.
- Inventing a performance requirement absent from evidence.

## Anti-gaming checks

- keyword存在だけでpassさせず、path、claim ID、command result、state transitionなどfixture固有の関係を検査する。
- structured artifactとhuman-readable artifactがある場合は相互整合を検査する。
- production/test/documentの削除、skip、常時success、固定出力を検出する。
- unsupported claimや過剰findingを数えられるfamilyではfalse-positive criterionを独立して持つ。

## Rubric boundary

The structured evaluator scores constraint/evidence/counterexample coverage. It does not claim the selected API is universally best beyond fixture constraints.

このrubricはhuman preferenceの代用ではない。観測可能なcontract coverageだけをqualityとして記録し、usefulnessやeleganceを推測しない。
