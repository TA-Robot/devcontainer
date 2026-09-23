---
name: kickoff-project
description: Turn a new product idea or a freshly installed agent template into an agreed product direction and a working, verified skeleton. Use right after the template is installed, when docs/product/brief.md still contains placeholders, or when the user describes a new product or a major new initiative. Produces the product brief, explicit assumptions, materially different directions with a recommendation, a walking skeleton with quality gates, and the first milestone, asking the user only direction-changing questions.
---

# Kick off a project

Own the outcome. The user brings intent and authority; the primary brings structure, missing perspectives, and a running skeleton. Never hand the user a form to fill in. If `docs/product/brief.md` is already `agreed`, use `$review-product-direction` instead.

## 1. Read before asking

Read `AGENTS.md`, `docs/product/`, `docs/agents/decisions.md`, the README, manifests, CI files, and recent Git history. Detect languages, package managers, test / lint / build commands, and deployment hints.

Replace the `<<...>>` project values in `AGENTS.md` with detected facts. Write `unknown` rather than inventing a command, and keep the unknowns for step 3.

## 2. Draft the brief from what is known

Write `docs/product/brief.md` from the user's statements and the repository. Keep what the user said, what the code shows, and what you infer visibly separate. Move every uncertain claim into `docs/product/assumptions.md` with its kind, confidence, impact if wrong, and the cheapest test.

Apply the `pre-mortem` and `product-strategy` lenses from `.agent/lenses/` to the draft yourself, or through `advisor` agents when delegation is allowed and an independent view is worth its cost. Record the findings the brief does not already cover.

## 3. Ask only direction-changing questions

Put candidate questions in the assumptions file. Ask the user only the ones whose answer changes direction, scope, or priority now, in one short batch. For each, state the default you will use if the user does not care, so the user can simply confirm. Proceed on recorded defaults for the rest.

## 4. Diverge before converging

Before committing to a solution, lay out directions that differ in substance: problem framing, target user, interaction model, delivery form, or architecture. Use the `reframe` lens to escape the first idea. Include a direction only when it would win under some identifiable condition; if the constraints leave one viable direction, write down why.

When anchoring is the risk and delegation is allowed, follow `$orchestrate-agent-collaboration`: give `advisor` agents the same brief with different lenses and keep them blind to each other's drafts. Derive each participant from a named risk or open assumption, not from the size of the lens catalog.

Compare directions on the brief's outcome, principles, riskiest assumptions, and cost. When the comparison cannot decide, propose the cheapest discriminating test (a paper prototype, spike, or user question) instead of debating. Present a recommendation, its trade-offs, and what evidence would change it. The user decides. Record the result in the brief's "Directions considered" and, for lasting choices, in `docs/agents/decisions.md`.

## 5. Build a walking skeleton with quality gates

Build the thinnest end-to-end path through the chosen direction that a user or client could exercise. It should include:

- one command that runs the product locally;
- at least one automated test on the real path, plus lint / format;
- a single check command suitable for CI, and CI configuration when the project uses a hosted repository;
- for user-facing products, a demo path verified with `$verify-product-experience`.

Follow the dependency policy in `AGENTS.md`. Propose new dependencies with reason, alternatives, and removal path when approval is required. Replace the provisional commands in `AGENTS.md` with the ones that now work.

## 6. Plan the first milestone

Fill the current milestone in `docs/product/roadmap.md`: a user-visible goal, a definition of done expressed as objective checks, the minimum must-do work, explicit non-goals, and the assumption ids the milestone should retire. Send everything else to the deferred table with a revisit trigger.

## 7. Hand off

Report briefly:

- the problem, target user, and chosen direction, plus rejected directions and why;
- the riskiest assumptions and how the first milestone tests them;
- questions still open for the user;
- skeleton evidence: commands run and their results;
- the next concrete step.

Stop when the brief is agreed and the skeleton checks pass, when a blocking question needs the user, or when the user ends the kickoff. Mark any unfinished section instead of presenting a draft as agreed.
