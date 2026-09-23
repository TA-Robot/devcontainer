Complete the same project lifecycle feature for interruption, concurrent use, recovery, and distribution in the devcontainer. Preserve phase 1 and phase 2 behavior.

Add:

    manage-agent-project recover --target TARGET --json
    manage-agent-project rollback --target TARGET --transaction ID --json

Required transactional behavior:
- Concurrent mutating operations on one target cannot interleave writes or publish contradictory ownership. Use an actual ownership/locking mechanism; separate target projects remain independent.
- Before changing target files, durably record the before-images and enough transaction state to recover a process crash. Stage content/preconditions before applying. A failure after changing one path must remain detectable.
- For reproducible CLI fault injection, support AGENT_PROJECT_TEST_CRASH_AFTER_REPLACE=N (positive integer) to terminate abruptly with exit 99 immediately after the Nth target file replacement/deletion in apply, after its recovery data is durable. It must be opt-in and documented as a test facility. Normal operation is unchanged without it.
- status includes pending_transaction (string or null). While a transaction is incomplete, another apply/adopt/rollback must refuse to mutate the project. Recovery is explicit.
- recover rolls an interrupted transaction back to its before-images and prior ownership, then marks it recovered. Repeated recovery with no pending transaction returns status "noop". If a user edited an affected path after interruption, refuse without overwriting that edit or any other affected file; explain what needs manual resolution. Preserve unrelated files and edits.
- rollback of the latest completed transaction restores its prior managed content and metadata. It requires unchanged after-images on affected paths, rejects rollback across later transactions, and does not discard intervening user edits. A repeated already-completed rollback is a no-op. Transaction IDs are opaque input: reject paths/traversal and unknown IDs.
- Corrupt/tampered recovery metadata, symlink replacement, and missing backups fail closed; they must not cause broad deletion or overwrite. A multi-file conflict is discovered before any partial rollback/recovery write.

Ship the tool and its default template in the devcontainer image. The installed manage-agent-project must work when invoked from an unrelated current directory, with no source repository mounted; plan/adopt can omit --source to use the shipped template. Explicit --source still works for repository development. Keep checkout execution and installed execution unambiguous. Update README and the lifecycle documentation with install, conflict resolution, adoption, interrupted update, rollback, limits, and verification instructions.

Validate unit/CLI lifecycle tests, injected crashes, two concurrent clients, old-state compatibility, actual template contract validation, and the required standard/frozen container builds and relevant smoke checks from AGENTS.md. Do not label unexecuted checks passed if the execution environment blocks them. Avoid broad Docker cleanup or changes to unrelated host state. Leave a reviewable complete implementation, tests, documentation and container packaging, with a factual handoff of validation and remaining risks.
