#!/usr/bin/env python3
"""Build the shallow Mira World runtime backdrop from its generated source."""

from __future__ import annotations

from pathlib import Path
import sys

try:
    from PIL import Image
except ImportError as exc:  # pragma: no cover - design-time dependency guard
    raise SystemExit(
        "Pillow is required only to rebuild Mira's generated world assets"
    ) from exc


ROOT = Path(__file__).resolve().parents[1]
WORLD_ROOT = ROOT / "assets" / "mira" / "worlds"
SOURCE = WORLD_ROOT / "workshop-source.png"
OUTPUT = WORLD_ROOT / "workshop.png"
EXPECTED_SOURCE_SIZE = (2172, 724)
CROP = (0, 294, 2172, 566)
OUTPUT_SIZE = (1536, 192)


def main() -> int:
    with Image.open(SOURCE) as source:
        if source.size != EXPECTED_SOURCE_SIZE:
            print(
                f"error: expected {EXPECTED_SOURCE_SIZE}, found {source.size}: {SOURCE}",
                file=sys.stderr,
            )
            return 1
        runtime = source.crop(CROP).resize(
            OUTPUT_SIZE,
            resample=Image.Resampling.NEAREST,
        )
        runtime.convert("RGBA").save(OUTPUT, format="PNG", optimize=True)

    print(OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
