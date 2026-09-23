# F11-S-BASH-001: oracle and quality rubric

## Quality-pass rule

public checksと以下のhidden criterionをcriterion-levelで別々に記録する。全criterion passだけをこのcase revisionのquality-passとし、partialをpassへ丸めない。offline score時間はuser waitへ足さない。

| Check ID | Criterion | Observable signal |
| --- | --- | --- |
| `ops-static-pass` | Bash parser accepts the script. | `bash -n` exits zero |
| `ops-behavior-matrix` | Host/container/default precedence equals gold. | hidden scenario outputs match |
| `ops-minimal-diff` | Only the missing terminator is added. | normalized diff allowlist passes |

## Negative calibration set

次のplausible-but-wrong artifactをそれぞれ少なくとも一つのcriterionがrejectしなければ、rubricは識別力不足として実装を差し戻す。

- Rewriting the entire `case` as nested `if` statements.
- Adding `;;` to the wrong arm while suppressing smoke failure.
- Changing version precedence as part of syntax cleanup.

## Anti-gaming checks

- keyword存在だけでpassさせず、path、claim ID、command result、state transitionなどfixture固有の関係を検査する。
- structured artifactとhuman-readable artifactがある場合は相互整合を検査する。
- production/test/documentの削除、skip、常時success、固定出力を検出する。
- unsupported claimや過剰findingを数えられるfamilyではfalse-positive criterionを独立して持つ。

## Rubric boundary

This case is a static/smoke baseline and intentionally does not represent full devcontainer lifecycle cost.

このrubricはhuman preferenceの代用ではない。観測可能なcontract coverageだけをqualityとして記録し、usefulnessやeleganceを推測しない。
