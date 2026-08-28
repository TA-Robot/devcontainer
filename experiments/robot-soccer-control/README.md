# Robot soccer control experiment

Status: v0 simulator and public controller contract

This experiment supplies a source-hidden Rust runtime for evaluating a central
controller that operates three omnidirectional friendly robots against two
built-in opponents. The target project receives only the runtime image and
[`PUBLIC-SPEC.md`](PUBLIC-SPEC.md); simulator source remains in this authoring
repository so hidden dynamics are not disclosed to the development agent.

The experiment is not a sample application. It is an evaluation fixture for
observing whether the devcontainer's primary agent can plan, delegate, compare
control approaches, inspect text traces, integrate results, and produce a
robust controller during one bounded goal.

## Build and run

The host repository intentionally does not require Rust. Build the source-hidden
runtime with the version- and digest-pinned containerized toolchain:

```bash
scripts/build-robot-soccer-simulator
docker run --rm -p 127.0.0.1:18080:8080 \
  robot-soccer-simulator:dev
```

Run the deliberately weak reference controller from another terminal:

```bash
python3 experiments/robot-soccer-control/examples/reference_controller.py \
  --base-url http://127.0.0.1:18080
```

The simulator writes a content-bearing development trace inside the runtime at
`/tmp/robot-soccer-simulator.jsonl`. Mount that exact file or its parent only
for private experiment diagnostics. It is not part of Mira's general telemetry.

## Dependency boundary

- reason: Rust provides a deterministic, low-overhead real-time physics core;
  `serde`, `serde_json`, and `tiny_http` provide the bounded JSON/HTTP surface.
- impact: crates are compiled only in the builder stage; the main Dev Container
  gains no Rust toolchain or runtime dependency.
- alternative: a Python simulator would simplify authoring but make real-time
  physics timing and source-hidden delivery less representative.
- removal: delete this experiment directory and its build/test scripts, then
  remove locally built `robot-soccer-simulator:*` images explicitly.

## Deliberate v0 boundary

- One active episode per runtime.
- Real-time only; no accelerated batch evaluator yet.
- Dynamics and opponent parameters are compiled into the runtime and absent
  from the public API.
- The HTTP API exposes no contact, kick-success, game-start, or true-state event.
- The private referee enforces a distinct friendly receiver and a receiver
  kick before a goal succeeds, without exposing touch or kick events.
- A controller may be written in any language capable of JSON over HTTP.
- UI, hidden evaluation corpus, randomized release packaging, and tmux goal
  runner are later layers; they do not block validation of physics/API semantics.
