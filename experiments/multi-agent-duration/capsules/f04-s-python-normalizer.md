# F04-S-PY-001: local tag normalizer

Implement `normalize_tag` in `tag_normalizer.py`.

Requirements:

- Accept a string and return a normalized tag.
- Trim leading and trailing whitespace.
- Convert ASCII letters to lowercase.
- Treat every run of spaces, tabs, underscores, or hyphens as one `-` separator.
- Keep only ASCII letters, digits, and normalized separators.
- Reject a result that is empty or longer than 32 characters by raising `ValueError`.
- Do not change the public function name or add third-party dependencies.

Scope:

- Modify `tag_normalizer.py` and tests only if useful.
- Keep the implementation deterministic and side-effect free.

Validation:

```bash
python3 -m unittest discover -s tests -v
```

Return a concise summary of changed files and validation results.
