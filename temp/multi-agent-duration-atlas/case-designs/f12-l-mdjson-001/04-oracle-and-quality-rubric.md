# F12-L-MDJSON-001: oracle and quality rubric

## Quality-pass rule

public checksと以下のhidden criterionをcriterion-levelで別々に記録する。全criterion passだけをこのcase revisionのquality-passとし、partialをpassへ丸めない。offline score時間はuser waitへ足さない。

| Check ID | Criterion | Observable signal |
| --- | --- | --- |
| `synthesis-claim-provenance` | Material proposal/evidence claims preserve provenance and condition. | claim/source/workload graph complete |
| `synthesis-metric-integrity` | Distributions, censoring, and invalid samples are represented correctly. | raw recomputation and exclusion reasons match |
| `synthesis-incident-security` | Incident and security evidence change option disposition/controls. | required decisive-evidence edges present |
| `synthesis-migration-operations` | Migration, ownership, operations, and rollback constraints are satisfied or explicitly gated. | constraint/gate matrix passes |
| `synthesis-decision-trace` | Selected staged/hybrid decision follows from supported tradeoffs. | decision dependency graph fully entailed |
| `synthesis-alternative-rejection` | Rejected alternatives cite bounded counterexamples rather than preference. | counterexample links execute/query |
| `synthesis-unknown-honesty` | Recovery/provider assumptions without evidence remain unknown. | calibrated unsupported-claim set absent |
| `synthesis-refresh-plan` | Staleness/evidence refresh triggers are concrete. | identity/window/incident trigger set complete |
| `synthesis-doc-json-sync` | Human record and machine graph agree. | normalized decision/claim sets match |

Revision 2 checks semantic evidence coverage rather than exact private identifiers. Any exact vocabulary or minimum evidence set used by the evaluator is present in the visible contract. It accepts both calibrated target designs and rejects only evidence/constraint violations; D→B is not a hidden preferred architecture.

## Negative calibration set

次のplausible-but-wrong artifactをそれぞれ少なくとも一つのcriterionがrejectしなければ、rubricは識別力不足として実装を差し戻す。

- Selecting A from warm median while hiding cold tail/censoring.
- Repeating C's pooled throughput claim despite invalid sample mixing.
- Listing incidents without changing cleanup ownership or rollback gates.
- Selecting B as 'most secure' while ignoring migration deadline constraints.
- A hybrid decision with no phase gates or rollback triggers.
- Closing D's recovery ownership gap by assumption.
- A huge summary that never traces evidence to the final decision.

## Anti-gaming checks

- keyword存在だけでpassさせず、path、claim ID、command result、state transitionなどfixture固有の関係を検査する。
- structured artifactとhuman-readable artifactがある場合は相互整合を検査する。
- production/test/documentの削除、skip、常時success、固定出力を検出する。
- unsupported claimや過剰findingを数えられるfamilyではfalse-positive criterionを独立して持つ。

## Rubric boundary

The calibrated corpus validates entailment, metric integrity, and decision trace against supplied evidence. It does not prove that the resulting design is globally optimal or predict future provider behavior.

At least two materially distinct valid artifacts must full-pass. A single known-good is insufficient evidence that the evaluator accepts the bounded solution space.

このrubricはhuman preferenceの代用ではない。観測可能なcontract coverageだけをqualityとして記録し、usefulnessやeleganceを推測しない。
