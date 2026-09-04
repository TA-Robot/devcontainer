# Cycle 001 — real maintenance under the devcontainer

Status: initial protocol recorded before the live development trials, 2026-09-05;
adaptive amendments are recorded below. See the [cycle report](../../../docs/agents/development-harness-cycle-001.md)
for results and final validation.

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

## Amendment A — model readiness before any development

The first baseline invocation terminated after 27.680 seconds with an explicit
provider error that GPT-6 Astra requires a newer Codex. It made zero tool calls
and no source changes; the failed observation is retained as infrastructure
readiness evidence. CLI 0.146.0 is therefore not a valid cell for this model.

Keep GPT-6 Astra/high. Use CLI **0.153.0**, the locally installed version, in
both development conditions. npm's current latest was 0.153.3, but latest is
not the selection criterion. For the control container, install exactly
`@openai/codex@0.153.0` into `/opt/devcontainer-ai-cli` and pass the corresponding
`DEVCONTAINER_CODEX_CLI_VERSION` to the run. The amended control is the original
image plus this explicit compatibility overlay, not an untouched frozen image.
The improved image pins that same CLI. Preserve both observations and count this
as the one allowed infrastructure launch retry, not an additional development
sample. Changing model silently would answer a different question.

## Amendment B — baseline-discovered false mount failures

The live control completed the semantic task (33/33 external checks), but its
mandatory duration regression run had four failures. Reproduction with the
original validator confirmed that these are unrelated to the task: tests reject
`/workspace` anywhere in the Docker argument JSON, including the allowed source
`/tmp/.../fixture/workspace`. The improved condition additionally replaces these
substring assertions with exact bind-source ancestry checks and adversarial
regressions (repository root, descendant and ancestor mounts must still fail).
This is an explicit treatment revision prompted by the baseline, not a change
to task acceptance or a weaker security requirement. Do not interpret this
single sequential pair as a preregistered causal estimate.

## Amendment C — deterministic test fixtures during release checks

Host release checks exposed two more fixture races: fake providers could exit
without consuming stdin while the broker was still writing the prompt, and a
same-parent/same-second cherry-pick could retain the worker SHA while a test
expected patch-ID recognition. Make fake providers consume their prompt and give
the patch-ID test a distinct integration parent. These changes preserve broker
runtime behavior and strengthen which branch the tests actually exercise. Retain
initial failures and rerun the affected suites; do not label them product fixes
or silently omit the failing checks.

The container release check also showed that Mira tests inherited the image's
persistent episode directory while expecting a private test directory. The
fixtures now set both UI state and episode paths, and explicitly enable episode
collection when testing correlation. This isolates test state without changing
production telemetry. After the fixes, the affected container subsets passed
83 tests; the other full-suite tests had already passed. Both initial failures
and reruns are retained.

## Post-comparison release verification

The integrated host suite exposed a bounded-cleanup calibration failure in
F06-L-PYBASH-001; a serial rerun passed that case but failed two supervisor queue
tests, one reporting that the local supervisor did not become ready. These
failures are preserved. A successful later run cannot establish their root
cause or justify a general reliability claim.

Separately, inspection found every supervisor fixture used a 400 ms orphan
window to accelerate one recovery test. Ordinary fixtures now use the production
30-second window; the recovery test kills and verifies its owned processes and
explicitly ages the dead attempt's heartbeat in its private database. The
orphan-state and cleanup assertions remain intact. This removes a real-time
sleep dependency from fault setup, but is not claimed to fix the observed
supervisor startup failure. It is a test-only release refinement made **after**
both live cells and is not part of the measured intervention.

Final validation uses the integrated frozen image and current repository tests
serially. Preserve the first failures and report the final target result
separately from host verification and from the development pair.

## Reproduction and interpretation

The committed source revision plus the explicit `intervention_paths` in the
published result identifies the treatment. Reconstruct each task checkout from
`git archive 5ca8a988efb74491cef0fa670d9137f85f855f82`, initialize a local Git
snapshot, and apply only that revision's diff for the listed paths in the
improved condition. Do not include the finite-number task fix or this evaluator
in either initial checkout. Keep candidate directories outside this repository.

Use `scripts/benchmark-devcontainer.py` to prepare the named container, then
`python3 experiments/development-harness/cycle-001/measure.py --container NAME --output PRIVATE_NEW_DIRECTORY`. This starts a real
provider invocation with the stated 900-second cap. Run `evaluate_task.py`
with `python3` and `--candidate CHECKOUT --output RESULT_JSON` against the
terminal candidate only; its exit code and `accepted` field are
semantic evidence, not a claim that every repository check was completed.
`python3 probe_environment.py` runs provider-free inside the tested image with immutable
source at `/workspace`. The five retention samples are a diagnostic repetition
cap, not a statistical reliability guarantee; primary owns that cap and any
revision if scheduling conditions change.

The CLI command counts include only surfaced completed `command_execution`
items. Nonzero command exits include search commands with no matches; they are
not a count of independent defects. Raw reasoning is discarded by the recorder.
Private commands/final messages are kept outside the repository; published
reports contain aggregates and artifact identities. One-time primary
implementation, review, build and evaluation effort is excluded from the live
cell clock, so this cycle does not establish net ROI or an amortization period.
