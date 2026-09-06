# Diagnose an interrupted worker

A worker processes the event at its saved offset. Operations that publish an
external effect and persist progress cross a process-crash boundary. Investigate
the checked-out implementation and demonstrate an interruption that produces a
delivery anomaly after a fresh process restarts. Do not repair production code.

Write only `reproduction.json` and `diagnosis.json`. All other supplied files
are immutable. Work inside this disposable repository, without network access
or inspecting parent directories. Temporary investigation data belongs in `/tmp`.

`reproduction.json` selects a deterministic interruption, with exactly these fields:

- `stop_after`: one of `append-effect`, `persist-offset`, `read-offset`.
- `restart_count`: integer `1`.

The operation names are vocabulary, listed here without a prescribed order.
The observation tool blocks the worker immediately after the chosen operation,
kills that owned process, observes its files, and starts a fresh process once.
It also records the same workload without interruption as a baseline.
No sleeps, arbitrary commands, paths, signals or cleanup instructions are accepted
in the plan. The default workload has `events = ["event-1"]`, initial offset `0`
and no external effects. Run:

```bash
python3 -B observe.py reproduction.json
```

Exit zero means observation completed; it does not mean your diagnosis is correct
or that an anomaly occurred. Read the observed states. Investigate the visible
worker and journal to explain them.

`diagnosis.json` must contain exactly these fields:

- `event_order`: each of the three published operations once, in actual worker order.
- `interruption`: an object with `after` and `before`, naming the adjacent operations
  around the selected crash window.
- `before_restart`, `after_restart`: objects with `offset` (nonnegative integer)
  and `effects` (ordered array of event strings), matching the default observation.
- `outcome`: `duplicate`, `lost` or `once`, describing delivery of the pending event.
- `exactly_once_established`: boolean indicating whether this experiment establishes
  an exactly-once delivery guarantee for the service generally.
- `explanation`: a nonempty explanation in any language. Wording is not graded;
  the structured claims and executable observation are the evaluated evidence.

Acceptance checks source integrity, plan validity, an actual delivery anomaly,
operation order and crash boundary, both observed states, outcome, and the limit
of what this finite experiment establishes. Evaluation executes the plan against
an evaluator-owned copy of this implementation; submitted success claims cannot
replace observed state. It repeats the observation and changes event identifiers
and the starting offset to verify that the same plan still exposes the window.
Those checks use the same published semantics, not an undisclosed new requirement.
An anomaly must differ from normal, uninterrupted delivery.

This is a bounded diagnosis task. It does not score repairing the worker, writing
an arbitrary regression program, or general prose quality.
