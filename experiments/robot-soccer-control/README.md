# Robot soccer control experiment

Status: v0 simulator and public controller contract

This experiment supplies a source-hidden Rust runtime for evaluating a central
controller that operates two omnidirectional friendly robots against three
built-in opponents in an attacking-half sideline-restart formation, analogous
to a throw-in or robot-soccer kick-in. The opponents actively adjust their
lane block, receiver mark, and goal coverage before and after the restart. The
target project receives only the runtime image and
[`PUBLIC-SPEC.md`](PUBLIC-SPEC.md); simulator source remains in this authoring
repository so hidden dynamics are not disclosed to the development agent.
The authoring-only rationale for the private opponent is recorded in
[`OPPONENT-DESIGN.md`](OPPONENT-DESIGN.md); do not copy it into an evaluation
target.

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

## Three-seed acceptance gate

A single successful episode is diagnostic evidence, not controller acceptance.
The development gate requires the same controller command to succeed on three
distinct simulator seeds. Seeds `1,2,3` are the default development triplet:

```bash
scripts/evaluate-robot-soccer-controller \
  --output-dir temp/robot-soccer-seed-gate/run-001 \
  -- python3 /path/to/controller.py
```

The evaluator starts a fresh simulator container for each seed, passes
`--base-url` and `--seed` to the controller, and writes the simulator trace,
controller stdout/stderr, and `summary.json` under the requested new output
directory. It exits zero only when the authoritative simulator result is
`success` for all three distinct seeds. A controller exit code or a success
claim in controller stdout cannot override a simulator failure.

Use `--seeds A,B,C` to select another triplet; duplicate seeds or any count
other than three are rejected. This is an authoring acceptance policy, not an
extra rule inside an individual 30-second episode.

## Streaming controller development

Use the development runner to evaluate each saved controller revision on eight
seeds concurrently. The runner copies the controller source tree into an
immutable revision directory before starting any episode, so an editor save
cannot change a controller that is already running:

```bash
scripts/develop-robot-soccer-controller \
  --controller /path/to/controller.py \
  --output-dir temp/robot-soccer-development/session-001 \
  --watch
```

The defaults are eight warm simulator workers and seeds `1,...,8`. Containers
start once when the runner session begins and are reused across controller
revisions; Docker startup is therefore outside episode timing. Each completed
seed is printed immediately as one JSON event; `revision_completed` includes the
success count, authoritative results, and average/worst wall-to-simulator time
ratio. Traces, stdout, stderr, the exact controller snapshot, and `summary.json`
are retained under `rNNNN-<digest>/`.

Keep one `--watch` process alive during an editing session instead of paying
worker startup for every revision. Establish broad default-seed coverage when a
strategy topology changes. Narrow `--seeds` is useful for reproducing a known
failure, but it is not evidence that a strategy generalizes; return to the broad
set before adopting or rejecting the candidate.

The entry point's parent directory is the default source tree. This preserves
local module imports, and edits to imported files trigger a new revision. Use
`--controller-root /path/to/source-tree` when the entry point is nested below
the desired root. Cache directories and bytecode are excluded; symlinks are
rejected so a saved revision cannot change through an external target. The
output directory must be outside the controller source tree.

If any snapshotted controller file changes while a revision is running, the
active immutable snapshot finishes and the newest saved content runs next.
Intermediate saves are intentionally coalesced so rapid editor writes do not
create an unbounded backlog. Stop watch mode with Ctrl-C. A one-shot eight-seed
run omits `--watch`:

```bash
scripts/develop-robot-soccer-controller \
  --controller /path/to/controller.py \
  --output-dir temp/robot-soccer-development/check-001
```

On Linux the runner assigns simulator workers to separate logical CPUs, using
one sibling from each physical core before reusing SMT siblings. Controller
processes are restricted to the remaining logical CPUs. This reduced the local
14-CPU WSL benchmark from an average/max real-time ratio of `1.123/1.237` to
`1.046/1.095` at eight concurrent episodes. Use `--no-cpu-pinning` only when an
external scheduler already owns CPU affinity or the host does not expose usable
CPU topology.

Custom controller launchers may use `{controller}`, `{base_url}`, and `{seed}`
placeholders after `--`. When placeholders are omitted, `--base-url` and
`--seed` are appended automatically:

```bash
scripts/develop-robot-soccer-controller \
  --controller /path/to/controller.py \
  --output-dir temp/robot-soccer-development/session-002 \
  --watch -- python3 -u '{controller}'
```

The streaming runner is for rapid exploration. The three-seed acceptance gate
above remains the final pass/fail policy and uses fresh simulator containers.

For bounded comparison evidence across a revision, summarize its trace files
instead of rebuilding long ad-hoc `jq` pipelines:

```bash
scripts/analyze-robot-soccer-traces \
  temp/robot-soccer-development/session-001/r0001-*/summary.json \
  --pretty
```

The report includes the authoritative terminal result, first ball motion,
largest velocity changes with the nearest friendly/enemy, maximum forward
progress, command counts, and `kick=true` counts. It is diagnostic evidence;
only the simulator terminal result decides success.

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
numbers. New traces include one private terminal snapshot so replay reaches
the actual terminal position despite observation latency. The snapshot is
written only after physics stops and is never exposed by the controller API.
Older traces receive a bounded estimate from their last public velocity.
Rendering does not expose exact contact events.

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
- Real-time only; the development runner parallelizes independent real-time
  episodes but does not accelerate simulation time within an episode.
- Dynamics and opponent parameters are compiled into the runtime and absent
  from the public API.
- The HTTP API exposes no contact, kick-success, game-start, or true-state event.
- The private referee enforces a distinct friendly receiver and a receiver
  kick before a goal succeeds, without exposing touch or kick events.
- A controller may be written in any language capable of JSON over HTTP.
- UI, a larger hidden evaluation corpus, randomized release packaging, and tmux
  goal runner are later layers. The three-seed authoring gate is intentionally
  small and does not claim holdout generalization.
