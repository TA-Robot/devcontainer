Implement independent acceptance-command execution for existing agentctl jobs.

Today `verify_result` checks Git independently, but accepts the provider's claim
that required commands passed. Operators need actual check results from the
submitted code, without starting another model session.

Add:

    agentctl --state-dir STATE job check JOB_ID --timeout SECONDS --json

Use the existing registered job, immutable task and latest successful terminal
attempt. Work in its actual attempt workspace. Refuse unknown jobs, absent or
active attempts, an unexpected HEAD, dirty submitted code or unsafe/missing
workspace before running any command. Preserve normal job run/validate behavior.

Execute only `acceptance` entries with `kind: "command"` from the stored immutable
task, in order, using a documented POSIX shell. Never execute commands from the
provider result. Do not invoke any provider, perform auth flows, push, merge,
alter the task or repair the user's source. Narrative acceptance entries remain
unexecuted and must not be presented as verified.

Honor an acceptance entry's optional `cwd` relative to the attempt workspace.
Validate these directories before executing the sequence: missing, symlinked or
escaping paths must not cause execution in an unintended directory. Report the
working directory for each check. The trusted command itself is not a sandbox.

`--timeout` is a finite positive number of seconds for the complete sequence,
not a fresh allowance per command; default 60 seconds. Terminate a timed-out
command and its process group. Nonzero exit stops the sequence and records later
commands as unexecuted. An empty command-acceptance list is `no-checks`, never a
successful verification. Bad options must fail before running commands.

Return JSON containing `schema_version: 1`, `job_id`, `attempt_id`, `status`,
`head_sha`, and a `checks` array in task order. Status is `passed`, `failed`,
`timed-out`, `source-changed`, or `no-checks`. Each check identifies its original
command as `command`, execution status as `status`, actual `exit_code` (null if
unavailable), `elapsed_seconds`, and `stdout_tail` / `stderr_tail` strings. Use at most 64 KiB retained across
both streams per command; drain large output without unbounded memory or disk.
Use the existing best-effort log redaction for returned tails. Synthetic secrets
only in tests; no new raw unbounded output files.
`head_sha` identifies the submitted HEAD captured before execution, even if a
command later changes HEAD. Each check's `cwd` is its validated absolute working
directory. Unexecuted commands have null exit code, zero elapsed seconds and
empty output tails. Elapsed seconds must be finite and nonnegative.

Check submitted source identity before and after execution. A changed tracked
file, changed HEAD/index, or newly introduced nonignored source file invalidates
verification. Observe tracked file bytes and modes, including paths hidden from
ordinary git status by index flags. Ignored test caches need not invalidate it.
Do not restore changes automatically. A command failure is still failure even if
its output says "passed"; zero exit with changed source is `source-changed`.

Exit zero only for `passed`; failed verification is nonzero. Store no successful
job-validation claim from merely starting a checker. Document the authority:
original task commands are trusted code running in the caller's execution
context, not an isolation boundary against a malicious same-UID process.

Add end-to-end tests with fake providers creating real existing job records,
including a provider claiming a failing command passed, wrong result command,
timeout and child cleanup, large output, source mutation, missing/active attempts,
ordinary success and existing regressions. Keep dependencies unchanged.
