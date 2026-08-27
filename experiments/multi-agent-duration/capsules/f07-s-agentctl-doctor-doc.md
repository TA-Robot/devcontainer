# Correct the doctor documentation

Update only `README.md`. The doctor examples must match the live parser,
including JSON output and the position of `--workspace`. Explain the actual
workspace-containment rule and what happens to an outside path without
inventing a bypass.

Keep the existing valid JSON example and local parser link. Add a `doc-facts`
JSON block that maps the containment claim to its visible source path and
symbols so the prose and source assertion can be checked together.

Do not modify the CLI, tests, or validators. Work only inside this disposable
repository, do not use the network, and do not inspect parent directories.

Validate with:

```bash
python3 -m unittest tests.test_cli -v
python3 tools/check_docs.py README.md
```
