# Prove the encoded-separator isolation bypass

Create only `finding.json` and `security_regression.py`. Trace the visible raw
name validator through the percent-decoding caller and demonstrate a concrete
single-encoded separator that violates the one-segment workspace contract.

`security_regression.py` must use `SECURITY_PROBE_ROOT`, exercise the real
caller, emit a JSON observation, and exit nonzero when the seeded vulnerability
is present. The supplied wrapper treats that exact expected failure and its
filesystem postcondition as a successful study artifact.

Bound the impact to the fixture contract, state canonicalize-once-before-
validation as the remediation invariant, and do not claim double decoding or
an arbitrary parent traversal that the fixture does not prove. Do not modify
source, tests, or validators.

Validate with:

```bash
python3 -m unittest discover -s tests -v
python3 tools/check_security_regression.py security_regression.py --expected encoded-separator-escape
python3 tools/validate_finding.py finding.json
```

