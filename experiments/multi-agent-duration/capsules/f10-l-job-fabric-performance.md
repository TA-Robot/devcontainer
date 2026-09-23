# F10-L-PYBASH-001: diagnose multi-stage job-fabric resources

Complete `instrumentation.py` and produce `performance.json` for the deterministic job simulator. No real Docker or provider access is needed or allowed.

Required analysis:

- correlate every job/stage event and preserve monotonic stage ordering;
- separately compute batch user wall time, worker span, worker interval union, aggregate worker time, stage totals, queue distributions, and resource signals;
- keep ascending and descending width blocks distinct;
- compare locked width-4 behavior with the no-lock counterfactual;
- identify the global image-probe lock as the width-dependent queue/tail cause;
- identify provider wait as the largest per-job active stage without calling it the width-tail cause;
- retain complete/timeout/failure and resource inventories, including censored runs;
- avoid treating aggregate time as wall/critical path or simulator units as production latency.

Only `instrumentation.py` and `performance.json` may be changed. Source, tests, launcher, validator, and extra paths are frozen.

Validation:

```bash
python3 -m unittest discover -s tests -v
bash bin/run-batch --matrix visible --output observations
python3 tools/validate_performance.py performance.json observations
```

Return the conditional bottleneck model and validation results.
