#!/usr/bin/env python3
"""Generate the monochrome status-bar icon font from Mira runtime sprites.

This is a design-time asset generator. The extension and VSIX build consume the
checked-in WOFF and do not require Pillow or fontTools at runtime.
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from fontTools.fontBuilder import FontBuilder
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.ttLib import TTFont
    from PIL import Image, ImageChops, ImageFilter
except ImportError as error:
    raise SystemExit(
        "build-mira-icon-font.py requires the design-time packages Pillow and fontTools"
    ) from error


ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets" / "mira" / "sprites"
OUTPUT = ROOT / "extensions" / "mira-companion" / "media" / "mira-icons.woff"
GRID = 24
CONTENT_SIZE = 22
UNITS_PER_EM = 1024
PIXEL_UNITS = 40
X_OFFSET = (UNITS_PER_EM - GRID * PIXEL_UNITS) // 2
Y_OFFSET = 32
# TrueType timestamps count seconds from 1904-01-01. A fixed value keeps the
# checked-in WOFF byte-for-byte reproducible across regeneration runs.
FONT_TIMESTAMP = 3_869_251_200  # 2026-08-11T00:00:00Z

ICON_SOURCES = [
    *[(f"mira-idle-{index}", ASSETS / "core-motion" / f"idle-{index:02d}.png") for index in range(1, 5)],
    ("mira-ready", ASSETS / "status-emotions" / "ready.png"),
    ("mira-thinking", ASSETS / "status-emotions" / "thinking.png"),
    *[(f"mira-research-{index}", ASSETS / "work-actions" / f"research-{index:02d}.png") for index in range(1, 5)],
    *[(f"mira-typing-{index}", ASSETS / "work-actions" / f"typing-{index:02d}.png") for index in range(1, 5)],
    *[(f"mira-terminal-{index}", ASSETS / "work-actions" / f"terminal-{index:02d}.png") for index in range(1, 5)],
    *[(f"mira-testing-{index}", ASSETS / "work-actions" / f"testing-{index:02d}.png") for index in range(1, 5)],
    ("mira-delegating-1", ASSETS / "orchestration" / "delegate-one.png"),
    ("mira-delegating-2", ASSETS / "orchestration" / "delegate-two.png"),
    ("mira-delegating-3", ASSETS / "orchestration" / "delegate-dispatch.png"),
    ("mira-delegating-4", ASSETS / "orchestration" / "delegate-watch.png"),
    ("mira-approval", ASSETS / "status-emotions" / "approval.png"),
    ("mira-success", ASSETS / "orchestration" / "complete.png"),
    ("mira-error", ASSETS / "status-emotions" / "error.png"),
]


def icon_mask(path: Path) -> Image.Image:
    image = Image.open(path).convert("RGBA")
    bounds = image.getchannel("A").getbbox()
    if bounds is None:
        raise ValueError(f"empty sprite: {path}")
    image = image.crop(bounds)

    # At 16px the full body becomes an unreadable blob. Use the upper 72% so
    # Mira's twin buns, face, hands, and the top of the active prop survive.
    image = image.crop((0, 0, image.width, max(1, round(image.height * 0.72))))
    visible = image.getchannel("A").getbbox()
    if visible is None:
        raise ValueError(f"empty upper sprite: {path}")
    image = image.crop(visible)

    ratio = min(CONTENT_SIZE / image.width, CONTENT_SIZE / image.height)
    size = (max(1, round(image.width * ratio)), max(1, round(image.height * ratio)))
    alpha = image.getchannel("A").resize(size, Image.Resampling.LANCZOS)
    silhouette = alpha.point(lambda value: 255 if value >= 64 else 0)
    edge = ImageChops.subtract(silhouette, silhouette.filter(ImageFilter.MinFilter(3)))

    dark_pixels = image.convert("L").point(lambda value: 255 if value < 115 else 0)
    dark_pixels = ImageChops.multiply(dark_pixels, image.getchannel("A"))
    dark_pixels = dark_pixels.resize(size, Image.Resampling.BOX)
    dark_pixels = dark_pixels.point(lambda value: 255 if value >= 40 else 0)

    line_art = ImageChops.lighter(edge, dark_pixels)
    canvas = Image.new("L", (GRID, GRID), 0)
    canvas.paste(line_art, ((GRID - line_art.width) // 2, (GRID - line_art.height) // 2))
    return canvas


def glyph_from_mask(mask: Image.Image):
    pen = TTGlyphPen(None)
    pixels = mask.load()
    for y in range(GRID):
        for x in range(GRID):
            if pixels[x, y] < 128:
                continue
            left = X_OFFSET + x * PIXEL_UNITS
            right = left + PIXEL_UNITS
            bottom = Y_OFFSET + (GRID - y - 1) * PIXEL_UNITS
            top = bottom + PIXEL_UNITS
            pen.moveTo((left, bottom))
            pen.lineTo((right, bottom))
            pen.lineTo((right, top))
            pen.lineTo((left, top))
            pen.closePath()
    return pen.glyph()


def main() -> int:
    missing = [str(path) for _, path in ICON_SOURCES if not path.is_file()]
    if missing:
        print("missing Mira icon sources:\n" + "\n".join(missing), file=sys.stderr)
        return 1

    glyph_order = [".notdef"] + [name for name, _ in ICON_SOURCES]
    glyphs = {".notdef": TTGlyphPen(None).glyph()}
    character_map = {}
    metrics = {".notdef": (UNITS_PER_EM, 0)}
    for index, (name, source) in enumerate(ICON_SOURCES, start=1):
        glyphs[name] = glyph_from_mask(icon_mask(source))
        character_map[0xE000 + index] = name
        metrics[name] = (UNITS_PER_EM, 0)

    builder = FontBuilder(UNITS_PER_EM, isTTF=True)
    builder.setupGlyphOrder(glyph_order)
    builder.setupCharacterMap(character_map)
    builder.setupGlyf(glyphs)
    builder.setupHorizontalMetrics(metrics)
    builder.setupHorizontalHeader(ascent=1000, descent=-24)
    builder.setupNameTable(
        {
            "familyName": "Mira Companion Icons",
            "styleName": "Regular",
            "uniqueFontIdentifier": "MiraCompanionIcons-0.2.0",
            "fullName": "Mira Companion Icons",
            "psName": "MiraCompanionIcons",
            "version": "Version 0.2.0",
        }
    )
    builder.setupOS2(
        sTypoAscender=1000,
        sTypoDescender=-24,
        usWinAscent=1000,
        usWinDescent=24,
    )
    builder.setupPost()
    builder.setupMaxp()

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT.with_name(f".{OUTPUT.name}.tmp")
    builder.save(temporary)
    font = TTFont(temporary, recalcTimestamp=False)
    font["head"].created = FONT_TIMESTAMP
    font["head"].modified = FONT_TIMESTAMP
    font.flavor = "woff"
    font.save(OUTPUT)
    temporary.unlink()
    print(f"{OUTPUT}: {len(ICON_SOURCES)} glyphs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
