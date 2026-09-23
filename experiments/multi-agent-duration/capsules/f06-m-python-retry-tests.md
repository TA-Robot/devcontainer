# F06-M-PY-001: design retry-policy mutation tests

Expand `tests/test_policy.py` into a clear table/property-style suite for the contract in `POLICY.md`. Production and the contract document are frozen.

Required coverage:

- status classification for 400, 429, and the boundaries of the 5xx range;
- idempotent versus non-idempotent methods;
- one-based attempt boundaries and the terminal last attempt;
- supplied server delay, deterministic default delay, and the maximum cap;
- critical multi-axis rows, including 429 combined with method and last-attempt behavior;
- failure output traceable to the input row.

Use `FakeClock` for all delay observations. Do not call wall-clock sleep or inspect production source text.

Scope:

- Modify only `tests/test_policy.py`.
- Do not change `retry/`, `POLICY.md`, or validation tools.
- Do not use the network or inspect paths outside this fixture.

Validation:

```bash
python3 -m unittest discover -s tests -v
python3 tools/check_test_only.py
```

Return a concise summary of the matrix and validation results.
