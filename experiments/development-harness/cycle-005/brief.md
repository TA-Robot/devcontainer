# Preserve usable AI CLIs when host-version synchronization fails

Improve this repository's startup synchronization, primarily `scripts/sync-host-ai-cli-versions`.
The current implementation installs npm CLIs into the live prefix before downloading Grok.
A later failure can leave only some tools updated. The real wrappers execute from that prefix.

Required behavior:

1. On successful edge synchronization, every requested supported CLI is executable and reports the
   requested version. A package.json version alone is insufficient. Prefix paths may contain spaces.
2. If installation, download, or executable/version verification fails, exit nonzero and preserve
   the previously usable installation's files, permissions and symlinks. No partial successful publication.
3. After SIGTERM or SIGKILL during preparation, a fresh synchronization can succeed once the old
   execution group has stopped. Preserve the usable installation during interruption. Do not assume
   a process survives container restart or require deletion of user-owned files to recover.
4. Concurrent synchronizations for one prefix must not execute competing installers. A second caller
   may fail promptly with an actionable diagnostic or wait within a finite bound. Successful updates
   publish a complete requested set; retrying a later manifest must converge to that manifest.
5. Preserve existing stable/edge/legacy-switch behavior, invalid-version rejection, synchronization
   opt-out, no installation when versions already match, and preservation of unspecified tools and
   unrelated prefix files. Continue accepting the existing environment-variable interfaces.
6. Existing physical-directory installations must remain usable through the change. Preserve normal
   wrapper permissions, authentication mounts and host configuration. Do not add services or dependencies.
7. Add meaningful regression coverage and document failure/retry behavior. Run the applicable repository
   checks, including `scripts/test-devcontainer-ai-cli-sync.sh` and `scripts/test-devcontainer-ai-cli-wrappers.sh`.
   If stronger executable verification requires more realistic fake installers, update those fixtures;
   retain their existing policy assertions. Apply AGENTS.md checks for any additional changed scope.

The implementation architecture is your choice. Helpers under scripts are permitted. Do not change
provider/model choices, pinned versions, ordinary sandbox policy, or container privileges for this task.
Do not modify this study's grading code, initiate model calls, publish externally, or use extra agents.
All public checks and their selection instructions are available to both conditions. You may inspect,
run, repeat and act on them yourself before submitting. Hidden evaluation happens after both developers stop.
