# Strong-solo scheduling difficulty calibration

**Completed 2026-09-08: both runs attained all targets; the two-start allowance is
consumed. See [results and decision](result.md).**

This task adapter implements the two fresh developer runs fixed in the
[H2 protocol](../workloads_v1/solo-protocol.md). It does not modify the frozen
scheduling evaluator or earlier model runs. A developer edits real policy files,
executes public experiments, selects submission.py, and is independently graded
only after its container stops. No hidden grade is returned to either developer.

## Public input and execution

`projection.py` creates an explicit nine-file allowlist. The actor receives public
contracts, development cases/targets, FIFO, and public experiment tools. Authoring
generator/seeds, reference policies, qualification/confirmation inputs and the
repository checkout are absent. The same public files are mounted read-only to
both runs; only each run's own /work is writable. Earlier work and responses are
not passed to the next run.

Public checks use Python subprocesses inside the actor's shell sandbox, with the
same immutable simulation/transport semantics as the final evaluator. Final
candidate code is never executed on the host; scoring uses the existing separate,
network/credential-free policy container. All final bytes are copied after actor
removal, bounded, checked against symlinks, hashed and linked to the evaluator seal.

## Actual CLI capability boundary

The image adds the pinned Codex code-mode host and bundled bubblewrap binary to
the prior minimal Codex/Python image. No package download, production dependency
or devcontainer distribution changes. Image/source IDs are in image.json.
Remove this adapter's image when retiring it; parent images have other users.

Pinned model metadata originally requested multi_agent_version=v2, exposing a
collaboration namespace despite features.multi_agent=false. The solo metadata
copy sets only that field to null, preserving model identity and remaining
metadata. Actual outgoing additional_tools items are checked for shell access
and absence of subagent tools; checking only top-level tools would miss them.
The fixed CLI's known code_mode startup notice is retained, not mistaken for a
failed tool call. Unknown errors, agents or tools prevent successful completion.

Shell commands use workspace-write sandboxing with network disabled. The outer
container permits the namespace syscalls needed by bubblewrap using
seccomp=unconfined, while keeping non-root, cap-drop ALL, no-new-privileges,
read-only root and limited mounts/resources. This outer adjustment does not
claim an unchanged Docker seccomp profile. The actual sandbox is verified by a
shell failing to connect to the live local synthetic endpoint that the Codex
controller itself is using. Prohibited additional model commands also trigger
withholding. These are checks on the pinned configuration, not a general proof
against arbitrary kernel exploits or a general Codex configuration recommendation.

The bundled sandbox helper was initially absent and the default outer seccomp
profile then prevented user-namespace creation. Those provider-free failures
were retained, fixed and rechecked; no live model was used to troubleshoot them.

## Validation and fixed runs

```bash
PYTHONDONTWRITEBYTECODE=1 SCHEDULING_SOLO_DOCKER=1 \
  python3 -m unittest scripts/test-scheduling-solo.py
```

The actual CLI is driven by a local synthetic Responses endpoint: create broken
policy, run public checks, repair it, rerun checks, and test shell network denial.
The two-run fake workflow, independent grades, exact source binding, unknown usage,
extra-model commands, deadline and container cleanup are checked. These synthetic
results do not establish task difficulty. Source-matched validation.json is a
mandatory gate for live execution.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 experiments/development-harness/scheduling/solo_v1/runner.py \
  --auth /path/to/existing/auth.json --output /path/to/new-private-run
```

This command consumes the fixed two-run allowance, not permission to run repeats.
Each developer has 1800 seconds and 60000 observed output tokens; overall budget
and independent assessment limits remain those in the H2 protocol. All live
starts, nonattainment, non-submission, invalid policies and infrastructure failures
are retained. Incomplete/unknown usage is not zero. The runner stops remaining
starts on infrastructure failure; genuine nonattainment does not discard the next
independent run. No confirmation assessment is executed.

Raw events, public test outputs and source remain private. The temporary auth
copy is removed in finally. Event capture is capped at 16 MiB combined stdout/
stderr per actor. Actor runtime is capped at 2 GiB, two CPUs and 256 processes;
/codex and /tmp each have 64 MiB tmpfs. These are cost caps for this adapter, not
model-optimal settings. Cleanup is explicit and unconfirmed cleanup is not success.
Abrupt SIGKILL/host loss still needs external recovery from saved container names.
