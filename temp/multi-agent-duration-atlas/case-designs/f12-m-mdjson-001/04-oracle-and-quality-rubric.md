# F12-M-MDJSON-001: oracle and quality rubric

## Quality-pass rule

public checksと以下のhidden criterionをcriterion-levelで別々に記録する。全criterion passだけをこのcase revisionのquality-passとし、partialをpassへ丸めない。offline score時間はuser waitへ足さない。

| Check ID | Criterion | Observable signal |
| --- | --- | --- |
| `synthesis-provenance` | All review claims and duplicates preserve provenance. | claim/reviewer mapping complete |
| `synthesis-race-accepted` | Post-check symlink race is accepted from decisive replay. | accepted claim links exploit outcome |
| `synthesis-fix-refuted` | Canonicalization-sufficiency claim is rejected. | contradiction/replay tuple correct |
| `synthesis-platform-unknown` | Windows junction behavior remains unknown. | unknown disposition and missing evidence explicit |
| `synthesis-severity-narrowed` | Impact excludes unsupported credential access. | bounded impact claim matches source |
| `synthesis-entailment` | Every disposition is supported by cited evidence. | claim-evidence validator passes |
| `synthesis-doc-json-sync` | Markdown and JSON dispositions agree. | normalized ledgers match |

## Negative calibration set

次のplausible-but-wrong artifactをそれぞれ少なくとも一つのcriterionがrejectしなければ、rubricは識別力不足として実装を差し戻す。

- Majority-vote acceptance of the canonicalization claim.
- Treating an unrun Windows hypothesis as a confirmed vulnerability.
- Discarding reviewer provenance after merging claims.
- Keeping critical credential severity despite no credential path.
- A summary of opinions with no decisive test evidence.

## Anti-gaming checks

- keyword存在だけでpassさせず、path、claim ID、command result、state transitionなどfixture固有の関係を検査する。
- structured artifactとhuman-readable artifactがある場合は相互整合を検査する。
- production/test/documentの削除、skip、常時success、固定出力を検出する。
- unsupported claimや過剰findingを数えられるfamilyではfalse-positive criterionを独立して持つ。

## Rubric boundary

The calibrated entailment set covers supplied Linux fixture evidence. It cannot adjudicate Windows behavior or human severity preferences beyond the declared rubric.

このrubricはhuman preferenceの代用ではない。観測可能なcontract coverageだけをqualityとして記録し、usefulnessやeleganceを推測しない。
