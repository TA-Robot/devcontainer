# F01-M-PYJS-001: oracle and quality rubric

## Quality-pass rule

public checksと以下のhidden criterionをcriterion-levelで別々に記録する。全criterion passだけをこのcase revisionのquality-passとし、partialをpassへ丸めない。offline score時間はuser waitへ足さない。

| Check ID | Criterion | Observable signal |
| --- | --- | --- |
| `trace-success-chain` | Complete normalized-event to renderer chain. | all gold nodes and ordered cross-language edges present |
| `trace-schema-boundary` | JSON producer and consumer fields agree. | state/status/category fields linked on both sides |
| `trace-fail-open-branches` | Both malformed input and write failure semantics are captured. | two distinct branch IDs reach unchanged/last-good state |
| `trace-no-telemetry-detour` | Telemetry distractor is not claimed as renderer input. | forbidden telemetry edge absent |
| `trace-evidence-integrity` | All citations resolve to visible paths and symbols. | reference resolver succeeds |

## Negative calibration set

次のplausible-but-wrong artifactをそれぞれ少なくとも一つのcriterionがrejectしなければ、rubricは識別力不足として実装を差し戻す。

- A Python-only trace that stops at `mira-state.json`.
- A trace that treats malformed input and write failure as the same exception path.
- A graph routing renderer reads through the unrelated telemetry ledger.

## Anti-gaming checks

- keyword存在だけでpassさせず、path、claim ID、command result、state transitionなどfixture固有の関係を検査する。
- structured artifactとhuman-readable artifactがある場合は相互整合を検査する。
- production/test/documentの削除、skip、常時success、固定出力を検出する。
- unsupported claimや過剰findingを数えられるfamilyではfalse-positive criterionを独立して持つ。

## Rubric boundary

The graph oracle checks required contract edges and branches. It does not prove that every incidental call in the implementation was listed.

このrubricはhuman preferenceの代用ではない。観測可能なcontract coverageだけをqualityとして記録し、usefulnessやeleganceを推測しない。
