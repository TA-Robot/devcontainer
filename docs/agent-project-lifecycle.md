# Project template lifecycle

`scripts/manage-agent-project` installs and conservatively updates the contents
of a template directory, including the real `project/` in this repository. It
requires Python 3.10+ and a Linux/POSIX filesystem supporting directory file
descriptors, `O_NOFOLLOW`, advisory `flock`, and atomic same-filesystem rename.
There are no third-party runtime dependencies or provider CLI calls.

## Usage

Run from this checkout; the target must be an **existing, separate directory**.
Create a new project directory explicitly if needed. `--source` names `project/`,
not this repository's root. Root paths and their ancestors must not be symlinks
and must not contain `..`. Source and target cannot contain one another.

```bash
mkdir -p /tmp/my-agent-project
scripts/manage-agent-project plan \
  --source project --target /tmp/my-agent-project --json > /tmp/agent-project-plan.json

# Review the saved JSON, especially status and actions, before applying it.
scripts/manage-agent-project apply \
  --target /tmp/my-agent-project --plan /tmp/agent-project-plan.json --json

scripts/manage-agent-project status --target /tmp/my-agent-project --json
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate-agent-contracts.py \
  --template-root /tmp/my-agent-project
```

Use the same plan/apply commands after updating the source template. Plans may
live outside TARGET; source files must remain available through apply. Status
uses only local metadata and does not require the source to exist. Recovery and
rollback also work without the source. JSON is also
the default output without `--json`. Errors produce `status: "error"` and a
nonzero exit code (argument parser errors use stderr).

Planning and status do not create files, metadata, lock files, or repair state.
Normal filesystem reads may update access times. A successfully computed plan
always exits zero, including `status: "conflict"`; automation must inspect the
status before applying. Invalid filesystems or metadata fail nonzero.

## Ownership and updates

The private `TARGET/.agent-project/state.json` records a schema version, source
absolute path, each managed file's upstream SHA-256 and POSIX permission bits,
the source directory inventory, the last transaction ID, and common base bytes.
The `bases` object maps every owned file to canonical base64 of its last upstream
contents; reads validate the inventory, encoding, and digest against `files`.
Keeping bases inside the single atomically replaced state file avoids a separate
object store and garbage collector. The metadata directory is created with mode
`0700` and state with `0600`. This encoding is not encryption. `.agent/` remains
the installed native contract and has no lifecycle state added to it.

Ownership is established by a successful add or explicit `adopt` command.
Plan/apply never adopt a pre-existing file, even when its contents and permissions
are identical to the template.
One conflict prevents the entire apply, including otherwise safe additions.
Existing `AGENTS.md` and provider settings consequently block installation at
their paths instead of being overwritten or merged. Existing directories can
be shared, and unrelated files in them are preserved.

To resolve an unmanaged conflict, use explicit matching adoption as described
below, or back up and relocate the conflicting project file before replanning.
A private source copy may omit paths you wish to leave unmanaged. There is no
force or exclusion flag. Customizing placeholders after installation counts as
a local edit.

For each managed file, compare the previous upstream baseline, current source,
and current target. Content **and file mode** participate in this comparison.

| Source versus baseline | Target versus baseline | Result |
| --- | --- | --- |
| Same | Same | Keep; no-op if nothing else changed |
| Same | Changed or missing | Keep local edit or local deletion |
| Changed | Same | Replace with new source bytes and mode |
| Changed | Already equals new source | Keep file; advance baseline |
| Changed | Different from both | Merge compatible text/content/mode changes; otherwise conflict |
| Deleted | Same | Delete managed file and relinquish ownership |
| Deleted | Locally changed or missing | Conflict |

The baseline remains the upstream version, not a retained local edit or merged
output. After a v1 → v2 merge, v3 is compared against upstream v2 so both old and
new local changes remain visible.
Convergence or a provenance-only change can advance state without rewriting
any project file. Replanning and applying an unchanged installation returns
`{"schema_version":1,"status":"noop","transaction_id":null}` without writing
metadata. A plan used for an actual change becomes stale after application;
generate a fresh plan to obtain the subsequent no-op.

`status` returns sorted `managed_paths` containing **files only**, plus
`local_changes` with paths, reasons (`modified`, `missing`, `directory`, or
`blocked`), and baseline/current fingerprints. `common_base_available` reports
whether recorded bytes are available for text merges. Status and plans return
hashes and modes, never base, local, or merged file contents. An unsafe symlink or unsupported
type is an error rather than something status silently repairs. An unmanaged
project returns empty lists. Missing owned files remain in `managed_paths`.

