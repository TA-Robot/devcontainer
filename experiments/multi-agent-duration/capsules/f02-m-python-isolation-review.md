# F02-M-PY-001: review coupled workspace-job changes

Review the complete multi-file proposal in `change.diff`. Do not patch the proposal.

Write ranked findings to `review.json`. Each finding must have a separate reproducible trigger, impact and severity, changed-source evidence, and remediation constraints. Include structured `relations` when findings interact. The public validator defines the exact JSON shape.

Required review properties:

- trace changed contracts through their callers across `jobs/`;
- report distinct reachable correctness or security defects separately;
- rank the defects and explain any combined blast radius through a finding relation;
- cite the changed symbols and affected callers with resolving path/line/snippet evidence;
- do not elevate the structured logging hunk without a concrete supported defect.

For machine comparison, use category/trigger/impact codes `symlink-after-validation` / `symlink-after-check` / `workspace-isolation-escape` and `cleanup-ownership` / `caller-label-collision` / `cross-job-deletion`. The symlink trigger records `link_target`, `link_name`, `requested_path`, and `expected_outcome`; the cleanup trigger records `existing_job_id`, `current_job_id`, `caller_label`, and `expected_deleted_job`. Link the two finding IDs with mechanism `escaped-output-enters-shared-runtime` and consequence `cross-job-data-loss` when your evidence supports the interaction. Finding IDs themselves remain your choice.

Scope:

- Read repository-contained source, tests, and the proposed diff.
- Write only `review.json`; do not modify source, tests, or validation tools.
- Do not use the network or inspect paths outside this fixture.

Validation:

```bash
python3 -m unittest discover -s tests -v
python3 tools/validate_review.py review.json
```

Return a concise summary of findings and validation results.
