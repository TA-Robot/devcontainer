---
name: review-collaboration-evidence
description: Inspect bounded, content-free project-local evidence about solo, delegated, consulted, competing, verifying, or scheduled agent work. Use when planning or revising multi-agent orchestration, reviewing whether an expected mechanism appeared, comparing observed wall time or coordination proxies, checking decision-correlation coverage, or determining that the project lacks enough evidence to change its planning priors.
---

# Review collaboration evidence

Query the local Mira episode ledger before changing project orchestration. Keep task-specific judgment with the primary agent.

## Workflow

1. Run the bundled wrapper with `--format markdown --max-groups 20 --max-output-bytes 32768`. It filters to the current workspace by default.
2. Check `status`, valid/invalid episode counts, decision-correlation coverage, exact semantic dimensions, terminal outcomes, coverage and observed duration ranges.
3. Compare groups only when task fingerprint, execution surface, oracle and risk are independently known to be comparable. The report does not establish those controls.
4. State whether evidence is absent, descriptive, conflicting, or sufficient to revise one named project-local hypothesis. Preserve unknowns.
5. If a planning prior changes, update the project decision packet. Do not create a global agent-count, round-count, provider, model or effort default.

```bash
python3 scripts/report_evidence.py \
  --format markdown --max-groups 20 --max-output-bytes 32768
```

Use `--all-workspaces` only for an explicit cross-project audit. Pass normal report options after it.

## Interpretation rules

- Treat min / median / max as descriptions of retained observations, not predictions or causal effects.
- Treat `terminalOutcome: success` as lifecycle completion, not artifact correctness.
- Treat `reviewProxy` as post-worker tail time, not human review time.
- Keep `managed-job`, `delegated` and `solo-observed` surfaces separate.
- Require `annotationSource: primary-plan` and correlated decision coverage before interpreting relation, lifecycle, mechanism or binding constraint.
- Return `unmeasured` when no valid project episode exists. Never substitute Atlas data or another workspace silently.
- Do not expose episode, session, plan, candidate, workspace or decision identifiers. The report intentionally emits only aggregate counts.
- Do not recommend automatic routing, recurring jobs, merge, push or external side effects from this report alone.
