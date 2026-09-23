#!/usr/bin/env bash
# No source checkout mount: verify the image is a complete distribution.
set -euo pipefail
image="${1:-devcontainer-smoke:latest}"
docker run --rm --network none -i -w /tmp "$image" python3 - <<'PY'
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


def run(*args):
    result = subprocess.run(["manage-agent-project", *map(str, args), "--json"],
                            check=True, capture_output=True, text=True, cwd="/")
    return json.loads(result.stdout)


with tempfile.TemporaryDirectory(prefix="agent-project-image-") as directory:
    root = Path(directory)
    target = root / "target"
    target.mkdir()
    (target / "user.txt").write_bytes(b"private user content")
    plan = run("plan", "--target", target)
    assert plan["source"] == "/usr/local/share/agent-project/template"
    assert not (target / ".agent-project").exists()
    saved = root / "plan.json"
    saved.write_text(json.dumps(plan))
    installed = run("apply", "--target", target, "--plan", saved)
    assert installed["status"] == "applied"
    assert run("adopt", "--target", target)["status"] == "noop"
    validation = "/usr/local/share/agent-project/validation/validate-agent-contracts.py"
    subprocess.run(["python3", validation, "--template-root", str(target)], check=True,
                   env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    source = root / "source"
    shutil.copytree(plan["source"], source)
    name = "docs/agents/runbook.md"
    base = (source / name).read_bytes()
    (target / name).write_bytes(b"Local notes\n\n" + base)
    (source / name).write_bytes(base + b"\nUpstream notes\n")
    saved.write_text(json.dumps(run("plan", "--source", source, "--target", target)))
    crashed = subprocess.run(["manage-agent-project", "apply", "--target", str(target),
                              "--plan", str(saved), "--json"],
                             env={**os.environ, "AGENT_PROJECT_TEST_CRASH_AFTER_REPLACE": "1"})
    assert crashed.returncode == 99
    assert run("status", "--target", target)["pending_transaction"]
    assert run("recover", "--target", target)["status"] == "recovered"
    assert (target / name).read_bytes() == b"Local notes\n\n" + base
    saved.write_text(json.dumps(run("plan", "--source", source, "--target", target)))
    updated = run("apply", "--target", target, "--plan", saved)
    assert (target / name).read_bytes() == b"Local notes\n\n" + base + b"\nUpstream notes\n"
    subprocess.run(["python3", validation, "--template-root", str(target)], check=True,
                   env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    assert run("rollback", "--target", target, "--transaction", updated["transaction_id"])["status"] == "rolled_back"
    assert (target / name).read_bytes() == b"Local notes\n\n" + base
    assert (target / "user.txt").read_bytes() == b"private user content"
print("ok - shipped lifecycle/default template, merge, crash recovery, rollback, native contracts")
PY
