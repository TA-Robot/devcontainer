# F04-M-PY-001: coupled state and CLI update

Complete the `kvtool` package so its CLI can update and read a JSON-backed key/value store.

Requirements:

- `python3 -m kvtool.cli --store PATH set KEY VALUE` stores or replaces one string value.
- `python3 -m kvtool.cli --store PATH get KEY` prints the stored value and exits 0.
- A missing key exits 3 without a traceback.
- An empty key exits 2 and must not modify the store.
- Persist a JSON object with deterministic key ordering.
- Replace the store atomically so an interrupted write cannot leave a partial JSON document.
- Preserve unrelated keys across updates.
- Do not add third-party dependencies.

Scope:

- Keep storage behavior in `kvtool/store.py` and argument/exit behavior in `kvtool/cli.py`.
- Update tests or `USAGE.md` when needed to keep the public contract aligned.

Validation:

```bash
python3 -m unittest discover -s tests -v
```

Return a concise summary of the implementation, changed files, and validation results.
