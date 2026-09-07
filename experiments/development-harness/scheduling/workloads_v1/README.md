# H1 workload and attainable-target calibration

The previous [independent boundary](../v1/README.md) remains unchanged.
This version adds four workload families, a fixed executable reference, a
contrasting risk-hint policy, and provider-free external measurement.

**H1 now has a heterogeneous population and an attainable reference vector.
Strong-solo difficulty and collaboration effects are still unmeasured.**
The reference is a transparent authoring heuristic, not an optimal solver or a
certification of a demanding real-world service level. H2 must establish whether
this level exposes a useful limitation; we will not call ordinary conformance a
hard problem merely because a broader corpus exists.

[Public workload contract](WORKLOAD.md); [raw-vector summary](qualification.json);
[source/measurement validation](validation.json).

## Fixed selection and scope

- Four families: dependency chains, wide frontier, scarce-worker compatibility,
  and expensive cache changes. Three generated structures and paired success/
  failure stress cases per family give 24 scenarios per population.
- Three policies: FIFO baseline, downstream rank with cache/resource-aware
  assignment (`rank_cache`), and risk hint per execution time (`risk_first`).
  These are distinct calibration approaches, not a recommended agent count.
- `rank_cache` was the target policy in the qualification program before running
  the policies. Targets are its actual vector, never per-cell minima across policies.
- Development and qualification were executed, 144 policy/scenario executions.
  Confirmation was not executed. The source generator knows all seeds and belongs
  only to the authoring side; it is never a developer tool or projection file.
- Risk hints are not calibrated probabilities; the paired failure sampling rule
  is disclosed in WORKLOAD.md. The corpus measures declared stress conditions,
  not expected real-world failure rates.

On qualification, rank_cache improves all twelve family/metric values over FIFO.
Risk-first trades slower successful completion for earlier failure detection in
some families, so no aggregate winner is manufactured. CPU/IPC timing noise is
not used to establish these differences.

## Reproduce authoring calibration

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest scripts/test-scheduling-workloads.py
PYTHONDONTWRITEBYTECODE=1 python3 experiments/development-harness/scheduling/workloads_v1/qualify.py \
  --output /path/to/new-private-qualification
```

The suite count is the coverage design above. Each run inherits the frozen
30-second scenario / 5-second response / cleanup caps from v1, giving a finite
144-execution authoring job. Those caps are runtime safeguards, not desired
policy times. Output paths are exclusive. No live provider or host credential is
used and no candidate code is executed on the host. The reference uses stdlib
only; no production dependency or container distribution changed.

The first attempt completed all six external batches but collided when writing
its summary to the already-used qualification input filename. Its artifacts are
preserved. The output is now `report.json`; an end-to-end regression verifies the
separate paths, and the complete calibration was rerun to a fresh directory.
Only the successful source-matched run is summarized, with the failed attempt
explicitly retained in validation. No policy winner was selected from retries.

## H2 entry

[The solo difficulty protocol](solo-protocol.md) fixes the intended question,
resources, information boundary and decision rules. Execution remains gated on
an actual public development tool/actor projection and source-matched capability,
repair, stop and independent-assessment checks. A no-tools advice relay is not a
substitute for a strong solo developer able to run repeated experiments.

There is no reason to add another generic runner or expand workload count before
those entry checks. Existing CLI, code-mode host, bounded capture and Docker
isolation can be reused. The current fixed image was inspected and contains the
code-mode-host binary, but its presence alone does not prove working tool access.
The [official config reference](https://learn.chatgpt.com/docs/config-file/config-reference)
documents the multi-agent feature setting; exact solo tool availability must be
checked on the pinned CLI, not inferred from configuration names.
