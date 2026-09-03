# LangCity — Game Flow Design Notes

Design-only documents. **No engine or content changes are proposed here**; each
document describes data shapes, state machines and tuning values that the
Flutter/Flame client would implement, plus the side-car JSON files this content
repo would eventually ship.

| Document | Covers |
|---|---|
| [`carry-system.md`](carry-system.md) | Carrying objects on back / front / hands (apple, ramen, boxes…), how it grades deliveries, and how it attaches to the 68 existing missions without editing them |
| [`companion-system.md`](companion-system.md) | NPC-follows-player (escort) and player-follows-NPC (guide). Guides walk, wait, cross roads, and hand off through doors |
| [`feature-ideas.md`](feature-ideas.md) | Ranked backlog of other features, each mapped to assets and data that already exist in this repo |

---

## The one rule everything else follows: the additive-overlay contract

The request was "connect with my existing missions **without changing mission
contexts**". Every design below is built on that constraint, stated formally:

**C1 — `missions.json` is frozen.** `world_missions[]` (68) and
`world_mission_nodes[]` (201) keep their current bytes. No node text,
`ai_instruction`, `checkpoints`, `matches`, `xp_reward` or ordering is rewritten.

**C2 — New behaviour ships in side-car files.** Carry and companion data live in
new files under `common/content/` and `<lang>/content/`, keyed by
`mission_id` + node `idx`. `scripts/build_world_pack.py` `rglob`s the pack tree,
so new JSON files ship in `common.zip` / `ja.zip` with **no build-script change**.

**C3 — Overlays are optional and non-blocking.** A node's completion predicate is
unchanged. An overlay may add a visible prop, a bonus objective, flavour lines and
extra XP — it may **never** be the reason a node fails to complete. Delete every
overlay file and the game plays exactly as it does today.

**C4 — Read, don't rewrite.** Where a system needs to know "where is the player
supposed to go", it *reads* the active node's existing `location_id` /`npc_id`
fields. This is what gives the guide system all 127 `goToLocation` nodes for free.

**C5 — New mechanics get new missions.** Anything that genuinely needs new node
types (`pickUpItem`, `deliverItem`, `escortNpc`) ships as **new** records appended
to `world_missions[]` with a new `kind` (`errand`), never by mutating an existing
mission.

### Prerequisite E0 (engine, ships before any new content)

Content packs are downloaded by clients that are already in the field. Before the
first pack containing a new node type ships, the client needs one defensive rule:

> When loading `world_missions`, skip any mission containing a node `type` the
> client does not recognise, and ignore unknown object keys everywhere else.

Until E0 is in the minimum shipped client version, Tier-2 missions
(see `carry-system.md`) ship with `"active": false` and a `min_client` field.
This is the only engine change that must land *first*; everything else is additive.

### Current data facts these designs rely on

| Fact | Where |
|---|---|
| Node types today: `goToLocation` (127), `sayPhrase` (65), `talkToNpc` (8), `studyBoard` (1) | `common/content/missions.json` |
| Missions: 57 `main`, 10 `side`, 1 untyped; 6 distinct `giver_npc_id`s | same |
| 63 locations with `id`, `zone`, `x`, `y`, `name_jp`, `direction_hint_jp` | `common/content/world_locations.json` |
| 57 destinations + 59 door gates with `source_zone`/`target_zone`/`required_level` | `common/content/place_registry.json` |
| NPCs already have multi-zone placements and patrol paths (`walk.path`, `walk.speed`) | `common/content/npc_locations.json` |
| Every character atlas has `idle_*`/`walk_*` in 4 directions; NPC atlases add `talk` | `*/characters/*/**_atlas.json` |
| Town map: 48 px tiles, 162×48, `collisions` (300 rects), `objects` (88 doors/props incl. vending machines), `rifts` (23) | `ja/images/tiles/tokyo_city/tokyo_city.tmj` |
| Interior maps expose `spawn` objects (`default`, `from_town`) | `ja/images/tiles/places/*.json` |
| UI kit already has inventory grid, energy/health bars, friendship meter, quest markers, direction arrow, toasts | `common/images/ui/langcity/` |
| Curriculum skills are addressable ids (`vocab.ramen`, `vocab.onigiri`, `grammar.tabemasu`) | `ja/content/curriculum/levels/level_*.json` |

Because all of that already exists, both systems below are mostly **data plus a
state machine** — not new art pipelines.
