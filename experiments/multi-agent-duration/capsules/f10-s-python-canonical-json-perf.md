# F10-S-PY-001: diagnose repeated canonical JSON work

Diagnose the local report hot path and write `performance.json`. Do not patch source or tests.

Copy `performance-template.json` to `performance.json`, then replace every
placeholder from local evidence. `performance.json` is the only editable path;
do not create scratch reports or benchmark-output files. Commands may write to
stdout, which must be embedded directly in the declared artifact.
Put any temporary data under `/tmp`. Before returning, `git status --short`
must list exactly `?? performance.json`; the public validator enforces this.

`performance-contract.json` is the public output vocabulary. Use its candidate,
relation, counter, strategy, condition, and preservation IDs verbatim. The contract defines
the answer shape, not which candidate the observations support; derive that from
the counters and source evidence.

Run the correctness suite and capture the JSON benchmark output for several field counts. The diagnosis must include:

- the exact reproducible command and embedded raw observations;
- deterministic serialization/sort counters for multiple sizes;
- source path, symbol, line, and snippet evidence for the scaling cause;
- comparative evidence that rules out the nearby sort as the primary scaling cause;
- a conditional optimization hypothesis that preserves canonical bytes, field order, and output count;
- no universal elapsed-time or percentage-speedup claim.

Only `performance.json` may be changed. Do not inspect implementation source from tests, change validators, or add extra artifacts.

Validation:

```bash
python3 -m unittest discover -s tests -v
python3 bench.py --json | python3 tools/validate_performance.py performance.json -
```

Return the measured counter relationship and validation results.
