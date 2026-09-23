# F11-S-BASH-001: repair one Bash case terminator

Fix the parser error in `sync-version.sh` with the smallest behavior-preserving patch.

Requirements:

- Run `bash -n` and repair the missing `;;` after the existing `host)` arm.
- Do not rewrite the `case`, reorder arms, change quoting, or alter `host`, `container`, `auto`, fallback, or error behavior.
- Preserve auto precedence: non-empty host version, then container version, then default version.
- Do not change tests, add dependencies, or reformat unrelated lines.

Validation:

```bash
bash -n sync-version.sh
bash tests/smoke.sh
```

Return the exact repair and validation results.
