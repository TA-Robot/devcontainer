# F06-L-PYBASH-001: build deterministic lease lifecycle tests

Complete `tests/test_lifecycle.py` and `tests/lifecycle.sh` without changing production. Exercise the lease worker's concurrency, crash, restart, ownership, expiry, and cleanup contracts through fresh local subprocesses.

Required behavior:

- coordinate two-worker handoff through explicit probe/gate state, not arbitrary sleeps;
- force-crash only subprocesses started by the test and verify expiry from a fresh process;
- overlap owners before expiry and prove that only one live owner exists;
- verify exact cleanup and preservation of a peer-prefix resource sentinel;
- use bounded waits/timeouts with useful failure diagnostics;
- leave no owned lease/resource residuals and never use global process-name cleanup;
- pass repeatedly against correct production while rejecting lifecycle contract violations.

Scope:

- Modify only `tests/test_lifecycle.py` and `tests/lifecycle.sh`.
- Do not change `lease/`, `bin/lease-worker`, unit tests, or validation tools.
- Use only the standard library and repository-contained commands.
- Do not use the network or inspect paths outside this fixture.

Validation:

```bash
bash -n tests/lifecycle.sh
python3 -m unittest discover -s tests -v
bash tools/run-lifecycle-repeat.sh 5
python3 tools/check_test_only.py
```

Return a concise summary of lifecycle phases, cleanup guarantees, and validation results.
