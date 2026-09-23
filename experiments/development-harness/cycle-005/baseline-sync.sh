#!/usr/bin/env bash
set -euo pipefail

sync_switch="${DEVCONTAINER_AI_CLI_SYNC:-}"
channel="${DEVCONTAINER_AI_CLI_CHANNEL:-stable}"

if [[ "$sync_switch" == "0" ]]; then
  echo "devcontainer: host AI CLI version sync is disabled"
  exit 0
fi

# DEVCONTAINER_AI_CLI_SYNC=1 was the old public switch. Keep it as an explicit
# edge opt-in during migration, while an unset value now means stable.
if [[ "$sync_switch" == "1" ]]; then
  channel="edge"
fi

case "$channel" in
  stable)
    echo "devcontainer: stable AI CLI channel; keeping image-pinned versions"
    exit 0
    ;;
  edge)
    ;;
  *)
    echo "error: DEVCONTAINER_AI_CLI_CHANNEL must be stable or edge (got: $channel)" >&2
    exit 2
    ;;
esac

version_file="${DEVCONTAINER_AI_CLI_VERSION_FILE:-/opt/devcontainer-host-ai-cli/versions.env}"
install_prefix="${DEVCONTAINER_AI_CLI_PREFIX:-/opt/devcontainer-ai-cli}"
npm_bin="${DEVCONTAINER_AI_CLI_NPM_BIN:-npm}"

if [[ ! -f "$version_file" ]]; then
  echo "devcontainer: edge channel host manifest not found; keeping image versions"
  exit 0
fi

declare -A desired_versions=()
while IFS='=' read -r key value; do
  case "$key" in
    CODEX_CLI_VERSION|CLAUDE_CODE_VERSION|GEMINI_CLI_VERSION|GROK_CLI_VERSION)
      if [[ ! "$value" =~ ^[0-9]+\.[0-9]+\.[0-9]+([-+][0-9A-Za-z.-]+)?$ ]]; then
        echo "error: invalid $key in $version_file: $value" >&2
        exit 1
      fi
      desired_versions["$key"]="$value"
      ;;
  esac
done <"$version_file"

if [[ ${#desired_versions[@]} -eq 0 ]]; then
  echo "devcontainer: host has no supported AI CLI version to sync; keeping image versions"
  exit 0
fi

mkdir -p "$install_prefix" "$install_prefix/bin"

read_installed_version() {
  local package_name="$1"
  local package_json="$install_prefix/lib/node_modules/$package_name/package.json"

  if [[ -f "$package_json" ]]; then
    node -e 'process.stdout.write(require(process.argv[1]).version || "")' "$package_json"
  fi
}

packages=(
  "CODEX_CLI_VERSION|@openai/codex|codex"
  "CLAUDE_CODE_VERSION|@anthropic-ai/claude-code|claude"
  "GEMINI_CLI_VERSION|@google/gemini-cli|gemini"
)

install_specs=()
for package_entry in "${packages[@]}"; do
  IFS='|' read -r version_key package_name command_name <<<"$package_entry"
  desired_version="${desired_versions[$version_key]:-}"
  [[ -n "$desired_version" ]] || continue

  installed_version="$(read_installed_version "$package_name")"
  if [[ "$installed_version" == "$desired_version" ]]; then
    printf 'devcontainer: %s %s already matches the host\n' "$command_name" "$installed_version"
  else
    printf 'devcontainer: syncing %s %s -> %s\n' \
      "$command_name" "${installed_version:-not-installed}" "$desired_version"
    install_specs+=("${package_name}@${desired_version}")
  fi
done

if [[ ${#install_specs[@]} -gt 0 ]]; then
  "$npm_bin" install --global --prefix "$install_prefix" --no-audit --no-fund "${install_specs[@]}"
fi

for package_entry in "${packages[@]}"; do
  IFS='|' read -r version_key package_name command_name <<<"$package_entry"
  desired_version="${desired_versions[$version_key]:-}"
  [[ -n "$desired_version" ]] || continue

  installed_version="$(read_installed_version "$package_name")"
  if [[ "$installed_version" != "$desired_version" ]]; then
    echo "error: $command_name version is ${installed_version:-missing}; expected $desired_version" >&2
    exit 1
  fi
done

read_grok_version() {
  local grok_bin="$install_prefix/bin/grok"

  if [[ -x "$grok_bin" ]]; then
    "$grok_bin" --version 2>/dev/null \
      | sed -nE 's/^[^0-9]*([0-9]+\.[0-9]+\.[0-9]+([-+][0-9A-Za-z.-]+)?).*$/\1/p' \
      | sed -n '1p'
  fi
}

desired_grok_version="${desired_versions[GROK_CLI_VERSION]:-}"
if [[ -n "$desired_grok_version" ]]; then
  installed_grok_version="$(read_grok_version)"
  if [[ "$installed_grok_version" == "$desired_grok_version" ]]; then
    printf 'devcontainer: grok %s already matches the host\n' "$installed_grok_version"
  else
    case "$(uname -m)" in
      x86_64|amd64) grok_arch="x86_64" ;;
      aarch64|arm64) grok_arch="aarch64" ;;
      *)
        echo "error: unsupported architecture for Grok edge sync: $(uname -m)" >&2
        exit 1
        ;;
    esac
    curl_bin="${DEVCONTAINER_AI_CLI_CURL_BIN:-curl}"
    command -v "$curl_bin" >/dev/null 2>&1 || {
      echo "error: curl is required to synchronize Grok on the edge channel" >&2
      exit 127
    }
    grok_download_base="${DEVCONTAINER_GROK_DOWNLOAD_BASE:-https://x.ai/cli}"
    grok_url="${grok_download_base}/grok-${desired_grok_version}-linux-${grok_arch}"
    grok_tmp="$install_prefix/bin/.grok.${desired_grok_version}.$$"
    trap 'rm -f "$grok_tmp"' EXIT HUP INT TERM
    printf 'devcontainer: syncing grok %s -> %s\n' \
      "${installed_grok_version:-not-installed}" "$desired_grok_version"
    "$curl_bin" -fsSL "$grok_url" -o "$grok_tmp"
    chmod 0755 "$grok_tmp"
    downloaded_grok_version="$($grok_tmp --no-auto-update --version 2>/dev/null \
      | sed -nE 's/^[^0-9]*([0-9]+\.[0-9]+\.[0-9]+([-+][0-9A-Za-z.-]+)?).*$/\1/p' \
      | sed -n '1p')"
    if [[ "$downloaded_grok_version" != "$desired_grok_version" ]]; then
      echo "error: downloaded grok version is ${downloaded_grok_version:-missing}; expected $desired_grok_version" >&2
      exit 1
    fi
    mv "$grok_tmp" "$install_prefix/bin/grok"
    trap - EXIT HUP INT TERM
  fi
fi

echo "devcontainer: host AI CLI versions synchronized"
