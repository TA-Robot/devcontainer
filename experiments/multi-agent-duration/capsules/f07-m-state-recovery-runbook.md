# Write the state-corruption recovery runbook

Create `RUNBOOK.md` and `runbook.json` from the visible doctor, backup, and
owned-service command contracts. The Markdown and manifest must contain the
same ordered commands.

Cover read-only diagnosis, evidence preservation, backup existence and digest
verification, atomic restore, restart of only `state-worker`, and state plus
service-health postconditions. Missing and invalid backups must stop before
restore and retain the corrupt state and captured evidence byte-for-byte.
Map factual claims to visible source symbols in the manifest.

Do not modify runtime code, source facts, or validators. Work only inside this
disposable repository, do not use the network, and do not inspect parent
directories.

Validate with:

```bash
python3 tools/check_runbook.py RUNBOOK.md runbook.json
bash tools/replay_runbook.sh runbook.json healthy
bash tools/replay_runbook.sh runbook.json corrupt
```
