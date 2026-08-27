# F05-S-PY-001: extract shared event-name normalization

Refactor the duplicate event-name normalization in `events.py` into one private helper without changing observable behavior.

Requirements:

- Both `emit_event` and `tag_event` must call the same private normalization helper.
- Preserve both public function names, signatures, annotations, and `__all__` exactly.
- Preserve normal outputs for the complete input matrix.
- Preserve exception classes, messages, and validation order. In particular, the two public callers intentionally do not validate every malformed input in the same order.
- Keep prefix construction and caller-specific validation in the appropriate public caller; extract only genuinely common normalization.
- Do not expose the helper or add another public symbol.
- Do not add dependencies or modify validation tools and existing tests.

Validation:

```bash
python3 -m unittest discover -s tests -v
python3 tools/compare_behavior.py
```

Return a concise summary of the extracted boundary and validation results.
