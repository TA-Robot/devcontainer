# Scheduling policy: public execution contract v1

Implement a Python 3.10 standard-library program that reads JSON lines on stdin
and emits one JSON line per request, flushing stdout. A fresh process is started
for each scenario. No network, credentials, evaluator source, scenario file, or
host filesystem is available. `/tmp` and `/work` are writable scratch space.

Request: `{"request_id": INTEGER, "state": OBJECT}`.
Response: `{"request_id": SAME_INTEGER, "assignments": [{"job_id": "...", "worker_id": "..."}]}`.
No additional fields or stdout prose. Stderr is diagnostic and counts against
the combined output cap. Never report your own quality metrics as a response.

The state contains `now`, `jobs`, `workers`, `ready`, `idle_workers`, `completed`,
`running`, and `cold_start`. Jobs contain id, dependency ids, compatible worker
kinds, duration by kind, cache label, and failure_probability. Workers have id,
kind, and last_cache. Running entries show job_id, worker_id, start, finish.
Failure probability is public information, not the actual future failure label.

Durations are positive integer ticks, not seconds. The cold-start penalty is
added when the worker's last completed cache differs from the job cache.
All jobs and dependency edges are known. Actual failing jobs are private.
A job becomes ready after all dependencies finish successfully. Assign only
ready jobs to idle, compatible workers, with neither id repeated in a response.
An empty/partial assignment is legal while another job runs; if nothing is
running and work remains, it deadlocks and is invalid. The next decision is at
a completion event. Arbitrary idle-time events and preemption are not supported.

At the earliest failing completion, all work stops. Busy-worker ticks count
actual elapsed execution up to that stop, including simultaneous workers.
Committed-worker ticks separately count full durations assigned, including work
cancelled at that stop. Simultaneous completions share the same exact integer
clock; no floating epsilon or rounding is used. No hidden failure is exposed
before its completion.

The evaluator owns state, transition legality, terminal status, clock, and all
quality metrics. Your outputs cannot replace them. Quality is a vector:
successful completion ticks, blocker detection ticks, busy-worker ticks, and
policy response elapsed time. The latter includes IPC/startup on first request;
it is not pure CPU time and cannot establish semantic policy separation.
Hard validity failures are not compensated by fast or low-resource results.

Current envelope (cost caps for this version, not recommended algorithm budgets):
1–256 jobs, 1–32 workers, duration 1–10000 ticks, cold start 0–10000 ticks;
64 KiB single source file; 1 MiB request; 256 KiB combined stdout/stderr per
scenario; 5 seconds per response and 30 seconds per scenario including startup;
256 MiB memory, 64 processes, one CPU, 16 MiB each scratch mount; cleanup 15 seconds.
Owner: primary/integrator. If useful legal policies cannot fit, revise and
recalibrate a new version; do not change a running comparison's envelope.
If a legal scenario produces an observation above the transport cap, assessment
is unmeasured because of evaluator capacity; it is not an invalid policy.

This version establishes the execution/evaluation boundary. Hand-authored
calibration examples are not proof of a hard task. Development and unseen
workload populations, practical attainment thresholds, and strong-solo budgets
must be fixed separately before a live difficulty calibration or comparison.
