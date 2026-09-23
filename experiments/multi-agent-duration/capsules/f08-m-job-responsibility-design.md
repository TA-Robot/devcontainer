# F08-M-MDJSON-001: local job responsibility architecture

Design the scheduler/supervisor/store responsibility split from `system.md`, `scenarios.json`, and `options/catalog.json`. A composed split is allowed; do not implement it.

Create only `PROPOSAL.md` and `proposal.json`. The JSON contract is:

- `schema_version`: `1`, plus a descriptive `selected_design` ID.
- `invariants`: every visible invariant ID and the visible scenario IDs that test it.
- `state_ownership`: exactly one owner and durability value for every visible state ID.
- `policies`: responsibility/restart policies using the exact public keys and values in `required_policies`.
- `transitions`: every visible scenario ID, its event trace, and observable result.
- `rejected_options`: every raw option ID, its declared counterexample scenario, expected failure, and executable simulator command.
- `migration`: ordered visible phases and an explicit rollback boundary.
- `observability`: every visible signal ID with an accountable component owner.
- `guarantees`: only evidence-supported guarantees.
- `unknowns`: all visible evidence-gap IDs retained as unknown with decision impact.
- `document_markers`: unique markers mirrored in Markdown as `<!-- architecture-marker:MARKER -->`.

Requirements:

- Preserve at-least-once execution, durable cancellation, a finite retry budget, and one process owner through restart/cancel/timeout/retry traces.
- Durable intent/budget/cancel data and ephemeral process/heartbeat/admission state each have exactly one visible contract owner.
- Rejections must reproduce fixture-declared failures; preference language alone is insufficient.
- Migration and the queue/provider/worker/retry/cancel signals must be actionable.
- Provider idempotency and heartbeat threshold remain unknown; do not claim exactly-once execution.

Validation:

```bash
python3 tools/validate_proposal.py proposal.json PROPOSAL.md
python3 simulator.py --proposal proposal.json --all-scenarios
```

Return the responsibility split, failure evidence, open gaps, and validation results.
