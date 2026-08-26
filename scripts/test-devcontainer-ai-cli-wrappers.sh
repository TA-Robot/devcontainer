#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

fail() {
  echo "not ok - $*" >&2
  exit 1
}

make_stub() {
  local path="$1"
  apply_stub="$path"
  printf '#!/usr/bin/env bash\nprintf "PROFILE=%%s\\n" "${AGENTCTL_PERMISSION_PROFILE:-}" >"${CAPTURE_PATH:?}"\nprintf "PATH=%%s\\n" "$PATH" >>"$CAPTURE_PATH"\nprintf "%%s\\n" "$@" >>"$CAPTURE_PATH"\n' >"$apply_stub"
  chmod +x "$apply_stub"
}

count_exact() {
  local file="$1" value="$2"
  grep -Fxc -- "$value" "$file" || true
}

codex_real="$tmp/codex-real"
claude_real="$tmp/claude-real"
grok_real="$tmp/grok-real"
make_stub "$codex_real"
make_stub "$claude_real"
make_stub "$grok_real"

capture="$tmp/capture"
CAPTURE_PATH="$capture" DEVCONTAINER_CODEX_REAL_BIN="$codex_real" \
  "$script_dir/devcontainer-codex" exec safe
[[ "$(count_exact "$capture" '--dangerously-bypass-approvals-and-sandbox')" == "0" ]] \
  || fail "normal codex must not inject the dangerous flag"

CAPTURE_PATH="$capture" DEVCONTAINER_CODEX_REAL_BIN="$codex_real" \
  "$script_dir/devcontainer-codex" --dangerously-bypass-approvals-and-sandbox exec explicit
[[ "$(count_exact "$capture" '--dangerously-bypass-approvals-and-sandbox')" == "1" ]] \
  || fail "explicit Codex dangerous flag must pass through exactly once"

CAPTURE_PATH="$capture" DEVCONTAINER_CODEX_REAL_BIN="$codex_real" \
DEVCONTAINER_CODEX_DANGEROUS_DEFAULT=1 \
  "$script_dir/devcontainer-codex" exec legacy
[[ "$(count_exact "$capture" '--dangerously-bypass-approvals-and-sandbox')" == "1" ]] \
  || fail "legacy Codex opt-in must remain available"

CAPTURE_PATH="$capture" DEVCONTAINER_CODEX_REAL_BIN="$codex_real" \
DEVCONTAINER_CODEX_WRAPPER_BIN="$script_dir/devcontainer-codex" \
  "$script_dir/devcontainer-codex-trusted" exec trusted
[[ "$(count_exact "$capture" '--dangerously-bypass-approvals-and-sandbox')" == "1" ]] \
  || fail "codex-trusted must inject the dangerous flag"
grep -qx 'PROFILE=trusted-fast' "$capture" || fail "codex-trusted must identify the profile"

CAPTURE_PATH="$capture" DEVCONTAINER_CLAUDE_REAL_BIN="$claude_real" \
  "$script_dir/devcontainer-claude" safe
grep -q '^PATH=/usr/local/lib/provider-sandbox:' "$capture" \
  || fail "Claude wrapper must expose only the provider sandbox helper path"
[[ "$(count_exact "$capture" '--dangerously-skip-permissions')" == "0" ]] \
  || fail "normal claude must not inject the dangerous flag"

CAPTURE_PATH="$capture" DEVCONTAINER_CLAUDE_REAL_BIN="$claude_real" \
  "$script_dir/devcontainer-claude" --dangerously-skip-permissions explicit
[[ "$(count_exact "$capture" '--dangerously-skip-permissions')" == "1" ]] \
  || fail "explicit Claude dangerous flag must pass through exactly once"

CAPTURE_PATH="$capture" DEVCONTAINER_CLAUDE_REAL_BIN="$claude_real" \
DEVCONTAINER_CLAUDE_DANGEROUS_DEFAULT=1 \
  "$script_dir/devcontainer-claude" legacy
[[ "$(count_exact "$capture" '--dangerously-skip-permissions')" == "1" ]] \
  || fail "legacy Claude opt-in must remain available"

CAPTURE_PATH="$capture" DEVCONTAINER_CLAUDE_REAL_BIN="$claude_real" \
DEVCONTAINER_CLAUDE_WRAPPER_BIN="$script_dir/devcontainer-claude" \
  "$script_dir/devcontainer-claude-trusted" trusted
[[ "$(count_exact "$capture" '--dangerously-skip-permissions')" == "1" ]] \
  || fail "claude-trusted must inject the dangerous flag"
grep -qx 'PROFILE=trusted-fast' "$capture" || fail "claude-trusted must identify the profile"

CAPTURE_PATH="$capture" DEVCONTAINER_GROK_REAL_BIN="$grok_real" \
  "$script_dir/devcontainer-grok" safe
grep -q '^PATH=/usr/local/lib/provider-sandbox:' "$capture" \
  || fail "Grok wrapper must expose only the provider sandbox helper path"
[[ "$(count_exact "$capture" '--no-auto-update')" == "1" ]] \
  || fail "managed grok must suppress its background self-updater"
[[ "$(count_exact "$capture" 'bypassPermissions')" == "0" ]] \
  || fail "normal grok must not inject bypassPermissions"
[[ "$(count_exact "$capture" 'off')" == "0" ]] \
  || fail "normal grok must not disable the sandbox"

CAPTURE_PATH="$capture" DEVCONTAINER_GROK_REAL_BIN="$grok_real" \
  "$script_dir/devcontainer-grok" --no-auto-update explicit
[[ "$(count_exact "$capture" '--no-auto-update')" == "1" ]] \
  || fail "an explicit Grok updater flag must not be duplicated"

CAPTURE_PATH="$capture" DEVCONTAINER_GROK_REAL_BIN="$grok_real" \
DEVCONTAINER_GROK_DANGEROUS_DEFAULT=1 \
  "$script_dir/devcontainer-grok" legacy
[[ "$(count_exact "$capture" 'bypassPermissions')" == "1" ]] \
  || fail "legacy Grok opt-in must remain available"
[[ "$(count_exact "$capture" 'off')" == "1" ]] \
  || fail "legacy Grok opt-in must disable the sandbox"

CAPTURE_PATH="$capture" DEVCONTAINER_GROK_REAL_BIN="$grok_real" \
DEVCONTAINER_GROK_WRAPPER_BIN="$script_dir/devcontainer-grok" \
  "$script_dir/devcontainer-grok-trusted" trusted
[[ "$(count_exact "$capture" 'bypassPermissions')" == "1" ]] \
  || fail "grok-trusted must inject bypassPermissions"
[[ "$(count_exact "$capture" 'off')" == "1" ]] \
  || fail "grok-trusted must disable the sandbox"
[[ "$(count_exact "$capture" '--no-auto-update')" == "1" ]] \
  || fail "grok-trusted must keep managed update ownership"
grep -qx 'PROFILE=trusted-fast' "$capture" || fail "grok-trusted must identify the profile"

echo "ok - devcontainer AI CLI safe/trusted wrappers"