All source directories, including empty ones, are installed if absent. Directory
actions are marked `entry_type: "directory"`; directory sharing does not convey
ownership. Directories are never removed by template deletion. Newly created
project directories use `0755` subject to umask; existing directory permissions
are untouched. Regular files retain their source `0000`–`0777` mode (including
executable bits), byte-for-byte binary content, dot names, Unicode and spaces.
File/directory type transitions are conservative conflicts. File hard links are
copied as independent files; replacing a managed hard link does not change its
other links.

## Explicit adoption of copied projects

```bash
scripts/manage-agent-project adopt \
  --source /path/to/matching-template --target /path/to/existing-project --json
scripts/manage-agent-project status --target /path/to/existing-project --json
```

Adoption checks the entire source and all corresponding target paths twice
before writing metadata. Every source file must already exist as a regular file
with identical bytes and identical owner/group/other executable bits (`0111`).
Other ordinary permission differences are preserved and reported as local mode
changes. Unrelated files remain unmanaged; target `.git` is ignored. Source or
affected target symlinks, unsafe types, reserved source paths, mismatches, and
malformed metadata reject the entire operation. An error creates no ownership.

Success uses the same JSON result shape as apply: `status: "applied"` and a
transaction ID for new ownership, or `status: "noop"` with a null ID for repeated
matching adoption. Project file bytes, modes, identities, and modification times
are untouched. Missing empty source directories are not created by adoption;
a later plan/apply can install them. Re-adoption requires matching source path,
baseline inventory, and directories in existing ownership; it cannot extend or
replace another registration. Use plan/apply for updates to registered projects.

For a copied project that is already customized, use the exact historical
template version it was copied from as SOURCE. Preserve customized files in a
backup outside TARGET, manually restore the matching historical template files,
adopt that version, and restore the customized files from the backup. Now plan
against the newer template and review/apply the result. Adoption never guesses
the historical base or changes project files to make them match. If the original
template is unavailable, compatible historical merges cannot be inferred safely;
reconcile a deliberate matching baseline before adoption.

## Supported merge semantics and conflict resolution

Content and the complete ordinary POSIX mode are separate three-way values. For
either value, a one-sided change wins and equal changes converge. Two different
mode changes conflict; permission bits are not combined individually. A local
executable-mode change can coexist with upstream content changes and vice versa.

When both sides changed content differently, all three versions must decode as
UTF-8 and contain no ASCII control bytes other than TAB, CR, and LF to qualify
for text merging (DEL is also excluded). A standard-library
`difflib.SequenceMatcher` (with autojunk disabled) finds edits to base lines.
Lines split only at LF; CRLF bytes and a missing final newline are preserved.
Disjoint replacement/deletion spans and separated insertions are combined in
base order, and identical edits are included once. Different overlapping edits
conflict. Insertions at the same position, or at either boundary of the other
side's replacement/deletion, conservatively conflict unless the complete edits
are identical. Adjacent nonempty replacement spans are disjoint and can merge.
Ambiguous alignment in repeated lines can produce a conservative conflict.
This is a line merge, without word-level, syntax-aware, rename, or move handling.
Two different edits on one line conflict even when they change different words.

Binary content (excluded control bytes or non-UTF-8) is copied exactly for one-sided updates, and
converges when both sides have identical bytes. Different changes on both sides
conflict. Text conflicts also leave every target file untouched: the tool never
inserts conflict markers. `compatible_changes_merged` actions identify successful
merges; file add/update actions include the computed output hash and mode in
`result`. These output fingerprints can differ from the proposed upstream baseline.

When a plan conflicts, preserve local work outside TARGET and inspect the
conflicting paths and source changes. To accept upstream for a conflicting file,
deliberately replace its target bytes/mode with the current source, then replan
and apply; convergence advances the baseline. To retain a manually composed
resolution of overlapping changes, save that resolution outside TARGET first,
perform the same convergence/apply step, then restore the resolution as a local
edit. Merely saving a different overlapping edit may still conflict against the
old base. Resolve all conflicts before applying; editing JSON decisions is not
a resolution mechanism. For an upstream deletion, preserve the local file,
restore its old baseline to allow the managed deletion, then optionally restore
the saved file as unmanaged. A future source addition at that path conflicts.

