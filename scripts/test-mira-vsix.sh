#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"
temporary_dir="$(mktemp -d)"
trap 'rm -rf -- "$temporary_dir"' EXIT HUP INT TERM
vsix_path="$temporary_dir/mira.vsix"

"$script_dir/build-mira-vsix" "$vsix_path" >/dev/null

python3 - "$vsix_path" <<'PY'
import json
import sys
import zipfile

path = sys.argv[1]
with zipfile.ZipFile(path) as archive:
    names = set(archive.namelist())
    required = {
        "[Content_Types].xml",
        "extension.vsixmanifest",
        "extension/package.json",
        "extension/src/extension.js",
        "extension/src/game.js",
        "extension/src/state.js",
        "extension/src/world.js",
        "extension/src/world-view.js",
        "extension/media/mira-icons.woff",
        "extension/media/mira-panel.svg",
        "extension/media/world.css",
        "extension/media/world-runtime.js",
        "extension/assets/manifest.json",
        "extension/assets/sprites/core-motion/idle-01.png",
        "extension/assets/sprites/work-actions/typing-04.png",
        "extension/assets/worlds/workshop.png",
    }
    missing = required - names
    if missing:
        raise SystemExit(f"missing VSIX entries: {sorted(missing)}")
    package = json.loads(archive.read("extension/package.json"))
    manifest = json.loads(archive.read("extension/assets/manifest.json"))
    if package["publisher"] != "asakura" or package["name"] != "mira-companion":
        raise SystemExit("unexpected extension identity")
    if package["version"] != "0.5.0":
        raise SystemExit(f"unexpected extension version: {package['version']}")
    contributes = package.get("contributes", {})
    containers = contributes.get("viewsContainers", {})
    if "activitybar" in containers:
        raise SystemExit("Mira must not reserve an Activity Bar view")
    if set(containers) != {"panel"}:
        raise SystemExit(f"Mira must contribute only a bottom panel container: {containers}")
    panel = containers["panel"]
    if len(panel) != 1 or panel[0].get("id") != "miraCompanion.worldContainer":
        raise SystemExit(f"unexpected Mira panel container: {panel}")
    views = contributes.get("views", {}).get("miraCompanion.worldContainer", [])
    if len(views) != 1 or views[0].get("id") != "miraCompanion.world":
        raise SystemExit(f"expected one Mira World view: {views}")
    if views[0].get("type") != "webview":
        raise SystemExit("Mira World must be a webview view")
    command_ids = {
        command.get("command") for command in contributes.get("commands", [])
    }
    if command_ids != {"miraCompanion.openWorld"}:
        raise SystemExit(f"active pet commands must not ship in v2: {sorted(command_ids)}")
    icons = contributes.get("icons", {})
    if len(icons) != 29:
        raise SystemExit(f"expected 29 micro-animation glyphs, found {len(icons)}")
    if not archive.read("extension/media/mira-icons.woff"):
        raise SystemExit("Mira icon font is empty")
    if manifest["frameCount"] != 80:
        raise SystemExit("unexpected Mira frame count")
    packaged_pngs = [name for name in names if name.startswith("extension/assets/sprites/") and name.endswith(".png")]
    if len(packaged_pngs) != 80:
        raise SystemExit(f"expected 80 runtime PNGs, found {len(packaged_pngs)}")
    if "extension/assets/worlds/workshop-source.png" in names:
        raise SystemExit("image-generation source must not bloat the runtime VSIX")
    world = manifest.get("worlds", {}).get("workshop", {})
    if (world.get("width"), world.get("height")) != (1536, 192):
        raise SystemExit(f"unexpected Mira World dimensions: {world}")
    runtime = archive.read("extension/media/world-runtime.js").decode("utf-8")
    for required_token in ("providerCounts", "companionDestinations", "dataset.provider"):
        if required_token not in runtime:
            raise SystemExit(f"provider-aware world runtime is missing {required_token}")
print("Mira VSIX OK: provider-aware bottom world, one tiny status toggle, 80 sprites, and no active pet commands")
PY

python3 - "$repo_root/.devcontainer/devcontainer.json" "$script_dir/devcontainer-post-start" <<'PY'
from pathlib import Path
import sys

config = Path(sys.argv[1]).read_text(encoding="utf-8")
post_start = Path(sys.argv[2]).read_text(encoding="utf-8")

required_attach = '"postAttachCommand": "bash /workspace/scripts/devcontainer-post-attach"'
if required_attach not in config:
    raise SystemExit("Mira VSIX must be installed from postAttachCommand")
if "install-mira-vscode-extension" in post_start:
    raise SystemExit("postStartCommand must not race the remote editor CLI")
print("Mira lifecycle OK: CLI sync on start, VSIX install after editor attach")
PY

