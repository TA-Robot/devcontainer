# Build the cross-boundary threat model

Create `THREAT-MODEL.md` and `threat-model.json` for the visible worktree,
Docker-bind construction, credential projection, and cleanup lifecycle.
The structured model must cover these public attack kinds:

- `worktree-marker-race`
- `bind-option-injection`
- `credential-scope-loss`
- `cleanup-owner-confusion`

For each, map preconditions, executable evidence, impact, preventive and
detective controls, a negative test, detection, containment, and a recovery
owner. Include the public topology and lifecycle, single-control
counterexamples, and explicit unknowns for host/kernel, Docker daemon, and
provider guarantees. A read-only rootfs must not be described as isolating a
mounted host socket.

The visible attack runner safely simulates Docker/Git/process/provider
boundaries; it never invokes a Docker daemon or uses real credentials. Do not
modify implementation source, scenarios, tests, or validators.

Validate with:

```bash
python3 tools/validate_threat_model.py threat-model.json THREAT-MODEL.md
bash scenarios/run-visible-attacks.sh threat-model.json
python3 -m unittest discover -s tests -v
```

