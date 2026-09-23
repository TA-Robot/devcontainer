---
name: verify-product-experience
description: Run the product and verify the user-visible experience through real interaction with captured evidence, not only unit tests. Use for UI, CLI, or API changes that affect what users see or do, before a demo or milestone exit, and to give the end-user lens real evidence instead of code-reading guesses.
---

# Verify product experience

Tests prove code paths; this skill checks what a user actually meets. Report exactly what was exercised and what was not.

## 1. Pick the journeys

Derive user journeys from the task, `docs/product/brief.md`, and the current milestone in `docs/product/roadmap.md`: start state, user goal, and success signal. Include the first-run path and at least one failure path when the change touches them.

## 2. Start the product

Use the documented run command from `AGENTS.md` or the README. A product that cannot start from its documentation is a finding. Use a free port and stop every process you start.

Keep evidence out of the working tree: write screenshots and logs to a temporary directory such as `mktemp -d`, or to a path the project already ignores, and report the paths.

## 3. Exercise the surface

**Web UI.** Prefer the project's own Playwright dependency when it exists. Otherwise use the devcontainer browser tools when installed:

```bash
with-browser-tools playwright --version
with-browser-tools playwright screenshot --full-page http://localhost:PORT/ "$OUT/home.png"
with-browser-tools node flow.cjs   # CommonJS script: require("playwright")
```

In a scripted flow, perform the journey step by step, take a screenshot after each meaningful step, and collect console errors, failed requests, and unexpected navigation. Check a desktop viewport and a narrow mobile viewport. For basic accessibility, walk the main path with the keyboard only and check the accessibility tree for unlabeled controls.

**CLI.** Run the commands a new user would run: help, the main task, invalid input, and a missing prerequisite. Capture output and exit codes.

**API.** Exercise the main sequence and its error cases with `curl` or the project client. Check status codes, error bodies, and idempotency where it matters.

## 4. Judge with the end-user lens

Answer the questions in `.agent/lenses/end-user.md` from what you observed. Separate observed problems from suspected ones.

## 5. Report

- journeys exercised, with pass / fail per step;
- evidence paths (screenshots, logs);
- issues with reproduction steps and user impact;
- what was not verified and why.

If no browser tooling is available, say so and do not claim visual verification. `with-browser-tools` explains how to enable the opt-in devcontainer tools; alternatively propose adding Playwright to the project under its dependency policy.
