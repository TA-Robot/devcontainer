# F05-L-PYBASH-001: backend and schema migration

Complete the job-ledger migration behind `JobBackend`, preserving v1 reads while introducing canonical schema v2 persistence, crash-safe resume, and non-destructive rollback export.

Requirements:

- Implement coherent file and memory backends. Migration and CLI command logic depend on the backend contract and must not reach into `FileBackend` paths.
- Preserve v1 read/list behavior throughout the declared compatibility window.
- Convert v1 job arrays into canonical v2 items without losing, duplicating, or changing job status.
- Stage a complete v2 candidate and journal before atomically replacing the committed state. Never expose a committed `version: 2` with incomplete v2 data.
- Support deterministic interruption cuts before the journal, after the journal, and after commit. A fresh-process retry must resume idempotently at every cut.
- Export rollback to a separate canonical v1 file; do not modify the v2 source.
- Preserve `--backend` selection through Python and `bin/jobctl`; the wrapper must forward all arguments and exit status.
- Complete `MIGRATION.md` with an executable migration/resume/rollback manifest, ownership, backup, and per-cut recovery behavior.
- Preserve old tests, use only the standard library, and do not weaken validators.

Validation:

```bash
python3 -m unittest discover -s tests -v
bash -n bin/jobctl
bash tests/migration-lifecycle.sh
python3 tools/check_docs.py MIGRATION.md
```

Return a concise summary of the backend boundary, commit ordering, rollback behavior, changed files, and validation results.
