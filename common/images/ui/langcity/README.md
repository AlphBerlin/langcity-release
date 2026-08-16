# Neon City Academy — Pixel-Art UI Kit

A complete 32-bit pixel-art UI toolkit for a vibrant top-down city-simulation /
educational adventure game. **235 components in 11 categories**, generated as
batched sheets, machine-split, normalized, and verified.

## What's inside

| Folder | Files | Contents |
|---|---|---|
| `assets/` | 235 | Canonical set — pure **#FF00FF magenta** background, fully opaque |
| `transparent/` | 235 | Alpha variant — background removed, binary alpha, despilled edges |
| `manifest.json` / `manifest.csv` | — | Per-asset metadata: category, state, dimensions, nine-slice compatibility, recommended padding, scaling mode (none / stretch / tile) |
| `plan.json` | — | The full batch plan used to build the kit (reproducible) |
| `raw/` | 45 | Original AI-generated batch sheets (source material) |

### Categories

- **buttons** (22) — primary (default/hover/pressed/focused/disabled), secondary, confirm, cancel, accept/decline/continue/skip/complete
- **controls** (30) — checkboxes, radios, switches, toggles, text/search inputs (5 states), sliders, scrollbars
- **hud** (41) — XP/health/energy/loading bars, coin/gem/ticket/streak/energy/skill-point counters, hearts, badges, quest markers, friendship meter, waveforms, profile cards
- **skills** (30) — 10 skill icons (speaking…exploration), skill-tree nodes (locked/available/active/completed/mastered × circle/square), connectors, junctions, dividers
- **dialogue** (29) — NPC dialogue window, speech/thought/chat bubbles, nameplate, typing indicator, portrait frames, mood & reaction icons, spinner frames
- **missions** (14) — mission cards (main/side/daily/quest), quest entries (default/active/completed/failed/locked), objective rows, progress tracker, timer
- **panels** (13) — main menu, pause, settings, profile, skills, missions log, inventory grid, city map, achievements, leaderboard, shop, help
- **overlays** (12) — mission complete/failed popups, reward window, confirmation & warning dialogs, daily rewards, toasts (default/success/error/warning), banners
- **navigation** (23) — 16 icon buttons, tabs (4 states), bottom-nav bar, section & accordion headers
- **map** (16) — minimap frame & background, 9 location markers, player/NPC markers, direction arrow, pagination dots
- **feedback** (5) — progress rings (empty → full)

## Conventions

- **Grid:** every canvas is exactly 32×32 or a multiple (96×32, 128×32, 64×64, 160×128 …). All states of one component share the identical canvas, alignment and proportions.
- **Background:** canonical files use pure opaque `#FF00FF` (chroma-key it in your engine), or use the ready-made `transparent/` alpha variants.
- **No text anywhere:** all text-bearing containers have clean, empty, text-safe interiors; glyphs (checkmarks, padlocks, chevrons) are drawn shapes. Render text with your engine's font at runtime.
- **Pixels:** crisp hard edges, quantized 32-color foreground palette, one theme palette across the whole kit (deep navy / warm amber / teal neon / cream / leaf-green / coral-red / gold).
- **Naming:** `{component}_{state}.png` in category folders, e.g. `buttons/button_primary_hover.png`.
- **Nine-slice & tiling:** see `manifest.json` — panels, bars and buttons carry nine-slice + padding metadata; connectors and dividers are marked tileable.

## Verified

278 pass / 3 design-intent warnings (spinner arc frames) / 0 failures —
multiple-of-32 canvases, exact #FF00FF corners, fully opaque, ≥2 px padding,
no edge bleed.
