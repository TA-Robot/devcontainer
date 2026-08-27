# Adjudicate the isolation reviews

Create `adjudication.json` and `ADJUDICATION.md` using the public review claim
IDs and evidence IDs. Merge duplicate race findings without losing reviewer
provenance. Replay the supplied Linux exploit and use it to accept the
post-check race and reject the claim that canonicalization alone is sufficient.

Keep Windows junction behavior unknown and state the missing Windows-specific
test surface. Narrow impact to the demonstrated workspace escape; credential
access is not evidenced. Every disposition needs decisive evidence or an
explicit missing-evidence boundary, plus calibrated confidence.

The Markdown ledger must match JSON. Do not modify reviews, evidence, sources,
or validators.

Validate with:

```bash
bash evidence/exploit.sh
python3 tools/validate_adjudication.py adjudication.json ADJUDICATION.md
```
