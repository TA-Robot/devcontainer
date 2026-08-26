# F05-M-PY-001: oracle and quality rubric

## Quality-pass rule

public checksと以下のhidden criterionをcriterion-levelで別々に記録する。全criterion passだけをこのcase revisionのquality-passとし、partialをpassへ丸めない。offline score時間はuser waitへ足さない。

| Check ID | Criterion | Observable signal |
| --- | --- | --- |
| `migration-all-callers` | Direct and reflective callers use the intended surface. | call graph/import inventory complete |
| `migration-policy-lifecycle` | One component-owned codec preserves injected schema policy. | identity/version trace passes |
| `migration-compat-bytes` | Deprecated shim output/errors equal old API. | hidden behavior matrix matches |
| `migration-warning-once` | Compatibility warning count/category is exact. | warning capture passes |
| `migration-api-surface` | New and deprecated exports match contract only. | API snapshot passes |

## Negative calibration set

次のplausible-but-wrong artifactをそれぞれ少なくとも一つのcriterionがrejectしなければ、rubricは識別力不足として実装を差し戻す。

- Creating `EventCodec()` inside every call.
- Migrating grep-visible callers but missing reflective import.
- A shim that returns equivalent JSON with different canonical bytes.
- Warning on every nested encode operation.

## Anti-gaming checks

- keyword存在だけでpassさせず、path、claim ID、command result、state transitionなどfixture固有の関係を検査する。
- structured artifactとhuman-readable artifactがある場合は相互整合を検査する。
- production/test/documentの削除、skip、常時success、固定出力を検出する。
- unsupported claimや過剰findingを数えられるfamilyではfalse-positive criterionを独立して持つ。

## Rubric boundary

The oracle proves the fixture's caller inventory and compatibility matrix. It does not establish compatibility with external unknown consumers.

このrubricはhuman preferenceの代用ではない。観測可能なcontract coverageだけをqualityとして記録し、usefulnessやeleganceを推測しない。
