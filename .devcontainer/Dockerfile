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

# ロケール設定
RUN locale-gen en_US.UTF-8

# Node.js 22.x インストール
ENV NODE_VERSION=22.22.3
ARG NODE_LINUX_X64_SHA256=2e5d13569282d016861fae7c8f935e741693c269101a5bebcf761a5376d1f99f
ARG CODEX_CLI_VERSION=0.138.0
ARG GEMINI_CLI_VERSION=0.45.2
ARG CLAUDE_CODE_VERSION=2.1.170
RUN curl -fsSL "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-x64.tar.xz" -o /tmp/node.tar.xz \
    && echo "${NODE_LINUX_X64_SHA256}  /tmp/node.tar.xz" | sha256sum -c - \
    && tar -xJf /tmp/node.tar.xz -C /usr/local --strip-components=1 \
    && rm /tmp/node.tar.xz \
    && ln -sf /usr/local/bin/node /usr/bin/node \
    && ln -sf /usr/local/bin/npm /usr/bin/npm \
    && npm cache clean --force

# 開発用グローバルパッケージ（必要に応じて追加）
RUN npm install -g \
    typescript \
    ts-node \
    eslint \
    prettier \
    @openai/codex@${CODEX_CLI_VERSION} \
    @google/gemini-cli@${GEMINI_CLI_VERSION} \
    @anthropic-ai/claude-code@${CLAUDE_CODE_VERSION} \
    && npm cache clean --force

# Codex セカンドエージェント用ラッパー（セッションID自動保持）
COPY scripts/codex-second-agent /usr/local/bin/codex-second-agent
COPY scripts/codex-second-agent-filter.py /usr/local/lib/codex-second-agent/filter.py
COPY scripts/devcontainer-sync-host-auth /usr/local/bin/devcontainer-sync-host-auth
RUN chmod +x /usr/local/bin/codex-second-agent /usr/local/bin/devcontainer-sync-host-auth

# 開発ユーザー作成
ARG USERNAME=devuser
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME -s /bin/bash \
    && echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# Codex/Gemini用エイリアス設定
USER $USERNAME
RUN echo '# Codex CLI aliases' >> ~/.bashrc \
    && echo 'alias codex-auto="codex --dangerously-bypass-approvals-and-sandbox"' >> ~/.bashrc \
    && echo 'alias codex-full="codex --full-auto"' >> ~/.bashrc \
    && echo '# Claude Code alias' >> ~/.bashrc \
    && echo 'alias claude-yolo="claude --dangerously-skip-permissions"' >> ~/.bashrc

# 作業ディレクトリ設定
WORKDIR /workspace

# デフォルトユーザー
USER $USERNAME

# デフォルトシェル
CMD ["bash"]
