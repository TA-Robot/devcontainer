#!/usr/bin/env python3
"""Discover the bounded report CLI and query the current workspace by default."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys


COMMAND_NAME = "report-agent-collaboration-evidence"


def discover_command() -> Path:
    configured = os.environ.get("AGENT_COLLABORATION_REPORT_COMMAND")
    if configured:
        path = Path(configured).expanduser().resolve()
        if path.is_file() and os.access(path, os.X_OK):
            return path
        raise ValueError("AGENT_COLLABORATION_REPORT_COMMAND is not executable")
    installed = shutil.which(COMMAND_NAME)
    if installed:
        return Path(installed).resolve()
    for origin in (Path.cwd(), Path(__file__).resolve().parent):
        for parent in (origin, *origin.parents):
            candidate = parent / "scripts" / COMMAND_NAME
            if candidate.is_file() and os.access(candidate, os.X_OK):
                return candidate.resolve()
    raise ValueError(f"{COMMAND_NAME} is not installed")


def workspace_key(path: Path) -> str:
    normalized = str(path.expanduser().resolve(strict=False))
    return hashlib.sha256(
        f"workspace:{normalized}".encode("utf-8", errors="replace")
    ).hexdigest()[:16]


def main(argv: list[str] | None = None) -> int:
    forwarded = list(sys.argv[1:] if argv is None else argv)
    all_workspaces = "--all-workspaces" in forwarded
    forwarded = [item for item in forwarded if item != "--all-workspaces"]
    has_workspace = any(
        item == "--workspace" or item.startswith("--workspace=")
        for item in forwarded
    )
    if not all_workspaces and not has_workspace:
        forwarded = ["--workspace", workspace_key(Path.cwd()), *forwarded]
    try:
        return subprocess.run([str(discover_command()), *forwarded], check=False).returncode
    except (OSError, ValueError) as exc:
        print(f"collaboration evidence skill failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
