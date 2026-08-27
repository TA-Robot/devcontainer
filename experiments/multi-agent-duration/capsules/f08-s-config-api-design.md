# F08-S-MDJSON-001: configuration API decision

Compare `pure-merge` and `config-builder` using `options.md`, all five entries in `constraints.json`, and the executable scenarios in `callers.py`. Do not implement either API.

Create only `DECISION.md` and `decision.json`. The JSON contract is:

- `schema_version`: `1`.
- `choice`: selected visible `option_id`, bounded `variant`, and explicit `request_isolation`, `deletion`, and `nested_values` semantics.
- `constraint_dispositions`: exactly one row per visible constraint ID, with status `satisfied`, its visible `required_semantic`, and `{path, anchor}` evidence resolving in the fixture.
- `counterexamples`: at least one for each raw option, with visible scenario ID, local command argv, and expected violated constraint ID.
- `claims`: stable claim IDs, text, non-empty visible constraint IDs, and resolving source evidence.
- `unknowns`: every decision-relevant visible open-question ID that evidence cannot close.
- `document_markers`: unique marker strings also present in Markdown as `<!-- architecture-marker:MARKER -->`.

Requirements:

- Evaluate all five visible constraints.
- Reproduce a concrete failure for each unmodified option using `callers.py`.
- The selected variant must provide fresh per-call state, a deletion sentinel distinct from JSON null, and opaque nested replacement.
- Do not invent performance, scale, or typing guarantees absent from fixture evidence.
- Keep Markdown and JSON claims synchronized; modify no fixture evidence or validator.

Validation:

```bash
python3 tools/validate_decision.py decision.json DECISION.md
python3 -m unittest discover -s tests -v
```

Return the choice, decisive counterexamples, unresolved questions, and validation results.
