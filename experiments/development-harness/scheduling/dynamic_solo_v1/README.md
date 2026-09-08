# Dynamic strong-solo development connection

**Initial allowance consumed. The developer submitted normally; the original
assessment is withheld after a scenario timeout. See [results and the separate
timing diagnosis](result.md).**

This task-specific adapter connects the frozen dynamic evaluator to a real
developer that can edit policies, run experiments, generate cases and select
a submission. The [protocol](protocol.md) fixes one initial 40-minute start and
continuous-quality reporting; no binary reference target is invented.

The pinned CLI/image, model metadata restriction and sandbox mechanism are reused
from static solo_v1 without changing that source. Actor CPU allocation is one
CPU; memory remains 2 GiB. Final policy runs remain on the dynamic evaluator's
one CPU/256 MiB boundary. The public local checker shares developer resources,
so exact timing parity is not claimed.

Public files are an explicit allowlist: TASK, RUNTIME, runtime/transport, FIFO,
public checker, development cases, a tiny smoke case and the actor marker.
The historical runtime contract's unfulfilled future absolute-target gate is
replaced in the projection by this protocol's continuous-quality scope. Runtime
scoring semantics and original files are unchanged. Reference code, authoring
generator, qualification and repository checkout are not mounted in the actor.

All source is snapshotted before projection and execution. The developer receives
no final qualification feedback. After its container is removed, the selected
source and a fixed non-agent joint-assignment reference are separately graded
on the same new qualification population. This reference is not an advisor.
Cases, sealed source, usage, failures and cleanup remain recorded. Final metadata
withholds interpretation on unknown usage, incomplete grading or unknown cleanup.

## Validation

```bash
PYTHONDONTWRITEBYTECODE=1 DYNAMIC_SOLO_DOCKER=1 \
  python3 -m unittest scripts/test-dynamic-solo.py
```

The actual CLI is driven by a synthetic endpoint to edit a broken policy, repair
it, run the public smoke case and confirm shell network denial. It checks the
actual additional-tool definitions for shell availability and absent subagents.
Tests also check independent scoring against public results, exact submitted
bytes, timeout cleanup, unknown usage and the public allowlist.
Persistent validation additionally runs all 24 public cases under one CPU and
compares every result and trace with frozen external FIFO results.

`validation.json` must match all current source hashes before live. The entry
command is `runner.py --auth EXISTING_AUTH --output NEW_PRIVATE_PATH`; it is not
permission for repeated starts. This protocol has exactly one live allowance.
Existing credentials are copied only for the finite developer job and deleted
in finally. Parent CLI networking and network-denied shell are separately scoped.
The legacy outer seccomp adjustment needed by bubblewrap remains unchanged.

No new production dependency, image build or devcontainer distribution change.
Retiring this adapter does not authorize deleting its shared image. Raw model
events and candidate source stay outside git; summary evidence uses hashes.

## Result recovery limitation

The original runner raised on incomplete assessment before embedding the grader
report, leaving cleanup unknown at its own layer. The raw grader report was
preserved. The reporting script now retains partial coverage/failure details, and
a separate audit verified the original 23 containers absent and credential copy
deleted. The original metadata is unchanged. Future controllers must retain
partial grader results on failure, as the timing diagnostic controller does.
