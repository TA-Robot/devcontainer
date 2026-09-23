# Termination-capture continuation pair

The [protocol](protocol.md) prospectively connects the validated deadline-capture
contract to both developers, a joint artifact barrier and independent assessment.
It preserves strong solo development and the shared initial implementation.
The [preflight record](preflight.md) also retains the discovery and recovery of
late-created containers, and the distinction between absence and proven recovery.

Current admission: **withhold**. Seven final-source tests passed, but the final
public calibration had one unmeasured initial-policy case. No live starts were
used. See [validation.json](validation.json) for source hashes and original records.

Synthetic preflight (real pinned CLI and Docker, no live provider or credentials):

```bash
TERMINATION_PAIR_DOCKER=1 TERMINATION_PAIR_EVIDENCE=NEW_PATH \
  PYTHONDONTWRITEBYTECODE=1 python3 -m unittest scripts/test-termination-pair.py
PYTHONDONTWRITEBYTECODE=1 python3 experiments/development-harness/scheduling/termination_pair_v1/calibrate.py --output NEW_PATH
```

All output paths are exclusive. Source-matched validation must exist before live
execution. This version does not reclassify old runs. Artifact quality, original
completion, observed capture time and output-budget admission remain separate.
