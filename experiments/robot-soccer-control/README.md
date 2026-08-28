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

## Offline video replay

Rendering is a separate post-processing job. The simulator never imports an
image or video library and performs no drawing while an episode is running.

```bash
scripts/build-robot-soccer-renderer
scripts/render-robot-soccer-trace \
  /path/to/robot-soccer-simulator.jsonl \
  /path/to/replay.mp4
```

The default compact profile is 960x640, 24 fps, H.264 CRF 30, and the `slow`
preset. It includes the field, robot heading, front kick segment, ball trails,
episode time, and terminal result. A specific run in a multi-episode trace can
be selected with `--episode 3`; `-1` selects the latest run.

Increase `--crf` toward 36 for a smaller, lower-quality file, or reduce it
toward 22 for inspection. Width and height must be even. Rendering reconstructs
only delivered public observation frames and linearly fills missing sequence
numbers; it does not gain access to hidden state or exact contact events.

## Dependency boundary

- reason: Rust provides a deterministic, low-overhead real-time physics core;
  `serde`, `serde_json`, and `tiny_http` provide the bounded JSON/HTTP surface.
  The optional renderer image uses Python, Pillow, DejaVu Font, and FFmpeg to
  turn completed public traces into compact H.264 video.
- impact: crates are compiled only in the builder stage; the main Dev Container
  gains no Rust toolchain or runtime dependency. Rendering dependencies live
  only in a digest-pinned Alpine image and do not enter the simulator image.
- alternative: a Python simulator would simplify authoring but make real-time
  physics timing and source-hidden delivery less representative. PNG frame
  directories were rejected because they consume much more intermediate disk.
- removal: delete this experiment directory and its build/test scripts, then
  remove locally built `robot-soccer-simulator:*` and
  `robot-soccer-renderer:*` images explicitly.

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
