# Implementation and pilot roadmap

## 1. Current status

The benchmark concept is ready for fixture design, not yet for an expensive
outer run. The 1,000-idea inventory and twelve product bets define headroom;
the public brief and quality vector define the candidate/evaluator boundary.

## 2. Milestone A — Freeze revision-zero contracts

Artifacts:

- `PUBLIC-BRIEF.md` from document 07;
- JSON schemas for campaign creation, state, event, and terminal evidence;
- authority contract;
- provider adapter contract;
- evaluator observation contract independent of candidate events.

Checks:

- minimal forwarding baseline can implement the API;
- contract does not prescribe orchestration features;
- invalid/unsafe cases are deterministic;
- zero-routine-human behavior is explicit.

## 3. Milestone B — Build deterministic P0 harness

Implement fake providers for:

- delayed success;
- parallel overlap;
- malformed and oversized output;
- partial artifact then failure;
- ignored TERM and nested session;
- stale-base result;
- duplicate/idempotent result;
- unavailable/unauthenticated readiness.

Implement workspace probes for dirty state, authority escape, restart, conflict,
and cleanup. Target runtime under three minutes.

## 4. Milestone C — Build M0 forwarding baseline

The baseline is intentionally competent in protocol and process safety. It
should not be a straw man. It provides:

- native compact room;
- campaign API;
- persistent runs/events;
- safe single-provider forwarding;
- terminal evidence and Git status;
- no advanced planning/collaboration.

This calibrates how much quality comes from the provider alone.

## 5. Milestone D — Create four campaign repositories

Each repository receives six design documents before implementation:

1. user objective and latent needs;
2. immutable fixture and public surface;
3. milestone and artifact contract;
4. hidden oracle and ambiguity audit;
5. fault/change overlays;
6. calibration handoff and expected mutant behavior.

Campaigns remain compact enough for repeated live evaluation.

## 6. Milestone E — Implement evaluator and criterion report

Output:

- hard-gate report;
- F/R/T/A/H/D/E vectors;
- per-campaign milestone evidence;
- resource and provider identity;
- source/artifact digests;
- failure taxonomy;
- raw event links;
- no single “100% complete” label.

## 7. Milestone F — Implement mutants M1–M11

Prefer small policy switches or wrapper variants over eleven full products.
Every mutant has an expected criterion effect. Run deterministic calibration
first, then semantic campaigns only for variants that need them.

## 8. Milestone G — Noise and forwarding pilot

Prerequisites:

- Codex live preflight passes repeatedly;
- Grok is either authenticated and fixed as a separate stratum or excluded;
- no hidden approval is required for campaign execution;
- environment image and cache policy are frozen.

Run M0/M9/reference repeatedly. Revise campaigns until downstream orchestration
headroom is visible.

## 9. Milestone H — First outer B60 calibration

Before three budget cells, run one 60-minute outer episode. Its purpose is to
find task-entry problems, missing tools, evaluator blind spots, and likely
ceiling—not to claim a time effect.

Review:

- whether the agent crossed the product floor;
- whether it discovered requirements beyond the brief;
- whether public dogfood changed implementation;
- whether hidden campaign feedback exposes actionable remaining work;
- whether outer collaboration trace is reconstructable;
- whether controller interventions occurred.

## 10. Milestone I — Matched B30/B60/B120 study

Only after calibration:

- independent runs from same base;
- same model/effort/environment;
- frozen evaluator revision;
- three repeats if operationally affordable;
- no cross-run answer transfer;
- criterion vectors and marginal deltas;
- natural collaboration analysis kept distinct from causal time comparison.

## 11. Milestone J — Product change extension

Apply one pre-registered change class to frozen candidates with a 30-minute
continuation. Measure adaptation and regression. Do not disclose the exact
change during V1 development.

## 12. Lightweight operational approach

The harness does not require a new orchestration platform before it can run.
Use:

- frozen Docker image;
- one tmux `/goal` outer process;
- external read-only event/process/Git observer;
- explicit provider preflight;
- exact start/stop timestamps;
- evaluator processes after artifact freeze;
- temp directories for fixtures and reports.

Add control-plane features only when repeated friction demonstrates need.

## 13. Immediate next implementation slice

1. create revision-zero JSON schemas;
2. implement the forwarding baseline;
3. build P0 deterministic harness;
4. design the ambiguous greenfield campaign and its change request;
5. run M0 against that single campaign;
6. decide whether the campaign separates requirement discovery from forwarding;
7. only then build H2–H4.

This slice is intentionally evaluator-first. Building a rich ForgeRoom
reference before proving campaign discrimination would repeat the v1 mistake.

## 14. Stop conditions

- Stop adding product ideas when they lack a campaign effect.
- Stop campaign expansion when existing families discriminate the intended
  mechanisms and evaluation cost becomes binding.
- Stop a pilot when provider/environment invalidates comparison.
- Stop and redesign if forwarding approaches the reference ceiling.
- Stop claiming improvement when criterion deltas are below noise.

## 15. Recommended next action

Proceed with Milestones A–C only. Do not yet run another one-hour outer goal.
The next evidence needed is whether a competent forwarding baseline can be
distinguished from requirement-discovery behavior on one deep campaign.
