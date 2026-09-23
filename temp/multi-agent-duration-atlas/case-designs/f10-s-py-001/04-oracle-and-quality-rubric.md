# F10-S-PY-001: oracle and quality rubric

## Quality-pass rule

public checksと以下のhidden criterionをcriterion-levelで別々に記録する。全criterion passだけをこのcase revisionのquality-passとし、partialをpassへ丸めない。offline score時間はuser waitへ足さない。

| Check ID | Criterion | Observable signal |
| --- | --- | --- |
| `perf-repro-command` | Recorded commands reproduce observations. | rerun data schema and digest match |
| `perf-scaling-evidence` | Multiple sizes show N serialization calls. | counter slope equals gold relation |
| `perf-root-cause` | Repeated canonicalization is localized to correct loop/symbol. | source/evidence tuple matches |
| `perf-distractor-rejected` | Sort is not claimed as the primary scaling cause. | comparative counter evidence present |
| `perf-claim-bounded` | Optimization claim is conditional and preserves canonical bytes. | unsupported absolute speedup claims absent |

Revision 5 hidden checks require only identifiers and fields visible in the contract/template. The public validator owns the single exact-edit-surface criterion; hidden semantic criteria verify protected inputs but do not repeat scope failure, so one scope error cannot masquerade as five semantic failures.

## Negative calibration set

次のplausible-but-wrong artifactをそれぞれ少なくとも一つのcriterionがrejectしなければ、rubricは識別力不足として実装を差し戻す。

- Declaring `sorted()` the bottleneck from one profile snapshot.
- Reporting only elapsed milliseconds with no input sizes/counters.
- Claiming a global percentage speedup without patch or distribution.
- Suggesting removal of canonical serialization and changing output bytes.

## Anti-gaming checks

- keyword存在だけでpassさせず、path、claim ID、command result、state transitionなどfixture固有の関係を検査する。
- structured artifactとhuman-readable artifactがある場合は相互整合を検査する。
- production/test/documentの削除、skip、常時success、固定出力を検出する。
- unsupported claimや過剰findingを数えられるfamilyではfalse-positive criterionを独立して持つ。

## Rubric boundary

Counter scaling makes the seeded cause deterministic; elapsed timings remain diagnostic and are not treated as portable speed guarantees.

このrubricはhuman preferenceの代用ではない。観測可能なcontract coverageだけをqualityとして記録し、usefulnessやeleganceを推測しない。
