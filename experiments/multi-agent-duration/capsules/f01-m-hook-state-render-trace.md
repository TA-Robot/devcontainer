# F01-M-PYJS-001: trace hook state to the renderer

Trace a successful `tool_end` event from the Python hook input through the atomic JSON state boundary to the JavaScript renderer. Also document malformed-input and atomic-write-failure behavior. The production code is already correct; do not change it.

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
  "contracts": [
    {"id": "contract-id", "producer": "node-id", "consumer": "node-id", "path": "schema/path", "fields": ["field"]}
  ],
  "branches": [
    {"id": "branch-id", "from": "node-id", "outcome": "observable outcome", "path": "repository/path", "symbol": "exact source symbol"}
  ],
  "uncertainties": []
}
```

Requirements:

- Use contract ID `mira-state-v1` and branch IDs `malformed-input` and `atomic-write-failure`; node IDs remain your choice as long as all references are internally consistent.
- The success graph must cover event normalization, the canonical envelope, state reduction, atomic storage, the versioned JSON schema, JavaScript decoding, world-state mapping, and rendering.
- Record the producer/consumer field contract across the JSON boundary, including every persisted state field used by the fixture.
- Record malformed input and atomic write failure as separate branches with their distinct last-good-state outcomes.
- Every cited path must exist and every symbol must be spelled exactly as it appears in that file.
- Do not route renderer input through either telemetry helper; they are unrelated distractors.
- Put any unresolved claim in `uncertainties`; do not invent evidence.
- Do not edit production code, tests, tools, instructions, or Git metadata.

Validation:

```bash
python3 -m unittest discover -s tests -v
node --test media/test/world.test.js
python3 tools/validate_trace.py trace.json
```

Return a concise summary of the success path, both fail-open paths, and validation results.
