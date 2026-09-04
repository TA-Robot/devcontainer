# Evidence Forge G3 live pilot — 2026-09-05

## Decision summary

The G3 concurrent invariant repair pilot delivered a correct artifact and
passed 7/7 external checks in 10 minutes 51 seconds. It also demonstrated the
desired clean-checkpoint `agentctl` flow and machine-correlated consult/verify
episodes. However, it did not demonstrate a marginal maker-checker quality gain:
the primary independently found every hidden defect family before worker reports
arrived, and the fresh verifier changed no code. The current fixture is saturated
and should not receive a matched solo quality comparison until its mutant bank
has more headroom.

## Fixed input and delivery

- fixture: G3 variant 0, base implementation;
- immutable start: `cf18c96b46aa731b2340e36406f3bd7fa05e46ff`;
- implementation checkpoint: `e96624b3698c0187c640af95abb0d0e33655ac09`;
- final commit: `5de1453e5b5189e8513cb9a2ed4a4b34633664da`;
- frozen image: `sha256:829d58c04a53f771e556407bbb634aeb8765e4e8f1bd9d3104f18c362713de88`;
- observed outer run: `2026-09-04T19:17:36Z` to `19:28:27Z`, 651 seconds;
- checks: 7/7 project tests, 25/25 repeated suites, 2,500 synchronized
  contention rounds, lint, and clean tree;
- external result: all functionality, assurance, and delivery checks passed.

## Delivered repair

The component now serializes all state transitions, allocates fencing tokens
from a persistent per-resource watermark, requires exact resource/owner/token
matches, returns detached records, and validates identities and TTL consistently.
The project retained a focused defect-to-reproducer-to-closure table in
`REPAIR.md` rather than reporting only a final pass.

## Collaboration path

The primary used a bounded `.git/g3-collab` spool so dynamically generated task
and decision packets remained inside the registered project without dirtying the
worktree. Two baseline consults started together; after a controller-owned clean
checkpoint, one fresh verifier reviewed that exact SHA.

| Participant | Relation | Active time | Broker terminal | Observed contribution |
|---|---|---:|---|---|
| specification audit | consult / one-shot | 114.337 s | failed | mapped every published invariant and concrete counterexamples |
| concurrency audit | consult / one-shot | 147.382 s | succeeded | added renew/release, successor-deletion, and double-release schedules |
| fixed artifact review | verify / one-shot | 118.350 s | failed | ran repeated probes and found no actionable defect |

All three jobs were decision-correlated in the content-free ledger. The report
correctly exposed their relation, lifecycle, mechanisms, late-failure binding
constraint, provider, role, outcome, and duration without retaining task text.
This closes the G1 uncertainty about whether a clean checkpointed Lane R flow can
work. It can; one baseline audit completed cleanly and succeeded.

The failed states are also informative:

1. The specification task required `python -m py_compile` in a read-only lane.
   `py_compile` writes `__pycache__` even with `PYTHONDONTWRITEBYTECODE=1`, so the
   check failed and the completed report could not validate.
2. The verifier put two manual acceptance claims into command `checks` with
   `exit_code: null`. The schema deliberately requires exit code zero for a
   passed command, so the broker rejected the envelope.

The target contract now explicitly keeps Lane R acceptance read-safe and puts
manual evidence in summary, risks, or follow-ups. `docs/agentctl.md` now matches
the actual project-local input constraint and documents the bounded `.git`
spool, including its linked-worktree limitation.

## Observation quality

The fixed workspace resolver worked during the run: the project skill reported
`observed`, not the false `unmeasured` seen in G2. The ledger retained three
correlated managed episodes plus provider and parent episodes.

The new `exec_command` recognition also classified tests: the parent episode
contained ten test-category events. Actual Codex hook responses did not include
an explicit structured process exit code, so five post-tool test outcomes were
stored as `unknown`. This is more accurate than zero test activity and preserves
the privacy rule against parsing arbitrary command output, but outcome coverage
is still incomplete.

## Why the benchmark is saturated

Before worker results returned, the primary's own baseline probe reproduced:

- multiple successful owners in every synchronized race round;
- token reuse after release;
- stale same-owner release of a successor;
- mutation of a returned record changing internal state.

Those are the evaluator's four assurance groups. The independent audit added
valuable schedules and the final verifier increased assurance, but neither
created a hidden-check transition beyond what the primary had already found.
Because the final evaluator is boolean and capped at 7/7, a solo run cannot show
whether additional reasoning would be better.

Do not use this pilot to infer that verification is useless. Use it to reject
the current G3 fixture as a marginal-quality benchmark. A revised family should
vary defect composition rather than names, include independent operation-order
mutants, separate plausible maker closure from deeper verifier-only obligations,
and retain some graded evidence beyond a basic full pass.

## Remaining work

- build and audit the G3 mutant bank before another live cell;
- add a matched solo/maker-only comparison only after external headroom exists;
- decide whether a provider-supported structured exit status can improve test
  outcome telemetry without parsing logs;
- repeat clean Lane R jobs with corrected acceptance/result guidance;
- preserve G2's non-scalar quality vector as the stronger current routing
  evidence.

Detailed raw evidence remains under
`temp/evidence-forge-live-runs/g3-live-01/`; the clean fixture remains under
`temp/evidence-forge-g3-live-20260905-01/`.
