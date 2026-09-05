# Independent acceptance execution: staged task draft

Status: selected real development need; public stages drafted, external evaluator
and execution budgets not yet frozen. Do not launch this campaign from these
drafts alone. Small-02's separately frozen comparison has finished; see its
[results](../small-result.json).

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

Before launch, enumerate the externally observable cases and calibrate the
evaluator with missing, fabricated-success and executable positive fixtures.
Freeze commands, schemas, timing tolerances, the stage-release rule, common
requirements for timepoint comparisons, model/CLI/permissions and finite caps.
All disposable projects, processes, Docker resources and state belong outside
the repository. No live model is needed for evaluator calibration.

The [real-job fixture](fixture.py) creates an actual submitted job through a fake
provider, counts provider invocations and allows a deliberately false success
claim. `scripts/test-independent-check-fixture.py` verifies that legacy validation
does not execute acceptance or result-only commands, while executing the original
command independently produces its witness and exit 17. It also covers a manual-only
task. These two tests establish the fixture and the missing capability; they are
not a calibrated evaluator for the future three-stage implementation.

A [draft core execution probe](evaluate_execution.py) now observes four properties:
actual execution, rejection and stopping after a falsely reported success,
authority from the original task, and absence of command proof for manual-only
acceptance. It checks external filesystem witnesses and actual exit status,
in addition to the JSON report. Calibration executes a small independent shell
reference against real jobs and rejects fabricated success, overridden failure,
and result-only command side effects. The expanded fixture/calibration suite has
six tests. This establishes these core observations only: timeouts, output bounds,
source identity, freshness, migration, concurrency and installed distribution
remain outside this draft probe. Its output explicitly leaves sustained-task
acceptance unknown; it must not be used to launch the full comparison yet.

Draft execution limits are task-local, owned by the primary/integrator. The
finite positive whole-sequence deadline, no implicit execution on reads, and
exclusive ownership per attempt are hard guards against false or overlapping
verification. The 64 KiB combined retained output is a resource cap aligned with
the existing default log view; it is not a quality score. The 60-second default
deadline is a planning prior for short acceptance checks, explicitly overridable
by the caller. Real checks that exceed it, required diagnostics lost to the cap,
or failures to terminate owned processes invalidate these assumptions and must be
resolved before freezing the study. The fixture's subprocess deadlines bound
provider-free setup; a setup timeout is an observer failure, not a fast candidate.
