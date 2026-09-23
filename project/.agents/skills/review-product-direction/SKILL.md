---
name: review-product-direction
description: Step back from implementation to check whether the product is heading where it should. Use when a milestone completes or stalls, before choosing the next milestone, after an important assumption is refuted, when the plan has gone unchallenged for a while, or when the user asks what they are missing. Applies selected perspective lenses, classifies findings, updates docs/product, proposes the next milestone, and tells the user only what changes a decision.
---

# Review product direction

The primary owns the review, its conclusions, and every document update. The aim is to surface what the user did not think to ask, without flooding them.

## 1. Gather evidence

Read `docs/product/brief.md`, `assumptions.md`, `roadmap.md`, and `docs/agents/decisions.md`. Compare the current milestone's definition of done with objective evidence: commands run, demo results, `$verify-product-experience` output, and user feedback. Use `$review-collaboration-evidence` only when orchestration cost is itself in question.

## 2. Close or re-scope the milestone

Record the milestone in "Completed milestones" as shipped, partial, or stopped, with evidence. Never mark it shipped without evidence. If it stalled, identify whether the cause is scope, a refuted assumption, a technical blocker, or a missing decision.

## 3. Apply lenses selected from risk

Choose lenses from `.agent/lenses/` by naming the risk each one addresses: an untested high-impact assumption, a new user-facing surface, new data or an external dependency, rising cost, or a plan nobody has challenged. Skip lenses that cannot change a decision now.

When delegation is allowed, run `advisor` agents with one lens each in parallel for coverage and latency overlap; brief them per `.agent/lenses/README.md`. Otherwise apply the lenses sequentially yourself and do not claim independent review.

## 4. Classify every finding

Decide each finding yourself; do not adopt advisor output by vote.

- `fix-now`: blocks the next milestone or risks safety, data loss, or a wrong completion claim.
- `scheduled`: valuable later; goes to the roadmap's deferred table with a revisit trigger.
- `accepted-risk`: known and consciously accepted; record why.
- `out-of-scope`: unrelated to the product's goal; record briefly.

Log them in the "Perspective findings" table. Add or update assumptions, including refuted ones.

## 5. Update direction documents

Change the brief only when evidence changed the problem, users, principles, or scope, and say what changed. Record lasting decisions in `docs/agents/decisions.md`.

## 6. Propose the next milestone

List candidates by user value and the assumptions they would retire, and recommend one. Fill the current milestone in the roadmap only after the user agrees, or when the user has delegated that choice.

## 7. Tell the user what matters

Keep the message short:

- the milestone result and its evidence;
- the few findings that change a decision, including ones the user did not ask about, each with its implication and your recommendation;
- questions only the user can answer, each with your proposed default;
- the recommended next milestone.

Leave the remaining findings in the documents instead of listing them. Stop when the documents are updated and the next milestone is proposed, or when a decision needs the user.