Legacy state without `bases` remains readable and obeys conservative
update rules. Read-only operations and no-op apply do not rewrite it. A successful
changing apply records current upstream bases for subsequent merges. If both
contents diverged while the historical bytes are unavailable, the plan conflicts
instead of inventing a base. Back up local work and use the convergence workflow
above for that first update. Regenerate saved plans after upgrading the tool;
plans are exact computed records, not a cross-version interchange format.

## Plan validation and filesystem safety

Public plans have `schema_version: 1`, a `ready` or `conflict` status, and
`actions` with relative POSIX `path` and `kind` (`add`, `update`, `delete`, `keep`,
or `conflict`). Reasons and entry types make them reviewable. Additional fields
contain source/target roots, the complete source inventory, affected target
paths and their ancestors, metadata preconditions, and the proposed baseline.

Apply does not interpret the plan as executable instructions. It validates the
action paths and uniqueness, recomputes the entire plan from current source,
ownership state, and target, and requires an exact structural match. JSON object
key order and formatting do not matter; duplicate keys, extra fields, missing
fields, invalid schema values, and edited decisions fail. Source additions,
deletions, permission changes, content changes, target changes, root replacement,
and metadata changes invalidate a saved plan. File observations include SHA-256,
mode, size, device/inode, link count, and nanosecond modification/change times.
Directory observations include identity and permissions, not modification time,
so unrelated file creation or edits do not invalidate a plan, including within
shared directories containing managed files. Output payloads and their modes
are recomputed from the actual source, target, and validated common base; plan
declarations cannot bypass a conflict or supply arbitrary replacement content.

All verification happens before target writes. Source bytes are read into memory
and checked again against the plan before staging. Operations walk directory
descriptors with `O_NOFOLLOW`, including root ancestors. Source, affected target,
plan, and metadata symlinks are rejected. FIFOs, sockets, devices, and files with
special permission bits are rejected. Absolute, empty, repeated-separator,
dot/dot-dot, backslash, and drive-letter action paths are rejected. Every source
path component named `.agent-project` or `.git` is reserved and rejected,
including empty directories with those names. Metadata must have precisely the
supported structure; symlinks, linked state files, invalid hashes/modes,
overlapping ownership, malformed/missing/mismatched base entries, and unexpected
files cause failure. The complete absence of the optional `bases` field is
accepted as the legacy state format; journals and their version flag
are validated separately.

Target `.git` files, directories, and symlinks are never traversed or modified.
The tool does not invoke Git, hooks, providers, installers, or project commands.
Installing a provider configuration is only a byte copy explicitly requested by
the template operation; no provider trust/permission commands are executed.

## Durable transactions, interrupted updates, and rollback

Apply/adopt/recover/rollback take a nonblocking exclusive `flock` on the open
target directory itself. Plan/status take a shared lock. There is no lock-file
creation or stale-lock cleanup, and the OS releases the lock on process exit.
Two mutators cannot interleave; a busy client exits nonzero and can retry.
Separate target directories remain independent.

Before any project replacement/deletion, the complete write set, before/after
bytes and modes, original ownership bytes, next ownership, target identity,
and directory preconditions are recorded in `.agent-project/<id>.json`.
Images are embedded canonical base64 with SHA-256 digests. Journals have a
versioned, strictly validated structure and a checksum over the entire record.
A durable `head.json` reference also detects removal of the latest journal; it
is published before project writes and checked alongside the ordered history.
Files and containing directories are fsynced; atomic same-filesystem renames
publish each journal update and target replacement. A reusable private `scratch`
file holds staged output and is never interpreted as executable instructions.
It may remain if staging was interrupted; read-only commands leave it alone.
If interrupted before the first journal was published, no project path has
changed and there is no pending transaction to restore. A scratch-only staging
remnant is harmless; an empty metadata directory is ambiguous and rejected for
manual inspection. Remove an empty remnant only after verifying that no ownership
or journal ever existed there.

A durable cursor records progress after each replacement. Recovery accepts only
the known before/after image at the single ambiguous crash boundary, completed
after-images before that boundary, and before-images after it. Ownership is
published after project changes, followed by the completed journal marker.
There is no multi-file atomic visibility: readers may see intermediate files.
Durability requires a filesystem/storage stack that honors fsync and rename.

