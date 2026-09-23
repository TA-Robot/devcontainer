# F09-M-PYBASH-001: oracle and quality rubric

## Quality-pass rule

public checksと以下のhidden criterionをcriterion-levelで別々に記録する。全criterion passだけをこのcase revisionのquality-passとし、partialをpassへ丸めない。offline score時間はuser waitへ足さない。

| Check ID | Criterion | Observable signal |
| --- | --- | --- |
| `security-symlink-exploit` | Post-check symlink escape is reproduced. | resolved target exits workspace |
| `security-env-root-exploit` | Inherited root override escape is reproduced. | launcher accepts untrusted root and reaches sentinel |
| `security-composition` | Layer interaction and patch-bypass risk are explained. | finding relation links both trust failures |
| `security-negative-tests` | Boundary tests fail seeded code and retain valid descendants. | negative/positive matrix matches |
| `security-mitigation-invariants` | Trusted root and resolved containment controls are both required. | control tuple complete |
| `security-no-false-positive` | Safe explicit workspace argument path is not flagged. | forbidden finding absent |

## Negative calibration set

次のplausible-but-wrong artifactをそれぞれ少なくとも一つのcriterionがrejectしなければ、rubricは識別力不足として実装を差し戻す。

- Finding only the symlink and recommending `resolve()` while leaving root override untrusted.
- Finding only environment override and missing in-root symlink escape.
- Tests that reject all symlinks including the documented safe internal link.
- A review requiring root privileges to reproduce.

## Anti-gaming checks

- keyword存在だけでpassさせず、path、claim ID、command result、state transitionなどfixture固有の関係を検査する。
- structured artifactとhuman-readable artifactがある場合は相互整合を検査する。
- production/test/documentの削除、skip、常時success、固定出力を検出する。
- unsupported claimや過剰findingを数えられるfamilyではfalse-positive criterionを独立して持つ。

## Rubric boundary

The exploit set covers this fixture's workspace entrypoints. It does not prove containment for every OS/filesystem or undisclosed environment variable.

このrubricはhuman preferenceの代用ではない。観測可能なcontract coverageだけをqualityとして記録し、usefulnessやeleganceを推測しない。
