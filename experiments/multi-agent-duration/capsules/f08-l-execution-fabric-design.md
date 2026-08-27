# F08-L-MDJSON-001: execution fabric and persistence design

Produce an execution-fabric design using every ID and contract in `requirements/`, `proposals/`, and `evidence/`. Do not implement the fabric.

Create only `DESIGN.md` and `design.json`. The JSON contract is:

- `schema_version`: `1`, plus a descriptive `selected_design` ID.
- `requirement_dispositions`: exactly one disposition with status `satisfied` for every functional, security, and operations requirement ID; evidence IDs must be accepted by that requirement and exist in the incident evidence.
- `topology`: unique components whose `role` values cover the visible `required_roles`; each declares whether its runtime lifecycle is bounded.
- `state_ownership`: exactly one row for every visible state ID, using its declared owner and durability.
- `failure_policies`: the public scenario keys and enforceable actions defined by `requirements/model.json`; policies must compose without scenario-specific correctness exceptions.
- `migration`: every public phase in order, with its public abort action, signal, `source_preserved`, and the complete rollback contract.
- `security_controls`: every security requirement ID with its public boundary, required control, owner, and incident counterexample.
- `observability`: every public diagnostic category with its signal and owner.
- `alternatives`: every raw proposal ID with disposition `rejected-as-standalone` or `incorporated-with-mitigation`, decisive incident evidence, and declared counterexample.
- `claims`: claim IDs with non-empty, valid requirement/evidence links.
- `unknowns`: every visible evidence-gap ID retained as unknown with decision impact.
- `document_markers`: unique markers mirrored in Markdown as `<!-- architecture-marker:MARKER -->`.

Requirements:

- Jobs, leases, attempt budget, events, provider processes, credentials, cleanup, workspaces, and UI state have single ownership.
- Crash, stale lease, provider loss, credential rotation, retry exhaustion, and UI disconnect retain finite lifecycle and job correctness.
- UI is fail-open and never owns durable job truth.
- Migration is staged, observable, abortable, resumable, source-preserving, and has non-destructive rollback export.
- Workspace, credential, Docker, and host boundaries use the exact enforceable controls supplied by security requirements.
- Signals distinguish queue, provider, worker, validation, recovery, and migration state.
- Alternative decisions must account for incident evidence, not only nominal benchmark latency.
- Provider idempotency and backend scale remain unknown; do not claim exactly-once, linearizability, or production capacity.

Validation:

```bash
python3 tools/validate_design.py design.json DESIGN.md
python3 simulator.py --design design.json --scenario-set visible
bash tools/replay_migration.sh design.json visible
```

Return the selected topology, ownership and migration decisions, decisive evidence, open gaps, and validation results.
