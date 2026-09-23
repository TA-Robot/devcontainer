# Prospective failure-refinement cohort

Fixed before model starts, 2026-09-09; owner: primary/integrator.

The primary contrast is the previously tested adaptive instruction (`standard`)
versus the failure-refinement instruction (`refined`), with identical collaboration
capability. A fresh strong `solo` is the capability reference. One start per
condition, serial order **standard, refined, solo**. No retry, replacement start,
continuation of previous developers or selection across repeated runs. This is
an exploratory check of an instruction change, not a stable effect estimate.

The refinement aims to turn common candidate failures and disagreements into
counterexamples and better implementations or new integrations. The expected
mechanisms are error decorrelation and evidence-producing refinement. Participants
and interaction depth remain the developer's choice. Conversation volume, role
names and candidate counts do not constitute improvement.

All conditions use gpt-6-astra/high, pinned CLI 0.153.0 and the same actor image,
public bytes, native workspace sandbox, shared development CPU 1 / memory 2 GiB,
90s per scenario / 5s per response. Solo keeps code execution, self-review,
alternative implementations and sequential experimentation. Both collaboration
conditions have the same native tools; their instruction text is the treatment.
Equal time and ceilings do not mean equal realized tokens or financial cost.

## Inputs and observation boundary

Use the unchanged dynamic generator with public seed base 1047293 and assessment
base 1303637; each expands by family*1000 + band*100 + replicate, as before.
Both populations contain 24 scenarios: three load bands, four families, two
replicates per cell. These seeds are fixed without inspecting candidate outcomes.
IDs retain development/qualification grouping for the frozen arithmetic reporter;
new content hashes and the campaign identity distinguish these populations.

These are new instances of an already explored family. They are not independent
new tasks or an unused confirmation population. No existing confirmation is used.
Public input validity and fixed FIFO execution may be checked before live; the
assessment input is validated and sealed without selecting on policy scores.
Generator, seed configuration, assessment input and other developers' work/results
are never mounted into an actor. Only the nine public projection files are exposed.
No hidden quality feedback is sent to any developer.

All three normally completed selected artifacts and actor result hashes must be
sealed before the assessment input is used for scoring. Verify that barrier before
each assessment. Hash mismatch, unknown cleanup, abnormal participant termination
or missing selected artifact stops further starts/scoring and retains the partial
cohort. Every attempted start is recorded before calling the actor. No failure
releases an extra start. An invalid policy is distinct from an evaluator failure.

## Budgets and independent result axes

| Parameter | Role | Scope, rationale and invalidation |
| --- | --- | --- |
| 3 starts, serial order | cost cap | One initial old/new/solo contrast; no replication or retry. Serial execution avoids direct CPU/provider concurrency competition between conditions |
| 2400s development each | cost cap | Same as the previous strong-solo/adaptive profile, with full development freedom |
| 160000 observed output each | post-response acceptance cap | All participants and compactions; same headroom as the previous pair. It is not a streaming enforcement or guarantee of maximum billing |
| 900s assessment each | cost cap | Revised evaluator previously measured full policies within this allowance; timeout preserves unmeasured status |
| 10500s outer job | cost cap | 7200s developers + 2700s assessments + 600s preparation/cleanup reserve |
| 24 public + 24 assessment cases | planning prior | Same broad load/family coverage with fresh draws; not 24 independent development runs |
| CPU/memory, source seals, information boundary | hard guard | Inherited validated isolation; any violation withholds comparison admission |

No limits are extended after starts. Unknown usage and observed output excess do
not erase normally completed artifact quality: continue the registered cohort and
retain output-budget admission as `withhold`. The primary report states quality
under the common development clock separately from output-cap admission and cost.
It must not claim quality at a certified token budget, cost efficiency or complete
billing when those are unknown. A known overrun is explicitly `exceeded`, never
zeroed or accepted. There are no additional model calls for judging or synthesis.

## Decision and reporting

Report all selected artifacts and 24 cases, 12 cells, three bands for each
condition: on-time value, critical service and denominators, unfinished value,
censored deficit, completed-only response tails and worker use. Show refined minus
standard as the primary contrast, and both versus solo. No scalar score hides a
critical regression. A Pareto improvement in aggregate value and critical service
is a promising observation only if every band's critical service is nondecreasing;
otherwise retain the tradeoff and cell regressions. Do not change that rule after
observing results. This rule is a scoped hypothesis/triage criterion, not proof of
general superiority or of online feasibility at perfect delivery.

The selected final artifact is primary. Better rejected candidates, common-failure
changes and useful critique are mechanism diagnostics, never replacement submissions.
Prompt verbosity and scheduling order are limitations; a single cohort cannot
identify which sentence or interaction caused a difference. The outer preparation,
human review and diagnostic costs are unmeasured and reported separately.

Live admission requires unchanged native recovery validation, source-matched
cohort preflight (normal, missing usage, output excess, deadline stop and exclusive
starts/barrier), and full public FIFO calibration. The fixed campaign directory
is single-use; preparation failure does not silently reopen it.
