# Independent scheduling policy assessment after runtime readiness

This version preserves the dynamic scheduling physics and JSONL policy protocol.
The evaluator owns released observations, future arrivals, actual processing times,
outages, resources, completion and every quality result. Candidate self-reports are
not scores. Preserve all workload bands, service classes and unfinished work.

A fixed evaluator-owned Python launcher reports runtime readiness and then blocks
on activation. The first five-second response clock starts before activation is
sent; parsing, imports and candidate initialization are inside that clock. The
candidate receives the original request and original source file, without a new
candidate readiness API. Later responses retain the same five-second cap.

The scenario cap remains 90 seconds from the start of container setup, including
runtime readiness, simulation and all requests. Runtime readiness has a separate
20-second guard inside that total. These are hard/cost guards owned by the primary
integrator for this version, not CPU-time claims or unbounded startup allowances.
See READY.md for the measurement contract and public-check scope.

The independent image, one CPU, 256 MiB, source/request/output caps, input validation
and physical simulator are unchanged. Runtime-readiness failure, response timeout,
invalid returned action and recovery uncertainty retain separate raw observations.
Any unmeasured case prevents a complete quality comparison. A missing cleanup proof
cannot be replaced by a single absence check after an uncertain create operation.

Current authorized calibration uses fixed non-agent fixtures, FIFO and the common
initial implementation on public inputs only. This version does not reinterpret
old episodes, scores or withholds, does not score qualification for task selection,
and does not establish hard-task eligibility or collaboration effectiveness.
A new fixed pair protocol and source-matched actor preflight are required for live.
