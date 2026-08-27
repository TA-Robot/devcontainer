# Synchronize backend migration documentation

Update `docs/ARCHITECTURE.md` and `docs/MIGRATION.md`, create
`docs/RECOVERY.md`, and create `docs-index.json`. Derive current/target backend,
compatibility-window, rollout, rollback, cleanup-gate, and ownership facts from
the visible Python and Bash implementation.

The index must map facts to source symbols and document anchors, define the
ordered replay scenarios, and use the exact commands shown in the documents.
Cover upgrade, mixed-version operation, interruption/abort, non-destructive
rollback export, and evidence-gated compatibility removal. Cross-document links
and owner assignments must agree.

Do not modify implementation source or validators. Work only inside this
disposable repository, do not use the network, and do not inspect parent
directories.

Validate with:

```bash
python3 tools/check_docs_index.py docs-index.json
python3 tools/check_links.py docs
bash tools/replay_migration_docs.sh docs-index.json
```
