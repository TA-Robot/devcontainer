# Inspect candidate acceptance

Assess the supplied CLI candidates against the quoted public requirements in
`requirements/`. The quoted development requests describe their required behavior;
your task is inspection, not implementing or repairing them.

This inspection covers only:
- `matching-adoption`: explicit adoption of existing matching files, mismatch
  rejection, preservation, repeat adoption, and subsequent updates.
- `path-boundaries`: separate source/target roots, reserved metadata/Git paths,
  and source/target/metadata symlink boundaries.

Other requirements and overall readiness are outside this assessment. A candidate
may have problems beyond these scopes. Candidate names convey no quality ranking.
Read the code and make your own public probes. Neither candidate must be accepted.

The inspection environment mounts this public directory at `/task`, read-only.
Your Python probe can use `/work` and `/tmp` for disposable files. Invoke candidate
CLIs with explicit source and target paths; their original repository is absent.
There is no network, credential mount, evaluator, or prior assessment available.
Do not modify the candidates or inspect outside the supplied task and scratch space.

Print one JSON object to stdout (send incidental diagnostics to stderr):

```json
{
  "candidates": [
    {
      "id": "candidate-1",
      "scopes": {
        "matching-adoption": "unknown",
        "path-boundaries": "unknown"
      },
      "evidence": ["probe.py"],
      "reason": "Describe findings and remaining uncertainty."
    }
  ],
  "selected": null
}
```

Include every supplied candidate exactly once. Scope values are `acceptable`,
`needs-repair`, or `unknown`. `selected` is a candidate ID or null; selection means
acceptable in both measured scopes, not generally ready for production. Leave it
null when no candidate is justified or more investigation is needed.

Evidence references can name `probe.py` (the submitted probe), or a real file
relative to `/task` such as `candidates/candidate-1/manage-agent-project`.
References are checked structurally; they do not by themselves prove the reasoning.
Do not infer success from an exit code alone when the interface returns a plan or
status: inspect the reported result and relevant filesystem behavior.
