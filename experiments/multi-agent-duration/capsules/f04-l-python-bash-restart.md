# F04-L-PYBASH-001: persistent queue lifecycle

Complete the persistent queue implementation across the Python storage module, Python CLI, and Bash entrypoint.

Requirements:

- `bin/queuectl --store PATH enqueue ID PAYLOAD` creates one pending item.
- `bin/queuectl --store PATH ack ID` marks an existing item acknowledged.
- Repeating `ack` for an acknowledged item succeeds without changing its acknowledgement count or duplicating data.
- Acknowledging an unknown ID exits 4 and leaves the store byte-for-byte unchanged.
- `bin/queuectl --store PATH pending` prints pending IDs in lexical order, one per line.
- State remains correct when each command runs in a fresh process.
- Writes replace the state atomically and never overwrite malformed existing JSON.
- The Bash entrypoint forwards all arguments and preserves the Python process exit status.
- Do not add third-party dependencies.

Scope:

- Preserve the separation between `queue_store.py`, `queue_cli.py`, and `bin/queuectl`.
- Keep the on-disk schema documented in `FORMAT.md` compatible with existing version 1 files.
- Add or update unit and lifecycle tests where useful.

Validation:

```bash
python3 -m unittest discover -s tests -v
bash -n bin/queuectl
```

Return a concise summary of implementation choices, changed files, and validation results.
