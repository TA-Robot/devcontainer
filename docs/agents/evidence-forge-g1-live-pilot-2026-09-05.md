# Evidence Forge G1 live pilot — 2026-09-05

## Decision summary

The first Evidence Forge live pilot completed G1 Coupled Contract Migration and
passed all external evaluator checks. It also falsified two infrastructure
assumptions: the frozen benchmark image did not contain the `tmux` required by
the runbook, and `agentctl` Lane R cannot truthfully complete while reviewing a
primary's uncommitted shared-checkout diff.

This is one observed run, not a causal comparison or a routing default.

## Fixed input and environment

- fixture: G1 variant 1, untouched v1 implementation;
- initial project commit: `6cf6e051a669e51f5c079f5e350c9d5dd47fcd42`;
- initial user state: one untracked note that had to remain byte-identical;
- image: `devcontainer-frozen-smoke:latest`;
- primary: Codex from the stable image;
- Grok: bounded read-only canary succeeded, but the primary did not select it;
- Claude: installed but unauthenticated;
- cost cap: 45 minutes;
- actual measured development window: 600 seconds;
- execution-surface deviation: detached `codex exec` with explicit terminal
  marker because `tmux` was absent.

The first two wrapper attempts did not receive a usable development objective
and made no source changes. They are harness failures and are excluded from the
600-second development observation.

## Delivered outcome

The primary produced commit
`73f32ccd4e93ca124903a39ca8f15b9fb3b14a8b`. The external evaluator passed:

| Group | Passed | Total |
|---|---:|---:|
| compatibility | 1 | 1 |
| contract | 2 | 2 |
| consumers | 2 | 2 |
| integration / delivery | 3 | 3 |

The final workspace contained only the original untracked user note. Generated
schema reproduction, the expanded 14-test public suite, lint, and diff checks
passed. The external evaluator finished in 7.795 seconds.

## Collaboration path and effect

The primary avoided overlapping write agents on the tightly coupled migration.
It used two sequential, decision-correlated `agentctl` participants:

| Relation | Role/provider | Active time | Broker terminal | Observed contribution |
|---|---|---:|---|---|
| consult / one-shot | researcher / Codex | 157.902 s | failed | enumerated missing v2 obligations and edge cases |
| verify / one-shot | reviewer / Codex | 135.627 s | failed | found schema/runtime numeric parity, legacy retry coverage, and duplicate-field gaps |

The verify result changed the delivered artifact. The primary added fixes and
regressions for the concrete findings. This supports an
evidence-producing-refinement interpretation for this run. It does not prove
that both participants were worth their combined 293.529 seconds; a matched
solo or checkpointed-verify cell is needed.

Both job failures were truthful. Lane R used the shared registered checkout
while the primary's implementation was uncommitted. Its clean-result contract
could not attribute the dirty state and therefore could not accept the result,
even though the report content was useful. The primary later removed pilot and
bytecode artifacts, committed the implementation, and passed external delivery
checks. Do not rewrite the two job outcomes as success.

## Efficiency and telemetry observations

- primary-reported model usage: 5,207,924 cumulative input tokens, including
  5,086,464 cached; 32,774 output; 13,691 reasoning;
- managed jobs were sequential; peak managed concurrency was one;
- the primary direct episode and two managed jobs were retained as separate
  ledger episodes, so the direct episode remained `solo-observed` rather than a
  parent campaign linked to managed children;
- content-free structured test counts were zero despite test evidence in the
  provider result and external evaluator.

The cached-token total is a project-local efficiency warning, not a billing
estimate or universal model characteristic. It should be compared under the
same task, model, evaluator, and execution surface.

## Changes justified by this pilot

1. Include `tmux` in the frozen image and assert it in the image smoke test.
2. State across target AGENTS, playbook, Codex skill, and `agentctl` docs that
   Lane R requires a clean registered checkout.
3. Run consultation before mutation; create a controller-owned checkpoint
   commit before an `agentctl` implementation review and bind the task to it.
4. If an uncommitted diff must be reviewed, use an explicitly permitted native
   advisory child or a separately prepared snapshot. Do not silently ignore
   pre-existing dirty paths without content attribution.

## Remaining experiments

- matched G1 solo versus checkpointed-verify run;
- repeated G2 matched pairs to estimate run-to-run variance;
- redesigned G3 mutant-bank attribution after the first live fixture saturated;
- parent-to-managed-job campaign correlation and structured test observation;
- Grok participation under a task where its distinct evidence source has a
  stated expected mechanism.

Detailed raw evidence remains under
`temp/evidence-forge-live-runs/g1-live-01/` and the target fixture under
`temp/evidence-forge-g1-live-20260905-01/`. Raw provider JSONL is intentionally
not copied into this durable documentation.

The completed G2 follow-up is documented in
[`evidence-forge-g2-live-pilot-2026-09-05.md`](evidence-forge-g2-live-pilot-2026-09-05.md).
