# F06-M-PY-001: oracle and quality rubric

## Quality-pass rule

public checksと以下のhidden criterionをcriterion-levelで別々に記録する。全criterion passだけをこのcase revisionのquality-passとし、partialをpassへ丸めない。offline score時間はuser waitへ足さない。

| Check ID | Criterion | Observable signal |
| --- | --- | --- |
| `test-kills-status-mutant` | 400/429/5xx classification mutants are rejected. | status mutant set killed |
| `test-kills-method-mutant` | Non-idempotent retry mutant is rejected. | method mutant killed |
| `test-kills-attempt-mutant` | Off-by-one/max-attempt mutants are rejected. | attempt mutant set killed |
| `test-kills-delay-mutant` | Server-delay and cap mutants are rejected deterministically. | delay mutant set killed with fake clock |
| `test-kills-interaction-mutant` | Critical cross-axis mutant is rejected. | interaction mutant killed |
| `test-production-untouched` | Production and contract docs are byte-identical. | base digests match |

## Negative calibration set

次のplausible-but-wrong artifactをそれぞれ少なくとも一つのcriterionがrejectしなければ、rubricは識別力不足として実装を差し戻す。

- A large table covering each axis independently but no interactions.
- Tests that use real `sleep` and pass nondeterministically.
- Changing policy code or weakening `POLICY.md` to fit tests.

## Anti-gaming checks

- keyword存在だけでpassさせず、path、claim ID、command result、state transitionなどfixture固有の関係を検査する。
- structured artifactとhuman-readable artifactがある場合は相互整合を検査する。
- production/test/documentの削除、skip、常時success、固定出力を検出する。
- unsupported claimや過剰findingを数えられるfamilyではfalse-positive criterionを独立して持つ。

## Rubric boundary

The mutation set represents the declared policy risks. It cannot prove tests are minimal or detect unrelated implementation changes.

このrubricはhuman preferenceの代用ではない。観測可能なcontract coverageだけをqualityとして記録し、usefulnessやeleganceを推測しない。
