# F01-S-PY-001: trace the `--state-dir` value

Explain where `--state-dir` is defined and how its parsed value reaches ownership validation and the final state-store consumer. The production code is already correct; do not change it.

Create only `trace.json`, with this versioned shape:

```json
{
  "trace_version": 1,
  "nodes": [
    {"id": "unique-id", "path": "repository/path", "symbol": "exact source symbol"}
  ],
  "edges": [
    {"from": "node-id", "to": "node-id"}
  ],
  "uncertainties": []
}
```

Requirements:

- Record ordered semantic nodes for the parser definition, parsed namespace field, dispatch argument, normalization, ownership-marker validation, and final consumer.
- Every edge endpoint must name a declared node ID and the edges must preserve causal value-flow order.
- Every node must cite an existing repository-relative path and a symbol spelled exactly as it appears in that file.
- Exclude similarly named helpers that do not receive the CLI flag.
- Put any unresolved claim in `uncertainties`; do not invent evidence.
- Do not edit production code, tests, tools, instructions, or Git metadata.

Validation:

```bash
python3 -m unittest discover -s tests -v
python3 tools/validate_trace.py trace.json
```

Return a concise summary of the traced path and validation results.
