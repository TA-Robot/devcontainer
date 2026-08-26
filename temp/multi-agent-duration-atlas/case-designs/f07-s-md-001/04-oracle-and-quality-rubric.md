# F07-S-MD-001: oracle and quality rubric

## Quality-pass rule

public checksと以下のhidden criterionをcriterion-levelで別々に記録する。全criterion passだけをこのcase revisionのquality-passとし、partialをpassへ丸めない。offline score時間はuser waitへ足さない。

| Check ID | Criterion | Observable signal |
| --- | --- | --- |
| `doc-command-replay` | Documented command parses and returns JSON. | extracted command exits zero and output parses |
| `doc-constraint-accurate` | Workspace-boundary constraint matches source behavior. | fact manifest maps text to parser/check symbols |
| `doc-invalid-form-removed` | Obsolete option order is absent. | forbidden command pattern absent |
| `doc-link-integrity` | Touched section links still resolve. | local link validator passes |

## Negative calibration set

次のplausible-but-wrong artifactをそれぞれ少なくとも一つのcriterionがrejectしなければ、rubricは識別力不足として実装を差し戻す。

- A doc that swaps argument order but omits the boundary constraint.
- A command using shell-specific placeholders that cannot be replayed.
- Text claiming `--allow-outside-workspace` exists when it does not.

## Anti-gaming checks

- keyword存在だけでpassさせず、path、claim ID、command result、state transitionなどfixture固有の関係を検査する。
- structured artifactとhuman-readable artifactがある場合は相互整合を検査する。
- production/test/documentの削除、skip、常時success、固定出力を検出する。
- unsupported claimや過剰findingを数えられるfamilyではfalse-positive criterionを独立して持つ。

## Rubric boundary

The evaluator verifies executable syntax and a small fact manifest. It does not score tone, pedagogy, or all documentation outside the touched section.

このrubricはhuman preferenceの代用ではない。観測可能なcontract coverageだけをqualityとして記録し、usefulnessやeleganceを推測しない。
