Develop a real project-template lifecycle feature for this devcontainer repository.

Today users copy project/ and manually avoid overwriting their AGENTS.md and provider settings. Implement a usable, dependency-light lifecycle tool, not a demo or design-only answer. Inspect the repository and its instructions. Preserve existing native contracts and the user's project content.

This phase delivers initial installation and conservative updates. Provide an executable scripts/manage-agent-project with these public commands (additional fields/options and internal architecture are your choice):

    manage-agent-project plan --source SOURCE --target TARGET --json
    manage-agent-project apply --target TARGET --plan PLAN_JSON --json
    manage-agent-project status --target TARGET --json

SOURCE is a template directory such as this repository's project/, not the repository root. TARGET is a separate project directory, which may contain existing files. plan must be read-only, including not creating metadata in TARGET. It prints a JSON document with schema_version: 1, status: "ready" or "conflict", and actions: [{path: relative POSIX path, kind: "add"|"update"|"delete"|"keep"|"conflict"}]. A successfully computed plan exits zero even when conflicts exist. Include enough preconditions for apply to verify the actual source and affected target paths have not changed since planning. The JSON plan is saved by the caller, outside TARGET if desired.

apply rechecks the plan before modifying anything. A conflicting, malformed, stale, or unsafe plan must fail nonzero without altering existing target content. Success returns JSON status "applied" or "noop", and transaction_id (a string for a change, null for a no-op). status returns JSON with managed_paths (sorted relative paths); explain locally modified managed files in additional fields. Read-only commands must not silently repair state.

Required behavior:
- Install the actual project/ template, including dot-directories, arbitrary binary bytes, Unicode/space names and executable bits. Preserve unrelated target files.
- Store ownership/provenance in TARGET/.agent-project/, separate from the installed .agent/ contracts. Treat this metadata as private to this tool; reject a source containing the reserved .agent-project or .git paths.
- Never adopt or overwrite pre-existing unmanaged files implicitly, even when their bytes match. A conflict must not result in a partially installed project.
- Replanning and applying the same installed source is a no-op. Updates replace an unchanged managed file when its upstream changes, retain a locally changed managed file when upstream is unchanged, and report conflict when both change incompatibly.
- Template deletion may delete only an unchanged managed file; a locally changed deleted file is a conflict. Do not remove unrelated files/directories.
- Validate all relative paths and filesystem types. Reject traversal, absolute action paths, duplicate actions, symlink escapes (source, destination, metadata), and malformed metadata. Do not execute code from the plan. Target .git contents are never managed or modified.
- Do not run Git add/commit, hooks, provider commands, package installers, or trust/permission changes in the target project.

Document design choices, CLI usage and limits in docs/agent-project-lifecycle.md, and add meaningful tests under scripts/. Verify installation of real project/ using scripts/validate-agent-contracts.py --template-root TARGET. Complete relevant repository checks. Tests must exercise the CLI and observe files, rather than only asserting internally reported success. Avoid third-party runtime dependencies unless their need and removal are documented. Keep all disposable target projects outside this repository or in test-managed temporary directories.

The public interface is fixed for independent acceptance; the implementation design is not prescribed. Later phases will extend this same feature. Finish and test the requested behavior now, preserve your source edits, and report remaining limitations honestly.
