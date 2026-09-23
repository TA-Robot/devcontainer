# Duration case family fragments

Each `fXX.json` is a standalone valid case catalog containing exactly the S/M/L cases for one family. This is the exclusive catalog edit surface for that family implementation.

Required rules:

- `catalog_id`: `duration-atlas-fXX`
- one family enum and exactly one `S`, `M`, `L` entry
- case IDs, profiles, criteria, capsule paths, and recipe IDs match the six design documents
- capsule digest is computed from the checked-in capsule bytes
- every task remains network-disabled and uses the common workspace/evaluator isolation contracts
- each hidden target maps to one concrete `unittest` target in the recipe's private evaluator

Family implementers do not edit the aggregate `../cases.json`. The primary agent reviews fragments and generates one new versioned aggregate after all families calibrate.

Focused tests should call `assert_family_calibrated()` from `scripts/agent_duration_case_testing.py`. This verifies initial-fail, private-known-good all-pass, and declared negative-mutant rejection for all three sizes.
