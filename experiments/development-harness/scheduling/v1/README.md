# Scheduling H1: independent evaluation boundary

This is the first bounded preparation job for [candidate A](../../../../docs/agents/hard-task-candidates.md).
It supplies evaluator-owned scheduling state and metrics, an isolated JSONL policy
process, a public execution contract, and provider-free calibration. It is not a
new scheduler service and does not change `agentctl` or the devcontainer image.

**The boundary is calibrated; the hard task is not yet qualified.** Small
constructed examples establish clock/accounting and meaningful policy separation.
They do not establish that strong solo agents struggle, or that collaboration
improves design, selection, or implementation.

## Contract and trust boundary

[TASK.md](TASK.md) is the public contract. Candidate Python is read as bounded
bytes and copied to an immutable-per-run snapshot, never imported or executed on
the host. The fixed Python-only image is
`sha256:df8eb7a18e1d462af44d23e9d9c0d32c2c960a49452c61fa17e0d215c821a9e0`;
its build source and provenance are the existing
[probe image](../../selection/lifecycle_v1/probe-image.json).
No new dependencies or image build are introduced. Removing this experiment and
its test removes its use of that shared image; do not remove an image still used
by other experiments.

Only the source snapshot is mounted read-only. No scenario file, evaluator,
reference policy, credentials, network, Docker socket, or project checkout is
mounted. A fresh container per scenario prevents policy memory crossing scenarios.
The host owns time and state; it sends a JSON value containing public observations
and accepts only matching request identity plus job/worker assignments. Future
failure labels stay on the evaluator side.

Each scenario is bounded and containers are explicitly removed on success,
invalid output, timeout, and handled SIGINT/SIGTERM. SIGKILL/power loss and Docker
daemon failure cannot guarantee cleanup; no crash-durability claim is made.
Unknown/unremoved execution is withheld. Oversize legal observations are evaluator
capacity failures, not evidence of an invalid candidate. Raw metrics and policy
response elapsed time are separate; timing noise cannot establish policy quality.

## Legacy G2 audit disposition

[The preparation seal](preparation.json) records the inspected legacy source hashes.
Legacy source remains unchanged and is not a runtime dependency of this version.

| Prior issue | New boundary | Remaining scope |
| --- | --- | --- |
| R1: candidate returns its own metrics | Candidate returns actions; host computes all outcomes | No candidate-owned simulator/CLI used for grading |
| R2: references to mutable evaluator state | JSON process boundary; trusted callback calibration also gets a deepcopy | Container isolation is required for untrusted code |
| R3: timing noise qualifies policy difference | Calibration requires deterministic completion 20 vs 10 ticks on the same workload | Broad policy/workload discrimination still needs H1 work |
| R4: full scheduled durations called consumption | Actual busy ticks until failure and committed ticks are separate | These are simulator worker units, not provider tokens or monetary cost |
| R8: executable source outside version control | Runtime, transport, evaluator, fixtures and calibration are tracked here | Legacy raw evidence stays private/local; no demo app is added |

Integer ticks are a deliberate new public contract. Old fractional scenarios and
scores are not silently converted or regraded. This version does not claim to
repair every property of the old G2 benchmark.

## Reproduce

```bash
PYTHONDONTWRITEBYTECODE=1 SCHEDULING_EVALUATOR_DOCKER=1 \
  python3 -m unittest scripts/test-scheduling-evaluator.py
PYTHONDONTWRITEBYTECODE=1 python3 experiments/development-harness/scheduling/v1/calibrate.py \
  --output /path/to/new-private-calibration
PYTHONDONTWRITEBYTECODE=1 python3 experiments/development-harness/scheduling/v1/evaluate.py \
  --candidate /path/to/policy.py --scenarios /path/to/scenarios.json \
  --output /path/to/new-assessment
```

All outputs require unused paths. The fixed image must already be present.
Tests and calibration use synthetic policies only; no live model or host auth.
Source, candidate, and scenario hashes are saved before assessment. Reports retain
per-scenario invalid/unmeasured outcomes and stop remaining scenarios on runtime
or capacity failure. No human/LLM score override is available.

[Validation](validation.json) records tests, source hashes, private calibration
location and hash, preparation time and the remaining H1/H2 work.

## Next work, with no new generic runner

The narrow boundary job ends here. Before strong-solo difficulty calibration:

1. Specify heterogeneous workload families (dependency bottlenecks, scarce-worker
   assignments, cache tradeoffs, wide frontiers), their public/unused split, and
   a useful target quality vector. These are not implemented by the three small
   calibration cases.
2. Verify attainable targets and meaningfully different valid policies on that
   population, plus overfit and common-failure candidates. Preserve negative
   results; do not tune for a collaborative winner.
3. Freeze H2 model/tool access, solo self-testing and iterative candidate ability,
   total runs/budgets, stop criteria and evidence. A legal policy and a passing
   transport test are not evidence of a hard task.

The future developer must be able to make, test, compare and revise real policies.
This work must not be shrunk back to classifying saved candidates or repeating
another fixed upfront-advisor comparison.
