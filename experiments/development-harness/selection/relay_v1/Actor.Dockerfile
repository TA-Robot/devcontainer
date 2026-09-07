# Verify local source-tag IDs against actor-image.json before rebuilding.
FROM devcontainer-collaboration-evidence:20260907 AS tool_source
FROM lifecycle-selection-probe:20260907
COPY --from=tool_source /opt/devcontainer-ai-cli/lib/node_modules/@openai/codex/node_modules/@openai/codex-linux-x64/vendor/x86_64-unknown-linux-musl/bin/codex /usr/local/bin/codex
COPY --from=tool_source /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/ca-certificates.crt
RUN chmod 0555 /usr/local/bin/codex && mkdir /codex && chmod 1777 /codex \
    && codex --version
ENV CODEX_HOME=/codex
WORKDIR /work
