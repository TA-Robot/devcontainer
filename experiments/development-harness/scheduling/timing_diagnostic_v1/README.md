# Frozen-artifact timing diagnosis

The original [dynamic solo profile](../dynamic_solo_v1/result.md) remains withheld
under its 30-second total scenario cap. This separate diagnostic changes only
that cap to 90 seconds for the same submitted artifact and fixed reference.
It does not run a model, choose another candidate or resume the original run.

[Contract and budget](TASK.md); [results and source seals](result.json).

Both artifacts completed all 24 qualification cases. The submitted policy's
maximum scenario time was 40.593 seconds, while its maximum request time was
0.390 seconds. The 21 originally measured case results and traces matched exactly.
All 48 diagnostic containers were removed and checked absent. Wall-clock variation
and host/IPC overhead remain part of these times.

```bash
PYTHONDONTWRITEBYTECODE=1 DYNAMIC_TIMING_DOCKER=1 \
  python3 -m unittest scripts/test-dynamic-timing-diagnostic.py
```

Two tests passed, no skips, in 1.398 seconds. They verify unchanged physical
runtime bytes, distinguish actual Docker scenario/response deadline failures,
and check cleanup. The full two-artifact assessment additionally validates this
execution path; its raw artifacts are in the path recorded by result.json.

The diagnostic allowance is consumed. `run.py --original-run ORIGINAL --output NEW`
is the reproduction interface, not authorization to repeat until a preferred
result appears. Each assessment is bounded to 900 seconds plus cleanup reserve.
Partial grader results and cleanup metadata are retained even after failure.

No production dependency or new image is added. The original image/CPU/memory
boundary is reused. `runtime.py` is byte-identical to dynamic_v1; transport adds
the diagnostic total cap, maximum request timing and timeout-cause detail.
Future live comparisons must fix and validate their own timing policy before
developer execution rather than retroactively adopting these diagnostic results.
