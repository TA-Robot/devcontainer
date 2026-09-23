# Development harness cycle 001 — 2026-09-05

Status: first improvement cycle complete, 2026-09-05. Plan, baseline, intervention,
live re-evaluation, accepted maintenance integration and final target checks are
recorded below; unresolved host-test failures remain explicit.

Scope clarification after review: this is a **small-maintenance pilot**. Running
the surrounding full test suite does not make the development task large-scale.
The [revised evaluation plan](development-harness-evaluation.md) requires separate
small- and large-scale evidence; this result supplies no large-scale observation.

## Decision

Keep the native-first environment and adopt the observed development-compatibility
fixes. Do not build ForgeRoom or enlarge G3 as the next step. A real maintenance
task exposed actionable environment defects and produced a useful code fix.

Both development conditions passed all 33 external semantic checks. The amended
control took 379.449 seconds; the improved condition took 235.089 seconds, a
38.04% observed reduction in this one pair. This is not an estimate of general
speedup. The stronger adoption evidence is that the actual environment defects
are reproduced and repaired, and the improved task no longer required a local
TOML workaround or triage of false mount failures.

## Task and conditions

The task was to reject non-finite JSON numbers in the repository's shared agent
contract validator while preserving finite values, large integers, booleans,
schema behavior and diagnostics. It was real maintenance, not a generated demo.
The task source initially passed 11/33 external checks. The source fix was absent
from both starting checkouts and was integrated only after the comparison.

The [protocol](../../experiments/development-harness/cycle-001/protocol.md)
records the task, source base, controls, limits and revisions. Both live cells
used GPT-6 Astra/high as requested, Codex 0.153.0, a fresh ephemeral noninteractive
session, workspace-write sandbox, no additional agents, and a 900-second wall
cap. Model/effort are requested settings; the recorder does not independently
attest provider-resolved settings.

The first launch on Codex 0.146.0 failed before any tool execution because the
provider required a newer CLI for this model. Its 27.680 seconds are retained as
readiness evidence, not included in the development pair. The control therefore
used the old frozen image with an explicit 0.153.0 compatibility overlay. The
improved image pinned the same CLI. A successful `doctor` auth/capability probe
had not established model compatibility.

## Observed development results

| Observation | Amended control | Improved |
| --- | ---: | ---: |
| External semantic checks | 33/33 | 33/33 |
| Live wall time | 379.449 s | 235.089 s |
| Reported input tokens | 1,194,536 | 706,423 |
| Included cached input tokens | 1,077,760 | 656,768 |
| Reported output tokens | 9,474 | 5,262 |
| Surfaced completed command items | 51 | 11 |
| Nonzero command exits | 9 | 1 |
| Task source files changed | 2 | 2 |
| Reported combined contract/duration check | 70 pass, 4 pre-existing failures | 76 pass, no failures |

Input fell 40.86% and output 44.46% in this pair. Input totals include repeated
cached context, not newly generated tokens; they are not currency estimates.
The improved run's single nonzero command was its initial regression test
against the unfixed validator. Nonzero exits are not all defects: the control
also had searches returning no matches.

The control created a temporary compatibility adapter to pip's existing TOML
parser, encountered compatibility errors while making it work, and reran the
four duration failures against the original validator to establish that they
were pre-existing. This was competent recovery, but avoidable work. The improved
run proceeded through the corresponding checks without that repair. Reported
suite results are distinguished from the independent acceptance and final
integration checks below.

## What changed in the environment

1. **Local code is actually exercised.** `scripts/agentctl` now selects sibling
   source libraries before installed libraries. Installed `agentctl` still uses
   its bundle. Tests distinguish local, installed and working-directory modules.
2. **Required validation works on shipped Python.** The template validator uses
   stdlib `tomllib` when available and distro `tomli` on Python 3.10. The image
   includes the compatibility package; there is no startup pip install.
3. **Asynchronous publication is awaited.** The supervisor retention test waits
   for the metadata it asserts, not only the earlier log truncation.
4. **Mount isolation tests inspect paths.** `/tmp/.../fixture/workspace` is no
   longer mistaken for `/workspace`. Exact repository, child and ancestor bind
   sources remain rejected, including alternate mount spellings.
5. **Fixtures are deterministic and isolated.** Fake providers consume prompt
   input before exiting; the patch-ID test uses a distinct integration parent;
   Mira tests explicitly set their private episode directory instead of
   inheriting the image's persistent ledger path.
