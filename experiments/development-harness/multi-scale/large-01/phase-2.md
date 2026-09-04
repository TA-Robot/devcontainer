Extend the existing project lifecycle feature for teams that already customized copied templates. Preserve every requirement and working behavior from phase 1.

Users need to retain local edits while taking compatible upstream changes, and migrate projects copied before this tool existed.

Add:

    manage-agent-project adopt --source SOURCE --target TARGET --json

Adoption is explicit ownership registration, not installation or overwrite. It succeeds only when every source file already exists with the same bytes and executable mode, no source/target symlink is involved, and no conflicting ownership exists. Unrelated project files are allowed and stay unmanaged. Any mismatch rejects the entire adoption without creating partial ownership. A repeated matching adoption is a no-op. Subsequent plan/apply/status must work normally after adoption.

Improve updates:
- Preserve both sides of non-overlapping text edits using the recorded common base. For example, local changes to the first line and upstream changes to the last line of a multi-line text file must both survive an update. Do not select an entire side and discard the other silently.
- Competing edits to the same region remain conflicts, with no conflict markers or partial writes inserted into target files. Binary changes on both sides remain conflicts unless the sides are byte-identical.
- An upstream deletion with local modifications remains a conflict; an upstream addition colliding with an unmanaged file remains a conflict.
- A saved plan is invalidated by a changed source or affected target file, including executable-mode changes. Unrelated new/edited target files do not invalidate an otherwise safe plan and must survive apply.
- Reject edited plans that try to redirect a target, traverse a directory, introduce conflicting/duplicate actions, or bypass a required conflict. A plan's declarations do not replace actual precondition checks.
- Document the supported merge semantics and user workflow for resolving conflicts; keep status informative without returning private file contents unnecessarily.

Add end-to-end tests using a source v1, locally edited target, and source v2, then v3. Run all earlier regressions. Verify the actual project/ template remains valid after an update. This is a continuation on the existing source, not permission to replace the feature with a shortcut specific to one fixture.
