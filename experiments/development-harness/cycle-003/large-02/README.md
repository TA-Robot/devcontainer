# Independent acceptance execution: staged study

Status: the three-stage live comparison, outside review and implementation integration
have finished. See [results](result.json) and the [cycle report](../../../../docs/agents/development-harness-cycle-003.md).
The [protocol](protocol.md), prompts and calibrated frozen observers retain their
pre-run bytes. Small-02 is reported [separately](../small-result.json).

The shipped broker now independently executes the original task's command
acceptance and can require fresh durable evidence for validation. The comparison
also exposed publication interruption, GC and Git metadata handling problems;
reviewed fixes were integrated into the existing control plane.

| Stage | User outcome | Independent evidence required |
| --- | --- | --- |
| [Execution](phase-1.md) | Run the task's checks against the actual delivery | A command that the fake provider claims passed actually exits nonzero; the CLI must reject it. Positive checks leave an external witness. Result-only commands never execute. Deadlines, bounded output and source mutation are observed directly. |
| [Fresh evidence](phase-2.md) | Inspect and require results for the current delivery | Real old jobs/databases remain readable; no proof is invented. Changes in source, task, attempt or report invalidate prior evidence. Querying never executes commands. |
| [Unattended use](phase-3.md) | Safe concurrent/restarted use and installed distribution | Concurrency/interruption cannot publish passing evidence; owned child processes stop. A real built image runs the complete fake-provider workflow without a source mount. |

This is a coupled development task: the second and third stages change how the
first stage's execution and evidence are used. Stage completion time is not an
independent replicate. Later-stage correctness, regressions and change effort
provide evidence about maintaining this implementation, with the same developer
model and limits in both conditions. They do not measure all forms of maintainability.

The [staged evaluator](evaluate_staged.py) contains 24 / 37 / 41 source
observations through the respective stages. The [installed evaluator](evaluate_installed.py)
contains 13 observations using shipped paths in a real final image, with no
candidate checkout mounted. Counts describe coverage; acceptance also requires
complete measurement, unchanged source, fixed regressions and source review.

The original [core probe](evaluate_execution.py) and its six-test calibration
remain as earlier evidence. The new eight-test staged calibration exercises all
41 observations with executable reference behavior and rejects identity,
integrity and deadline mutants. Two runtime tests verify readiness and cache
identity before any model call. See [calibration evidence](calibration.json) and
[protocol limitations](protocol.md), including the reference's in-memory index.

Tasks, hidden evaluators and reference code are absent from the developer
checkout. Each condition receives later stages only after its recorded earlier
session completes; external findings are withheld. Disposable projects, provider
logs, Docker resources and all raw evidence remain outside this repository.

Raw frozen recovery observations remain 40/41 source and 12/13 installed for the
control candidate. Its documented `--recover-incomplete` workflow passes a
separate probe after the operator establishes the old process group has stopped.
This is an observer applicability limitation, not a silently revised frozen score.
The improved candidate submitted earlier but failed the additional SQL publication
interruption probe. Both candidates required GC fixes. The control exceeded its
observed output cap; it is not a success within the same budget.
