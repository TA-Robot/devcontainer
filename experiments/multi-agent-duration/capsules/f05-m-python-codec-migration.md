# F05-M-PY-001: migrate to an injected `EventCodec`

Complete the migration from the old module-level `encode_event(dict)` API to an injected `EventCodec` object while retaining a byte-compatible deprecated shim.

Requirements:

- Implement `SchemaPolicy` and `EventCodec` in `events/codec.py`; encoded JSON bytes must be deterministic and carry the injected schema version.
- Migrate `Producer`, `Ledger`, and `Replay` to receive and retain one component-owned codec. Do not construct a codec for every event.
- Discover and migrate the reflective plugin registry as well as grep-visible imports.
- Keep deprecated `encode_event` available through `events.compat` and the package export, but not from `events.codec`.
- The compatibility shim must produce the old canonical bytes and the same exceptions for valid and invalid inputs.
- Each compatibility call emits exactly one `DeprecationWarning`; direct `EventCodec.encode` calls emit none.
- Preserve only the documented new and deprecated exports. Do not add dependencies or weaken existing tests/tools.

Validation:

```bash
python3 -m unittest discover -s tests -v
python3 tools/check_callers.py
```

Return a concise caller inventory, compatibility note, and validation results.