if ! MIRA_COMPANION_ATTACH_MODE=headless \
  MIRA_COMPANION_EDITOR_CLI=mira-editor-cli-that-does-not-exist \
  "$script_dir/devcontainer-post-attach" >/dev/null 2>&1; then
  echo "Mira post-attach rejected a valid headless runtime" >&2
  exit 1
fi

if MIRA_COMPANION_ATTACH_MODE=editor \
  MIRA_COMPANION_EDITOR_CLI=mira-editor-cli-that-does-not-exist \
  MIRA_COMPANION_EDITOR_CLI_WAIT_SECONDS=0 \
  "$script_dir/devcontainer-post-attach" >/dev/null 2>&1; then
  echo "Mira post-attach accepted a missing CLI during editor attach" >&2
  exit 1
fi

if MIRA_COMPANION_EDITOR_CLI=mira-editor-cli-that-does-not-exist \
  MIRA_COMPANION_REQUIRE_EDITOR_CLI=1 \
  MIRA_COMPANION_EDITOR_CLI_WAIT_SECONDS=0 \
  "$script_dir/install-mira-vscode-extension" >/dev/null 2>&1; then
  echo "Mira installer unexpectedly accepted a missing required editor CLI" >&2
  exit 1
fi

mock_editor_cli="$temporary_dir/mira-editor-cli"
mock_editor_state="$temporary_dir/mira-editor-cli.state"
cat >"$mock_editor_cli" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" == "--list-extensions" ]]; then
  if [[ -f "$MIRA_TEST_EDITOR_STATE" ]]; then
    echo "asakura.mira-companion@0.5.0"
  fi
  exit 0
fi
if [[ "${1:-}" == "--install-extension" ]]; then
  [[ -f "${2:-}" ]]
  : >"$MIRA_TEST_EDITOR_STATE"
  exit 0
fi
echo "unexpected mock editor arguments: $*" >&2
exit 2
SH
chmod +x "$mock_editor_cli"

installer_output="$(
  MIRA_COMPANION_EDITOR_CLI="$mock_editor_cli" \
    MIRA_COMPANION_REQUIRE_EDITOR_CLI=1 \
    MIRA_COMPANION_EDITOR_CLI_WAIT_SECONDS=0 \
    MIRA_TEST_EDITOR_STATE="$mock_editor_state" \
    "$script_dir/install-mira-vscode-extension"
)"
if [[ "$installer_output" != *"mira-companion: installed asakura.mira-companion@0.5.0 with $mock_editor_cli"* ]]; then
  echo "Mira installer did not exercise the detected editor CLI" >&2
  exit 1
fi

fallback_home="$temporary_dir/fallback-home"
stale_cli_dir="$temporary_dir/.vscode-server/bin/stale/bin/remote-cli"
fallback_bin="$temporary_dir/fallback-bin"
server_cli="$fallback_home/.vscode-server/bin/current/bin/code-server"
fallback_state="$temporary_dir/fallback-editor.state"
mkdir -p "$stale_cli_dir" "$fallback_bin" "$(dirname -- "$server_cli")"

cat >"$stale_cli_dir/code" <<'SH'
#!/usr/bin/env bash
echo "stale remote IPC" >&2
exit 1
SH
cat >"$fallback_bin/ps" <<'SH'
#!/usr/bin/env bash
exit 0
SH
cat >"$server_cli" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
if [[ "${1:-}" == "--server-data-dir" ]]; then
  [[ -n "${2:-}" ]]
  shift 2
fi
if [[ "${1:-}" == "--list-extensions" ]]; then
  if [[ -f "$MIRA_TEST_EDITOR_STATE" ]]; then
    echo "asakura.mira-companion@0.5.0"
  fi
  exit 0
fi
if [[ "${1:-}" == "--install-extension" ]]; then
  [[ -f "${2:-}" ]]
  : >"$MIRA_TEST_EDITOR_STATE"
  exit 0
fi
echo "unexpected server mock arguments: $*" >&2
exit 2
SH
chmod +x "$stale_cli_dir/code" "$fallback_bin/ps" "$server_cli"

fallback_output="$(
  HOME="$fallback_home" \
    PATH="$stale_cli_dir:$fallback_bin:$PATH" \
    VSCODE_IPC_HOOK_CLI="$temporary_dir/missing.sock" \
    MIRA_COMPANION_FORCE_INSTALL=1 \
    MIRA_COMPANION_REQUIRE_EDITOR_CLI=1 \
    MIRA_COMPANION_EDITOR_CLI_WAIT_SECONDS=0 \
    MIRA_TEST_EDITOR_STATE="$fallback_state" \
    "$script_dir/install-mira-vscode-extension"
)"
if [[ "$fallback_output" != *"with $server_cli"* ]]; then
  echo "Mira installer did not bypass the stale remote IPC CLI" >&2
  exit 1
fi
echo "Mira installer OK: missing CLI failures are visible, stale IPC falls back, and install succeeds"