```bash
manage-agent-project status --target /path/to/project --json
# When pending_transaction is non-null:
manage-agent-project recover --target /path/to/project --json
# Replan against the desired source before retrying the update.
```

Status always includes `pending_transaction` (opaque ID or null) when metadata
is valid. During interruption it reports the current published ownership and
actual local fingerprints; these can temporarily reflect partly applied files.
Another apply/adopt/rollback and planning refuse while a transaction is pending.
Recovery is explicit and needs no original source or saved plan.

Recover validates all journals, backups, parent directories, ownership, and
**all affected paths before any restoration write**. It restores before-images
and the exact prior ownership bytes, marks the journal `recovered`, and returns
that status with its ID. Repeated recovery returns `noop` and a null ID.
Restoration has its own durable cursor: interrupted recovery can be retried.
Recover also resumes an interrupted rollback, returning `rolled_back`.

If an affected path changed after the interruption, recovery refuses the entire
operation. It lists paths requiring manual resolution without exposing contents.
Save those edits outside TARGET, inspect the journal's before/after images and
the actual files, deliberately restore the expected version, and retry recovery.
Then reintroduce your saved edits. A missing/corrupt backup, checksum mismatch,
unknown metadata entry, symlink, or changed parent identity also fails closed.
Preserve the target and metadata for manual inspection; do not remove journals
to bypass this check. No automatic repair guesses missing recovery data.

```bash
# ID comes from the successful apply/adopt result or status.transaction_id.
manage-agent-project rollback --target /path/to/project --transaction ID --json
```

Rollback is allowed only for the latest recorded, completed transaction. It
requires unchanged after-images for every path that transaction wrote and
unchanged resulting ownership; changes on unrelated or retained paths survive.
It restores exact prior bytes/modes, including local edits present before a
merge, and the prior ownership/common bases. A rolled-back adoption relinquishes
ownership without touching adopted files. Rollback returns `rolled_back` and the
ID; repeating it before another transaction returns `noop` and null. IDs are
validated as opaque tokens, never paths. Unknown IDs and rollback across any
later recorded transaction are rejected, including across a recovered or
rolled-back transaction. This is one-step undo, not a history-rewinding stack.

Directories are shared and never owned: explicit recovery/rollback leaves
created directories in place, including empty ones, preserving unrelated files
inside them. Ordinary I/O failures attempt immediate restoration and remove
only empty directories created by that failed invocation. If that restoration
fails, the pending journal remains detectable and explicit recovery is required.
Completed/recovered/rolled-back journals remain private history; they are not
removed on success. There is no automatic history pruning.

### Compatibility and private data

Earlier `state.json`-only installations remain readable and updatable. No-op
or read-only commands do not migrate them. The first changing transaction adds
journals and `journal_version: 1` to ownership. Its rollback restores the old
state exactly. Older transactions cannot be rolled back because no before-images
were retained. Old interrupted `transaction-*` directories lack the durable journal
recovery contract and require manual inspection; they are rejected unchanged.

`.agent-project/` uses mode 0700; journal and state files use 0600. This directory
contains historical project contents (including local before-images), so keep
it private and back it up appropriately. Newly created ownership directories
include a tool-owned `.agent-project/.gitignore` containing `*`, so ordinary Git
discovery and add operations exclude this private state. The tool does not edit
the project's own `.gitignore` or `.git`, or untrack already committed files.
Older metadata directories without this file remain unchanged, including on
no-op/read-only operations; keep those excluded through the project's existing
Git exclusion settings. An ignore-only bootstrap remnant or an altered private
ignore file is rejected for inspection, not silently repaired.
Plans/status expose only fingerprints, not private
file contents. Journals are checksummed local records, not signed authority:
an actor able to rewrite all metadata and recompute checksums is outside this
integrity boundary. Do not copy ownership metadata between target directories;
transaction records are bound to their original absolute path and root identity.

### Reproducible crash tests

Only opt in on a disposable project:

```bash
AGENT_PROJECT_TEST_CRASH_AFTER_REPLACE=1 manage-agent-project apply \
  --target /tmp/disposable-project --plan /tmp/disposable-plan.json --json
# Expected exit 99, no success JSON; recovery data was already made durable.
manage-agent-project recover --target /tmp/disposable-project --json
```

