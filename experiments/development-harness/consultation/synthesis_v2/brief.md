# Structured fabric decision — scope v2

Compare supplied proposals A/B/C/D, benchmarks, incidents, security findings and migration
constraints. Produce `decision-record.json` and `DECISION-RECORD.md` only. Do not change
inputs/tools, execute submitted gate commands, add dependencies, call providers or other agents.
Temporary files belong in `/tmp`. The controller supplies a separate contract for any advisor.

Start from `decision-record.template.json`; follow `decision-contract.json`.
Use record `version: 2` and `evaluation_contract: consultation-synthesis-scope-v2`.
The old F12 record is a different task version and is not automatically converted or rescored.

Each claim has `scope: {population, workloads}`. `supplied-samples` describes only the
supplied numeric observations for the listed workload, without population, throughput,
production-tail or universal claims. `supplied-evidence` describes only the supplied
qualitative evidence/constraints; `not-established` records a claim that evidence cannot
establish. The permitted scope for each claim and minimum evidence/provenance edges are
published in `claim_scopes` and `claim_evidence`. C's pooled measurements cannot establish
throughput; reject that claim. D's recovery claim remains unknown with missing evidence.

Every unknown has a unique author-chosen `unknown_id`, `status: unknown`, nonempty
`missing_evidence`, known evidence references (an empty list is allowed when evidence is
absent) and nonempty `topics`, a list of unique topic strings. Cover both `recovery` and
`provider`. Every `recovery` item must cite `INC-D-RECOVERY`. Additional topics and multiple
items per topic are allowed. One item may concern multiple topics. There is no exact-one
topic count and no requirement to use the English word provider in explanatory prose.
Keep at least two unknown items, matching the explicit minimum in the contract.

All evidence references must exist in `evidence/index.json`; all claim provenance paths
must identify supplied sources. IDs are unique within each collection (including all
phase gates together, and all rollback triggers together). Gate references from the
constraint matrix must resolve to a gate or rollback trigger. Preserve numeric types:
booleans are not numbers. Fields are exactly those published in `required_fields` and
`record_fields`; scope has exactly the two fields above. Collections have at most 128 items.

Run these public tools from the workspace root:

```bash
python3 -B tools/synthesis_rules.py render
python3 -B tools/synthesis_rules.py check
```

Rendering includes the entire JSON record in Markdown, with deterministic formatting;
do not hand-edit the generated Markdown. The check reports requirements separately.
The external evaluator also rejects modified inputs, extra paths, symlinks/nonregular
files and files over 262144 bytes; `.git` is controller metadata and is never executed.

Free prose (including negation, quotations and non-English explanations) is not interpreted
for truth. Structured scopes and evidence edges are authoritative for scoring. Contradictory
prose can therefore remain undetected. Owners, gates, rollback actions and decision effects
are checked for required structure/references, not for real operational effectiveness.
Passing means structured evidence assembly, not general design quality or collaboration benefit.
