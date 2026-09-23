# Workload contract for scheduling difficulty calibration

The policy execution interface and evaluator-owned integer-tick semantics are
specified by scheduling/v1/TASK.md. This contract supplements that interface.
It does not claim that the task is already difficult for a strong solo agent.

The workload has four declared families: short dependency chains with unrelated
work, wide runnable frontiers with dependent tails, heterogeneous workers with
restricted jobs, and cache-sensitive dependency graphs. Jobs have 32–72 nodes,
4 or 8 workers, CPU/GPU-compatible subsets, variable duration and cache labels.
These are declared test-domain properties, not evidence that larger is harder.

Each population has three structural instances per family. Each instance has a
success and a failure stress case with identical initially observable job data.
The failure stress case ends at one hidden failing job. `failure_probability`
is retained from the interface as a **risk hint**, not a calibrated probability:
these paired stress cases are not independent Bernoulli draws. In this generator,
a failure stress case samples one job uniformly among hints at least 0.4, if
any, or among all jobs otherwise. A hint of 0.7 is not more likely than 0.4 in
that selection. Do not interpret these results as real-world expected failure
cost under the numerical probabilities.

Quality remains a vector per family: summed successful completion ticks,
summed blocker detection ticks, and summed actual busy-worker ticks across its
six stress cases. Lower is better. The pair and family are correlated units;
24 scenarios and twelve metric cells are not 24 or twelve independent trials.
Every scenario must be legal and measured. Invalid/unmeasured outcomes prevent
attainment and must not become zeros or disappear from the report.

The target is one concrete reference policy's vector, fixed before solo runs.
Meeting that entire vector demonstrates attainment of that reference level.
It is not a claim of optimality or an externally validated operational SLA.
More quality can exist beyond the target, and all raw metrics remain visible.
Public development target values may be provided; hidden qualification targets
are only applied after the actor freezes its chosen submission.

Develop and compare actual implementations, not just a classification of saved
policies. You may revise hypotheses, produce multiple candidates, build local
experiments and tests, analyze failure traces, and select your final policy
using public evidence. Your selected source is the result; the grader's best
score among rejected candidates is not substituted for your choice.

Authoring generator source, generation seeds, qualification/confirmation inputs,
the reference and contrasting policy implementations, their private traces,
and the authoring repository must not be included in the developer projection.
Public development fixtures may include their known outcomes to support local
experiments, but they reveal no unseen population's seeds or failure labels.
Confirmation is reserved for a later fixed comparison. Qualification is used
for authoring and strong-solo difficulty calibration, not reported as untouched
confirmation after that use. Same graph grammar with changed instances supports
within-domain evidence only.
