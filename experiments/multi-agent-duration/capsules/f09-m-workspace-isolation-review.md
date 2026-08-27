# Review the composed workspace isolation bypasses

Complete `security_regression.py` and create `security-review.json`. Reproduce
both visible trust failures independently: an in-workspace symlink whose
resolved target escapes, and inherited `TASK_WORKSPACE` replacing the trusted
launcher root. Also prove a direct descendant and a safe internal symlink still
work.

The regression must use `SECURITY_PROBE_ROOT`, emit structured observations,
and exit nonzero only when both seeded escapes are observed. The public wrapper
converts that exact expected failure into success. The review must connect both
layers and require trusted root provenance plus post-resolution containment;
it must not flag the safe explicit-root path or require privileges/network.

Do not modify runtime source, tests, launchers, or validators.

Validate with:

```bash
bash -n bin/run-task
python3 -m unittest discover -s tests -v
python3 tools/check_security_regression.py security_regression.py --expected symlink,env-root
python3 tools/validate_security_review.py security-review.json
```

