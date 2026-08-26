# F04-L-PYBASH-001: oracle and quality rubric

## Quality-pass rule

public checksと以下のhidden criterionをcriterion-levelで別々に記録する。全criterion passだけをこのcase revisionのquality-passとし、partialをpassへ丸めない。offline score時間はuser waitへ足さない。

| Check ID | Criterion | Observable signal |
| --- | --- | --- |
| `hidden-restart-idempotence` | Fresh-process restart and repeated acknowledgement are durable/idempotent. | hidden lifecycle test passes |
| `hidden-invalid-state-integrity` | Unknown and malformed state paths preserve bytes and exact errors. | hidden integrity test passes |

## Negative calibration set

次のplausible-but-wrong artifactをそれぞれ少なくとも一つのcriterionがrejectしなければ、rubricは識別力不足として実装を差し戻す。

- An in-memory acknowledgement that passes one-process unit tests.
- A wrapper using only `$1`.
- A repeated ack that increments the counter again.
- Error handling that rewrites malformed state into a default object.

## Anti-gaming checks

- keyword存在だけでpassさせず、path、claim ID、command result、state transitionなどfixture固有の関係を検査する。
- structured artifactとhuman-readable artifactがある場合は相互整合を検査する。
- production/test/documentの削除、skip、常時success、固定出力を検出する。
- unsupported claimや過剰findingを数えられるfamilyではfalse-positive criterionを独立して持つ。

## Rubric boundary

The current 4/4 effective rubric saturated from medium through ultra in first coverage. A revisioned evaluator must split lifecycle subcriteria and negative mutants before using this case for deeper-quality claims.

このrubricはhuman preferenceの代用ではない。観測可能なcontract coverageだけをqualityとして記録し、usefulnessやeleganceを推測しない。
