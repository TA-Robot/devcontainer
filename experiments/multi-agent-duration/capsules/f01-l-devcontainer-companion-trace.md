# F01-L-PYBASHJS-001: trace the devcontainer companion lifecycle

Produce a cross-boundary lifecycle trace from devcontainer rebuild through Mira world rendering. The fixture simulates the lifecycle locally; do not modify it or claim the frozen legacy wrapper participates in the active path.

Create only `trace.json`, with this versioned shape:

```json
{
  "trace_version": 1,
  "nodes": [
    {"id": "unique-id", "path": "repository/path", "symbol": "exact source symbol", "location": "host|container|extension"}
  ],
  "edges": [
    {"from": "node-id", "to": "node-id", "artifact": "transported artifact", "owner": "boundary owner"}
  ],
  "recoveries": [
    {"id": "failure-id", "owner": "responsible component", "recovery": "concrete recovery", "retained_state": "state retained across recovery"}
  ],
  "uncertainties": []
}
```

Requirements:

- Node IDs remain your choice. Use recovery IDs `missing-wrapper`, `stale-runtime-state`, and `extension-restart` for machine comparison.
- Use transported-artifact vocabulary `initializeCommand`, `provider-wrapper-cache`, `installed-provider-wrapper`, `provider-activity-event`, `activity-envelope-v1`, `mira-state.json`, and `companion-state-v1`; use owner vocabulary `devcontainer-host`, `host-provisioner`, `container-startup`, `agentctl`, `mira-hook`, `companion-state-bridge`, and `mira-extension`.
- Cover rebuild configuration, host initialization, container post-start, provider activity, the `agentctl` envelope, hook persistence, extension state loading, and world rendering.
- Label each node `host`, `container`, or `extension` according to where it executes.
- Every edge must name the concrete transported artifact and its owner.
- Follow provider wrapper/version material from host preparation into container runtime, then follow provider activity to the rendered world.
- Record separate recovery ownership, concrete recovery, and retained state for a missing wrapper, stale runtime state, and extension restart.
- Exclude `scripts/second-agent`; it is a deliberate, frozen legacy distractor.
- Every cited path must exist and every symbol must be spelled exactly as it appears in that file.
- Put any unresolved claim in `uncertainties`; do not invent evidence.
- Do not edit production code, tests, tools, instructions, or Git metadata.

Validation:

```bash
python3 -m unittest discover -s tests -v
bash tests/lifecycle-smoke.sh
node --test extension/test/world.test.js
python3 tools/validate_trace.py trace.json
```

Return a concise summary of lifecycle boundaries, recovery ownership, and validation results.
