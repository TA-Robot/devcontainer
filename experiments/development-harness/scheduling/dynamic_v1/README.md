# Dynamic scheduling: broad difficulty calibration

This new task version implements continuing arrivals, deadlines, weighted service,
heterogeneous workers, shared memory, cache setup, uncertain execution time and
worker interruption/recovery in one evaluator-owned event loop. It preserves all
old scheduling source, scores and unused confirmation data.

The [public contract](TASK.md) describes exact observation and event semantics.
The workload spans 96/288/768 jobs rather than adding a few cases to the old
32–72-job task. Each band contains burst, scarce-resource, cache and mixed families,
two authoring instances each. Three-stage chains are the current topology; this
does not yet establish generality to arbitrary workflow graphs.

The four non-agent approaches are FIFO, earliest deadline, dependency-aware value
density, and a bounded beam over joint assignments. The internal mode name
`lookahead` denotes that assignment beam; it does not simulate unknown future
arrivals or use an offline oracle. It is not a proven strong optimizer. All modes
receive exactly the same public-information interface, with no generator access.

## Run and verify

```bash
PYTHONDONTWRITEBYTECODE=1 SCHEDULING_DYNAMIC_DOCKER=1 \
  python3 -m unittest scripts/test-scheduling-dynamic.py
PYTHONDONTWRITEBYTECODE=1 python3 experiments/development-harness/scheduling/dynamic_v1/calibrate_v2.py \
  --output /path/to/new-private-calibration --max-cases 24
```

The calibration fixes all 24 development cases and four approaches before starting,
uses fresh network/credential-free policy containers for 96 executions, and records
each case. Each approach batch has a 300-second cost cap and 30-second graceful
cleanup reserve, with forced child-controller termination after that reserve if
needed. These are finite authoring cost caps, not a developer budget or measured
optimal settings. Invalid policy or unmeasured execution stops subsequent batches;
no winning subset is selected. Missing cleanup evidence prevents success.

The reviewed controller `calibrate_v2.py` snapshots all scoring/workload/reference
source before generating inputs, launches only that snapshot, retains attempted
starts, verifies exact coverage and assessment seals, and ends failures as
`withhold`. Killing the evaluator process is not proof that its Docker children
were removed: interrupted/missing cleanup remains unknown and requires recovery.
The original `calibrate.py` is retained for historical source identity and should
not be used for new runs. It could leave launch failures marked running and read
changed source after recording a plan hash.

`transport.py` is a byte-identical copy of the frozen v1 transport; `evaluate.py`
reuses the same snapshot, process isolation, limits and result-recovery structure
with a new kind and this version's runtime. Those copies keep the old source
immutable and make the new source seal self-contained. Candidate Python is never
imported or executed on the host. In-process unit fixtures use only trusted local
callbacks to check arithmetic and information isolation.

No dependency or production container change is introduced. The existing pinned
Python policy image is reused. Retire this task by removing its directory/tests;
do not remove the shared image as though it belonged only to this task.

## Completed authoring calibration

2026-09-08: all 96 independent policy executions completed in 369.045 seconds;
10 tests passed with no skips, including real Docker checks. All owned containers
were removed. See [results and limitations](result.md) and [source-bound data](calibration.json).

## Admission status

The [2026-09-08 review](../../../../docs/project-review-2026-09-08.md) verified the
new controller on all 96 executions, with identical scoring results and traces.
Its [necessary-bound audit](bounds-audit.json) shows that completing all offered
work is capacity-impossible in four severe cases. Missing value is therefore not
all recoverable by better reasoning. The audit does not prove online feasibility
for the critical class. Stronger references are diagnostic work, not an indefinite
prerequisite for the next bounded solo quality exploration.

Runtime validity, reference quality separation, attainment targets, strong-solo
difficulty and collaboration effect are distinct. This is authoring calibration;
live developer runs have not started. No threshold is manufactured from per-cell
best scores, and no perfect service requirement is imposed on overloaded inputs.
The next admission decision must connect a demanding reachable quality level to
the work protected by deadlines. Do not label the task hard from node count or
the number of runtime features alone.

The clock records completed-job response tails alongside unfinished value, service
classes and weighted deadline deficit. Busy, interrupted and unfinished execution
costs are retained separately. Recovery traces are available, but a scalar recovery
service measure and a validated strong-reference frontier remain outstanding.
