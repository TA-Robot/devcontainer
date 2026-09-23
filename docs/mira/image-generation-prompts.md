# ミラ image generation prompt set

生成日: 2026-08-11

実行経路: built-in image generation tool

input references:

- Image 1: `assets/mira/reference/mira-original-reference.png` — identity / original design reference
- Image 2: `assets/mira/character-sheet/mira-character-sheet.png` — sprite生成時のidentity / costume anchor

## Character sheet

```text
Use case: stylized-concept
Asset type: definitive anime character design sheet for a VS Code animated assistant named Mira
Input images: Image 1 is the identity and costume reference. Preserve the same character identity and recognizable design.
Primary request: Create one polished, production-ready character sheet for Mira. Show a full-body front view, full-body 3/4 view, full-body back view, a clean head close-up, and six small facial-expression studies: confident smile, curious thinking, excited discovery, focused work, approval-waiting concern, and relieved success.
Subject: age-appropriate nonsexual teenage tech-lead character; golden-blonde hair in two rounded buns with long symmetrical spiral side locks; dark purple spherical hair ornaments with pink highlights; warm amber-brown eyes; white Japanese sailor-style blouse with oversized sleeves, dark navy-purple collar and cuffs, cyan-blue necktie, dark pleated skirt, dark knee socks and simple black loafers. Preserve the reference's wink-capable playful confidence and graphic silhouette.
Style/medium: high-end clean anime production character sheet, crisp controlled line art, cel shading, precise consistent proportions, readable costume construction, original design.
Composition/framing: landscape sheet, orderly spacing, every full body visible from hair to shoes, no overlapping figures, ample margins.
Scene/backdrop: flat warm off-white studio sheet with subtle pale gold geometric dividers only.
Color palette: pale gold hair, warm skin, white, navy-purple, cyan-blue, dark violet ornaments, amber eyes.
Constraints: keep all views recognizably the same person and outfit; modest age-appropriate presentation; no sexualized pose; no text, letters, numbers, labels, logos, signatures, or watermark; no additional characters; no cropped feet or hair; no props obscuring the design.
Avoid: painterly rendering, photorealism, 3D, busy background, costume changes, extra accessories, inconsistent eye or hair colors.
```

## Core motion sheet

```text
Use case: stylized-concept
Asset type: square 4-by-4 pixel-art sprite sheet for a VS Code desktop pet
Input images: Image 1 is Mira's original identity reference. Image 2 is the definitive character sheet. Preserve the same character and costume.
Primary request: Create exactly sixteen full-body chibi pixel-art sprites in a strict 4 columns by 4 rows matrix, designed as animation frames.
Frame order: row 1 = four subtle idle breathing and blinking frames; row 2 = four walking-right frames; row 3 = four walking-left frames; row 4 = four friendly waving frames.
Subject: Mira, golden-blonde twin round buns, long spiral side locks, dark purple spherical hair ornaments, amber eyes, white sailor blouse with navy-purple collar and cuffs, cyan necktie, dark pleated skirt, dark knee socks, black loafers.
Style/medium: authentic hand-authored 32-bit pixel art, crisp hard square pixels, limited palette, dark readable 1-pixel-style outline, no antialiasing, consistent 3-head-tall chibi proportions.
Composition/framing: exactly 4x4 equal cells filling a square canvas; one centered complete sprite per cell; identical scale, baseline, camera, costume, and body proportions; generous empty padding inside every cell; no overlap across cell boundaries.
Scene/backdrop: perfectly flat solid #00ff00 chroma-key background across the entire sheet for local removal, with no grid lines.
Constraints: background is one exact uniform color with no shadows, gradients, floor, texture, reflections, or lighting variation; do not use green anywhere in the character; no cast shadow; no text, labels, numbers, logos, watermark, UI, borders, or extra characters; every frame fully visible.
Avoid: smooth vector edges, anime illustration rendering, painterly shading, subpixel details, changing hair shape, changing outfit, cropped sprites.
```

## Work actions sheet

```text
Use case: stylized-concept
Asset type: square 4-by-4 pixel-art sprite sheet for a VS Code coding-agent pet
Input images: Image 1 is Mira's original identity reference. Image 2 is the definitive character sheet. Preserve the same character and costume.
Primary request: Create exactly sixteen chibi pixel-art work animation frames in a strict 4 columns by 4 rows matrix.
Frame order: row 1 = Mira seated at a small desk typing on a laptop, four sequential frames; row 2 = Mira operating a terminal screen, four sequential frames; row 3 = Mira reading code or documentation with a magnifying glass and notebook, four sequential frames; row 4 = Mira watching tests run, then noticing completion, four sequential frames.
Subject: Mira, golden-blonde twin round buns, long spiral side locks, dark purple spherical hair ornaments, amber eyes, white sailor blouse with navy-purple collar and cuffs, cyan necktie, dark pleated skirt.
Props: tiny dark desk and laptop/terminal only where required, consistent across each row.
Style/medium: authentic hand-authored 32-bit pixel art, crisp hard square pixels, limited palette, dark readable outline, no antialiasing, consistent 3-head-tall chibi proportions.
Composition/framing: exactly 4x4 equal cells filling a square canvas; one centered complete sprite vignette per cell; same scale, baseline, camera, costume, desk size, and proportions; generous empty padding; no overlap across cells.
Scene/backdrop: perfectly flat solid #00ff00 chroma-key background across the entire sheet, no grid lines.
Constraints: one exact uniform green with no shadow, gradient, floor plane, texture, reflection, or lighting variation; no green in subjects; no text or readable code; no labels, numbers, logos, watermark, UI frame, borders, or additional people.
Avoid: photorealism, smooth illustration, inconsistent props, cropped hair, changing costume or colors.
```

