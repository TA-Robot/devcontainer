@AGENTS.md

## Claude Code native agents

Project-scoped role definitions live in `.claude/agents/`. The provider-neutral role, lane, permission, and result contracts under `.agent/` remain authoritative.

Project skills live in `.claude/skills/`, a byte-identical mirror of the canonical `.agents/skills/` (without each skill's Codex-only `agents/` metadata). Invoke them as `/name`; `AGENTS.md` writes them as `$name`.
