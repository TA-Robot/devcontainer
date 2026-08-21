# Mira World workshop backdrop

`workshop-source.png` is the retained image-generation source. `workshop.png`
is the 1536 x 192 RGBA runtime crop built by:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/build-mira-world-assets.py
```

The runtime crop is deliberately shallow: all five destinations and Mira's
walking baseline survive a normal bottom-panel height without vertically
squashing the art.

## Generation record

The source was generated with the built-in image-generation tool on
2026-08-12. The user-provided Mira illustration was used only as a palette and
world-style reference; no character pixels were copied into the environment.

Base request: a seamless, environment-only 16-bit pixel-art developer atelier
with a research library, planning pavilion, coding workshop, test signal gate,
dispatch dock, and an unobstructed walking lane. Palette: cream, warm yellow,
pale cyan, deep plum, and small coral accents. No people, characters, text,
logos, UI chrome, or watermarks.

Composition edit: preserve the world and style, but scale every destination
into the middle 28 percent of the canvas so an 8:1 production crop contains
all roofs, destinations, and the complete walking lane.

## Exact prompts

Base generation (`mira-original-reference.png` was Image 1):

```text
Use case: stylized-concept
Asset type: horizontal pixel-art game environment backdrop for a VS Code bottom panel
Input image role: Image 1 is a character and palette style reference only; do not place, redraw, or include the character.
Primary request: a single connected side-view workshop-village map where a tiny developer companion can walk between coding-related destinations.
Scene/backdrop: one continuous indoor-outdoor atelier world, left to right: a compact research library and telescope nook, a planning table pavilion, a bright coding workshop with tiny monitors and tools, a test signal gate with green/amber lamps, and a dispatch dock with mailbox and paper-airplane motif. These are parts of one world, not separate panels.
Style/medium: crisp hand-authored 16-bit pixel art, clear blocky clusters, low visual noise, readable when displayed only 96–180 pixels tall.
Composition/framing: extremely wide panoramic side view; straight-on game camera; continuous ground lane across the lower middle; keep the central walking lane uncluttered and leave generous negative space around each station for a 48–64 pixel character sprite. Props belong mainly against the back wall and outer edges. No foreground objects that would cover a walking character.
Lighting/mood: warm, cheerful, quietly alive, cozy afternoon atelier lighting with subtle lamps.
Color palette: cream and soft warm yellow, pale cyan accents, deep plum and charcoal outlines, tiny coral highlights; derive only the palette mood from Image 1.
Constraints: environment only; absolutely no people, characters, animals, mascots, silhouettes, faces, portraits, text, letters, numbers, logos, interface chrome, buttons, borders, panels, grids, watermarks, or speech bubbles. One seamless world with a flat playable ground line. Pixel-perfect hard edges; no painterly blur, antialiasing, depth-of-field, or photorealism.
Output intent: production game backdrop to be cropped and downsampled to a 1536 x 192 runtime PNG behind an independently animated character sprite.
```

Composition edit (`workshop` base generation was Image 1):

```text
Image 1: edit target.
Change only the composition and scale for an ultra-shallow panoramic UI band. Preserve the same connected atelier world, the five coding destinations, exact pixel-art rendering, palette, lighting, and environment-only constraint.

Re-layout the entire library, planning pavilion, coding workshop, test gate, dispatch dock, and continuous walking path as much smaller miniature structures inside one centered horizontal band occupying only about the middle 28 percent of the canvas height. Every destination must remain fully visible from roof to ground within that shallow middle band. Keep a clean, continuous playable lane in front of them. Fill the large area above with simple pale sky and sparse blocky clouds; fill the large area below with a simple flat deep-plum ground/fade so the middle band can later be cropped to an extremely wide 8:1 asset without losing any roof, station, or walking path.

Keep unchanged: crisp hand-authored 16-bit pixel art; cream, warm yellow, pale cyan, deep plum palette; straight-on side-view camera; one seamless world.
Constraints: no people, characters, animals, mascots, faces, portraits, readable text, letters, numbers, logos, interface chrome, buttons, borders, panels, grids, watermark, speech bubbles, blur, antialiasing, or foreground occlusion. Do not add or remove destinations.
```
