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

# Probe the required daemon from this execution context before an npx bootstrap.
# A host-side doctor result does not establish a sandboxed command's access.
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
import shutil
import subprocess
import sys

if shutil.which("docker") is None:
    sys.exit("error: frozen build requires the Docker CLI in this execution context")
try:
    result = subprocess.run(
        ["docker", "info", "--format", "{{.ServerVersion}}"],
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, timeout=10,
    )
except subprocess.TimeoutExpired:
    sys.exit("error: Docker readiness probe exceeded 10 seconds; frozen build was not run")
if result.returncode:
    if result.stderr.strip():
        print(result.stderr.strip(), file=sys.stderr)
    sys.exit("error: Docker is unavailable in this execution context; frozen build was not run")
PY

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

(
  # The official CLI derives some generated paths from a millisecond clock.
  # Separate build scratch space even when callers already use distinct tags.
  build_scratch="$(mktemp -d "${TMPDIR:-/tmp}/devcontainer-frozen.XXXXXX")"
  trap 'rm -rf -- "$build_scratch"' EXIT
  export TMPDIR="$build_scratch"
  "${cli[@]}" build \
    --workspace-folder "$repo_root" \
    --config "$config" \
    --frozen-lockfile \
    --image-name "$image_name"
)

echo "ok - frozen Dev Container build: $image_name"

if docker inspect "$image_name" --format '{{range .Config.Env}}{{println .}}{{end}}' \
  | grep -Eq '^(OPENAI_API_KEY|SAKANA_API_KEY|GEMINI_API_KEY|ANTHROPIC_API_KEY|XAI_API_KEY)='; then
  echo "error: API key variables must not be baked into the stable image ENV" >&2
  exit 1
fi
echo "ok - stable image ENV contains no API key variables"

docker run --rm --network none "$image_name" bash -lc \
  'grep -Fx "check_for_update_on_startup = false" /etc/codex/config.toml >/dev/null; test "$(stat -c %a /etc/codex/config.toml)" = 444'
echo "ok - centrally pinned Codex disables interactive startup update checks"

docker run --rm --network none "$image_name" bash -lc \
  'test ! -e /usr/bin/bwrap; test ! -e /usr/local/bin/bwrap; test -x /usr/local/lib/provider-sandbox/bwrap; /usr/local/lib/provider-sandbox/bwrap --version >/dev/null; command -v socat >/dev/null; socat -V >/dev/null; command -v tmux >/dev/null; tmux -V >/dev/null'
echo "ok - provider sandbox and durable terminal runtime: bubblewrap + socat + tmux"

docker run --rm --network none "$image_name" bash -lc \
  'test "$(devcontainer --version)" = "$DEVCONTAINER_CLI_VERSION"'
echo "ok - pinned Dev Container CLI is available without npm bootstrap or network"

docker run --rm --network none --read-only --interactive \
  --env PYTHONDONTWRITEBYTECODE=1 --entrypoint python3 "$image_name" - <<'PY'
import json
import os
import runpy

agentctl = runpy.run_path("/usr/local/bin/agentctl")
checks = []
agentctl["provider_capability"](
    checks, name="codex", binary="/usr/local/bin/codex",
    help_commands=[["exec", "--help"]], required=["--json", "--model", "--sandbox"],
    expected_version=os.environ["DEVCONTAINER_CODEX_CLI_VERSION"],
)
assert checks[0]["status"] == "pass", json.dumps(checks)
PY
echo "ok - installed Codex capability probe tolerates read-only PATH-alias warnings"

# Verify development checks on the shipped Python, not only installed runtime.
docker run --rm --network none -v "$repo_root:/workspace:ro" -w /workspace \
  "$image_name" bash -lc \
    'PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate-agent-contracts.py && PYTHONDONTWRITEBYTECODE=1 python3 -m unittest scripts.test-agentctl.AgentctlImportTests'
echo "ok - repository template validation and checkout library selection"

"$script_dir/test-agent-project-container.sh" "$image_name"
"$script_dir/test-agentctl-check-container.sh" "$image_name"

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
