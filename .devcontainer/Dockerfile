# Cursor Dev Container用 Dockerfile
FROM ubuntu:22.04@sha256:3ba65aa20f86a0fad9df2b2c259c613df006b2e6d0bfcc8a146afb8c525a9751

# 環境変数設定
ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    SHELL=/bin/bash

# 基本パッケージのインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    apt-transport-https \
    bubblewrap \
    build-essential \
    ca-certificates \
    curl \
    git \
    gnupg \
    jq \
    less \
    locales \
    openssh-client \
    procps \
    python3 \
    python3-pip \
    python3-venv \
    ripgrep \
    sudo \
    unzip \
    vim \
    wget \
    xz-utils \
    zsh \
    && rm -rf /var/lib/apt/lists/*

# Claude Code's fail-closed Linux sandbox uses socat for its network proxy.
# Keep this separate from the base package layer so sandbox-helper updates do
# not invalidate the full developer toolchain package installation.
RUN apt-get update && apt-get install -y --no-install-recommends socat \
    && rm -rf /var/lib/apt/lists/*

# ロケール設定
RUN locale-gen en_US.UTF-8

# Node.js 22.x インストール
ENV NODE_VERSION=22.22.3
ARG NODE_LINUX_X64_SHA256=2e5d13569282d016861fae7c8f935e741693c269101a5bebcf761a5376d1f99f
ARG CODEX_CLI_VERSION=0.146.0
ARG GEMINI_CLI_VERSION=0.45.2
ARG CLAUDE_CODE_VERSION=2.1.220
ARG GROK_CLI_VERSION=1.0.3
ARG GROK_CLI_LINUX_X64_SHA256=2a7d46dea3fbed067e4072258b835d401e017d6848dc996279f0fb3d668a0961
ARG TYPESCRIPT_VERSION=5.9.3
ARG TS_NODE_VERSION=10.9.2
ARG ESLINT_VERSION=10.8.1
ARG PRETTIER_VERSION=3.9.6
ARG DOCKER_COMPOSE_VERSION=2.40.3
ARG DOCKER_COMPOSE_LINUX_X64_SHA256=dba9d98e1ba5bfe11d88c99b9bd32fc4a0624a30fafe68eea34d61a3e42fd372
RUN curl -fsSL "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-x64.tar.xz" -o /tmp/node.tar.xz \
    && echo "${NODE_LINUX_X64_SHA256}  /tmp/node.tar.xz" | sha256sum -c - \
    && tar -xJf /tmp/node.tar.xz -C /usr/local --strip-components=1 \
    && rm /tmp/node.tar.xz \
    && ln -sf /usr/local/bin/node /usr/bin/node \
    && ln -sf /usr/local/bin/npm /usr/bin/npm \
    && npm cache clean --force

# Stable toolchain: global package versions are intentionally exact. Update
# these in a dedicated canary change rather than resolving latest during build.
RUN npm install -g \
    "typescript@${TYPESCRIPT_VERSION}" \
    "ts-node@${TS_NODE_VERSION}" \
    "eslint@${ESLINT_VERSION}" \
    "prettier@${PRETTIER_VERSION}" \
    && npm cache clean --force

# The docker-in-docker Feature only accepts the floating major selector `v2`
# for Compose. Install an exact verified plugin here and tell the Feature not to
# download its own floating copy.
RUN mkdir -p /usr/local/lib/docker/cli-plugins \
    && curl -fsSL \
      "https://github.com/docker/compose/releases/download/v${DOCKER_COMPOSE_VERSION}/docker-compose-linux-x86_64" \
      -o /usr/local/lib/docker/cli-plugins/docker-compose \
    && echo "${DOCKER_COMPOSE_LINUX_X64_SHA256}  /usr/local/lib/docker/cli-plugins/docker-compose" | sha256sum -c - \
    && chmod +x /usr/local/lib/docker/cli-plugins/docker-compose \
    && ln -s /usr/local/lib/docker/cli-plugins/docker-compose /usr/local/bin/docker-compose

# AI CLIs are image-pinned on stable. The optional edge channel may install the
# host's version into this container-native prefix at startup.
ENV DEVCONTAINER_AI_CLI_PREFIX=/opt/devcontainer-ai-cli \
    DEVCONTAINER_AI_CLI_CHANNEL=stable \
    AGENTCTL_STATE_DIR=/var/lib/agentctl \
    DEVCONTAINER_TYPESCRIPT_VERSION=${TYPESCRIPT_VERSION} \
    DEVCONTAINER_TS_NODE_VERSION=${TS_NODE_VERSION} \
    DEVCONTAINER_ESLINT_VERSION=${ESLINT_VERSION} \
    DEVCONTAINER_PRETTIER_VERSION=${PRETTIER_VERSION} \
    DEVCONTAINER_CODEX_CLI_VERSION=${CODEX_CLI_VERSION} \
    DEVCONTAINER_GEMINI_CLI_VERSION=${GEMINI_CLI_VERSION} \
    DEVCONTAINER_CLAUDE_CODE_VERSION=${CLAUDE_CODE_VERSION} \
    DEVCONTAINER_GROK_CLI_VERSION=${GROK_CLI_VERSION} \
    DEVCONTAINER_DOCKER_VERSION=29.7.2 \
    DEVCONTAINER_DOCKER_BUILDX_VERSION=0.36.1 \
    DEVCONTAINER_DOCKER_COMPOSE_VERSION=${DOCKER_COMPOSE_VERSION} \
    DEVCONTAINER_GITHUB_CLI_VERSION=2.97.0
RUN npm install -g --prefix "${DEVCONTAINER_AI_CLI_PREFIX}" \
    @openai/codex@${CODEX_CLI_VERSION} \
    @google/gemini-cli@${GEMINI_CLI_VERSION} \
    @anthropic-ai/claude-code@${CLAUDE_CODE_VERSION} \
    && npm cache clean --force

# Codex 0.146 uses its digest-checked bundled bubblewrap when /usr/bin/bwrap is
# absent. Ubuntu 22.04's older bwrap takes Codex's compatibility path and cannot
# resolve the synthetic codex-linux-sandbox helper under the strict profile.
# Claude and Grok discover the distro helper through their wrapper-scoped PATH.
RUN install -d -m 0755 /usr/local/lib/provider-sandbox \
    && mv /usr/bin/bwrap /usr/local/lib/provider-sandbox/bwrap

# Grok Build is an official native binary rather than an npm runtime dependency.
# Pin both its versioned artifact and digest on the stable channel.
RUN install -d -m 0755 "${DEVCONTAINER_AI_CLI_PREFIX}/bin" \
    && curl -fsSL \
      "https://x.ai/cli/grok-${GROK_CLI_VERSION}-linux-x86_64" \
      -o /tmp/grok \
    && echo "${GROK_CLI_LINUX_X64_SHA256}  /tmp/grok" | sha256sum -c - \
    && install -m 0755 /tmp/grok "${DEVCONTAINER_AI_CLI_PREFIX}/bin/grok" \
    && rm /tmp/grok \
    && "${DEVCONTAINER_AI_CLI_PREFIX}/bin/grok" --no-auto-update --version | grep -F "${GROK_CLI_VERSION}"

# Normal Codex / Claude / Grok commands preserve provider approvals and sandboxing.
# Explicit `*-trusted` commands expose the legacy-equivalent bypass profile.
COPY scripts/devcontainer-codex /usr/local/bin/codex
COPY scripts/devcontainer-claude /usr/local/bin/claude
COPY scripts/devcontainer-grok /usr/local/bin/grok
COPY scripts/devcontainer-codex-trusted /usr/local/bin/codex-trusted
COPY scripts/devcontainer-claude-trusted /usr/local/bin/claude-trusted
COPY scripts/devcontainer-grok-trusted /usr/local/bin/grok-trusted
COPY scripts/agentctl /usr/local/bin/agentctl
COPY scripts/agentctl_jobs.py /usr/local/lib/agentctl/agentctl_jobs.py
COPY scripts/agentctl_supervisor.py /usr/local/lib/agentctl/agentctl_supervisor.py
COPY scripts/agent_contracts.py /usr/local/lib/agentctl/agent_contracts.py
COPY .devcontainer/codex-requirements.toml /etc/codex/requirements.toml
COPY .devcontainer/claude-mira-managed-settings.json /etc/claude-code/managed-settings.d/50-mira-companion.json
COPY .devcontainer/grok-mira-managed-config.toml /etc/grok/managed_config.toml
COPY scripts/mira-codex-hook.py /usr/local/lib/mira-companion/mira-codex-hook.py
RUN chmod +x /usr/local/bin/codex /usr/local/bin/claude /usr/local/bin/grok \
    /usr/local/bin/codex-trusted /usr/local/bin/claude-trusted /usr/local/bin/grok-trusted \
    /usr/local/bin/agentctl \
    /usr/local/lib/mira-companion/mira-codex-hook.py \
    && chmod 0444 /usr/local/lib/agentctl/agentctl_jobs.py /usr/local/lib/agentctl/agentctl_supervisor.py /usr/local/lib/agentctl/agent_contracts.py \
    && chmod 0444 /etc/codex/requirements.toml \
      /etc/claude-code/managed-settings.d/50-mira-companion.json \
      /etc/grok/managed_config.toml \
    && ln -s /usr/local/lib/mira-companion/mira-codex-hook.py /usr/local/bin/mira-codex-hook \
    && ln -s /usr/local/lib/mira-companion/mira-codex-hook.py /usr/local/bin/mira-claude-hook \
    && ln -s /usr/local/lib/mira-companion/mira-codex-hook.py /usr/local/bin/mira-grok-hook \
    && ln -s "${DEVCONTAINER_AI_CLI_PREFIX}/bin/gemini" /usr/local/bin/gemini

# Legacy frozen second-agent wrapper (kept during the parallel migration).
COPY scripts/second-agent /usr/local/bin/second-agent
COPY scripts/codex-second-agent /usr/local/bin/codex-second-agent
COPY scripts/claude-second-agent /usr/local/bin/claude-second-agent
COPY scripts/devcontainer-fugu /usr/local/bin/fugu
COPY scripts/fugu /usr/local/lib/devcontainer/fugu
COPY scripts/codex-second-agent-filter.py /usr/local/lib/second-agent/codex-second-agent-filter.py
COPY scripts/claude-second-agent-filter.py /usr/local/lib/second-agent/claude-second-agent-filter.py
RUN chmod +x /usr/local/bin/second-agent /usr/local/bin/codex-second-agent /usr/local/bin/claude-second-agent /usr/local/bin/fugu /usr/local/lib/devcontainer/fugu

# 開発ユーザー作成
ARG USERNAME=devuser
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME -s /bin/bash \
    && install -d -m 0700 -o $USERNAME -g $USERNAME /var/lib/agentctl \
    && install -d -m 0700 -o $USERNAME -g $USERNAME /var/lib/mira-observations \
    && echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME \
    && chown -R $USERNAME:$USERNAME "${DEVCONTAINER_AI_CLI_PREFIX}"

# AI CLI aliases. `*-auto` / `*-yolo` remain compatibility spellings, while
# new automation should use the explicit `*-trusted` executable names.
USER $USERNAME
RUN mkdir -p ~/.config ~/.codex ~/.claude ~/.grok \
    && echo '# Codex CLI aliases' >> ~/.bashrc \
    && echo 'alias codex-auto="codex-trusted"' >> ~/.bashrc \
    && echo 'alias codex-full="codex --full-auto"' >> ~/.bashrc \
    && echo 'alias codex-ask="codex"' >> ~/.bashrc \
    && echo '# Fugu via Codex CLI' >> ~/.bashrc \
    && echo 'alias fugu-ultra="fugu --model fugu-ultra"' >> ~/.bashrc \
    && echo '# Claude Code alias' >> ~/.bashrc \
    && echo 'alias claude-yolo="claude-trusted"' >> ~/.bashrc \
    && echo 'alias claude-ask="claude"' >> ~/.bashrc \
    && echo '# Grok Build aliases' >> ~/.bashrc \
    && echo 'alias grok-yolo="grok-trusted"' >> ~/.bashrc \
    && echo 'alias grok-ask="grok"' >> ~/.bashrc

# 作業ディレクトリ設定
WORKDIR /workspace

# デフォルトユーザー
USER $USERNAME

# デフォルトシェル
CMD ["bash"]
