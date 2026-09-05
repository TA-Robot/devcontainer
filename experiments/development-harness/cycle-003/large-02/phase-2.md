Continue independent command verification while preserving all phase-1 behavior.

Operators need to inspect past checks without executing them again, and require
fresh independent evidence before sealing a job for integration.

Add:

    agentctl --state-dir STATE job checks JOB_ID --json
    agentctl --state-dir STATE job validate JOB_ID --require-checks --json

Persist completed check reports under the existing private state, with an opaque
`verification_id`, task digest, attempt identity, source fingerprint and report
integrity digest. Preserve prior records on a later failed run. The read-only
`checks` command returns `schema_version: 1`, `job_id`, `latest` (the latest
observation or null), `fresh` (boolean), and `stale_reasons` (array of strings).
With no report, return an explicit absence, not a passing
empty report. Reading must not create state, execute commands or repair files.

`validate --require-checks` must accept only complete passing independent evidence
for the current stored task, latest attempt and exact current source. Model
results cannot manufacture that evidence. Reject missing, failed, incomplete,
corrupted or stale reports, a modified task, changed HEAD/index, edited tracked
bytes/modes, new nonignored files and a later retry. A previous pass must not hide
a later failed check. Reject mismatches before changing job validation state.

Use the phase-1 executor rather than reimplementing command semantics. Re-running
`job check` is an explicit new execution and produces a new observation; `checks`
and `validate` never silently run commands. Existing `validate` without the new
flag preserves legacy behavior, but its report/documentation must distinguish
provider-reported command checks from independently executed evidence.

Support existing databases and jobs created before verification evidence existed;
do not fabricate historic checks. Retain job/attempt states, leases, queued jobs,
native task/result contracts and legacy validation compatibility. Tests must use
an actual earlier database/state and verify both successful upgrade and absence
of fabricated evidence, plus successful recheck after a legitimate source update
through the existing job workflow. Use synthetic credentials only.
