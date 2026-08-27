# F11-L-BASHDOCKER-001: simulated devcontainer rebuild recovery

Repair the deterministic local rebuild/reopen fixture. This task must not invoke host Docker, mount a Docker socket, build an image, or touch state outside the disposable workspace and process-owned temporary trees.

The lifecycle and marker owners are public in `.devcontainer/devcontainer.json`:

1. `initialize-host` runs as host owner for CLI/extension artifacts and version-bound markers.
2. `post-create` runs as container owner for persistent schema migration.
3. `post-start` runs as container owner for verified runtime readiness.

Requirements:

- `migrate_state.py` accepts schema v1 and v2. Conversion stages a complete canonical v2 candidate and source digest beside the source, then atomically commits version and data together.
- Support deterministic cuts `before-stage`, `after-stage`, and `after-commit`; fresh-process retry resumes idempotently without losing the canonical v1 or v2 source.
- `rollback --state STATE --output OUTPUT` writes a separate canonical v1 export without modifying v2.
- `initialize-host.sh HOST_ROOT CLI_VERSION EXTENSION_VERSION [CUT]` atomically installs/verifies artifacts before writing `host-cli=VERSION` and `extension=VERSION` markers. Public cuts are `after-cli-artifact` and `after-extension-artifact`.
- Stale, missing, or boolean host markers are repaired only by their host lifecycle owner. `post-start` verifies exact artifact/version binding and must not trust marker existence alone.
- `post-create.sh VOLUME_ROOT [CUT]` propagates migration interruption and never deletes state, journal, volume, workspace, or peer files.
- `post-start.sh HOST_ROOT VOLUME_ROOT RUNTIME_ROOT` resumes migration, verifies host/extension markers and schema v2, then atomically publishes a version-bound runtime marker.
- Repeated rebuild/reopen converges without repeated installs or residual owned journals/temp files. Peer and persistent sentinels survive.
- Write `RECOVERY.md` with a JSON `recovery-contract` manifest containing exact lifecycle owners and executable `diagnose`, `resume`, `rollback-export`, `reopen-host`, and `reopen-runtime` commands accepted by the supplied validator.
- Recovery must diagnose and export original state; “delete and rebuild everything” is forbidden.

Validation:

```bash
bash -n initialize-host.sh post-create.sh post-start.sh tests/rebuild.sh
python3 -m unittest discover -s tests -v
bash tests/rebuild.sh --scenario visible-all
python3 tools/check_recovery_docs.py RECOVERY.md
```

Return the lifecycle ownership, fault-cut recovery, marker repair, rollback/export behavior, changed files, and validation results.
