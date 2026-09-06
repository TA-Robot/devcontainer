# Queue implementation review and repair

Inspect the supplied queue implementation and fix violations of the following contract.
It may already satisfy the contract: do not invent defects or force a change. Preserve
working behavior. The same brief and public tools apply to every initial implementation.

- `bin/queuectl --store PATH enqueue ID PAYLOAD` stores a pending item and preserves payload bytes as UTF-8 text.
- `ack ID` acknowledges an existing item. Repeated ack succeeds with byte-for-byte unchanged state and ack_count 1.
- Unknown ack exits 4 and preserves the store. Invalid existing JSON must produce a nonzero exit without modifying it.
- `pending` prints IDs in lexical order, one per line, with exit 0.
- Every invocation works in a fresh process from an arbitrary working directory.
- Preserve argument boundaries, including spaces and Unicode in PATH/ID and spaces, quotes and newlines in PAYLOAD.
- Keep FORMAT.md's version 1 schema. Successful updates of an existing store by enqueue or ack replace
  the file: an already open reader retains the full old bytes, while opening the path returns the new state.
- Preserve the Python storage / Python CLI / Bash entrypoint separation and exit statuses. No third-party dependencies.

Only `queue_store.py`, `queue_cli.py`, `bin/queuectl` may change. You may add `tests/test_repair.py`.
All supplied tests, tools, documentation and instructions are fixed inputs. Preserve an executable
`bin/queuectl`. Temporary files belong in `/tmp`; do not create handoff files or commit.
Run public checks as often as useful:

```bash
python3 -B tools/check_queue.py
python3 -B -m unittest discover -s tests -v
bash -n bin/queuectl
```

The external checker observes the same behavioral requirements while running implementation files
in fresh containers with no network, no credentials, read-only implementation and writable temporary
state only. Submitted tests are not an external success oracle. State files must be regular files at
most 524288 bytes, implementation files at most 1 MiB, and combined stdout/stderr at most 65536 bytes per invocation.
Finish with a concise explanation of findings, changes (or why no change was needed), validation and uncertainty.

This task measures ordinary command completion and observable file replacement. Process kills during
writes, power-loss durability, concurrent writers, throughput and general design quality are not measured.
