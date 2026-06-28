#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "$script_dir/.." && pwd)"

assert_contains() {
  local haystack="$1"
  local needle="$2"
  local message="$3"
  if [[ "$haystack" != *"$needle"* ]]; then
    printf 'not ok - %s\n' "$message" >&2
    printf 'missing: %s\nin: %s\n' "$needle" "$haystack" >&2
    exit 1
  fi
}

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

stub_dir="$tmp/bin"
mkdir -p "$stub_dir"
cat >"$stub_dir/codex" <<'EOF'
#!/usr/bin/env bash
{
  printf 'SAKANA_API_KEY=%s\n' "${SAKANA_API_KEY:-}"
  printf 'ARGV='
  for arg in "$@"; do
    printf '<%s>' "$arg"
  done
  printf '\n'
} >"${CAPTURE_PATH:?}"
EOF
chmod +x "$stub_dir/codex"

capture="$tmp/capture"

CAPTURE_PATH="$capture" PATH="$stub_dir:$PATH" SAKANA_API_KEY="env-key" \
  "$repo_root/scripts/fugu" exec "hello"
out="$(cat "$capture")"
assert_contains "$out" 'SAKANA_API_KEY=env-key' "uses SAKANA_API_KEY when present"
assert_contains "$out" '<--disable><image_generation>' "disables image_generation"
assert_contains "$out" '<--model><fugu-ultra>' "defaults to fugu-ultra"
assert_contains "$out" '<--config><model_provider="sakana">' "selects sakana provider"
assert_contains "$out" '<exec><hello>' "passes codex args through"

api_key_file="$tmp/fugu-api"
printf ' file-key \n' >"$api_key_file"
CAPTURE_PATH="$capture" PATH="$stub_dir:$PATH" \
  "$repo_root/scripts/fugu" --api-key-file "$api_key_file" --model fugu exec "light"
out="$(cat "$capture")"
assert_contains "$out" 'SAKANA_API_KEY=file-key' "reads API key from --api-key-file"
assert_contains "$out" '<--model><fugu>' "allows model override"
assert_contains "$out" '<exec><light>' "passes args after wrapper options"

printf 'ok - fugu wrapper\n'
