# Diagnose the explicit-zero failure

One test in this repository fails because an explicit configuration value is
not preserved. Diagnose the failure without changing production source or
tests. Write `diagnosis.json` containing:

- the exact root-cause path, symbol, expression, and semantic distinction;
- a minimal local reproducer command and input, with expected and observed
  values;
- repository evidence for the claim; and
- a concrete regression-test proposal that treats a missing value and an
  explicit zero as separate scenarios.

Work only inside this disposable repository. Do not use the network, inspect
parent directories, commit, or modify any path other than `diagnosis.json`.

Validate the result with:

```bash
python3 tools/confirm_seeded_failure.py --test tests.test_limits --signature explicit-zero
python3 tools/validate_diagnosis.py diagnosis.json
```

