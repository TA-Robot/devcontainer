# Stable and edge toolchain policy

## Stable is the default

The devcontainer image is the stable release unit. Its base image digest, Dev
Container Features, Node version, global npm tools, and AI CLIs are pinned in the
repository. Opening or restarting a stable container performs no CLI version
probe on the host and no package install. The managed Grok wrapper also passes
its supported no-auto-update flag so the binary cannot silently leave the
selected channel.

Current direct pins:

| Component | Version/source |
|---|---|
| Ubuntu | `22.04` image digest in `Dockerfile` |
| Python / TOML validation | Ubuntu Python 3.10 + `python3-tomli`; stdlib `tomllib` on Python >= 3.11 |
| Provider sandbox helpers | Ubuntu `bubblewrap` and `socat` packages from the pinned base distribution |
| Node | `22.22.3` plus archive SHA-256 |
| TypeScript | `5.9.3` |
| ts-node | `10.9.2` |
| ESLint | `10.8.1` |
| Prettier | `3.9.6` |
| Moby engine/CLI | `29.7.2` Feature option |
| Docker Buildx | `0.36.1` Feature option |
| Docker Compose | `2.40.3` plus binary SHA-256 |
| GitHub CLI | `2.97.0` Feature option |
| Codex CLI | `0.153.0` |
| Gemini CLI | `0.45.2` |
| Claude Code | `2.1.220` |
| Grok Build | `1.0.3` official Linux x86_64 binary, SHA-256 `2a7d46dea3fbed067e4072258b835d401e017d6848dc996279f0fb3d668a0961` |
| Dev Container CLI shipped in image and used by frozen smoke | `0.88.0` |

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

## Edge is explicit

Set the following on the host before opening the devcontainer:

```bash
export DEVCONTAINER_AI_CLI_CHANNEL=edge
```

The host initializer then records supported CLI version numbers (never package
directories or credentials). At container start, mismatched npm-based CLIs are
installed and the matching versioned Grok binary is downloaded into
`/opt/devcontainer-ai-cli` for the container OS/CPU.

`DEVCONTAINER_AI_CLI_SYNC=1` remains a migration-compatible spelling for edge.
`DEVCONTAINER_AI_CLI_SYNC=0` disables host probing/synchronization. New automation
should use `DEVCONTAINER_AI_CLI_CHANNEL`.

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
