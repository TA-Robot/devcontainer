#!/usr/bin/env bash
# Only synthetic test drivers/archived migration fixtures enter via stdin.
# No checkout mount and no current runtime module is supplied by this test.
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"
image="${1:-devcontainer-smoke:latest}"
docker image inspect "$image" >/dev/null
tar -C "$repo_root" -cf - \
  scripts/test-agentctl-jobs.py \
  scripts/fixtures/agentctl-history/baseline-source.tar.gz \
  scripts/fixtures/agentctl-history/reproduce-baseline-upgrade.py \
  scripts/fixtures/agentctl-history/phase-2-source.tar.gz \
  scripts/fixtures/agentctl-history/reproduce-phase2-upgrade.py |
  docker run --rm --network none -i --entrypoint bash -w /tmp \
    -e PYTHONDONTWRITEBYTECODE=1 -e MIRA_COMPANION_ENABLED=0 \
    -e AGENTCTL_TEST_BIN=/usr/local/bin/agentctl \
    -e AGENTCTL_TEST_LIBRARY=/usr/local/lib/agentctl \
    -e AGENTCTL_TEST_TEMPLATE=/usr/local/share/agent-project/template \
    "$image" -c '
      set -euo pipefail
      test "$(id -u)" -ne 0
      test -r /usr/local/share/agentctl/README.md
      fixture=$(mktemp -d /tmp/agentctl-shipped-check.XXXXXX)
      trap '\''rm -rf -- "$fixture"'\'' EXIT
      tar -xf - -C "$fixture"
      cd "$fixture"
      test ! -e scripts/agentctl_jobs.py
      PYTHONPATH=/usr/local/lib/agentctl python3 -c '\''import agentctl_jobs; assert agentctl_jobs.__file__ == "/usr/local/lib/agentctl/agentctl_jobs.py"'\''
      python3 -m unittest scripts/test-agentctl-jobs.py -k test_check
    '
