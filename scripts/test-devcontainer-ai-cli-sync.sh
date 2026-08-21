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
probe_log="$tmp/probes.log"
mkdir -p "$stub_dir" "$host_home"

cat >"$stub_dir/codex" <<'EOF'
#!/bin/sh
echo codex >>"${PROBE_LOG:?}"
echo "codex-cli 1.2.3"
EOF
cat >"$stub_dir/claude" <<'EOF'
#!/bin/sh
echo claude >>"${PROBE_LOG:?}"
echo "4.5.6 (Claude Code)"
EOF
cat >"$stub_dir/gemini" <<'EOF'
#!/bin/sh
echo gemini >>"${PROBE_LOG:?}"
echo "7.8.9"
EOF
cat >"$stub_dir/grok" <<'EOF'
#!/bin/sh
echo grok >>"${PROBE_LOG:?}"
echo "grok 1.0.3 (fixture) [stable]"
EOF
chmod +x "$stub_dir/codex" "$stub_dir/claude" "$stub_dir/gemini" "$stub_dir/grok"

# Stable is the default and must not execute host CLI probes.
PROBE_LOG="$probe_log" HOME="$host_home" PATH="$stub_dir:/usr/bin:/bin" \
  sh "$host_init" >/dev/null
manifest="$host_home/.cache/devcontainer-ai-cli/versions.env"
[[ ! -s "$probe_log" ]] || fail "stable initialize must not probe host AI CLIs"
[[ "$(wc -l <"$manifest" | tr -d ' ')" == "1" ]] || fail "stable manifest should contain only its header"
[[ "$(cat "$host_home/.claude.json")" == "{}" ]] || fail "Claude state file was not initialized"

# Edge explicitly probes the host and records only version numbers.
: >"$probe_log"
PROBE_LOG="$probe_log" HOME="$host_home" PATH="$stub_dir:/usr/bin:/bin" \
DEVCONTAINER_AI_CLI_CHANNEL=edge sh "$host_init" >/dev/null
grep -qx 'CODEX_CLI_VERSION=1.2.3' "$manifest" || fail "edge host Codex version was not detected"
grep -qx 'CLAUDE_CODE_VERSION=4.5.6' "$manifest" || fail "edge host Claude version was not detected"
grep -qx 'GEMINI_CLI_VERSION=7.8.9' "$manifest" || fail "edge host Gemini version was not detected"
grep -qx 'GROK_CLI_VERSION=1.0.3' "$manifest" || fail "edge host Grok version was not detected"
[[ "$(wc -l <"$probe_log" | tr -d ' ')" == "4" ]] || fail "edge should probe each supported host CLI"

prefix="$tmp/prefix"
npm_log="$tmp/npm.log"
download_log="$tmp/download.log"
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

cat >"$stub_dir/curl" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

url=""
output=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    -o)
      output="$2"
      shift 2
      ;;
    http://*|https://*)
      url="$1"
      shift
      ;;
    *)
      shift
      ;;
  esac
done
[[ -n "$url" && -n "$output" ]]
version="$(sed -nE 's|.*/grok-([0-9]+\.[0-9]+\.[0-9]+)-linux-.*|\1|p' <<<"$url")"
printf '%s\n' "$url" >>"${DOWNLOAD_LOG:?}"
printf '#!/bin/sh\necho "grok %s (fixture) [stable]"\n' "$version" >"$output"
EOF
chmod +x "$stub_dir/curl"

# Even a populated host manifest must not mutate the stable prefix.
NPM_LOG="$npm_log" \
DEVCONTAINER_AI_CLI_VERSION_FILE="$manifest" \
DEVCONTAINER_AI_CLI_PREFIX="$prefix" \
DEVCONTAINER_AI_CLI_NPM_BIN="$stub_dir/npm" \
DEVCONTAINER_AI_CLI_CURL_BIN="$stub_dir/curl" \
DOWNLOAD_LOG="$download_log" \
  "$sync_script" >/dev/null
[[ ! -e "$npm_log" ]] || fail "stable startup must not invoke npm"

NPM_LOG="$npm_log" \
DEVCONTAINER_AI_CLI_CHANNEL=edge \
DEVCONTAINER_AI_CLI_VERSION_FILE="$manifest" \
DEVCONTAINER_AI_CLI_PREFIX="$prefix" \
DEVCONTAINER_AI_CLI_NPM_BIN="$stub_dir/npm" \
DEVCONTAINER_AI_CLI_CURL_BIN="$stub_dir/curl" \
DOWNLOAD_LOG="$download_log" \
  "$sync_script" >/dev/null

grep -q '@openai/codex@1.2.3' "$npm_log" || fail "Codex package was not synchronized on edge"
grep -q '@anthropic-ai/claude-code@4.5.6' "$npm_log" || fail "Claude package was not synchronized on edge"
grep -q '@google/gemini-cli@7.8.9' "$npm_log" || fail "Gemini package was not synchronized on edge"
grep -q 'grok-1.0.3-linux-' "$download_log" || fail "Grok binary was not synchronized on edge"
[[ "$($prefix/bin/grok --version)" == "grok 1.0.3 (fixture) [stable]" ]] \
  || fail "Grok edge binary version was not installed"

: >"$npm_log"
: >"$download_log"
NPM_LOG="$npm_log" \
DEVCONTAINER_AI_CLI_CHANNEL=edge \
DEVCONTAINER_AI_CLI_VERSION_FILE="$manifest" \
DEVCONTAINER_AI_CLI_PREFIX="$prefix" \
DEVCONTAINER_AI_CLI_NPM_BIN="$stub_dir/npm" \
DEVCONTAINER_AI_CLI_CURL_BIN="$stub_dir/curl" \
DOWNLOAD_LOG="$download_log" \
  "$sync_script" >/dev/null
[[ ! -s "$npm_log" ]] || fail "matching edge versions should not invoke npm"
[[ ! -s "$download_log" ]] || fail "matching Grok edge version should not download"

# The old explicit enable switch remains an edge opt-in during migration.
rm -rf "$prefix/lib"
: >"$npm_log"
NPM_LOG="$npm_log" \
DEVCONTAINER_AI_CLI_SYNC=1 \
DEVCONTAINER_AI_CLI_VERSION_FILE="$manifest" \
DEVCONTAINER_AI_CLI_PREFIX="$prefix" \
DEVCONTAINER_AI_CLI_NPM_BIN="$stub_dir/npm" \
DEVCONTAINER_AI_CLI_CURL_BIN="$stub_dir/curl" \
DOWNLOAD_LOG="$download_log" \
  "$sync_script" >/dev/null
grep -q '@openai/codex@1.2.3' "$npm_log" || fail "legacy explicit sync enable should select edge"

if DEVCONTAINER_AI_CLI_CHANNEL=invalid "$sync_script" >"$tmp/out" 2>"$tmp/err"; then
  fail "invalid channel should fail"
fi
grep -q 'must be stable or edge' "$tmp/err" || fail "invalid channel failure should be actionable"

echo "ok - devcontainer stable/edge AI CLI version policy"
