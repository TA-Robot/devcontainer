# Atlas profile fields

Use these fields to narrow a duration lookup. Do not substitute a nearby value for an omitted or unavailable exact cell.

## Primary strata

- Task: `family`, structural `size`, `profile_id`, case ID and revision.
- Collaboration: relation, participant plan, actual participant/worker counts, peak concurrency, nested-delegation policy and lane.
- Runtime: every participant's role, provider, model identity confidence, resolved/requested identity, generation-setting status and applied value, CLI build, execution surface and permission mode.
- Environment: image digest, machine class, session context, repository/dependency/Docker/provider-cache state, compaction, competing load and timezone.
- Observation boundary: study ID and observation window.

Changing a primary field produces a different series. Never merge `requested` or `unknown` effort with an `applied` effort cell.

## Evidence fields

- `single-observation`: one raw point; it is not a typical range.
- `same-case-repeat`: multiple observations of one exact case; its range is case-local.
- `family-provisional`: multiple case strata exist, but study-specific coverage and precision may still be unassessed.
- `quality-pass`, `quality-fail`, `quality-unknown`: separate populations.
- `right-censored` / `administratively-censored`: terminal time is a lower-bound or interrupted observation, not a successful completion.
- First artifact is available only when `resolution=progress-envelope`.

## Query discipline

Start with the fields the user actually supplied. If several primary values remain, return a compact value inventory and ask for refinement rather than pooling them. Preserve the source run-set digest and observation window in any numerical answer.
