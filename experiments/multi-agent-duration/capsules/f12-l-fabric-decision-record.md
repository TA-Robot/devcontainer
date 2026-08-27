# Build the execution-fabric decision record

Create `decision-record.json` and `DECISION-RECORD.md` from every public
proposal claim, benchmark distribution, incident/security finding, and hard
constraint. Preserve workload, sample count, censoring, invalid-run exclusions,
source identity, confidence, and unknown boundaries.

The selected or staged design must trace to cited evidence. Include alternatives
with bounded counterexamples, migration/operations ownership, executable gates,
rollback triggers, incident/security controls, unresolved recovery/provider
assumptions, and evidence-refresh triggers. Do not infer a universal winner or
revive the invalid pooled-throughput claim.

The Markdown ledger and decision summary must match the structured record.
Do not modify evidence, proposals, constraints, or validators.

Validate with:

```bash
python3 tools/validate_decision_record.py decision-record.json DECISION-RECORD.md
python3 tools/recompute_metrics.py evidence/benchmarks decision-record.json
python3 tools/check_entailment.py decision-record.json
```
