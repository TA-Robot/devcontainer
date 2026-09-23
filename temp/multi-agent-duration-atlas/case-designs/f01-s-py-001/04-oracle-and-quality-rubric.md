# F01-S-PY-001: oracle and quality rubric

## Quality-pass rule

public checksと以下のhidden criterionをcriterion-levelで別々に記録する。全criterion passだけをこのcase revisionのquality-passとし、partialをpassへ丸めない。offline score時間はuser waitへ足さない。

| Check ID | Criterion | Observable signal |
| --- | --- | --- |
| `trace-required-nodes` | All six gold semantic nodes are represented. | normalized symbol/path pairs match the gold node set |
| `trace-required-edges` | The value-flow order is causally correct. | gold edges occur in order without a distractor hop |
| `trace-evidence-exists` | Evidence references real visible source. | each cited path/symbol resolves |
| `trace-no-distractor` | Unrelated similarly named helper is excluded. | forbidden distractor node/edge absent |

## Negative calibration set

次のplausible-but-wrong artifactをそれぞれ少なくとも一つのcriterionがrejectしなければ、rubricは識別力不足として実装を差し戻す。

- A trace that jumps directly from argparse to the final consumer and omits validation.
- A trace that follows the unused `legacy_state_path` helper because names look similar.
- A prose-only answer with no machine-checkable edges.

## Anti-gaming checks

- keyword存在だけでpassさせず、path、claim ID、command result、state transitionなどfixture固有の関係を検査する。
- structured artifactとhuman-readable artifactがある場合は相互整合を検査する。
- production/test/documentの削除、skip、常時success、固定出力を検出する。
- unsupported claimや過剰findingを数えられるfamilyではfalse-positive criterionを独立して持つ。

## Rubric boundary

The oracle measures repository trace recall and causal ordering, not prose quality or whether the selected symbol names are aesthetically concise.

このrubricはhuman preferenceの代用ではない。観測可能なcontract coverageだけをqualityとして記録し、usefulnessやeleganceを推測しない。
