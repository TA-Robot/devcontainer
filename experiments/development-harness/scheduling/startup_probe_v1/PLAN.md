# Fixed startup / response diagnostic

The active question is whether the first response deadline mixes runtime startup
with policy work. Use the unchanged timing transport and its fixed policy image,
one CPU, 256 MiB, no network or credentials. No model or previous candidate runs.

Run six observations: normal, six-second delay before a fixed readiness marker,
and six-second delay after reading the request; each under the legacy immediate
request and a wait-for-marker request. Both use the unchanged five-second response
guard and 90-second scenario guard. The ready path waits at most 20 seconds inside
the same scenario guard. Six seconds is a hypothesis fixture chosen to exceed the
five-second guard; it is not a new policy performance target. Six trials are a
cost cap, with one observation per condition, no retries. Stop on any unexpected
outcome, unknown recovery or source mismatch. Primary/integrator owns these bounds.

Expected: normal responds under both clocks; startup delay times out only under
legacy; response delay times out under both. Save exclusive output, exact source
and policy hashes, all phases, raw transport clocks and separate recovery audits.
The finite bound is also enforced by each create/close operation, readiness wait,
scenario and response guard. SIGINT/SIGTERM stop subsequent observations.

The marker is trustworthy only because this is a fixed non-agent fixture. A
future production marker must come from an evaluator-owned launcher **before any
candidate code executes**. A candidate's self-reported readiness must not postpone
its clock. Candidate imports and initialization remain part of candidate time.
Keep a total scenario cap; moving startup outside the response guard must not
create an unbounded allowance.

Success demonstrates the controlled clock distinction. It does not attribute the
earlier timeout to a particular host cause, prove stable latency, qualify a hard
task, change any old score, or admit live comparison. Decide the smallest clock
change from this result before rerunning a full calibration or model episode.
