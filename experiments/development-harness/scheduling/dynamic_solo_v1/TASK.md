# Strong-solo online scheduling quality exploration

Implement a robust policy for the continuing service described in RUNTIME.md.
Maximize on-time delivered value across all public workload families and load
bands while preserving critical (weight 16) service. Report both objectives:
gains in other classes must not hide a critical-class regression. Keep unfinished
value, deadline deficit, response tails and actual resource use visible too.
No binary pass target or claim that 100% delivery is feasible is imposed.
Some severe workloads have insufficient capacity for all work; choosing which
work to protect and how to allocate resources is part of the problem.

Develop and compare multiple real implementations, self-review, generate tests,
experiment with algorithms, and select one final source using public evidence.
You are one reasoning agent. Do not call another model or spawn an agent.
Ordinary local algorithms and non-model subprocesses are allowed.

Read /public/RUNTIME.md for exact events, observations and constraints.
/public/development.json contains 24 public cases covering every declared band
and family. Their private-for-runtime fields are visible for public experiments;
do not use case memorization or future labels in policy decisions. Unseen cases
are externally graded after submission; none of their data or feedback is given
to the developer. /public/probe.json is a tiny public smoke example.
No authoring generator or alternative reference implementation is provided.
FIFO is a starting implementation, not the target quality ceiling.

Run `python3 /public/public_check.py --candidate /work/POLICY.py --output /work/NEW.json`.
Use --cases /work/YOUR_CASES.json for subsets or your own valid scenarios.
Keep distinct source revisions and experimental reports; choose using broad
coverage after narrowing for diagnosis. Public runtime/evaluator semantics match
external scoring. Public experiments share one CPU and 2 GiB with the developer;
external policy has one CPU and 256 MiB. Self-tests do not certify final resource
compliance; remain within the published final limits. Time includes IPC and host
simulation, not only policy computation. External timeout is unmeasured.

Save the selected single-file Python policy at /work/submission.py (max 64 KiB).
Finish with a concise account of compared approaches, experiments, selection and
remaining weaknesses. Self-selected submission is primary; rejected candidates
are not silently substituted after hidden evaluation.

Development budget: 2400 seconds including experiments and selection; 80000
observed output tokens. You may finish early. Full public evaluation currently
takes roughly 1–2 minutes for the supplied non-agent policies; use the time for
substantial redesign and repeated tests. A clean final turn with usage is required.
