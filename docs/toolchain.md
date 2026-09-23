# Stable and edge toolchain policy

## Stable images and local edge startup

The devcontainer image is the stable release unit. Its base image digest, Dev
Container Features, Node version, global npm tools, and AI CLIs are pinned in the
repository. The checked-in Cursor / VS Code launch configuration defaults to
edge and synchronizes host CLI versions. Standalone image runs still default to
stable. Opening or restarting an explicitly stable container performs no CLI version
probe on the host and no package install. The managed Grok wrapper also passes
its supported no-auto-update flag so the binary cannot silently leave the
selected channel.

Current direct pins:

| Component | Version/source |
|---|---|
| Ubuntu | `22.04` image digest in `Dockerfile` |
| Python / TOML validation | Ubuntu Python 3.10 + `python3-tomli`; stdlib `tomllib` on Python >= 3.11 |
| Provider sandbox helpers | Ubuntu `bubblewrap` and `socat` packages from the pinned base distribution |
| Persistent terminal frontend | Ubuntu `byobu` package using the existing `tmux` backend |
| Node | `22.22.3` plus archive SHA-256 |
| TypeScript | `5.9.3` |
| ts-node | `10.9.2` |
| ESLint | `10.8.1` |
| Prettier | `3.9.6` |
| Moby engine/CLI | `29.7.2` Feature option |
| Docker Buildx | `0.36.1` Feature option |
| Docker Compose | `2.40.3` plus binary SHA-256 |
| GitHub CLI | `2.97.0` Feature option |
| Codex CLI | `0.156.0` |
| Gemini CLI | `0.45.2` |
| Claude Code | `2.1.280` |
| Grok Build | `1.0.41` official Linux x86_64 binary, SHA-256 `9ce03ed23e16ea01072b4496263d6213a27899e1e3e107f008d36edf82e70407` |
| OpenCode | `2.0.14` (`@opencode/cli`); OpenCode Go is a separately authenticated provider |
| Dev Container CLI shipped in image and used by frozen smoke | `0.88.0` |

The [2026-09-23 model refresh](agents/model-refresh-2026-09-23.md) records the
CLI compatibility checks and current model entry points: `gpt-6-sol`,
`grok-4.7`, and `claude-opus-5-5`. Native roles continue to inherit their model;
CLI upgrades do not change the model inherited by native roles.
Opus 5.5 requires Claude Code 2.1.280 or later. Edge startup still follows the
host version, so update the host CLI as well when adopting a new stable pin.

The Feature OCI digest alone does not freeze option defaults. In particular,
Docker-in-Docker and GitHub CLI default to `latest`; stable therefore pins engine,
Buildx, and `gh` options explicitly. The Feature only offers floating `v2` for
Compose, so the Dockerfile installs the exact Compose binary with SHA-256 and the
Feature's Compose download is disabled.