6. **The selected model can run.** Codex is pinned to 0.153.0. Model readiness is
   documented separately from request-free CLI/auth diagnostics.

The provider-free environment probe changed from **1/8 to 8/8**: template
validation, checkout source selection, installed CLI execution and five retention
checks. The retention sequence changed from 0/5 to 5/5. These are diagnostic
checks and bounded repetitions, not a general harness score or reliability SLA.

No broker validation or isolation policy was relaxed to turn the tests green.
Initial failures, targeted retries and later fixes are retained in the evidence.

## Accepted maintenance artifact

The improved candidate's validator and regression tests were reviewed and
integrated. Validation scans the complete instance once before schema traversal,
so unconstrained children cannot bypass the finite-number rule. JSON decoder
hooks also reject overflow and invalid values overwritten by duplicate keys.
The finite test applies only to floats, preserving arbitrary-size integers and
the existing boolean distinction. This avoids rescanning the entire tree at
every schema branch. Only the two expected task files were taken from the
candidate; infrastructure changes were made separately by the primary.

## Verification and reproducibility

- Both candidates: 33/33 externally executed semantic checks, source digest
  unchanged by evaluation, and only the expected two task files modified.
- Intervention: host agentctl suite 45/45; affected container subsets 83/83 after
  repairing the recorded fixture failures. Other cases in the initial full suite
  passed. Standard and frozen builds, container start/doctor, native hook and
  persistent observation smoke passed before the development re-evaluation.
- Final integrated frozen container: **121/121 tests passed** in 303.947 seconds,
  including the shared contract, agentctl/job/supervisor and required duration
  suites. Source was mounted read-only and networking disabled; no image build
  or other full suite ran concurrently.
- Final standard and frozen image builds passed. Required syntax checks,
  template validation, lock and AI CLI sync/wrapper checks, host doctor,
  container hook/persistent observation smoke and Codex/Claude legacy CLI flag
  contracts passed. The final CLI contract check did not skip either provider.
- The accepted task is commit `89ca54d`; the subsequent test-only orphan fixture
  refinement is `38d707f`. The final code/test revision and exact image digests
  are in the result JSON. Final source matches the externally accepted candidate.

Two integrated host-wide runs were not green: the first had a bounded-cleanup
failure in F06-L-PYBASH-001 (120/121 passed); the serial repeat passed that case
but had two supervisor queue startup/submit failures (119/121 passed). The root
causes of these intermittent failures are not established. They remain recorded
risks, even if a subsequent target-container run passes.

After the comparison, supervisor fixtures were refined separately: normal tests
use the production 30-second orphan window, and the fault test explicitly ages
the heartbeat after verifying owned process termination. The actual orphan and
cleanup assertions remain. This test-only change removes a 400 ms deadline from
unrelated queue tests; it is not claimed to fix the observed startup failure or
contribute to the live timing difference. Production timeout policy is unchanged.

[Machine-readable results](../../experiments/development-harness/cycle-001/result.json)
record source/image/task/evaluator identities, the separate failed launch,
observations, semantic acceptance, environment probes and validation evidence.
Private candidate patches and command/final-message records are preserved under
`$HOME/.local/state/devcontainer-evaluations/cycle-001/`; private reasoning is not
retained by the recorder or copied into the report. Starting source is restored
from the committed base plus the listed intervention paths; do not require the
old untracked Evidence Forge source to reproduce this cycle.
Validation logs, including failed runs, are retained in that directory's
`validation/` subdirectory; published SHA-256 digests identify them without
publishing private process or environment details. Both live trial containers
were stopped after evidence collection.

## Limits and next decision

This is one task and one sequential pair, with an adaptive intervention informed
by the control. Run order, provider variation, caches, image rebuilding and the
candidate's own implementation choices can contribute to the timing difference.
The experiment does not attribute a separate speed gain to each fix, compare
models, prove multi-agent benefit or measure interactive `/goal` behavior.
One-time primary investigation, implementation, review, build and evaluation
costs are outside the live clock, so net ROI remains unmeasured.

The next cycle should use a different real development task that requires an
actual behavior change across components. Keep these parity fixes as the working
baseline. Select the next intervention from observed search, test or integration
waste; do not add a generic orchestrator or a larger benchmark merely to find a
winner. If a broad speed claim is needed, predeclare multiple task/run pairs and
alternate execution order. Keep null results and quality regressions visible.
