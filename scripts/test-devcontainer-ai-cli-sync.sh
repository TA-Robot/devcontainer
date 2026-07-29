#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"
sync_script="$repo_root/scripts/sync-host-ai-cli-versions"
host_init="$repo_root/.devcontainer/initialize-host.sh"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

fail() {
  echo "not ok - $*" >&2
  exit 1
}

stub_dir="$tmp/stubs"
host_home="$tmp/home"
mkdir -p "$stub_dir" "$host_home"

cat >"$stub_dir/codex" <<'EOF'
#!/bin/sh
echo "codex-cli 1.2.3"
EOF
cat >"$stub_dir/claude" <<'EOF'
#!/bin/sh
echo "4.5.6 (Claude Code)"
EOF
cat >"$stub_dir/gemini" <<'EOF'
#!/bin/sh
echo "7.8.9"
EOF
chmod +x "$stub_dir/codex" "$stub_dir/claude" "$stub_dir/gemini"

HOME="$host_home" PATH="$stub_dir:/usr/bin:/bin" sh "$host_init" >/dev/null
manifest="$host_home/.cache/devcontainer-ai-cli/versions.env"

grep -qx 'CODEX_CLI_VERSION=1.2.3' "$manifest" || fail "host Codex version was not detected"
grep -qx 'CLAUDE_CODE_VERSION=4.5.6' "$manifest" || fail "host Claude version was not detected"
grep -qx 'GEMINI_CLI_VERSION=7.8.9' "$manifest" || fail "host Gemini version was not detected"
[[ "$(cat "$host_home/.claude.json")" == "{}" ]] || fail "Claude state file was not initialized"

prefix="$tmp/prefix"
npm_log="$tmp/npm.log"
mkdir -p "$prefix"

cat >"$stub_dir/npm" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

printf '%s\n' "$*" >>"${NPM_LOG:?}"
prefix=""
specs=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --prefix)
      prefix="$2"
      shift 2
      ;;
    @*)
      specs+=("$1")
      shift
      ;;
    *)
      shift
      ;;
  esac
done

for spec in "${specs[@]}"; do
  package_name="${spec%@*}"
  version="${spec##*@}"
  package_dir="$prefix/lib/node_modules/$package_name"
  mkdir -p "$package_dir"
  printf '{"version":"%s"}\n' "$version" >"$package_dir/package.json"
done
EOF
chmod +x "$stub_dir/npm"

NPM_LOG="$npm_log" \
DEVCONTAINER_AI_CLI_VERSION_FILE="$manifest" \
DEVCONTAINER_AI_CLI_PREFIX="$prefix" \
DEVCONTAINER_AI_CLI_NPM_BIN="$stub_dir/npm" \
  "$sync_script" >/dev/null

grep -q '@openai/codex@1.2.3' "$npm_log" || fail "Codex package was not synchronized"
grep -q '@anthropic-ai/claude-code@4.5.6' "$npm_log" || fail "Claude package was not synchronized"
grep -q '@google/gemini-cli@7.8.9' "$npm_log" || fail "Gemini package was not synchronized"

: >"$npm_log"
NPM_LOG="$npm_log" \
DEVCONTAINER_AI_CLI_VERSION_FILE="$manifest" \
DEVCONTAINER_AI_CLI_PREFIX="$prefix" \
DEVCONTAINER_AI_CLI_NPM_BIN="$stub_dir/npm" \
  "$sync_script" >/dev/null

[[ ! -s "$npm_log" ]] || fail "matching versions should not invoke npm"

echo "ok - devcontainer host AI CLI version sync"
