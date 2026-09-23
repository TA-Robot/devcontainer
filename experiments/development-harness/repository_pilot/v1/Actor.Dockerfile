# Source tag must match the image ID recorded in the preparation manifest.
FROM devcontainer-model-refresh:20260923 AS tools
FROM ghcr.io/scaleapi/swe-bench_pro-v2@sha256:74ef826866ce57312db8311f14ec0c2ce2d03570028b5951653607f0ed72fb79
COPY --from=tools /opt/devcontainer-ai-cli/lib/node_modules/@openai/codex/node_modules/@openai/codex-linux-x64/vendor/x86_64-unknown-linux-musl/bin/ /usr/local/bin/
COPY --from=tools /opt/devcontainer-ai-cli/lib/node_modules/@openai/codex/node_modules/@openai/codex-linux-x64/vendor/x86_64-unknown-linux-musl/codex-resources/bwrap /usr/local/bin/codex-resources/bwrap
COPY --from=tools /opt/devcontainer-ai-cli/lib/node_modules/@openai/codex/node_modules/@openai/codex-linux-x64/vendor/x86_64-unknown-linux-musl/codex-path/rg /usr/local/bin/rg
RUN mkdir /codex /control /observation /sealed && codex --version \
    && chown -R 1000:1000 /app /codex
ENV CODEX_HOME=/codex
WORKDIR /app
USER 1000:1000
