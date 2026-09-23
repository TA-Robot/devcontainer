# F02-L-PYBASHJS-001: review provider-hook lifecycle

Review the complete lifecycle proposal in `change.diff`, spanning the Bash wrapper, Python event store, JavaScript restart renderer, and cleanup script. Do not patch the proposal.

Write ranked findings to `review.json`. The public validator defines the exact JSON shape. Every blocking finding must include:

- a separate, reachable category and concrete boundary trigger;
- impact code, severity, and source-chain evidence whose path/symbol/line/snippet resolve;
- bounded remediation constraints that preserve the wrapper's fail-open provider-result behavior where relevant.

Also include a structured `lifecycle` model covering input, persistence, restart/render, and cleanup/ownership, plus relations between findings where state or ownership crosses boundaries. Reproduce normal, error, restart, and cleanup implications from repository-contained evidence. Do not elevate cosmetic CSS or comment changes to blocking findings.

For machine comparison, use these canonical codes while deriving their values and evidence from the fixture:

- `redaction-order` / trigger `multiline-oversized-event` / impact `credential-fragment-persisted`
- `stale-restart` / trigger `restart-with-stale-transient` / impact `stale-active-render`
- `cleanup-owner-prefix` / trigger `peer-prefix-resource` / impact `peer-resource-deletion`

The lifecycle stages are `input`, `persistence`, `restart`, `render`, `cleanup`, and `ownership`. A supported redaction-to-restart relation uses mechanism `persisted-event-replayed-after-restart` and consequence `unsafe-state-survives-process-boundary`. Finding IDs and their relative order remain your choice; rank all three blocking findings ahead of any non-blocking observation.

Scope:

- Read repository-contained source, tests, scripts, and the proposed diff.
- Write only `review.json`; do not modify source, tests, or validation tools.
- Do not use the network or inspect paths outside this fixture.

Validation:

```bash
bash tests/replay-review-surface.sh
python3 -m unittest discover -s tests -v
node --test extension/test/*.test.js
python3 tools/validate_review.py review.json
```

Return a concise summary of findings and validation results.
