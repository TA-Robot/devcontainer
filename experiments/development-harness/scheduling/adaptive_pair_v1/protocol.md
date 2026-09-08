# Prospective adaptive scheduling exploration, pair v1

Fixed before live starts, 2026-09-09. Owner: primary/integrator.
Question: does adaptive collaboration produce a stronger selected policy on the
current dynamic scheduling domain than a fresh strong solo under the same
development deadline and output ceiling? This is one exploratory pair, not an
estimate of stable success rates or proof of solo impossibility.

Order is **solo, then adaptive**, one start each, serial. No retries, replacement
starts, winner selection across runs, continuation of prior developers, or reuse
of the withheld solo as control. Both artifacts are sealed before either receives
external qualification scoring. The developer never receives that scoring.
The 24 qualification cases are hidden from these developers but already known to
the outer project; this is not unused confirmation data. No confirmation is spent.

Expected collaboration mechanisms are coverage of different policy approaches,
independent counterexamples/review, empirical prototype selection and integration.
The developer chooses the relationship and number of participants. Fixed advisor
messages or a prescribed number of parallel implementations are not the treatment.

Both conditions use gpt-6-astra/high, CLI 0.153.0, the same pinned actor image,
public input bytes, 1 CPU / 2 GiB shared development resources, workspace isolation,
90s per scenario / 5s per response, and no shell network access. Only native
collaboration availability and its instructions differ. Full-participant costs,
including compaction, are counted from response records, not root stdout.

| Parameter | Role | Scope and rationale / invalidation |
| --- | --- | --- |
| 2 starts, fixed order | cost cap | This exploratory pair; sufficient for a first contrast, not replication. Failure does not grant another start |
| 2400s development each | cost cap | Previous strong solo needed about 2380s. Same prospective deadline for both |
| 160000 observed output tokens each | cost cap | Headroom for independent exploration and integration beyond the previous 52233 solo output; same ceiling, actual usage is reported separately |
| 900s per qualification assessment | cost cap | Prior full-policy assessment about 389s under the revised clock; stop and withhold if exceeded |
| 7500s whole job | cost cap | Two developers, two assessments and preparation/cleanup reserves |
| 4 concurrent native slots | planning prior / runtime capacity | Observed in the pinned CLI contract and four-node tree probe; not an optimal participant count |
| No evaluator input or credentials in developer work | hard guard | Existing container/public projection boundary; any violation withholds the comparison |

Token caps are post-response accounting/acceptance caps, not precise streaming
limits. Equal ceilings and wall time do not imply equal realized compute or equal
financial cost. Output overrun, unknown usage, unfinished participants, missing
submission, invalid policy, measurement failure or unknown cleanup are reported;
an incomplete condition cannot support a quality-effect claim. Stop the pair on
actor/measurement infrastructure failure and retain every attempted start.

Report all 24 cases, 12 family/band cells and 3 bands: deadline value, critical
on-time counts and denominators, unfinished value, deadline deficit and worker
use. Never trade away a critical regression inside a single aggregate score.
Keep selected artifacts primary; an unselected better prototype is diagnostic.
Report participant/response costs, total elapsed time and coordination evidence
without treating agent count as an outcome. Do not infer causation from dialogue
volume or a single pair. A subsequent harness change needs a new protocol and
new evaluation boundary.

Live admission requires the fixed source manifest, completed source-matched
actor probes (including tree, local/remote compaction, and missing usage), and
the pair's provider-free end-to-end preflight. The campaign output directory is
single-use; a failed preparation is not silently reopened.
