# Make duplicate delivery deterministic

A lifecycle test intermittently observes duplicate delivery after a worker
crash. Do not fix production code. Produce both:

- `diagnosis.json`, with the exact external-effect/durable-ack ordering,
  journal state before and after restart, and an honest statement of the
  delivery guarantee; and
- `regression.sh`, a deterministic crash/restart regression that uses the
  repository's explicit synchronization barrier, has a bounded timeout, and
  cleans only resources owned by the run.

The regression must return nonzero when it observes the seeded duplicate. The
public wrapper treats that exact, evidenced failure as a successful
reproduction. Timing guesses such as short sleeps are not an acceptable
synchronization mechanism.

For machine comparison, record the root-cause `event_order` as
`load-offset`, `external-effect`, `barrier`, `durable-ack`; use barrier event
`external-effect`; report delivery guarantee `at-least-once` and
`exactly_once_guaranteed: false`. The two evidence phases are
`before-restart` and `after-restart`. These are output vocabulary, not a
substitute for running the barrier and recording its actual journal/effect
observations.

Work only inside this disposable repository. Do not use the network, inspect
parent directories, commit, or modify paths other than `diagnosis.json` and
`regression.sh`.

Validate the result with:

```bash
bash -n regression.sh
python3 tools/validate_diagnosis.py diagnosis.json
bash tools/check-regression.sh regression.sh
```
