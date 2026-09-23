# Large-02: independent acceptance through continued development

Owner: primary/integrator. This protocol is prospective. Launch requires the
calibration and exact-context cache preflight recorded alongside its manifest;
the manifest and input hashes are sealed before the first model session.

## Question and intervention

Measure separately (a) time to declared behavioral quality and (b) quality of the
delivery at observed development times. Required verification being executable
is an intermediate mechanism, not a quality result. This extends small-02 to
coupled execution, evidence freshness/migration, and unattended distribution.
It is an hours-scale development task, not evidence about weeks of product work.

Both conditions start with source commit
`464c6b6603c59d89e6877817d9505613e2d2fe18`, overlaid only with the Dockerfile from
`b719efefd29a383db8225a88a852b6b69edfe363`. The overlay uses the same signed Ubuntu
archives over HTTPS for downstream installation. Its normal/frozen builds,
startup and Mira checks passed; installed package inventories matched the prior
image. It is a common baseline change, not the condition difference.

Common execution image:
`sha256:2448848444c0c224d5741ee8677dccb987d3b3121b9285f9c3ae7a6c56ac9901`.
Requested model/effort: GPT-6 Astra/high, Codex 0.153.0. Applied model and effort
remain unknown unless reported. Each condition receives an identical fresh Git
tree and initial commit. Future stage prompts, evaluators, reference checker and
completed candidate sources are absent from its checkout and image.

The intervention remains command network access: control false, improved true,
with the existing workspace-write filesystem sandbox. Approval is never; other
agents are disabled. Network authority differs, so this is not a comparison at
identical permissions, or evidence that this control is the best possible solo
workflow. Both receive the same temporary Docker client configuration and cache
facility. Normal project/user permission defaults are unchanged.

One improved condition (opaque runtime label A), then one control (B), serial.
One run per condition is an exploratory cost cap, not a replication design.
No extra runs are added to obtain a favorable result. No heavy outside build or
regression suite runs alongside a live provider. Ordinary primary bookkeeping
and read-only review may continue; the host is not exclusively reserved.

## Stages and stopping

Publish [phase 1](phase-1.md), [phase 2](phase-2.md), then [phase 3](phase-3.md).
Each gets a fresh ephemeral session with the same released task history and the
persisted source/handoff. Release the next stage after the current recorded
session terminates and the unchanged finite runner admits continuation. Do not
send external evaluator findings to developers. Stages are dependent work, not
independent statistical samples.

Study-local caps, owned by the primary:

| Setting | Value | Kind and rationale |
| --- | --- | --- |
| Phase wall limits | 1,800 / 1,500 / 2,400 seconds | Cost caps: executor/identity work, evidence evolution, then concurrency and real packaging. More time for the final stage's required builds. |
| Whole condition | 5,700 seconds, 3 sessions | Cost caps, no automatic retry or deadline reset. |
| Observed output | 80,000 tokens per condition | Admission cost cap for three implementation stages and their tests; not exact within-turn billing enforcement. |
| Snapshots | Every 300 cumulative seconds and each terminal submission | Planning prior for sustained changes; record actual trigger times. |
| Snapshot source payload | 512 MiB each | Storage cap permitting bounded migration fixtures and prior source alongside the roughly 40 MiB baseline; no image archives or package downloads in the checkout. |
| Outside checker observation | 20 seconds per `job check` invocation | Observer cost cap above the finite fixture checks, with explicit termination handling. |
| Retained observer stdout/stderr | 2 MiB per stream | Observer resource cap; an oversized checker response is a failed observation. |

Unavailable usage, lost recorder ownership, failed snapshot or interrupted
container is handled by the existing conservative recovery contract. Preserve
the exact run and all failures; do not create a replacement session. A budget
stop or inability to continue is censored noncompletion, never a fast success.
These priors may be amended only prospectively with the reason and original
record retained. A needed runtime/observer repair after launch is reported as a
deviation; affected old observations are not silently rewritten.

The container restarts between stages and its `/tmp` is reset. Developers are
told to retain factual handoff and bounded reproducible migration evidence in
the workspace. Named job-state storage and nested-Docker storage persist. Do not
assume a live checker or arbitrary temporary process survives restart.

## Comparable quality and time

[Source observations](evaluate_staged.py) cover 24 requirements/examples after
phase 1, 37 after phase 2 and 41 after phase 3, grouped by user outcome:
actual execution, source preconditions/identity, working directories, bounded
execution/evidence, freshness/integrity, migration, and interruption/concurrency.
Counts are coverage, not an overall quality score. The behavioral threshold is
all declared observations through the released phase, complete measurement and
unchanged candidate source. A selected subset cannot claim a whole-phase pass.
An absent check interface cannot earn apparent quality through refusing every
negative fixture. Initial absence is one missing capability, not 41 defects.

