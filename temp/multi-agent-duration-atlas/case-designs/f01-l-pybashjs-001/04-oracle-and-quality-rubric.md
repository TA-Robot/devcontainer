# F01-L-PYBASHJS-001: oracle and quality rubric

## Quality-pass rule

public checksと以下のhidden criterionをcriterion-levelで別々に記録する。全criterion passだけをこのcase revisionのquality-passとし、partialをpassへ丸めない。offline score時間はuser waitへ足さない。

| Check ID | Criterion | Observable signal |
| --- | --- | --- |
| `trace-lifecycle-nodes` | All mandatory lifecycle stages and locations are present. | gold node/location tuples match |
| `trace-boundary-artifacts` | Host/container/extension edges name the correct transported artifact. | gold edge/artifact/owner tuples match |
| `trace-runtime-chain` | Provider activity reaches hook state and renderer without a legacy detour. | ordered runtime subgraph matches |
| `trace-recovery-ownership` | Three seeded recovery paths assign the correct owner and retained state. | recovery tuple set complete |
| `trace-no-legacy-path` | Frozen legacy wrapper is not claimed as an active dependency. | forbidden nodes/edges absent |
| `trace-evidence-integrity` | Every citation resolves and schema is internally connected. | reference and graph validation pass |

## Negative calibration set

次のplausible-but-wrong artifactをそれぞれ少なくとも一つのcriterionがrejectしなければ、rubricは識別力不足として実装を差し戻す。

- A runtime-only graph that omits rebuild and host provisioning.
- A lifecycle list with no artifact/owner labels on boundary crossings.
- A graph that routes provider activity through the legacy second-agent wrapper.
- A recovery section that says 'retry' without naming retained state or cleanup owner.

## Anti-gaming checks

- keyword存在だけでpassさせず、path、claim ID、command result、state transitionなどfixture固有の関係を検査する。
- structured artifactとhuman-readable artifactがある場合は相互整合を検査する。
- production/test/documentの削除、skip、常時success、固定出力を検出する。
- unsupported claimや過剰findingを数えられるfamilyではfalse-positive criterionを独立して持つ。

## Rubric boundary

The structured gold covers the fixture's intended lifecycle, not every VS Code or Docker implementation detail. Timing from the simulator is not real image-build timing.

このrubricはhuman preferenceの代用ではない。観測可能なcontract coverageだけをqualityとして記録し、usefulnessやeleganceを推測しない。
