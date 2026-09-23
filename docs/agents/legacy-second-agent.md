# Legacy `second-agent` policy and recovery

## Status

`scripts/second-agent` and its Codex/Claude shims are **legacy and feature-frozen**
from 2026-08-12. They remain supported during the parallel migration period.

Allowed changes:

- security and credential-exposure fixes;
- data-loss, path-scope, cleanup, and false-success fixes;
- compatibility fixes required to keep the pinned stable CLIs working;
- tests and documentation that make existing behavior observable.

Not accepted in the legacy engine:

- another provider adapter;
- job/attempt state machines, schedulers, detached supervisors, or Docker leases;
- new implicit retries or automatic integration;
- silent forwarding to `agentctl`.

Those capabilities belong to the new execution fabric described by
[`ADR-0001`](../adr/0001-native-first-multi-agent-execution.md).

## Non-destructive inventory

From the target repository, run:

```bash
agentctl legacy inventory
agentctl legacy inventory --json
```

The inventory is read-only. It lists session files, known state/worktree paths,
matching local branches, and log bytes for both backends. It does not infer that
a saved session is still live and never removes anything.

The provider-specific legacy commands remain useful for detail:

```bash
codex-second-agent agents
codex-second-agent --agent NAME status --verbose
codex-second-agent worktree list
claude-second-agent agents
claude-second-agent --agent NAME status --verbose
claude-second-agent worktree list
```

## Recovery contract

1. Stop issuing new work to the affected agent name.
2. Capture `status --verbose`, `paths`, the last bounded log lines, `git status
   --short`, and `git worktree list --porcelain`.
3. Treat a missing process or an empty `nohup` file as unknown, not success.
4. Inspect and commit/recover useful work from the worktree before cleanup.
5. Use `reset` only to discard the saved provider session ID. It does not delete
   the worktree or logs.
6. Use `worktree remove NAME --keep-branch` when the branch is the recovery
   artifact; omit `--keep-branch` only after its contents are known expendable.
7. Never delete legacy state as part of new-fabric installation or migration.

There is no in-place conversion of provider session state. Finish or abandon the
legacy session explicitly, then pass a reviewed commit SHA into the new path.

The command-by-command compatibility procedure is kept separately in
[`legacy-second-agent-runbook.md`](legacy-second-agent-runbook.md) so wrapper
choreography does not leak back into the native-first project template.
