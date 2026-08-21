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
| Node | `22.22.3` plus archive SHA-256 |
| TypeScript | `5.9.3` |
| ts-node | `10.9.2` |
| ESLint | `10.8.1` |
| Prettier | `3.9.6` |
| Moby engine/CLI | `29.7.2` Feature option |
| Docker Buildx | `0.36.1` Feature option |
| Docker Compose | `2.40.3` plus binary SHA-256 |
| GitHub CLI | `2.97.0` Feature option |
| Codex CLI | `0.146.0` |
| Gemini CLI | `0.45.2` |
| Claude Code | `2.1.220` |
| Grok Build | `1.0.3` official Linux x86_64 binary, SHA-256 `2a7d46dea3fbed067e4072258b835d401e017d6848dc996279f0fb3d668a0961` |
| Dev Container CLI used by frozen smoke | `0.88.0` |

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