## Status and emotions sheet

```text
Use case: stylized-concept
Asset type: square 4-by-4 pixel-art emotion and status sprite sheet for a VS Code coding-agent pet
Input images: Image 1 is Mira's original identity reference. Image 2 is the definitive character sheet. Preserve the same character and costume.
Primary request: Create exactly sixteen full-body chibi pixel-art status poses in a strict 4 columns by 4 rows matrix.
Frame order: row 1 = curious thinking, sudden discovery, confidently pointing, excited sparkle; row 2 = politely raising a hand for approval, concerned waiting, nervous sweat, patient seated wait; row 3 = small success jump, peace sign, relieved smile, confident thumbs-up; row 4 = surprised error, disappointed slump, retrying with determination, recovered ready pose.
Subject: Mira with golden-blonde twin buns, long spiral side locks, purple spherical ornaments, amber eyes, white sailor blouse with navy-purple trim, cyan necktie, dark pleated skirt, dark knee socks, black loafers.
Style/medium: authentic hand-authored 32-bit pixel art, crisp hard square pixels, limited palette, dark readable outline, no antialiasing, consistent 3-head-tall chibi proportions.
Composition/framing: exactly 4x4 equal cells filling a square canvas; one centered complete sprite per cell; identical size, baseline, camera, costume, and proportions; generous empty padding; no overlap across cells.
Scene/backdrop: perfectly flat solid #00ff00 chroma-key background, no grid lines.
Constraints: green background must be exact and uniform with no shadows, gradient, floor, texture, reflection, or lighting variation; no green in character; simple pixel status marks such as sparkle, exclamation, check, or sweat are allowed but no words; no text, labels, numbers, logos, watermark, borders, or extra characters; every sprite fully visible.
Avoid: smooth illustration, photorealism, outfit changes, cropped hair, inconsistent scale.
```

## Orchestration sheet

```text
Use case: stylized-concept
Asset type: square 4-by-4 pixel-art orchestration sprite sheet for a multi-agent VS Code pet
Input images: Image 1 is Mira's original identity reference. Image 2 is the definitive character sheet. Preserve the same character and costume.
Primary request: Create exactly sixteen chibi pixel-art orchestration scenes in a strict 4 columns by 4 rows matrix.
Frame order: row 1 = Mira studies a tiny planning board, draws a dependency arrow, identifies a critical path, points decisively; row 2 = Mira calls one tiny helper, calls two helpers, dispatches them in different directions, watches them work; row 3 = Mira receives a report, compares two reports, reviews a checklist, integrates results at a laptop; row 4 = Mira resolves a conflict, runs final validation, presents a completed check mark, celebrates with the helper team.
Subject: Mira with golden-blonde twin buns, long spiral side locks, purple spherical ornaments, amber eyes, white sailor blouse with navy-purple trim, cyan necktie, dark pleated skirt. Tiny helpers are simple small round robot-like pixel mascots in cyan, purple, and gold, not additional human characters.
Style/medium: authentic hand-authored 32-bit pixel art, crisp hard square pixels, limited palette, dark readable outline, no antialiasing, consistent chibi proportions and prop scale.
Composition/framing: exactly 4x4 equal cells filling a square canvas; one centered complete vignette per cell; same Mira scale, baseline, camera, costume, and proportions; generous padding; no overlap between cells.
Scene/backdrop: perfectly flat solid #00ff00 chroma-key background, no grid lines.
Constraints: green background is exact uniform flat color with no shadows, gradient, floor, texture, reflection, or lighting variation; no green in subjects; board and reports contain only abstract pixels, no readable writing; no text, labels, numbers, logos, watermark, UI border, or cropped figures.
Avoid: detailed office scenery, smooth illustration, photorealism, changing outfit, inconsistent helpers.
```

## Companion agents sheet

```text
Use case: stylized-concept
Asset type: square 4-by-4 pixel-art mini-agent companion sprite sheet for a VS Code multi-agent pet
Input images: Image 1 is Mira's original identity reference. Image 2 is the definitive character sheet and palette anchor.
Primary request: Create exactly sixteen tiny companion sprites in a strict 4 columns by 4 rows matrix. Four role families, four frames each.
Frame order: row 1 = researcher companion in blue with tiny book/magnifier: idle, walk, inspect, report; row 2 = implementer companion in cyan with tiny laptop/wrench: idle, walk, type, deliver commit; row 3 = reviewer companion in purple with tiny clipboard/check: idle, walk, review, raise warning; row 4 = tester companion in warm gold with tiny console/flask: idle, walk, run test, celebrate pass.
Subject: cute nonhuman round robot/fairy mascots inspired by Mira's dark purple spherical hair ornaments and cyan/gold palette; each has a tiny pair of side spirals as a visual family trait; no human bodies.
Style/medium: authentic hand-authored 32-bit pixel art, crisp hard square pixels, limited palette, strong silhouette, dark 1-pixel-style outline, no antialiasing, consistent tiny mascot proportions.
Composition/framing: exactly 4x4 equal cells filling a square canvas; one centered complete mascot per cell; identical scale and baseline within each row; generous padding; no overlap across cell boundaries.
Scene/backdrop: perfectly flat solid #00ff00 chroma-key background, no grid lines.
Constraints: exact uniform green with no shadows, gradients, floor, texture, reflections, or lighting variation; no green in mascots; props use abstract pixels only; no text, labels, numbers, logos, watermark, borders, humans, or cropped sprites.
Avoid: detailed backgrounds, smooth vector art, 3D, photorealism, inconsistent mascot anatomy.
```
