# F05-S-PY-001: oracle and quality rubric

## Quality-pass rule

public checksと以下のhidden criterionをcriterion-levelで別々に記録する。全criterion passだけをこのcase revisionのquality-passとし、partialをpassへ丸めない。offline score時間はuser waitへ足さない。

| Check ID | Criterion | Observable signal |
| --- | --- | --- |
| `refactor-equivalence-output` | All normal output traces equal baseline. | hidden behavior matrix matches |
| `refactor-equivalence-errors` | Exception classes and validation order equal baseline. | error trace matrix matches |
| `refactor-helper-shared` | Both callers use one private helper. | AST call graph has one shared private target |
| `refactor-api-stable` | Public API surface is unchanged. | export/signature snapshot matches |

## Negative calibration set

次のplausible-but-wrong artifactをそれぞれ少なくとも一つのcriterionがrejectしなければ、rubricは識別力不足として実装を差し戻す。

- A helper that always prefixes before validation.
- Two renamed duplicate helpers instead of one shared helper.
- A refactor exposing the helper in `__all__`.

## Anti-gaming checks

- keyword存在だけでpassさせず、path、claim ID、command result、state transitionなどfixture固有の関係を検査する。
- structured artifactとhuman-readable artifactがある場合は相互整合を検査する。
- production/test/documentの削除、skip、常時success、固定出力を検出する。
- unsupported claimや過剰findingを数えられるfamilyではfalse-positive criterionを独立して持つ。

## Rubric boundary

Behavior equivalence is measured over an exhaustive fixture matrix and API snapshot, not performance or subjective readability.

このrubricはhuman preferenceの代用ではない。観測可能なcontract coverageだけをqualityとして記録し、usefulnessやeleganceを推測しない。
