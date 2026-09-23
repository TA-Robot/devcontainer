# F05-L-PYBASH-001: oracle and quality rubric

## Quality-pass rule

public checksと以下のhidden criterionをcriterion-levelで別々に記録する。全criterion passだけをこのcase revisionのquality-passとし、partialをpassへ丸めない。offline score時間はuser waitへ足さない。

| Check ID | Criterion | Observable signal |
| --- | --- | --- |
| `migration-v1-compat` | Existing v1 state/readers remain supported during the declared window. | old contract matrix passes |
| `migration-backend-boundary` | Callers use interface and backend selection is preserved. | call graph and CLI/wrapper selection trace pass |
| `migration-atomic-order` | Version/data commit ordering is crash-safe. | fault injection at each write point never exposes invalid committed state |
| `migration-resume` | Interrupted upgrades resume idempotently. | multi-cut restart harness passes |
| `migration-rollback` | Rollback export produces canonical v1 data without mutating v2 source. | round-trip and byte-integrity checks pass |
| `migration-operations-doc` | Commands, ownership, backup, and failure recovery are executable and accurate. | doc manifest and replay checks pass |

## Negative calibration set

次のplausible-but-wrong artifactをそれぞれ少なくとも一つのcriterionがrejectしなければ、rubricは識別力不足として実装を差し戻す。

- Writing `version: 2` before converting items.
- An interface added while callers still reach `FileBackend.path`.
- A resume path that duplicates converted items.
- Rollback that destructively rewrites the only v2 state.
- Python backend selection not forwarded by Bash wrapper.

## Anti-gaming checks

- keyword存在だけでpassさせず、path、claim ID、command result、state transitionなどfixture固有の関係を検査する。
- structured artifactとhuman-readable artifactがある場合は相互整合を検査する。
- production/test/documentの削除、skip、常時success、固定出力を検出する。
- unsupported claimや過剰findingを数えられるfamilyではfalse-positive criterionを独立して持つ。

## Rubric boundary

The fixture covers file and memory test backends plus v1/v2. It does not prove compatibility with an unimplemented remote backend or real distributed transactions.

このrubricはhuman preferenceの代用ではない。観測可能なcontract coverageだけをqualityとして記録し、usefulnessやeleganceを推測しない。
