# Verification history: bounded read-only pagination

Independent check records are durable, but `job checks JOB --json` exposes only
the latest one. Add a usable, bounded history view without changing that default.

Provide `job checks JOB --history [--limit N] [--cursor TOKEN] --json`.
The JSON contains `job_id`, `items` (newest recorded observation first), and
`next_cursor` (an opaque string or null). Each item includes `verification_id`,
`attempt_id`, `status`, `report_path`, `started_at`, and `finished_at` from the
recorded observation. Do not invent absent history. Default limit is 20; allowed
integer limits are 1 through 100. Reject malformed/invalid cursors and limits.
The valid integer range is an interface guard, with 100 as the per-page resource
cost cap; 20 is a planning prior for a useful CLI-sized page. These choices apply
only to this history interface, are owned by the primary, and must be revisited
before sealing if real history volume or observer calibration contradicts them.

Enumerating a complete history must return every record for the selected job
exactly once, even when several observations belong to the same attempt or have
identical timestamps. Do not include other jobs' records. Paging terminates with
null, including for an empty history. Failed and incomplete observations are
history too; do not return only passing checks.

This is read-only inspection. It never executes acceptance commands, starts a
provider, validates a job, repairs a report, or creates missing state. Preserve
existing task/result contracts, default `job checks`, retry and validation behavior.
Document the interface and add focused regressions using real jobs/fake providers.
