# Reject ambiguous duplicate JSON object keys

The shared `scripts/agent_contracts.py:load_json` accepts repeated object names
with last-value-wins behavior. A task, result or schema can therefore contain
conflicting declarations that disappear before validation. Fix the shared loader.

Reject duplicate decoded property names at every object depth, including objects
inside arrays and equivalent escaped names. Raise `ContractValidationError` with
a useful diagnostic identifying duplicate-key ambiguity and the input path.
Do not include property values or the entire document in that diagnostic.
Equal names in separate sibling objects are allowed. Names are compared after
JSON escape decoding, without case folding or Unicode normalization.

Preserve ordinary JSON values and their types, including top-level arrays and
scalars. Preserve rejection of non-finite literals and overflowing floating-point
numbers, JSON syntax errors, and file I/O errors. `validate_file` must enforce
the same policy for both the instance and schema. Do not rewrite input files.
Keep the public interfaces and dependencies unchanged. Add relevant regressions
and documentation, and execute the applicable repository checks.

This task concerns the shared contract loader, not every unrelated JSON parser
or log-redaction path in the repository. Keep the change scoped to that behavior.
