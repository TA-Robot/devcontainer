# Online scheduling development contract, dynamic v1

Build a policy for a continuing service: finish valuable dependent work before
its deadlines while sharing limited memory and heterogeneous workers, and recover
from worker outages. A legal assignment alone is not the quality objective.

## Public interface

Python standard-library JSONL process. Read `{request_id, state}` and return
`{request_id, assignments: [{job_id, worker_id}, ...]}` with the matching integer
ID, one line, flushed, no extra fields. State owns no writable evaluator objects.

Only released jobs are visible. Each has id, release, deadline, weight, deps,
estimated duration by compatible worker kind, memory and cache. Dependencies
must finish before the job is ready. Zero-weight intermediate work unlocks
valuable dependent work; it is not itself a service completion. Jobs and their
dependencies can arrive together. Future dependent jobs need not yet be known.

State includes now, horizon, heartbeat, cold_start, memory, memory_free, released
jobs, ready jobs, workers, idle_workers, completed job/time mapping, attempts and
running job/worker/start records. Events report completed/interrupted attempts
and worker availability changes at this tick. No actual future completion time,
future arrivals, future outage schedule, generator or private labels are exposed.
The horizon and heartbeat are public. The public development workload supplies
experiments; unseen instances follow the declared domain rather than hidden rules.

## Clock, interruption and capacity

Time is integer ticks. Decision events occur at arrivals, completions, worker
outage/recovery, and fixed heartbeat multiples. Empty assignments are legal,
including when no work runs: wait for the next event or heartbeat. The evaluator
ends at horizon. Jobs completed exactly at horizon count; no assignments start then.

At one tick, completions happen first, then recovery, then new outages, then the
policy observes and acts. Thus completion exactly at outage start succeeds.
Outage cancels an unfinished attempt, discards its progress and clears worker
cache. The job can restart on another compatible worker; successful prerequisites
remain complete. Recovery time is unknown until the recovery occurs. Actual job
duration by kind is fixed for the scenario and unknown; repeated attempts use the
same duration, plus cold_start if the worker's cache differs. A successful job
sets the cache. No policy preemption, checkpointing or migration is available.

One job per worker; unique ready job/idle online worker per action. A job's memory
must fit the worker and remaining shared memory for the entire attempt, including
cache setup. Assignments consume shared memory together. Completion/interruption
releases it. Actual durations and future events remain evaluator-owned.

## Quality and experiments

The primary benefit is on_time_value: sum of positive job weights finished no
later than deadline. Always retain offered_value, class-specific deadline counts,
completed_value and unfinished_value. Missing work never disappears from quality.
Retain weighted deadline deficit, using horizon as a lower bound for unfinished
jobs' eventual completion time. This is a censored deficit, not actual tardiness.
The p95 response time covers completed positive-weight jobs only and is accompanied
by its sample count and unfinished value; dropping work cannot improve main benefit.

Actual busy_worker_ticks includes all running workers up to horizon. Interrupted
ticks count lost attempts, unfinished ticks count running work at horizon; these
are portions of busy ticks, not quantities to add on top. Assignment traces and
completion times support time-window diagnostics. Recovery quality is not yet
reduced to an independently validated scalar.

Report quality per workload family and load band, without replacing it by one
overall average. No reference-vector pass threshold or live difficulty claim is
fixed yet. A reachable demanding target will be fixed after non-agent calibration,
before measured developer runs. Perfect service on physically overloaded inputs
is not assumed achievable. Offline future-aware bounds cannot be online targets.

## Domain and resource envelope

Authoring calibration covers 96, 288 and 768 jobs with 6, 8 and 12 workers over
1200 ticks. Burst arrivals, scarce kinds/shared memory, cache costs and mixed
outages span three broadly separated load bands. Each job chain currently has
three stages. Actual processing time is the estimate multiplied by a draw from
0.7, 1, 1, 1.4, 1.8, floored with minimum one; times by kind may differ. Heavy
cache families use 14 setup ticks, others 3. These are calibration design priors,
not empirical difficulty categories or real service SLAs. The authoring suite
keeps each family/band separately even when a reference performs poorly.

Runtime hard guards: 1–2048 jobs, 1–32 workers, horizon 1–10000, heartbeat 1–100,
at most 256 nonoverlapping outages per scenario, positive integer duration/memory.
Compatibility must admit each job, and dependency graphs must be acyclic with
prerequisites released no later than dependents. All fields are validated.

Transport cost caps initially reuse the frozen scheduling boundary: one CPU,
256 MiB, 64 KiB source, 1 MiB request, 256 KiB combined output, five seconds per
response and 30 seconds per scenario including startup. Evaluator capacity and
timeouts are unmeasured, not intellectual failure. Revise a new version before
live if meaningful experiments cannot fit. No developer budget is fixed here.
Owner for caps/priors and their revision: primary/integrator. No production
dependency or devcontainer distribution change is required.
