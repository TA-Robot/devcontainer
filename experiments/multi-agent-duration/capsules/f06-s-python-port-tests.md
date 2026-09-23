# F06-S-PY-001: complete the port parser tests

Augment `tests/test_ports.py` to cover the complete documented `parse_port` contract. Production `ports.py` is frozen.

Required coverage:

- valid integer and decimal-string values, including 0 and 65535;
- adjacent invalid values below and above the range;
- booleans and floats as distinct invalid types;
- empty, whitespace-only, surrounding-whitespace, non-ASCII, and malformed strings;
- public return values and exception classes, without inspecting implementation source.

Scope:

- Modify only `tests/test_ports.py`.
- Do not change production, inspect source text from tests, or add dependencies.
- Do not use the network or inspect paths outside this fixture.

Validation:

```bash
python3 -m unittest discover -s tests -v
git diff --exit-code -- ports.py
```

Return a concise summary of the partitions covered and validation results.
