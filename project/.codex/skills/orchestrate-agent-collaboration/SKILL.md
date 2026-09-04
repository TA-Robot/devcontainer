---
name: orchestrate-agent-collaboration
description: Plan and adapt multi-agent collaboration for a nontrivial development goal when delegation is allowed. Use at goal start, after a strategy is falsified or repeated work stops producing new evidence, when distinct candidates become comparable, or before independent verification and integration. Select participants and exchanges from the current mechanism, bottleneck, permission boundary, and evaluator; never impose a fixed agent count or round count.
---

# Orchestrate agent collaboration

Read `AGENTS.md` and `docs/agents/collaboration-playbook.md`. Keep the primary responsible for decisions, synthesis, integration, and user-facing conclusions.

## Build the current decision

1. State the artifact or decision, acceptance evidence, scope, risk, and binding constraint.
2. Name the improvement mechanism that collaboration could add: latency overlap, context partitioning, coverage, error decorrelation, empirical selection, or evidence-producing refinement.
3. Choose the relation from the work, not from a default count:
   - `delegate` independent bounded artifacts or shards.
   - `consult` for a genuinely distinct perspective, evidence source, or failure hypothesis.
   - `compete` only when approaches differ materially and one evaluator can distinguish them.
   - `verify` a fixed artifact against a named failure mode.
   - `solo` when serialization, review, integration, permission, or evaluator cost dominates.
4. Derive each participant from its unique artifact, perspective, approach, or error mode. Do not duplicate the same prompt merely to increase votes.
5. Give every participant a bounded brief: context paths, allowed actions, expected evidence or artifact, acceptance, and stop condition. Keep the primary on integration-critical work.

## Preserve the permission claim

- Use native Lane R only when the parent is safe.
- Use an `agentctl` safe read job when cross-provider Codex / Claude / Grok consultation or a durable structured result is valuable. It runs in the registered checkout without a worktree and does not inherit a trusted interactive parent's native-child override.
- Treat a clean registered checkout as a precondition for `agentctl` read jobs,
  not as a cleanup request to the worker. Run pre-implementation consultation
  before mutation. For review of an implementation, create a controller-owned
  checkpoint commit first and bind the review task to that SHA. If an
  uncommitted diff must be reviewed, use an explicitly permitted native
  advisory child or a separately prepared snapshot; do not send a shared dirty
  checkout to Lane R and reinterpret the inevitable dirty-state failure as a
  successful job.
- Before creating an `agentctl` participant job, save the primary-owned collaboration decision packet and pass it through `agentctl job create --collaboration-decision <path>`. The broker validates the packet, checks its immutable base, computes the digest, and derives the content-free task projection. Do not hand-copy the projection or ask the user to annotate it. If no packet exists, the job remains visibly uncorrelated rather than receiving inferred semantics.
- If the whole session or workspace is explicitly authorized for `trusted-fast`, bounded consult / verify children may run as `trusted advisory`. State that their read-only instruction is behavioral, not enforced isolation. Do not ask them to edit files or perform external side effects.
- Do not extend permission granted to one write job to unrelated children.
- Use a dedicated worktree for each write agent. Use isolation when credentials, untrusted code, Docker state, or destructive actions require a real boundary.
- If delegation is unavailable, continue solo and do not claim independent review or parallelism.

## Adapt while executing

Re-evaluate the collaboration decision when evidence changes, especially when:

- the current strategy is falsified;
- repeated iterations remain in one failure class without a new claim transition;
- distinct candidates become measurable;
- an artifact stabilizes enough for independent verification;
- review, integration, quota, or shared-resource cost becomes the bottleneck.

Do not use revision count, elapsed time, participant count, or exchange count alone as a global trigger. Ask what changed the expected value of solo, consult, compete, or verify.

Prefer deterministic parallel compute for parameter or seed coverage. Use agents where independent reasoning, implementation, or checking adds evidence. For optimization work, a useful progression can be: primary establishes a measurable baseline; consultation produces distinct failure hypotheses; competing agents implement materially different strategies in separate worktrees; the primary evaluates them under one contract; a fresh verifier checks the selected artifact. Apply only the stages whose expected benefit exceeds coordination cost.

## Stop and synthesize

Stop a participant or exchange when acceptance is met, its hypothesis is falsified, it adds no new evidence, authority is needed, or expected gain falls below coordination cost. Synthesize by evidence rather than vote and record:

- what collaboration changed;
- the decision packet and correlated `agentctl` job IDs;
- decisive tests or artifacts;
- rejected alternatives and why;
- elapsed / coordination / integration cost that can be observed;
- missing evidence and the next re-evaluation trigger.

Use `$review-collaboration-evidence` when retained project evidence exists. An `unmeasured` report is not a blocker and must not be converted into a global default.
