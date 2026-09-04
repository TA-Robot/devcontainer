# Cycle 001 — real maintenance under the devcontainer

Status: preregistered before the live development trials, 2026-09-05.

## Purpose and unit

Improve the environment's ability to support real repository maintenance. The task is the actual non-finite-number correctness gap in `scripts/agent_contracts.py`, not a generated demo. The full [task](task.md) is identical across conditions. Task success is independently checked outside the candidate, including unconstrained nested values, finite/large integer/bool compatibility and preserved existing contracts.

Baseline source: `5ca8a988efb74491cef0fa670d9137f85f855f82` (git archive into a disposable external checkout). Baseline frozen image: `sha256:829d58c04a53f771e556407bbb634aeb8765e4e8f1bd9d3104f18c362713de88`. Candidate checkouts contain only tracked base content, not this review, protocol, evaluator, or earlier live runs.

## Initial observation and revision

The proposed first task was supervisor test repair. Actual image checks exposed a more fundamental prerequisite: Python 3.10 cannot import the template validator's tomllib, and checkout agentctl resolves its installed library before local source. The first intervention therefore targets development/runtime parity, plus the observed flaky publication check. These fixes do not implement the non-finite-number task.

Hypothesis: removing these environment defects improves mandatory-check completion and reduces irrelevant recovery during real maintenance. Alternatives considered: upgrade all of Ubuntu/Python (larger migration), create a custom TOML parser (unnecessary maintenance), tell each agent to patch its environment (repeated work), add more agents (does not solve runtime identity). Prefer a narrow compatibility dependency plus correct source selection and explicit publication waiting.

## Conditions and limits

- One baseline live cell and one improved live cell, serial, fresh/ephemeral. This is a **cost cap**, not a statistical sample-size claim. An infrastructure-only failed launch may be retried once with its reason preserved; no silent substitution of failed development runs.
- Model: `gpt-6-astra`; requested effort: `high`; same CLI 0.146.0. These are a **planning prior** matching the capable model used in this session, not a universal recommendation. Verify request/readiness; record applied values only if observed.
- `codex exec --json --ephemeral --ignore-user-config` in the frozen devcontainer, with explicit workspace-write sandbox and approvals disabled for noninteractive work. Same provider permissions in both conditions. A failure of this surface must be recorded rather than silently widened.
- Maximum live wall time: 900 seconds per cell (**cost cap**, first-cycle feasibility; owner: primary). No mid-run hints, solution injection, model switching or additional agents. Model usage is reported, never inferred from wall time. Stop on terminal completion, deadline, auth failure or violated authority.
- Evaluation is provider-free and external to candidate source. Exit zero from Codex is not task acceptance. Candidate source is frozen/hash-checked before testing.
- Development wall, input/cached/output tokens, command count and nonzero command outcomes are distinct observations. A shell command failure is not automatically an environmental error: inspect only source-linked summaries when classifying recovery. Do not retain private reasoning in published evidence.
- Baseline and improved source differ only by the declared infrastructure patch. The final non-finite-number fix is integrated after the comparison, not present in either starting condition.
- Same shell surface/order can still leave cache/provider/load confounds. This pair supports a feasibility decision; do not claim causal general speedup or broad model ranking.

## Objective checks

1. Source identity: in a temporary checkout copy, a sentinel error in local agentctl_jobs must be seen by the local CLI even when installed library exists. Installed CLI must still work. Also test local preference with hostile current-working-directory modules.
2. Standard-image template validator and mandatory contract suite must start without ad hoc pip installs.
3. Supervisor retention metadata test: original assertions retained, publication awaited with a deadline, no fixed additional sleep used as the correctness mechanism. Repeated focused runs plus full required agentctl checks.
4. Independent non-finite-number behavior tests against the completed task; existing schema/template tests; changed-path and diff review. Partial successes remain partial.
5. Required plain/frozen build and container smoke for shipped image changes. Record exact resulting image/source identities.

## Adoption and completion

Adopt parity fixes when objective checks pass and normal installed/runtime behavior is preserved. Interpret live efficiency only alongside accepted quality; if task acceptance differs, report that difference rather than computing a misleading speed ratio. Retain a null or negative result. Complete the cycle only after an implemented intervention has actually been tried, external re-evaluation is recorded, useful task output is reviewed, and the next decision is written.

CLI output/usage semantics were checked against the [official non-interactive documentation](https://learn.chatgpt.com/docs/non-interactive-mode) and the actual frozen binary's help. Official current documentation is not a claim that every new flag exists in the pinned binary.
