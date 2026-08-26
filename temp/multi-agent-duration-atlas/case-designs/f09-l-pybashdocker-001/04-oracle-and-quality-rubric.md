# F09-L-PYBASHDOCKER-001: oracle and quality rubric

## Quality-pass rule

public checksと以下のhidden criterionをcriterion-levelで別々に記録する。全criterion passだけをこのcase revisionのquality-passとし、partialをpassへ丸めない。offline score時間はuser waitへ足さない。

| Check ID | Criterion | Observable signal |
| --- | --- | --- |
| `threat-assets-boundaries` | Assets, actors, boundaries, phases, and owners are complete. | gold topology coverage complete |
| `threat-worktree-race` | Marker replacement/race attack and controls are correct. | hidden interleaving reproducer/control test passes |
| `threat-bind-injection` | Bind path option-injection attack and safe encoding are covered. | hidden path corpus reproduces/rejects correctly |
| `threat-credential-scope` | Provider/scope loss and least-privilege rotation controls are covered. | scope transition model passes |
| `threat-cleanup-ownership` | PID/name reuse cannot authorize peer cleanup. | owner-token lifecycle scenarios pass |
| `threat-detection-recovery` | Detection, containment, cleanup, and recovery ownership are actionable. | incident scenario mapping complete |
| `threat-control-counterexamples` | Single-control bypasses and control interactions are analyzed. | required counterexample set present |
| `threat-unknown-honesty` | Unobservable host/kernel/provider assumptions remain unknown. | unsupported guarantee set absent |

## Negative calibration set

次のplausible-but-wrong artifactをそれぞれ少なくとも一つのcriterionがrejectしなければ、rubricは識別力不足として実装を差し戻す。

- A checklist listing threats without attack preconditions or tests.
- Validating names while authorizing cleanup by reusable PID/name.
- Masking credential values but ignoring provider/scope ownership.
- Escaping shell text while passing unsafe Docker bind option syntax.
- Claiming container rootfs read-only fully isolates a mounted host socket.
- A threat model with prevention but no detection/recovery owner.

## Anti-gaming checks

- keyword存在だけでpassさせず、path、claim ID、command result、state transitionなどfixture固有の関係を検査する。
- structured artifactとhuman-readable artifactがある場合は相互整合を検査する。
- production/test/documentの削除、skip、常時success、固定出力を検出する。
- unsupported claimや過剰findingを数えられるfamilyではfalse-positive criterionを独立して持つ。

## Rubric boundary

The simulator validates fixture attack paths and control invariants. It is not a certification of Docker, Git, provider auth, or the host kernel.

このrubricはhuman preferenceの代用ではない。観測可能なcontract coverageだけをqualityとして記録し、usefulnessやeleganceを推測しない。
