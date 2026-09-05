# Independent acceptance execution: staged study

Status: source/installed observers and finite execution protocol are calibrated.
The [protocol](protocol.md) fixes the three-stage comparison; exact tasks, runtime,
source, image, cache and manifests are sealed in private provenance before launch.
Small-02's separately frozen comparison has finished; see its
[results](../small-result.json). This page does not claim a completed large trial.

The current broker verifies Git and the shape of the provider result, but does
not independently execute the original task's command acceptance. This affects
whether a reported successful job can be trusted for integration. The proposed
feature extends the existing control plane; it does not create another scheduler.

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
