# F11-M-BASH-001: oracle and quality rubric

## Quality-pass rule

public checksと以下のhidden criterionをcriterion-levelで別々に記録する。全criterion passだけをこのcase revisionのquality-passとし、partialをpassへ丸めない。offline score時間はuser waitへ足さない。

| Check ID | Criterion | Observable signal |
| --- | --- | --- |
| `ops-version-normalization` | CRLF/whitespace values normalize; malformed/multiline values reject. | input matrix passes |
| `ops-idempotent-install` | Matching version avoids reinstall; mismatch installs once. | installer call ledger matches |
| `ops-ready-after-verify` | Ready marker appears only after installed version verifies. | fault cut never exposes false ready |
| `ops-restart-recovery` | Interrupted install recovers on next start. | two-process lifecycle reaches ready |
| `ops-state-cleanup` | Only owned transient files are removed and no residual remains. | sentinel/resource inventory passes |

## Negative calibration set

次のplausible-but-wrong artifactをそれぞれ少なくとも一つのcriterionがrejectしなければ、rubricは識別力不足として実装を差し戻す。

- Using `tr -d '
 '` and accepting malicious multiline versions.
- Writing ready before invoking installer.
- Always reinstalling to avoid comparison complexity.
- Deleting the persistent metadata directory on failure.

## Anti-gaming checks

- keyword存在だけでpassさせず、path、claim ID、command result、state transitionなどfixture固有の関係を検査する。
- structured artifactとhuman-readable artifactがある場合は相互整合を検査する。
- production/test/documentの削除、skip、常時success、固定出力を検出する。
- unsupported claimや過剰findingを数えられるfamilyではfalse-positive criterionを独立して持つ。

## Rubric boundary

The harness models host/container metadata and restarts locally; it does not measure a real VS Code reopen or external package installation.

このrubricはhuman preferenceの代用ではない。観測可能なcontract coverageだけをqualityとして記録し、usefulnessやeleganceを推測しない。
