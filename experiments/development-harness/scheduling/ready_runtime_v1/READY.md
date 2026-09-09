# Runtime-ready clock contract

The evaluator starts its fixed Python launcher and waits up to 20 seconds for
runtime readiness. The launcher cannot load or execute the candidate before
receiving an activation byte. The evaluator starts the five-second first-response
clock before sending activation together with the original JSONL request.
Candidate parsing, imports and initialization are included in that response cap.
Later responses retain the same five-second cap. The 90-second total scenario
cap includes Docker creation, runtime readiness, simulation and all responses.

The candidate still receives exactly the original JSONL protocol and original
source bytes at its original path; no readiness message is requested from it.
Its stdout remains response-only. Candidate-emitted stderr cannot reset a clock
or create another readiness phase. Runtime readiness failure is separate from
response timeout and invalid policy output. None is retroactively assigned to
old results.

20 seconds is a hard startup guard for this version, scoped to evaluator runtime
readiness and owned by primary/integrator. It is not extra candidate development
or unlimited startup permission. The observed six-second synthetic delay informs
the separation, not stable performance or a universal startup bound. Further
failure invalidates calibration and motivates a new prospective decision.

The physical simulator, workload inputs, policy image, CPU/memory limits, response
cap, total scenario cap and quality arithmetic remain unchanged. Both the public
actor checker and independent Docker assessment use the same launcher, activation
handshake and request loop. Public timing includes its actor process environment;
independent timing includes Docker. Equality of physics/results is checked, not
assumed equality of observed latency.

Current scope: fixed non-agent tests and public FIFO/initial calibration only.
No old live artifact or private qualification is regraded. A new pair protocol and
matching actor preflight are required before any live use of this clock contract.
