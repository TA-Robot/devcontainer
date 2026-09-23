# ADR-0002: Product direction layer and cross-provider skills

- Status: Accepted
- Date: 2026-09-24
- Owners: repository maintainers

## Context

ADR-0001 and the collaboration model cover *how* agents execute and coordinate:
lanes, worktrees, job state, relations, and evidence. The target template had no
place for *what* to build and *why*. All roles were engineering roles, and the
persona asked for milestone goals and deferred items without anywhere to keep
them, so they were lost between sessions. Missing perspectives and product
direction depended entirely on unprompted model behavior.

Template skills also lived only in `.codex/skills/`. Codex 0.156 still discovers
that path, but its documented project location is `.agents/skills/`, Grok Build
reads `.agents/skills/` and `.claude/skills/`, and Claude Code reads only
`.claude/skills/`. A Claude or Grok primary therefore could not use the
orchestration skills. One skill also referenced a document removed from the
repository.

## Decision

1. **Product documents.** Ship `docs/product/brief.md`, `assumptions.md`, and
   `roadmap.md` in the template. The primary maintains them during normal work
   and never asks the user to fill in a form. They are context, not
   instructions, and do not change instruction precedence.
2. **Perspective lenses instead of more roles.** Add one read-only `advisor`
   role and provider-neutral lens briefs under `.agent/lenses/`. Adding a lens
   needs no provider mapping. Lenses are chosen from a named risk or open
   assumption. Neither the catalog size nor a participant count is a default.
3. **Workflow skills.** Add `kickoff-project` (idea to agreed direction and a
   verified skeleton), `review-product-direction` (milestone-boundary lens
   review with the `fix-now / scheduled / accepted-risk / out-of-scope`
   classification), and `verify-product-experience` (exercise the running
   product and capture evidence).
4. **Skill location.** Author skills once in `.agents/skills/` and mirror them
   byte for byte, excluding each skill's Codex-only `agents/` metadata, to
   `.claude/skills/`. `scripts/sync-project-skills` generates the mirror, and
   the template validator rejects drift.
5. **Reference integrity.** The template validator rejects Markdown links and
   template-path references to files the template does not ship. The one
   deliberate pointer into this base repository is allow-listed.
6. **Browser tools.** Offer Playwright with headless Chromium as an opt-in,
   image-pinned build layer used through `with-browser-tools`. See
   `docs/toolchain.md`.

## Consequences

- A new project gets a product anchor that survives sessions, plus a repeatable
  way to surface perspectives the user did not state.
- The template has two copies of each skill. The validator and sync script turn
  drift into a failed check, not a silent divergence.
- Existing installations see `.codex/skills/**` deletions on update. Locally
  edited old skills surface as conflicts, handled by the lifecycle guide's
  migration note.
- The Mira activity bridge shows `advisor` jobs with the reviewer sprite.
  There is no new visual asset.

## Non-goals

- No scheduler, recurring product review, or automatic routing.
- No automatic adoption of advisor output. The primary classifies every
  finding, and the user decides direction.
- No new agentctl runtime behavior: roles are already read from
  `.agent/config.json`.

## Revisit conditions

Revisit if the product documents go stale in practice, if lens reviews mostly
produce findings classified as `out-of-scope`, if a provider stops discovering
the chosen skill paths, or if the mirror causes repeated update conflicts.
