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


def discover_validity(explicit: Path | None, atlas: Path) -> Path | None:
    if explicit is not None:
        resolved = _regular_file(explicit)
        if resolved is None:
            raise ValueError("explicit duration validity companion does not exist")
        return resolved
    configured = os.environ.get("AGENT_DURATION_VALIDITY_PATH")
    if configured:
        resolved = _regular_file(Path(configured))
        if resolved is None:
            raise ValueError("AGENT_DURATION_VALIDITY_PATH does not name a file")
        return resolved
    # Never attach a validity audit from a different snapshot merely because it
    # is bundled with the skill. Project, skill, and system atlas snapshots all
    # place their matching companion beside the selected atlas.
    if atlas.name != "current.json":
        return None
    return _regular_file(atlas.with_name("current-validity.json"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-h", "--help", action="store_true")
    parser.add_argument("--atlas", type=Path)
    parser.add_argument("--validity", type=Path)
    parser.add_argument("--print-atlas-path", action="store_true")
    parser.add_argument("--print-validity-path", action="store_true")
    args, forwarded = parser.parse_known_args(argv)
    try:
        if args.help:
            print(
                "usage: query_atlas.py [--atlas PATH] [--validity PATH] "
                "[--print-atlas-path] [--print-validity-path] "
                "QUERY_OPTIONS...\n\n"
                "Discovers and injects the atlas positional argument; do not pass it "
                "again in QUERY_OPTIONS.\n\n"
                "Atlas discovery order:\n"
                "  1. --atlas PATH\n"
                "  2. AGENT_DURATION_ATLAS_PATH\n"
                "  3. nearest generated/duration-atlas/current.json\n"
                "  4. this skill's assets/current.json\n"
                "  5. /usr/local/share/mira-duration-atlas/current.json\n\n"
                "A matching validity companion is injected when available; override it with "
                "--validity or AGENT_DURATION_VALIDITY_PATH.\n"
                "--print-atlas-path or --print-validity-path prints the selected file and exits without querying.\n\n"
                "Query options from the bounded CLI follow:\n",
                flush=True,
            )
            try:
                command = discover_query_command()
            except ValueError as exc:
                print(f"query CLI help unavailable: {exc}", file=sys.stderr)
                return 0
            return subprocess.run([str(command), "--help"], check=False).returncode
        atlas = discover_atlas(args.atlas)
        if args.print_atlas_path:
            print(atlas)
            return 0
        validity = discover_validity(args.validity, atlas)
        if args.print_validity_path:
            print(validity if validity is not None else "not-found")
            return 0 if validity is not None else 2
        command = discover_query_command()
        injected = [str(command), str(atlas)]
        if validity is not None:
            injected.extend(["--validity", str(validity)])
        return subprocess.run([*injected, *forwarded], check=False).returncode
    except (OSError, ValueError) as exc:
        print(f"duration atlas skill query failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
