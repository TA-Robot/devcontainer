# Legacy `second-agent` compatibility runbook

Status: feature-frozen compatibility path. New projects should use native agents plus the `.agent` task / result contract. This runbook exists only to finish or recover existing `codex-second-agent` / `claude-second-agent` work safely.

Policy and retirement gates are in [`legacy-second-agent.md`](legacy-second-agent.md). Do not add new orchestration behavior to the legacy engine.

## Identify the configured workspace

```bash
codex-second-agent paths
codex-second-agent doctor
codex-second-agent status --verbose
```

For Claude-backed legacy state, replace `codex-second-agent` with`claude-second-agent`.

If no workspace is configured and an old job must be completed:

```bash
codex-second-agent workspace init <target-project-git-root>
```

Do not point this at the devcontainer basis repository when the intended target is another Git project.

## Continue an existing named agent

```bash
codex-second-agent --agent <existing-agent-name> "<bounded follow-up>"
```

The agent name is legacy identity: it may also select an existing session, branch, worktree, lock, and log path. Do not rename it mid-recovery.

## Observe background work

Resolve paths first instead of guessing:

```bash
codex-second-agent --agent <agent-name> paths
codex-second-agent --agent <agent-name> status --verbose
```

- `transcript.jsonl` is the normal human-readable history.
- `events.jsonl` is provider/debug detail.
- redirected `nohup` stdout can remain empty and is not completion evidence.
- a missing shell PID is not success; inspect the worktree and logs.

Use a bounded timeout for read-only reviewer calls when terminal return is required. A timeout is a failed/interrupted attempt until its result is recovered and validated.

## Recover a stopped legacy write agent

1. Run `paths`, then inspect the exact reported worktree.
2. Record `git status --short`, `git log --oneline`, and the branch head.
3. Preserve useful dirty changes as a reviewed patch or explicit commit.
4. Finish the old session only if its workspace and intent are still valid.
5. Otherwise create a new native-contract job from a full base SHA and pass the recovered commit / patch as explicit context.
6. Never treat a stale session ID as the new job identity.

## Integrate

The legacy worker still must not merge or push to main. The primary agent checks its commit, scope, tests, and dirty state, then performs single-writer integration. Translate the handoff into the common result fields where practical:

- summary
- full head SHA
- changed paths
- dirty state
- checks and exit codes
- risks and followups

## Remove a legacy worktree

Only after changes are integrated or intentionally abandoned:

```bash
codex-second-agent worktree remove <agent-name> --keep-branch
```

Keeping the branch is the conservative first cleanup. Delete a branch only after separately proving it has no unique commit. Never bulk-delete legacy state during migration.

For a read-only inventory of all local legacy state, use:

```bash
agentctl legacy inventory
agentctl legacy inventory --json
```
