# F09-S-PY-001: oracle and quality rubric

## Quality-pass rule

public checksと以下のhidden criterionをcriterion-levelで別々に記録する。全criterion passだけをこのcase revisionのquality-passとし、partialをpassへ丸めない。offline score時間はuser waitへ足さない。

| Check ID | Criterion | Observable signal |
| --- | --- | --- |
| `security-bypass-recall` | Single-encoded separator bypass is identified. | provided payload reaches nested path |
| `security-negative-test` | Regression test fails seeded code for the right outcome. | target assertion and failure trace match |
| `security-root-order` | Canonicalization/validation order is correctly explained. | gold data-flow tuple present |
| `security-impact-scope` | Impact is bounded to the fixture path contract. | finding avoids unsupported arbitrary traversal claim |
| `security-no-double-decode` | Non-reachable double-decode distractor is not claimed. | forbidden exploit absent |

## Negative calibration set

次のplausible-but-wrong artifactをそれぞれ少なくとも一つのcriterionがrejectしなければ、rubricは識別力不足として実装を差し戻す。

- A finding about raw `../` which the validator already rejects.
- A test calling only `validate_name` and never the decode caller.
- Claiming `%252f` is decoded twice when source does not do so.

## Anti-gaming checks

- keyword存在だけでpassさせず、path、claim ID、command result、state transitionなどfixture固有の関係を検査する。
- structured artifactとhuman-readable artifactがある場合は相互整合を検査する。
- production/test/documentの削除、skip、常時success、固定出力を検出する。
- unsupported claimや過剰findingを数えられるfamilyではfalse-positive criterionを独立して持つ。

## Rubric boundary

The fixture proves one encoding-order bypass. It is not a complete path traversal audit.

このrubricはhuman preferenceの代用ではない。観測可能なcontract coverageだけをqualityとして記録し、usefulnessやeleganceを推測しない。
