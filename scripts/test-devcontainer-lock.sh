#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"
config="$repo_root/.devcontainer/devcontainer.json"
lock="$repo_root/.devcontainer/devcontainer-lock.json"

usage() {
  echo "usage: $0 [--build]" >&2
}

build=0
case "${1:-}" in
  "") ;;
  --build) build=1 ;;
  -h|--help) usage; exit 0 ;;
  *) usage; exit 2 ;;
esac

PYTHONDONTWRITEBYTECODE=1 python3 "$script_dir/validate-devcontainer-lock.py" \
  --config "$config" --lock "$lock"

if [[ $build -eq 0 ]]; then
  exit 0
fi

image_name="${DEVCONTAINER_FROZEN_IMAGE:-devcontainer-frozen-smoke:latest}"
cli_version="${DEVCONTAINER_CLI_VERSION:-0.88.0}"

if [[ -n "${DEVCONTAINER_CLI_BIN:-}" ]]; then
  cli=("$DEVCONTAINER_CLI_BIN")
elif command -v devcontainer >/dev/null 2>&1; then
  cli=(devcontainer)
else
  command -v npx >/dev/null 2>&1 || {
    echo "error: devcontainer CLI is unavailable; install it or provide DEVCONTAINER_CLI_BIN" >&2
    exit 127
  }
  cli=(npx --yes "@devcontainers/cli@${cli_version}")
fi

"${cli[@]}" build \
  --workspace-folder "$repo_root" \
  --config "$config" \
  --frozen-lockfile \
  --image-name "$image_name"

echo "ok - frozen Dev Container build: $image_name"

if docker inspect "$image_name" --format '{{range .Config.Env}}{{println .}}{{end}}' \
  | grep -Eq '^(OPENAI_API_KEY|SAKANA_API_KEY|GEMINI_API_KEY|ANTHROPIC_API_KEY|XAI_API_KEY)='; then
  echo "error: API key variables must not be baked into the stable image ENV" >&2
  exit 1
fi
echo "ok - stable image ENV contains no API key variables"

docker run --rm --network none "$image_name" bash -lc \
  'test ! -e /usr/bin/bwrap; test ! -e /usr/local/bin/bwrap; test -x /usr/local/lib/provider-sandbox/bwrap; /usr/local/lib/provider-sandbox/bwrap --version >/dev/null; command -v socat >/dev/null; socat -V >/dev/null'
echo "ok - provider sandbox runtime: bubblewrap + socat"

if [[ "${DEVCONTAINER_FROZEN_RUN_SMOKE:-1}" == "1" ]]; then
  # Feature entrypoints are runtime metadata and are not written into the image
  # Config by `devcontainer build`, so invoke docker-init explicitly here.
  docker run --rm --privileged \
    -v "$repo_root:/workspace:ro" \
    "$image_name" \
    /usr/local/share/docker-init.sh bash -lc \
      'set -e; agentctl doctor --json --workspace /workspace >/tmp/agentctl-doctor.json; jq -e '\''.ok == true and (.checks | map(select(.id == "runtime.docker"))[0].status == "pass")'\'' /tmp/agentctl-doctor.json >/dev/null'
  echo "ok - frozen Dev Container start and agentctl doctor"
fi
