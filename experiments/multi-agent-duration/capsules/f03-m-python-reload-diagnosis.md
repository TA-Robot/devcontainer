# Diagnose the reload-only expiry failure

The expiry integration test fails only after a job has been serialized and
reloaded. Diagnose the failure without changing source or tests. Write
`diagnosis.json` containing:

- an ordered causal chain from the serialization/reload boundary to the
  scheduler decision;
- executable local observations contrasting fresh and reloaded jobs;
- evidence for the relevant timestamp-state transition;
- unit-level and reload-integration regression proposals; and
- evidence that rules out the nearby scheduler-boundary distractor.

Work only inside this disposable repository. Do not use the network, inspect
parent directories, commit, or modify any path other than `diagnosis.json`.

Validate the result with:

```bash
python3 tools/confirm_seeded_failure.py --test tests.test_expiry --signature reload-retained
python3 tools/validate_diagnosis.py diagnosis.json
```

