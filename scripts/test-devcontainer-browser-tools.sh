#!/usr/bin/env bash
# Verify the opt-in browser tool wrapper.
#
#   scripts/test-devcontainer-browser-tools.sh              # wrapper contract only
#   scripts/test-devcontainer-browser-tools.sh IMAGE [0|1]  # also inside IMAGE
#
# IMAGE built with DEVCONTAINER_BROWSER_TOOLS=1 must drive a real Chromium;
# a default image must refuse with guidance instead of downloading anything.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
wrapper="$repo_root/scripts/devcontainer-with-browser-tools"
scratch="$(mktemp -d "${TMPDIR:-/tmp}/browser-tools-test.XXXXXX")"
trap 'rm -rf -- "$scratch"' EXIT

fail() { echo "not ok - $*" >&2; exit 1; }

# Missing tools: exit 127 with enablement guidance, never a download attempt.
set +e
output="$(DEVCONTAINER_BROWSER_TOOLS_PREFIX="$scratch/absent" "$wrapper" playwright --version 2>&1)"
status=$?
set -e
[[ $status -eq 127 ]] || fail "missing tools exited $status"
grep -q "DEVCONTAINER_BROWSER_TOOLS=1" <<<"$output" || fail "missing enablement guidance"
echo "ok - missing browser tools fail closed with guidance"

# Installed layout: the environment is scoped to the wrapped command.
prefix="$scratch/prefix"
mkdir -p "$prefix/bin" "$prefix/browsers" "$prefix/lib/node_modules"
printf '#!/bin/sh\necho fake-playwright "$@"\n' >"$prefix/bin/playwright"
chmod 0755 "$prefix/bin/playwright"
output="$(DEVCONTAINER_BROWSER_TOOLS_PREFIX="$prefix" NODE_PATH=/existing "$wrapper" \
  sh -c 'playwright --version; echo "$PLAYWRIGHT_BROWSERS_PATH|$NODE_PATH|$PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD"')"
grep -qx "fake-playwright --version" <<<"$output" || fail "wrapped PATH does not resolve playwright"
grep -qx "$prefix/browsers|$prefix/lib/node_modules:/existing|1" <<<"$output" || fail "unexpected env: $output"
[[ -z "${PLAYWRIGHT_BROWSERS_PATH:-}" ]] || fail "caller environment was modified"
set +e
DEVCONTAINER_BROWSER_TOOLS_PREFIX="$prefix" "$wrapper" >/dev/null 2>&1
status=$?
set -e
[[ $status -eq 2 ]] || fail "missing command exited $status"
echo "ok - wrapper scopes Playwright environment to one command"

image="${1:-}"
[[ -n "$image" ]] || exit 0
expected="${2:-}"
if [[ -z "$expected" ]]; then
  expected="$(docker run --rm "$image" sh -c 'echo "${DEVCONTAINER_BROWSER_TOOLS:-0}"')"
fi

if [[ "$expected" == "0" ]]; then
  docker run --rm --network none "$image" bash -c '
    set -u
    with-browser-tools playwright --version >/tmp/out 2>&1; status=$?
    [[ $status -eq 127 ]] && grep -q DEVCONTAINER_BROWSER_TOOLS=1 /tmp/out
    [[ ! -e /opt/devcontainer-browser-tools ]]
  ' || fail "default image must not ship browser tools"
  echo "ok - default image ships no browser tools and refuses with guidance"
  exit 0
fi

docker run --rm --network none -i -w /tmp "$image" bash -s <<'SH' || fail "browser tools do not drive Chromium in $image"
set -euo pipefail
with-browser-tools playwright --version | grep -F "$DEVCONTAINER_PLAYWRIGHT_VERSION"
cat >/tmp/page.html <<'HTML'
<!doctype html><title>probe</title><button id="go" onclick="document.body.dataset.done='yes'">Go</button>
HTML
cat >/tmp/flow.cjs <<'JS'
const { chromium } = require("playwright");
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
  const errors = [];
  page.on("console", (message) => message.type() === "error" && errors.push(message.text()));
  await page.goto("file:///tmp/page.html");
  await page.getByRole("button", { name: "Go" }).click();
  if ((await page.evaluate(() => document.body.dataset.done)) !== "yes") throw new Error("click failed");
  await page.screenshot({ path: "/tmp/flow.png" });
  await browser.close();
  if (errors.length) throw new Error(errors.join("\n"));
})().catch((error) => { console.error(error); process.exit(1); });
JS
with-browser-tools node /tmp/flow.cjs
with-browser-tools playwright screenshot file:///tmp/page.html /tmp/cli.png >/dev/null
for png in /tmp/flow.png /tmp/cli.png; do
  [[ "$(head -c 8 "$png" | od -An -tx1 | tr -d ' \n')" == "89504e470d0a1a0a" ]]
done
[[ -z "${PLAYWRIGHT_BROWSERS_PATH:-}" ]]
SH
echo "ok - opt-in image drives Chromium offline and captures screenshots"
