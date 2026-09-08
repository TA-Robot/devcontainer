# Post-run timing diagnosis: frozen policies, no developer rerun

The original dynamic-solo profile remains WITHHOLD. Its submitted policy hit the
30-second total scenario cap on qualification-severe-cache-1 after 21 measured
cases. No continuation of that profile, retry of its developer or score replacement
is permitted here.

This separate provider-free diagnostic evaluates exactly two frozen artifacts:
the original selected submission and the originally fixed joint-assignment
reference, on all the same 24 qualification cases. No new candidate is generated
or selected. Retain the original submission SHA and input hash.

The only scoring-environment change is a 90-second scenario cost cap, instead of
30 seconds. Per-response cap remains 5 seconds; CPU, memory, Python, observations,
physical clock and metrics are unchanged. runtime.py is byte-identical to dynamic_v1.
Transport additionally reports maximum request wall time and distinguishes total
scenario deadline from per-response deadline. It still includes IPC/serialization.

Rationale: the original failed case used about 21.9 request seconds over 551
responses; total elapsed reached 30 seconds. Public cases had completed under the
original cap. This suggests the inherited total cap was too tight for accumulated
policy work plus host simulation, rather than proving a slow single response.
90 is a finite diagnostic cost cap, not a measured optimal budget or a newly
validated production default. Owner: primary/integrator; scope: these two fixed
artifact evaluations only. Each whole evaluation also has a 900-second cap plus
30-second cleanup reserve. Stop on any invalid/unmeasured outcome; no repeated
extension. No model calls, credentials, confirmation population or host execution
of candidate code.

Report the diagnostic separately from the failed original measurement. Compare
overlapping measured results for reproducibility, do not overwrite them. Successful
completion here does not retroactively satisfy the original 30-second contract or
establish collaboration efficacy. The qualification data is now known diagnostic
data. A future live protocol must fix and preflight any revised time budget first.
