# Verification history: consistent filters and continuation

Extend the existing history view with `--attempt ATTEMPT_ID` and `--status STATUS`.
A supported status is one of the actual stored command-verification statuses.
Reject invalid status values. Results must belong to the selected job and satisfy
all supplied filters; a foreign attempt must never reveal another job's records.

A cursor belongs to the job and filter set for which it was issued. Reject a cursor
used with another job or different filters. Existing pagination must not include
observations appended after its first page, repeat a record, or skip an existing
matching record. A new query without a cursor can see new observations.

History remains available when the latest delivery is dirty, failed, or otherwise
not eligible for fresh verification. Preserve recorded identities and statuses;
viewing history must not imply that an old pass is fresh or authorize validation.
Exercise reads across independent CLI processes and preserve the earlier phase's
read-only and pagination requirements.
