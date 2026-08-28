# Simulator authoring architecture

This document belongs to the devcontainer infrastructure repository and must
not be copied into the controller target project.

```text
authoring source
  -> pinned Rust builder stage (tests + release build)
  -> source-free runtime image
  -> public HTTP contract
  -> arbitrary-language central controller
```

The core simulator is deterministic under a seed and advances with fixed
physics steps. The runtime layer attaches those steps to wall-clock time. Tests
exercise the core without sleeping; the HTTP smoke test exercises real-time
delivery and lifecycle behavior.

Public geometry and game rules are represented separately from the private
dynamics configuration. `/v1/spec` is constructed only from the public type and
must never serialize the private configuration.

The private referee observes exact collision and kicker geometry internally.
It records the first friendly contact, a later contact by a distinct friendly,
and a front-segment kick by that receiver. Only a goal after this sequence is a
success. These internal events are used for scoring but are never included in
the observation or trace, so the controller must infer them from ball motion.

Before the first friendly contact, enemy steering is supplemented by a hard
geometric projection at the published exclusion radius. The rule therefore
does not depend on the built-in opponent policy tracking its target accurately.

The observation pipeline samples true state at a nominal 30 Hz, assigns a
private delayed release time of nominal 200 ms plus seeded jitter, and exposes
only the newest released frame. It never serializes the sample time or true
state.

The text trace records public requests, delivered observations, and public
results. At termination it records one `terminal_snapshot` so offline replay
can show the goal or boundary crossing hidden behind observation latency. This
is a single post-physics write, is not exposed through the controller API, and
adds no per-tick rendering or serialization. The trace intentionally omits
private configuration and all other unreleased true state. Because it can still
contain controller behavior and coordinates, it is private experiment evidence
rather than general telemetry.
