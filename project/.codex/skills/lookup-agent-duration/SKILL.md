---
name: lookup-agent-duration
description: Query measured, quality-conditioned agent task duration evidence from the versioned devcontainer atlas. Use when estimating how long an agent task may take, checking S/M/L or family coverage, comparing explicitly requested provider/model/effort/collaboration conditions, inspecting failure criteria or censoring, or determining that an exact condition is unmeasured.
---

# Lookup agent duration

Use the bundled discovery wrapper to query only the relevant atlas cells. Keep project-specific routing decisions outside the atlas.

## Query workflow

1. Identify the requested task family, structural size/profile and any explicit provider, model, effort, relation, runtime or environment conditions.
2. If profile values are unknown, run `coverage` with the known filters. Return the compact value inventory and ask for refinement; do not select a nearby cell silently.
3. Run `summary` for an exact cell. Start with `--max-rows 12 --max-output-bytes 32768`; these are context-safety caps, not agent-count or statistical defaults.
4. Use `compare` or `curve` only for dimensions the user explicitly asks to inspect. Show every other differing primary field alongside the observations.
5. Report the observation window, source run-set digest, evidence state, quality populations, failed criterion IDs, censoring, first-artifact resolution and inference-validity status with any duration.

Run from the directory containing this skill, or pass its absolute path:

```bash
python3 scripts/query_atlas.py \
  --mode summary --format markdown \
  --max-rows 12 --max-output-bytes 32768 \
  --family failing-test-diagnosis --size M
```

Set `AGENT_DURATION_ATLAS_PATH` or pass `--atlas PATH` to override data discovery. Use `AGENT_DURATION_VALIDITY_PATH` or `--validity PATH` for its companion. The wrapper checks project, skill and installed snapshots in that order. It auto-pairs only `current.json` with a same-directory `current-validity.json`; pass both paths for differently named snapshots. Use `--print-atlas-path` and `--print-validity-path` to disclose both sources.

## Interpretation rules

- Treat `single-observation` as one raw point, never as a typical band.
- Treat `same-case-repeat` as an exact-case observed range. Do not flatten runs across cases.
- Use case-aware output only when the versioned query returns it. Never invent quantiles, p95, prediction intervals or interpolation.
- Keep `requested`, `applied`, `rejected` and `unknown` generation settings separate.
- Keep quality-pass, quality-fail and quality-unknown populations separate. Include content-free failed criterion IDs when available.
- Treat `excluded` as unusable for effort-quality inference and `conditional-only` as exploratory evidence. `eligible-pending-comparison-gates` still requires matched identity, applied-setting evidence, repeat/singleton review and score headroom; it is not a recommendation. An all-pass ceiling does not prove reasoning saturation.
- A failed observation without an actually present, complete retained task artifact cannot establish that more effort failed to improve reasoning; preserve `task-artifact-not-retained`, `task-artifact-partial`, or `task-artifact-missing`.
- Keep right/admin-censored runs visible. Do not count a fast failure as a fast completion.
- Emit first-artifact time only for `progress-envelope`; preserve `not-observed`, `not-applicable` and `unknown`.
- Never rank providers/models/efforts/relations or generate a default configuration from this evidence.
- Return `unmeasured` when no exact cell exists. Adjacent identifiers are refinement hints, not substitute duration values.

Read [references/profile-fields.md](references/profile-fields.md) when mapping a task to filters. Read [references/interpretation.md](references/interpretation.md) when explaining evidence state, quality, censoring, comparison or missing data.
