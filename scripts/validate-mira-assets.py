#!/usr/bin/env python3
"""Validate Mira's generated runtime asset contract without image dependencies."""

from __future__ import annotations

import json
from pathlib import Path
import struct
import sys
from typing import Any, Iterator


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
EXPECTED_FRAME_COUNT = 80
EXPECTED_FRAME_SIZE = (256, 256)
EXPECTED_WORLD_SIZE = (1536, 192)
RGBA_COLOR_TYPE = 6


def png_header(path: Path) -> tuple[int, int, int]:
    with path.open("rb") as source:
        signature = source.read(8)
        if signature != PNG_SIGNATURE:
            raise ValueError(f"not a PNG: {path}")
        length = struct.unpack(">I", source.read(4))[0]
        chunk_type = source.read(4)
        if chunk_type != b"IHDR" or length != 13:
            raise ValueError(f"missing canonical IHDR: {path}")
        width, height, _depth, color_type, _compression, _filter, _interlace = struct.unpack(
            ">IIBBBBB", source.read(13)
        )
    return width, height, color_type


def png_paths(value: Any) -> Iterator[str]:
    if isinstance(value, dict):
        for nested in value.values():
            yield from png_paths(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from png_paths(nested)
    elif isinstance(value, str) and value.endswith(".png"):
        yield value


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    asset_root = repo_root / "assets" / "mira"
    manifest_path = asset_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    errors: list[str] = []
    if manifest.get("schemaVersion") != 1:
        errors.append("manifest schemaVersion must be 1")
    if manifest.get("frameCount") != EXPECTED_FRAME_COUNT:
        errors.append(f"manifest frameCount must be {EXPECTED_FRAME_COUNT}")

    runtime_frames = sorted((asset_root / "sprites").glob("*/*.png"))
    if len(runtime_frames) != EXPECTED_FRAME_COUNT:
        errors.append(
            f"expected {EXPECTED_FRAME_COUNT} runtime frames, found {len(runtime_frames)}"
        )

    for path in runtime_frames:
        try:
            width, height, color_type = png_header(path)
        except (OSError, ValueError, struct.error) as exc:
            errors.append(str(exc))
            continue
        if (width, height) != EXPECTED_FRAME_SIZE:
            errors.append(f"unexpected frame size {width}x{height}: {path}")
        if color_type != RGBA_COLOR_TYPE:
            errors.append(f"runtime frame is not RGBA PNG: {path}")

    referenced = set(png_paths(manifest.get("sets", {})))
    for relative in sorted(referenced):
        path = asset_root / relative
        if not path.is_file():
            errors.append(f"manifest path does not exist: {relative}")

    manifest_runtime = {path for path in referenced if path.startswith("sprites/")}
    disk_runtime = {path.relative_to(asset_root).as_posix() for path in runtime_frames}
    missing_from_manifest = sorted(disk_runtime - manifest_runtime)
    if missing_from_manifest:
        errors.append(
            "runtime frames missing from manifest: " + ", ".join(missing_from_manifest)
        )

    workshop = manifest.get("worlds", {}).get("workshop", {})
    world_relative = workshop.get("background")
    if not isinstance(world_relative, str):
        errors.append("manifest worlds.workshop.background must be a path")
    else:
        world_path = asset_root / world_relative
        try:
            width, height, color_type = png_header(world_path)
            if (width, height) != EXPECTED_WORLD_SIZE:
                errors.append(
                    f"unexpected world size {width}x{height}: {world_path}"
                )
            if color_type != RGBA_COLOR_TYPE:
                errors.append(f"runtime world is not RGBA PNG: {world_path}")
        except (OSError, ValueError, struct.error) as exc:
            errors.append(str(exc))

    if (workshop.get("width"), workshop.get("height")) != EXPECTED_WORLD_SIZE:
        errors.append(
            "manifest workshop dimensions must match the 1536x192 runtime world"
        )

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(
        f"Mira assets OK: {len(runtime_frames)} RGBA frames, "
        f"{len(referenced)} sprite references, 1 validated world"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
