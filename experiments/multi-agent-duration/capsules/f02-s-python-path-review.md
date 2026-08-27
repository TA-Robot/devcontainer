# F02-S-PY-001: review path containment change

Review `change.diff` for correctness and security regressions. Do not patch the proposal.

Write a ranked `review.json` containing:

- a short `summary`;
- a non-empty `findings` array with stable IDs, contiguous ranks, severity, category, title, impact code and explanation;
- for each finding, a structured `trigger`, source `evidence` with path/symbol/line/snippet, and a remediation strategy with constraints;
- `relations` and `lifecycle` arrays/objects when applicable.

The review must identify any reachable changed-line defect, provide a concrete reproducer, justify severity and impact, and avoid unsupported blocking findings on unchanged safe code. The public validator defines the exact JSON shape.

For machine comparison, a path-containment finding uses these canonical codes and trigger fields:

```json
{
  "category": "path-containment",
  "impact_code": "workspace-escape",
  "trigger": {
    "kind": "peer-prefix-path",
    "root": "absolute example root",
    "candidate": "absolute example candidate",
    "observed_acceptance": true,
    "expected_containment": false
  },
  "remediation": {
    "strategy": "canonical-relative-containment",
    "constraints": ["resolve-root-and-candidate", "use-path-relative-to", "reject-peer-prefix"]
  }
}
```

Scope:

- Read repository-contained source, tests, and the proposed diff.
- Write only `review.json`; do not modify source, tests, or validation tools.
- Do not use the network or inspect paths outside this fixture.

Validation:

```bash
python3 -m unittest discover -s tests -v
python3 tools/validate_review.py review.json
```

Return a concise summary of the finding and validation results.