`AGENT_PROJECT_TEST_CRASH_AFTER_REPLACE=N` requires a positive integer and exits
99 immediately after the Nth apply file replacement/deletion, before progress
publication. Directories and ownership writes are not counted. If fewer than N
files change, no crash occurs. `AGENT_PROJECT_TEST_CRASH_AFTER_RESTORE=N` similarly
tests interruption after N actual recovery/rollback file restorations. These
variables are test facilities only; unset them for normal operation and retries.

## Distribution and limits

The devcontainer image ships `/usr/local/bin/manage-agent-project`, its default
source `/usr/local/share/agent-project/template/`, this guide, and a native
contract validator under `/usr/local/share/agent-project/validation/`. Rebuild the
image to update the shipped template; installed project updates remain explicit.
From any working directory, without a checkout mount:

```bash
manage-agent-project plan --target /path/to/project --json > /tmp/project-plan.json
manage-agent-project apply --target /path/to/project --plan /tmp/project-plan.json --json
# For a matching historical copy (registration only):
manage-agent-project adopt --target /path/to/matching-project --json
```

The installed executable resolves its template relative to its installation
prefix (`bin/../share/agent-project/template`), never relative to cwd. Checkout
execution through `scripts/manage-agent-project` defaults to sibling `project/`.
Explicit `--source` always overrides either default. Copying just the executable
to a custom location requires an explicit source or that installation layout.
Removing the binary and `/usr/local/share/agent-project/` removes the image
feature; it does not delete any target files or ownership. No new third-party
runtime dependencies were added. The shipped validator reuses the image's
already-declared Python 3.10 TOML compatibility package.

Advisory locks coordinate this tool, not editors or other programs. Stop
concurrent external writers during apply/recovery/rollback; descriptors prevent
symlink traversal but do not isolate against hostile directory renames or mount
changes. Templates should be trusted before providers later consume their
instructions/settings. No trust/permission command is run by the lifecycle tool.
ACLs, xattrs, ownership, timestamps, directory modes, sparse layout, and hard-link
relationships are not replicated. Multiple templates, automatic historical-base
discovery, case-insensitive filesystems, cross-mount commits, and Windows are
unsupported. Roots must remain in place for recovery. Bytes and journal history
are buffered in memory, history grows with transactions, base64 adds about one
third, and line matching can take quadratic time on repetitive text. Full journal
snapshots are flushed per progress step; this suits small templates, not bulk
datasets. Files must be readable and their containing directories writable.

## Verification

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest scripts/test-manage-agent-project.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate-agent-contracts.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest scripts/test-agent-contracts.py
scripts/test-devcontainer-lock.sh
scripts/test-devcontainer-ai-cli-sync.sh
scripts/test-devcontainer-ai-cli-wrappers.sh
bash -n scripts/devcontainer-grok scripts/devcontainer-grok-trusted scripts/sync-host-ai-cli-versions .devcontainer/initialize-host.sh scripts/test-agent-project-container.sh
docker build -f .devcontainer/Dockerfile -t devcontainer-smoke:latest .
scripts/test-mira-container-hook.sh devcontainer-smoke:latest
scripts/test-agent-project-container.sh devcontainer-smoke:latest
scripts/test-devcontainer-lock.sh --build
```

The lifecycle tests invoke the executable CLI and inspect files in test-managed
`/tmp` directories. They include installation of this repository's actual
`project/`, validation with `--template-root TARGET`, binary/mode fidelity,
unmanaged conflicts, explicit adoption (including rejection without writes),
v1/local/v2/v3 merges, conflicts, binary and newline behavior, content/mode merges,
read-only/no-op behavior, stale/edited plans and metadata, path/type attacks,
locking, and I/O rollback. A copy of actual `project/` is updated with simultaneous
local/upstream edits and validated again using `--template-root TARGET`.

CLI regressions additionally inject crashes at every position of a
three-file update/deletion, interrupt recovery and rollback, verify all-path
conflict preflight, tampered/missing backup and symlink rejection, repeated
operations, merged-output rollback, state-only compatibility, concurrent
clients, and independent targets. The container smoke mounts no repository and
uses no network; it installs the shipped real template, validates it, merges an
update, crashes/recovers/retries it, validates again, and rolls it back. Frozen
build verification invokes this smoke too. See `DEVELOPMENT_HANDOFF.md` in the
checkout for the actual executed checks and environment blockers.
