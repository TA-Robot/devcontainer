# Synthesize the wrapper evidence

Create `synthesis.json` and `SYNTHESIS.md`. Both analyses expose public input
claim IDs and the source snippets expose evidence IDs. Give every input claim a
disposition, canonical claim, cited evidence list, and evidence-bounded note.

Preserve the argv-forwarding agreement. Correct both blanket environment-
override claims to the conditional behavior shown by the source branch. Keep
logging assertions unsupported when no supplied source entails them. Do not add
recommendations beyond the evidence.

The Markdown must contain the same normalized claim ledger as JSON; prose style
is otherwise unrestricted. Do not modify analyses, sources, or validators.

Validate with:

```bash
python3 tools/validate_synthesis.py synthesis.json SYNTHESIS.md
```
