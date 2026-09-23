# Rebuild only after verifying both local tags against image.json source IDs.
FROM devcontainer-collaboration-evidence:20260907 AS tools
FROM lifecycle-selection-actor:20260907
COPY --from=tools /opt/devcontainer-ai-cli/lib/node_modules/@openai/codex/node_modules/@openai/codex-linux-x64/vendor/x86_64-unknown-linux-musl/bin/codex-code-mode-host /usr/local/bin/codex-code-mode-host
COPY --from=tools /opt/devcontainer-ai-cli/lib/node_modules/@openai/codex/node_modules/@openai/codex-linux-x64/vendor/x86_64-unknown-linux-musl/codex-resources/bwrap /usr/local/bin/codex-resources/bwrap
RUN chmod 0555 /usr/local/bin/codex-code-mode-host
