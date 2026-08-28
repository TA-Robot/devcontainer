#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
dockerfile="$repo_root/.devcontainer/Dockerfile"
shim="$repo_root/scripts/devcontainer-report-agent-collaboration-evidence"

python3 - "$dockerfile" "$shim" <<'PY'
from pathlib import Path
import sys

dockerfile = Path(sys.argv[1]).read_text(encoding="utf-8")
shim = Path(sys.argv[2]).read_text(encoding="utf-8")
required = (
    "COPY scripts/devcontainer-report-agent-collaboration-evidence",
    "/usr/local/bin/report-agent-collaboration-evidence",
    "scripts/report-agent-collaboration-evidence",
    "scripts/collaboration_evidence.py",
    "/usr/local/lib/mira-collaboration-evidence/",
)
missing = [value for value in required if value not in dockerfile]
if missing:
    raise SystemExit(f"Dockerfile collaboration evidence runtime is incomplete: {missing}")
if "PYTHONPATH=\"$runtime_root\"" not in shim:
    raise SystemExit("report shim must use only the root-owned runtime module path")
if "exec /usr/bin/python3 \"$entrypoint\" \"$@\"" not in shim:
    raise SystemExit("report shim does not exec the fixed runtime entrypoint")
PY

PYTHONDONTWRITEBYTECODE=1 python3 "$repo_root/scripts/test-collaboration-evidence.py"
echo "ok - collaboration evidence report runtime and Dockerfile COPY surface"
