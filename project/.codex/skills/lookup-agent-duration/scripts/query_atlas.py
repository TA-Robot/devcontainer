#!/usr/bin/env python3
"""Discover the installed duration atlas and invoke the bounded query CLI."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys


ATLAS_RELATIVE = Path("generated/duration-atlas/current.json")
SYSTEM_ATLAS = Path("/usr/local/share/mira-duration-atlas/current.json")


def _regular_file(path: Path) -> Path | None:
    try:
        resolved = path.expanduser().resolve()
    except OSError:
        return None
    return resolved if resolved.is_file() else None


def discover_atlas(explicit: Path | None) -> Path:
    if explicit is not None:
        resolved = _regular_file(explicit)
        if resolved is None:
            raise ValueError("explicit duration atlas does not exist")
        return resolved

    configured = os.environ.get("AGENT_DURATION_ATLAS_PATH")
    if configured:
        resolved = _regular_file(Path(configured))
        if resolved is None:
            raise ValueError("AGENT_DURATION_ATLAS_PATH does not name a file")
        return resolved

    candidates: list[Path] = []
    for origin in (Path.cwd(), Path(__file__).resolve().parent):
        for parent in (origin, *origin.parents):
            candidates.append(parent / ATLAS_RELATIVE)
    candidates.extend(
        (
            Path(__file__).resolve().parent.parent / "assets" / "current.json",
            SYSTEM_ATLAS,
        )
    )
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = _regular_file(candidate)
        if resolved is not None and resolved not in seen:
            return resolved
        if resolved is not None:
            seen.add(resolved)
    raise ValueError(
        "duration atlas not found; set AGENT_DURATION_ATLAS_PATH or provide --atlas"
    )


def discover_query_command() -> Path:
    configured = os.environ.get("AGENT_DURATION_QUERY_COMMAND")
    if configured:
        resolved = _regular_file(Path(configured))
        if resolved is None or not os.access(resolved, os.X_OK):
            raise ValueError("AGENT_DURATION_QUERY_COMMAND is not executable")
        return resolved
    installed = shutil.which("query-agent-duration-atlas")
    if installed:
        return Path(installed).resolve()
    for origin in (Path.cwd(), Path(__file__).resolve().parent):
        for parent in (origin, *origin.parents):
            candidate = parent / "scripts" / "query-agent-duration-atlas"
            if candidate.is_file() and os.access(candidate, os.X_OK):
                return candidate.resolve()
    raise ValueError("query-agent-duration-atlas command is not installed")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--atlas", type=Path)
    parser.add_argument("--print-atlas-path", action="store_true")
    args, forwarded = parser.parse_known_args(argv)
    try:
        atlas = discover_atlas(args.atlas)
        if args.print_atlas_path:
            print(atlas)
            return 0
        command = discover_query_command()
        return subprocess.run([str(command), str(atlas), *forwarded], check=False).returncode
    except (OSError, ValueError) as exc:
        print(f"duration atlas skill query failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
