# Build the execution-fabric decision record

Create `decision-record.json` and `DECISION-RECORD.md` from every public
proposal claim, benchmark distribution, incident/security finding, and hard
constraint. Preserve workload, sample count, censoring, invalid-run exclusions,
source identity, confidence, and unknown boundaries.

Start by copying `decision-record.template.json` to `decision-record.json` and
`DECISION-RECORD.template.md` to `DECISION-RECORD.md`. Fill or duplicate the
declared entity shapes from evidence; do not modify source/template files or
create other artifacts. These two target files are the complete editable surface.
Put any temporary data under `/tmp`. Before returning, `git status --short`
must list exactly the two target files; the public validator enforces this.

`decision-contract.json` publishes the required claim/option/constraint,
confidence/status vocabulary, minimum evidence obligations, and bounded decision space. It deliberately leaves control,
unknown, and trigger IDs to the author and permits either A or B as the eventual
target after the D migration bridge, provided the selected target's evidence
and controls are traced. Do not infer a hidden preferred identifier or wording.

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