Report each stage's terminal quality and time, the cumulative timeline, and
first observed threshold attainment with intervals where necessary. At similar
cumulative timepoints compare only requirements already released to both
conditions. When stage information differs, report that difference and exclude
unreleased requirements from the common quality comparison. A carried terminal
artifact can represent later observation times; waiting is not added to its
development time. Do not divide checkpoint intervals into a claimed speed ratio.

Submission time excludes preparation, outside verification, review and
integration. Record those separately, including cache preparation and actual
build durations, and report end-to-end elapsed time where observed. Do not sum
overlapping work or invent unmeasured human-review time. Preserve input, cached
input, output and reasoning usage (cached input is included in input; reasoning
output is included in output). Monetary cost remains unknown without billing
evidence. Small and sustained results are never collapsed into one percentage.

## Independent evidence and release

Actual jobs are created through deliberately dishonest fake providers. Observe
command witnesses and exit codes independently, source bytes/modes/index/HEAD,
query/validation side effects, persisted report corruption, and actual owned
process lifetime. Only synthetic secrets and owned temporary data are used.
Earlier-state observations run the actual older CLI, not a reconstructed table
schema. Phase 3 additionally consumes phase 2's actual source to produce and
preserve its evidence across the code upgrade. An unavailable prior passing
report is unknown migration evidence, not a fabricated pass.

The global-deadline fixture has a 1.5-second allowance: a one-second first command
then a waiting worker. Independently observe the first command's monotonic start
and the worker's actual termination within 2.3 seconds; CLI source prechecks and
postprocessing are excluded from this interval. The 0.8-second allowance is
fixture-specific scheduling/cleanup tolerance. The
executable reference passes and a per-command deadline-reset mutant fails.
SIGTERM child-stop observation allows two seconds and checker process
termination ten seconds. These are calibrated
observation tolerances, not new production defaults. The output fixture drains
16 MiB and checks bounded retained tails plus redaction; finite load does not
prove asymptotic memory behavior. Code review must inspect unbounded buffering,
authority, source identity, ownership and recovery before adoption.

Calibration uses executable reference behavior for all 41 source observations,
real legacy jobs, fabricated-success/side-effect mutants, stale-source and
corrupt-report mutants, and a deadline-reset mutant. The reference evidence
index is held in the test process: it calibrates observer semantics and process
witnesses, not the candidate's production durability. The actual candidate is
still exercised across independent CLI invocations and old-state migration.
The initial reference SIGTERM failure and its correction are retained.

[Installed observations](evaluate_installed.py) exercise 13 declared scenarios
through shipped paths in an actual newly built final image. The outer runner
must verify that no candidate checkout is mounted; the evaluator cannot infer
that from a success flag. Use a dedicated results directory that contains no
source tree, and compare the installed entrypoint/core module hashes to the
candidate. Initial setup with an overly broad results mount was rejected and
retained as an observer preparation error, not an installed result.

Release requires source threshold, actual installed behavior, required core
regressions, applicable normal/frozen container checks and a completed source
review. Native task/result contracts and legacy job behavior remain compatible.
Report additional review findings separately from frozen observations; preserve
original candidate artifacts and scores. Integration repairs and their cost are
outside developer timing. Do not mark this study complete after only a model
submission or a successful image build.

## Cache and execution preparation

Use isolated benchmark containers, private nested-Docker volumes, no host Docker
socket, and only the required Codex credential mount. Evaluators have no provider
credentials, no network, read-only candidate/installed code and owned temporary
state. The privileged development container is not a strong isolation boundary.

The common cache contains the pre-task toolchain only. The same artifact and
startup procedure are supplied to both conditions. Verify actual layer reuse
on a source-only change before launch; image loading alone is insufficient.
Record the cache's digest and preparation time separately from model time.
The [BuildKit local cache interface](https://docs.docker.com/build/cache/backends/local/)
uses an OCI directory. Persist cache content outside `/tmp`; prepare writable
client metadata after `docker-init` resets temporary storage on each start.
Use the original RUN network mode when testing cache reuse, since changing it
changes the execution cache identity. These are explicit common study setup
conditions, not a newly deployed general build service.

Freeze task, runner, fixture/evaluator, source, cache and image hashes in outer
provenance before either condition. Keep raw evidence and temporary projects
outside this repository. Do not publish raw provider logs or require the user
to maintain observation forms.