Exact direct versions do not by themselves create a cryptographic npm dependency
lock for every transitive package. Grok is the exception here: stable downloads
the versioned official artifact and verifies its recorded digest before install.
Its CLI source is also published in xAI's official
[grok-build repository](https://github.com/xai-org/grok-build). The immutable
image digest produced by CI remains the distribution/rollback unit; adding a
fully locked npm installation is a separate hardening item.

OpenCode is included so OpenCode Go can be selected inside the container. This
adds one pinned npm CLI and its platform binary to the image, plus host mounts for
`~/.config/opencode` and `~/.local/share/opencode`. Go subscription and login stay
with the user; no key enters the image or version manifest. Edge selects the
`opencode-ai` package for host OpenCode 1.x and `@opencode/cli` for 2.x, then
checks the installed executable before publication. Directly mounting a host
binary is unsuitable across host/container OS and CPU differences. To remove
OpenCode, delete its Dockerfile ARG/install/ENV/symlink, the two mounts and host
directory setup, and its sync mapping and tests; rebuilding the previous image
digest is the rollback path. A host CLI installed through npm can be removed
separately with `npm uninstall -g @opencode/cli`.

`bubblewrap` and `socat` are installed because Claude Code's fail-closed Linux
sandbox requires both its filesystem sandbox and network proxy helpers; Grok
custom profiles with read-deny rules also require `bwrap`. Without them, the safe
provider path either refuses to start or cannot enforce the declared boundary.
They add two small OS executables and no extension/runtime API. The alternative
is to use provider bypass modes, which is not acceptable for controlled agent
runs. To remove them, first remove or replace every Claude sandbox and Grok
custom-deny profile, update their safety contracts, then delete the Dockerfile
package entries and rebuild the image; the previous image digest is the rollback
unit.

The Ubuntu 22.04 `bwrap` executable is relocated from `/usr/bin` to
`/usr/local/lib/provider-sandbox` and is added to `PATH` only by the Claude/Grok
wrappers and their isolated study runner. Codex 0.146 otherwise discovers the
distro version, enters an old-bwrap compatibility path, and cannot resolve its
synthetic sandbox helper under the strict duration profile. Keeping the distro
helper outside the global and Codex runner paths makes Codex use its own
digest-checked bundled build, matching the frozen-image behavior. Remove this
split only after a Codex/Ubuntu update passes the no-generation workspace-write,
unrelated-read, and network-denial probe with the system helper.

The `mira` terminal launcher adds Byobu so interactive CLI processes survive an
SSH client disconnect while the container remains running. The existing tmux
package remains the backend; Byobu adds its profile, status UI and launcher
commands. A plain tmux wrapper was possible but would not provide the requested
Byobu interface. To remove this dependency, delete the Byobu install and `mira`
COPY/chmod in the Dockerfile, remove `scripts/mira` and its test, and rebuild the
image. Stopping the container still ends its processes; Byobu is not a restart
checkpoint.

## Selecting the local startup channel

Local editor startup defaults to edge. To keep the pinned image versions instead,
set the following on the host and launch the editor from that environment:

```bash
export DEVCONTAINER_AI_CLI_CHANNEL=stable
```

With edge selected (or the local setting unset), the host initializer records
supported CLI version numbers (never package
directories or credentials). At container start, mismatched npm-based CLIs are
installed and the matching versioned Grok binary is downloaded into
`/opt/devcontainer-ai-cli` for the container OS/CPU.

`DEVCONTAINER_AI_CLI_SYNC=1` remains a migration-compatible spelling for edge.
`DEVCONTAINER_AI_CLI_SYNC=0` disables host probing/synchronization. New automation
should use `DEVCONTAINER_AI_CLI_CHANNEL`.

Edge synchronization prepares changed tools in a separate, clean temporary npm
prefix. It checks each requested executable's exit status and reported version
with `--version` (Grok also receives `--no-auto-update`); package metadata alone
does not count. Each version probe has a 20-second timeout. Matching executables
do not trigger installation or downloads.
This is a per-probe cost cap owned by the toolchain maintainer, intended to avoid
holding update ownership on a hung version command. Recalibrate it with regression
evidence if supported CLI startup behavior changes.

Only after all requested tools pass verification does synchronization publish a
complete executable directory. The existing physical prefix stays in place, so
the container user needs no write access to `/opt` and wrappers keep using
`$DEVCONTAINER_AI_CLI_PREFIX/bin`. New images seed `bin` and `lib` as links to a
stable generation, so the first edge update can atomically replace the `bin`
link on Docker overlayfs. Legacy images with a physical `bin` directory attempt
an atomic Linux `renameat2` exchange; filesystems that reject it leave the old
installation usable and require an image rebuild. Later updates atomically
replace the symlink.
The active npm library lives alongside `bin` inside its `.ai-cli-generation-*`
directory. The top-level `lib` points to the stable generation and is not the
active edge inventory. Unspecified tools and unrelated prefix files are retained.
Publication does not alter wrapper flags, authentication mounts or host settings.

An install, download or executable verification failure exits nonzero and leaves
the previous executable set usable. Fix the reported cause and rerun
`scripts/sync-host-ai-cli-versions` with the same edge environment, or reopen the
container. A kernel lock on the physical prefix excludes concurrent installers,
including callers using a symlink alias. A competing caller fails promptly with
a retry diagnostic. Installer children inherit the lock: after SIGTERM/SIGKILL,
retry once the old execution group has stopped. Container restart releases the
lock too; recovery never requires a surviving coordinator or deleting lock files.
A later manifest is read by a fresh invocation and converges on retry.
Termination after the atomic publication can leave the new complete generation
active even if the caller did not receive the final message. A retry verifies the
requested versions; it does not infer rollback from that missing message.

Failed preparation normally removes its temporary files. Forced termination can
leave unused temporary directories, or an unreferenced generation if interrupted
during the final copy. They cannot become active on retry. Published generations
and the original `bin` are retained so existing processes can still access older
files; updates therefore require additional disk space. Container recreation
reclaims the default prefix's writable layer without a user-maintained recovery
journal. A custom prefix on a persistent external volume is outside that reclaim
behavior; this updater does not garbage-collect its generations.
The sync regression suite includes provider-free failure, interruption,
concurrency, symlink and executable-version checks; run
`scripts/test-devcontainer-ai-cli-sync.sh` and
`scripts/test-devcontainer-ai-cli-wrappers.sh`.

Changing an environment variable in a separate terminal does not update an
already-running editor. Restart the editor with the intended environment and
recreate the container after changing its channel. Returning an edge container
to pinned versions requires recreation from the image; skipping sync alone does
not undo previously installed packages. `initialize-host.sh` and
`devcontainer.json` share the local edge default, while the Dockerfile and the
standalone sync command retain stable as their default.

Edge is a canary surface. It is not reproducible, may require npm registry and
`x.ai` access, and must pass `agentctl doctor --json` before its capabilities are
assumed. Unlike stable, the edge Grok download is version-checked but does not
have a repository-pinned digest.

## Feature lock ownership and provenance

`.devcontainer/devcontainer-lock.json` uses the official Dev Container CLI lock
schema and pins all three configured Features by OCI digest. It first appeared as
an untracked working-tree file, so its original generating command cannot be
recovered from Git history. On 2026-08-12 it was deliberately accepted as the
Phase 1 lock source after verifying exact config-key coverage, digest format, and
resolved/integrity equality.

Repository maintainers own updates. Validate structure without building:

```bash
scripts/test-devcontainer-lock.sh
```

Build through the pinned official CLI and reject any lock mutation:

```bash
scripts/test-devcontainer-lock.sh --build
```

Each frozen build owns a temporary directory under `${TMPDIR:-/tmp}` and removes
it when the CLI exits, including on failure. This prevents concurrent CLI calls
from sharing generated Feature Dockerfiles. Concurrent callers must also select
distinct `DEVCONTAINER_FROZEN_IMAGE` tags.

The build command uses `devcontainer build --frozen-lockfile`; if no global
`devcontainer` command exists, it uses `npx --yes @devcontainers/cli@0.88.0`.
The smoke also rejects API key variables in the built image ENV and starts the
Feature-provided DinD entrypoint before running `agentctl doctor`.

Before invoking or bootstrapping that CLI, the script probes `docker info` in
the calling execution context. A missing/inaccessible daemon or a probe timeout
stops the check with a nonzero exit and an explicit unexecuted-build diagnostic.
The 10-second probe deadline is a local cost cap for detecting an unavailable
daemon, owned by repository maintainers; revisit it only with evidence of a
healthy daemon needing more time. An outer host's successful doctor result does
not establish access from a provider sandbox. The check neither changes sandbox
permissions nor marks a blocked build successful.

The provider-free preflight regressions run with
`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest scripts/test-devcontainer-build-preflight.py`.
They cover an absent, inaccessible and unresponsive daemon, plus propagation of
the real frozen CLI command after a successful probe.

The image includes this already-required CLI at build time. In a fresh image,
`devcontainer --version` must work with networking disabled and match
`DEVCONTAINER_CLI_VERSION`; frozen smoke checks that condition. This removes the
implicit npm installation from normal repository checks. It does **not** make
the frozen build offline: the pinned CLI still retrieves Feature manifests and
blobs from OCI registries. The distinction is visible in the
[CLI's versioned OCI implementation](https://github.com/devcontainers/cli/blob/v0.88.0/src/spec-configuration/containerCollectionsOCI.ts).
Network-denied agent commands may therefore still need a separately authorized
release-check environment. Report that limitation instead of weakening the
provider's sandbox or claiming the build passed.

The dependency adds the official CLI and its npm dependencies to the development
image; it changes neither agentctl nor the editor extension's runtime API.
Alternatives are the existing on-demand npx bootstrap, which fails before the
check when registry access is unavailable, or a custom Feature cache/build
implementation, which adds maintenance and does not solve permission parity.
To remove the bundled CLI, delete its Dockerfile ARG/RUN/ENV block and the
offline availability smoke, update this table, rebuild, and provide the same
pinned CLI externally through `DEVCONTAINER_CLI_BIN` or the documented host
fallback. Its installation layer precedes repository source copies, so editing project
scripts does not reinstall the CLI. No package installation is added to
container startup.

Development-user creation and AI-tool ownership also precede repository source
copies. The control image had a roughly 1.23 GB ownership-change layer after
those copies, so ordinary source edits invalidated it. This ordering change
keeps the same ownership and user behavior while allowing that layer to be
reused. It does not remove the layer or promise a smaller initial image.

## Stable update flow

After CA certificates and the toolchain are installed, the Ubuntu archive URLs
use HTTPS for Feature installation and later package operations. The archive
hosts, suites and APT signature verification are unchanged. This addresses HTTP
retrieval retries observed during cycle-003 release verification; it does not
avoid rebuilding Feature layers after a base-image change. The first bootstrap
APT operation still uses the pinned Ubuntu image's initial sources. No new
dependency is added. Reverting the Dockerfile's archive-transport `RUN` restores
the prior transport; mirror or cache architecture changes remain separate work.

1. Create a dedicated toolchain update change; do not mix it with product code.
2. Update exact Dockerfile pins and, when Features change, run the pinned
   `devcontainer build` once without `--frozen-lockfile` to deliberately refresh
   the lock.
3. Review every version and digest change.
4. Run the structural lock check, frozen build, container hook smoke, and
   `agentctl doctor --json` inside the built image.
5. Run provider contract tests and one small live canary for each updated provider.
6. Promote the image digest only after canaries pass; retain the prior digest for
   rollback.

Normal `codex`, `claude`, and `grok` preserve provider approvals/sandboxing. Use
`codex-trusted`, `claude-trusted`, or `grok-trusted` only for trusted local code
when the speed tradeoff is intentional. The current privileged container and
credential mounts remain outside any strong security boundary in either profile.

## Optional browser tools

Product-experience verification needs a real browser: the target-template skill
`$verify-product-experience` drives the running product, captures screenshots,
and gives the end-user lens observed evidence instead of code-reading guesses.
The Chromium OS libraries are the part a project cannot easily add by itself in
this image, so the base repository offers them as an **opt-in, image-pinned**
layer.

```bash
# host, before starting the editor; then "Dev Containers: Rebuild Container"
export DEVCONTAINER_BROWSER_TOOLS=1
```

- `devcontainer.json` passes `${localEnv:DEVCONTAINER_BROWSER_TOOLS:0}` as a build
  argument. The default `0` leaves the image unchanged and ships no browser.
- `1` installs the exact `PLAYWRIGHT_VERSION` from the Dockerfile into
  `/opt/devcontainer-browser-tools`, plus one headless Chromium shell and its
  apt dependencies through `playwright install --with-deps --only-shell`. The
  build verifies the CLI version. Stable startup performs no download.
- Only `with-browser-tools COMMAND...` sets `PLAYWRIGHT_BROWSERS_PATH`,
  `NODE_PATH`, and `PATH` for one command. No image-wide ENV redirects a
  project's own Playwright dependency, which keeps its default browser cache and
  install behavior. Without the layer the wrapper exits 127 with enablement
  guidance and never downloads anything.
- Impact: a larger image and one more pinned third-party package when enabled.
  The value `0 | 1` is validated at build time.
- Alternatives considered: always installing (penalizes projects without a UI),
  installing at startup (breaks the no-startup-install stable contract), and
  requiring every project to add Playwright (still needs root-installed OS
  libraries, so the wrapper-free path stays available for projects that prefer
  their own dependency).
- Update: bump `PLAYWRIGHT_VERSION` in a dedicated canary change, rebuild with
  `--build-arg DEVCONTAINER_BROWSER_TOOLS=1`, and run
  `scripts/test-devcontainer-browser-tools.sh IMAGE 1`.
- Removal: delete the Dockerfile layer, the `with-browser-tools` wrapper and its
  test, the build argument, and the fallback text in the
  `verify-product-experience` skill. Projects that depend on the wrapper should
  first add Playwright as their own dependency.

## Repository development compatibility

`python3-tomli` supports the native-agent template validator on Ubuntu 22.04's
Python 3.10. Python's standard-library
[`tomllib` starts at 3.11](https://docs.python.org/3/library/tomllib.html);
the [Jammy package](https://packages.ubuntu.com/jammy/python3-tomli) supplies the
compatible reader without startup installs. This adds one development-time OS
package, not an agentctl or extension runtime dependency. It follows the same
distro-package update policy as base Python, with the resulting image digest as
the reproducible distribution unit. Alternatives were upgrading the OS/Python,
repeatedly installing a user package, or maintaining our own TOML parser; each
adds unnecessary work for this compatibility gap. When the stable Python floor
reaches 3.11, remove the package layer and fallback import, then rerun template
validation and frozen-image smoke. An external Python 3.10 virtualenv needs its
own Tomli installation; Python >= 3.11 does not.

When developing this repository, use `scripts/agentctl`: it loads sibling
checkout libraries before the installed bundle. `/usr/local/bin/agentctl`
continues to load its installed bundle. The current working directory must not
choose the implementation. Frozen-image smoke now verifies template validation
and this import boundary against the shipped Python.
