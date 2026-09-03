# Companion System — Follow & Guide

> Design only. No code or content changes in this document.
> Read [`README.md`](README.md) first — the additive-overlay contract (C1–C5) governs everything here.

## 1. Two directions, one core

| Role | Who leads | Example | Player skill practised |
|---|---|---|---|
| `guide` | **NPC leads, player follows** | 「こうばんまで あんないして ください」 — Hana walks you to the police station, waiting whenever you fall behind | Listening to directions, landmark vocabulary |
| `escort` | **NPC follows player** | A lost child, a tourist, a porter carrying your box | Producing directions, reassurance phrases |
| `pet` *(later)* | Follows player, no dialogue | Cat from the animal café | — |

All three are the **same component** with a different target-selection strategy.
Build the guide first; escort is ~15% extra work on top of it.

## 2. Why this needs no mission edits (contract C4)

The guide never needs its own destination list baked into missions. When the
player asks an NPC for directions, the system reads the **active mission node's
existing `location_id`** — a field all 201 nodes already have. That instantly
gives guide support to all **127 `goToLocation` nodes** and every `talkToNpc` /
`sayPhrase` node that names a place.

Destination candidates offered in the dialogue, in priority order:

1. `location_id` of the player's current active mission node
2. The location the player has been visibly failing to find
   (**stuck detection**: an active `goToLocation` node, > 90 s of movement, and no
   net progress toward the target — a strong, silent tutoring signal)
3. Locations already discovered by the player, filtered by the NPC's `guide_scope`
4. The NPC's own home zone

Nothing above writes to mission data. Guides are a **service layer on top of
existing missions**, exactly like a map or a compass would be.

## 3. Requesting a guide

Three entry points, all optional:

1. **Dialogue menu** on any NPC with `can_guide: true` → "Guide me to…".
2. **In-language request** — the player types/says
   「こうばんは どこですか」 or 「こうばんまで あんないして ください」.
   Matched with the same `matches[]` keyword mechanism the 65 `sayPhrase` nodes
   already use (`こうばん` + `どこ|あんない`). Asking in Japanese awards bonus XP;
   asking via the menu does not. This is the intended reward gradient.
3. **Offered by the NPC** when stuck detection fires — the NPC walks up and offers,
   once, then goes quiet for 5 minutes if declined.

`world_locations.json` already carries `direction_hint_jp` for every location
(e.g. 「こうばんは まちの みぎがわの うえの ドアから はいれます」) — that string is
the guide's opening line, free of new content authoring.

## 4. Guide state machine

This is the heart of the "walks and waits for us" requirement.

```
        Idle
         │ accept request
         ▼
      Routing ──no path──► VerbalOnly (falls back to directions + marker)
         │
         ▼
   ┌─► Leading ──dist > wait_radius──► Pausing ──dist > recall_radius──► Returning
   │      │  ▲                            │                                  │
   │      │  └──────dist < resume_radius──┴──────────────────────────────────┘
   │      │
   │      ├─ waypoint.crossing ──► Crossing (look L/R, warn, cross)
   │      ├─ waypoint.gate ─────► AtGate ──player enters door──► ZoneHandoff ──►┐
   │      ├─ blocked > 3 s ─────► Unstick                                       │
   │      ├─ dist > teleport_radius or off-camera > 4 s ──► CatchUp (warp) ─────┤
   │      └─ dialogue / minigame / menu ──► Suspended ──resume──────────────────┤
   │                                                                            │
   └────────────────────────────────────────────────────────────────────────────┘
         │ within arrive_radius of destination
         ▼
      Arrived ──► (optional arrival quiz) ──► Farewell ──► Dismissed
```

### 4.1 The states that matter

**`Leading`** — the NPC walks the route at
`guide_speed = min(npc_walk_speed, player_speed × 0.9)`. It is deliberately
*slower* than the player so a following player never has to sprint. It plays the
existing `walk_*` animations; no new art.

**`Pausing`** — the moment the player is more than `wait_radius` behind, the NPC
**stops at the nearest waypoint** (never mid-road), turns to face the player,
plays the existing `talk` animation, and bubbles 「こっち こっち！」. A direction
arrow (`common/images/ui/langcity/map/arrow_direction.png`) points from the NPC toward the next
waypoint. This is the behaviour the request describes — it waits, visibly, and
tells you where it is.

**`Returning`** — if the player is *very* far behind (`recall_radius`), waiting in
place looks dumb. The NPC walks back up to 2 waypoints toward the player, then
waits. Nudge audio every 8 s, at most 3 times, then silent (anti-nag rule).

**`Crossing`** — waypoints tagged `crossing: true` (roads, station concourse). The
NPC stops, plays `idle_left` for 0.6 s then `idle_right` for 0.6 s (a
look-both-ways beat assembled purely from existing animations), says
「くるまに きを つけて」, then crosses. It will **not** start crossing unless the
player is within `wait_radius`, so nobody gets separated at a road.

**`AtGate` / `ZoneHandoff`** — the critical one, because `place_registry.json`
already models every door as a gate with `source_zone` / `target_zone`:

1. NPC walks to the door object (e.g. `door_police-station` at `4621, 680` in
   town), stops **beside** it (never on the trigger tile), faces it.
2. Line: 「ここから はいります。どうぞ」 + door highlight marker.
3. Waits indefinitely. No timeout. The player triggers the door themselves —
   the guide never yanks the player through a transition.
4. On the new zone loading, the companion is re-instantiated at that zone's
   `spawn` object (`default`, or `from_<zone>` where authored) with a 0.4 s
   fade-in and one step forward, so it reads as "walked in behind you".
5. If the player instead enters a **different** door, the companion follows them
   there anyway and re-routes from the new zone. **A guide is never abandoned and
   never abandons.**

This requires the companion to be a **session-scoped entity, not a zone-scoped
one** — the single most important architectural note in this document.

**`Unstick`** — companions are non-blocking to the player (no mutual collision), so
the classic doorway-jam can't happen. If pathing still fails for 3 s, allow a
≤ 1-tile nudge through geometry.

**`CatchUp`** — beyond `teleport_radius`, or off-camera for 4 s, the NPC warps to a
valid walkable tile **behind the player, outside the camera frustum**, and
resumes. Warps must never be visible.

**`VerbalOnly`** — if no path exists (locked gate, level-gated zone,
`required_level` unmet), the guide does not walk. It gives the
`direction_hint_jp` line, drops a map marker, and explains the gate
(「レベル５から はいれます」). Graceful degradation instead of a broken escort.

**`Suspended`** — any dialogue, minigame, study board, or menu freezes the
companion in place. It resumes facing the player.

### 4.2 Dismissal

Guide ends on: arrival, 「ありがとう」/ dismiss menu, mission node completion that
made the guide moot, player travelling 3 zones off-route, or 15 minutes.
Farewell line always plays; the NPC then walks back to its `npc_locations`
patrol path and resumes its normal `walk.path` loop.

## 5. Escort mode (NPC follows the player)

Same component, inverted target. Technical recommendation:

- The follower targets a **follow anchor**: 1 tile behind the player's facing,
  offset to a formation slot if several followers exist (6 slots, ring layout).
- Path by **breadcrumb trail**, not A*: store the player's last 64 positions at
  12 px spacing and walk that polyline. It is cheap, and it looks natural because
  the follower literally retraces the player's steps rather than cutting corners.
- Fall back to A* only when the breadcrumb is broken (zone change, warp,
  > `teleport_radius`).
- Followers respect the same `Pausing` / `CatchUp` / `Suspended` rules, mirrored.
- Escort NPCs speak: 「こっちで いいの？」 when the player backtracks twice,
  「つかれた…」 after 4 minutes, 「ここ？」 at the destination. Uncertainty lines are
  what make an escort feel alive — and they are *comprehension checks in disguise*.

## 6. Data shapes (new files, all additive)

### 6.1 `common/content/npc_capabilities.json`

Kept **separate from `npc_content.json`** so persona content and behaviour flags
version independently. Defaults are all-false, so unlisted NPCs are unaffected.

```json
{
  "schema_version": 1,
  "npcs": {
    "old_lady": {
      "can_guide": true,
      "guide_scope": ["policeStation", "park", "town", "konbini"],
      "guide_style": "elder_polite",
      "walk_speed": 18,
      "can_escort": true,
      "escort_reason": "frail",
      "can_carry_for_player": false
    },
    "20": {
      "can_guide": true,
      "guide_scope": ["policeStation", "town", "station", "hospital"],
      "guide_style": "formal",
      "walk_speed": 28,
      "can_escort": false,
      "can_carry_for_player": true,
      "porter_capacity": 2
    },
    "13": { "can_guide": true, "guide_scope": ["station", "town"], "guide_style": "casual", "walk_speed": 26 }
  }
}
```

`guide_style` selects a line pack rather than scripting each NPC — voice variety
for free.

### 6.2 `common/content/guide_routes.json` (optional, hero routes only)

A* on the `collisions` layer works, but hand-authored polylines make guides use
sidewalks and crosswalks instead of hugging walls. Author these for the 10–15
most-walked routes; everything else falls back to A*.

```json
{
  "schema_version": 1,
  "routes": [
    {
      "id": "route.park_to_police",
      "from": { "zone": "town", "near": "park" },
      "to": { "zone": "policeStation", "anchor": "spawn:default" },
      "legs": [
        { "zone": "town",
          "waypoints": [
            { "x": 2448, "y": 1152 },
            { "x": 2880, "y": 1104, "say": "line.turn_right" },
            { "x": 3456, "y": 1104, "crossing": true, "say": "line.watch_cars" },
            { "x": 4200, "y": 768,  "say": "line.landmark_ahead", "landmark": "policeStation" },
            { "x": 4621, "y": 680,  "gate": "gate_door_police-station" }
          ] },
        { "zone": "policeStation",
          "waypoints": [ { "x": 697, "y": 487 }, { "x": 688, "y": 420, "say": "line.arrived" } ] }
      ]
    }
  ]
}
```

Coordinates above are the real ones in this repo: park is at `2448,1152`
(`world_locations.json`), the town-side door object `door_police-station` sits at
`4621,680` (`tokyo_city.tmj`), the interior `spawn:default` is `697,487`
(`police-station.json`), and Officer Yamada (`npc_id: "20"`) stands at `688,384`
(`npc_locations.json`).

### 6.3 `<lang>/content/guide_lines.json`

```json
{
  "schema_version": 1, "language": "ja",
  "styles": {
    "formal": {
      "line.accept":       { "jp": "はい、ごあんない します。", "en": "Yes, I'll show you the way." },
      "line.wait":         { "jp": "こちらです。おまちしますよ。", "en": "This way. I'll wait." },
      "line.turn_right":   { "jp": "つぎの かどを みぎです。", "en": "Right at the next corner." },
      "line.watch_cars":   { "jp": "くるまに きを つけて ください。", "en": "Watch for cars." },
      "line.landmark_ahead": { "jp": "あれが {landmark_jp} です。", "en": "That's the {landmark_jp}." },
      "line.gate":         { "jp": "ここから はいります。", "en": "We enter here." },
      "line.arrived":      { "jp": "つきました。こちらが {dest_jp} です。", "en": "We've arrived." }
    },
    "casual":       { "line.wait": { "jp": "こっち こっち！", "en": "This way!" } },
    "elder_polite": { "line.wait": { "jp": "ゆっくりで いいのよ。", "en": "No rush, dear." } }
  }
}
```

`{landmark_jp}` / `{dest_jp}` interpolate from `world_locations.json` `name_jp` —
so adding a location automatically gives guides something to say about it.

### 6.4 `common/content/companion_tuning.json`

| Key | Default | Tiles (48 px) | Meaning |
|---|---:|---:|---|
| `resume_radius` | 144 px | 3 | Close enough — guide resumes walking |
| `wait_radius` | 240 px | 5 | Guide stops and calls out |
| `recall_radius` | 480 px | 10 | Guide walks back toward the player |
| `teleport_radius` | 900 px | ~19 | Off-screen warp behind the player |
| `arrive_radius` | 96 px | 2 | Destination reached |
| `guide_speed_factor` | 0.9 | — | Fraction of player speed |
| `nudge_interval_s` | 8 | — | Time between "this way" calls |
| `nudge_max` | 3 | — | Then go quiet (anti-nag) |
| `blocked_timeout_s` | 3 | — | Before unstick |
| `offcamera_timeout_s` | 4 | — | Before catch-up warp |
| `session_timeout_min` | 15 | — | Auto-dismiss |
| `crossing_look_s` | 0.6 | — | Per-direction look at crossings |

## 7. The language layer (this is the point)

A guide that just walks is a convenience feature. A guide that *narrates* is a
listening lesson that the player asked for.

**Three guidance levels**, selected by player level or difficulty setting:

| Level | Behaviour | Skill practised |
|---|---|---|
| **Lead** (lvl 1–8) | Walks the whole way, narrates turns as they happen, waits forever | Passive exposure to direction words |
| **Verbal + wait** (lvl 9–18) | Walks, but says the *next* instruction **before** turning and waits for the player to move first | Comprehension under mild pressure |
| **Verbal once** (lvl 19+) | Gives the full route in Japanese once, then **does not walk**. Player navigates alone; can ask 「もういちど おねがいします」 (limited) | Real navigation from listening |

Vocabulary surfaced naturally: みぎ・ひだり・まっすぐ・つぎの かど・となり・
まえ・うしろ・わたる・のぼる, plus every `name_jp` in `world_locations.json`.

**Arrival check** (optional, +XP, never blocking): 「ここは どこ ですか」 answered
with the location's `name_jp`. Reuses the existing checkpoint `matches[]`
mechanism — no new dialogue tech, same as the carry hand-over.

**Ask-again** is itself content: 「すみません、もういちど おねがいします」 is one of
the most useful real-world phrases a learner can own, and this feature is the
only place a game can make them *want* to say it.

## 8. Integration with existing missions

Zero-touch by design (§2). Optionally, a **guide overlay** file can nominate a
recommended guide for specific nodes so the right NPC offers help at the right
moment — still non-blocking, still no mission edits:

```json
{
  "schema_version": 1,
  "min_client": "1.7.0",
  "overlays": [
    { "mission_id": "lost_purse_report", "node_idx": 2,
      "offer_guide_from": "old_lady", "destination": "policeStation",
      "offer_after_seconds": 60, "blocking": false, "bonus_xp": 15 }
  ]
}
```

Reading that against the real mission: at node 2 ("Go to the police station
(こうばん) and report it"), if the player is still wandering after a minute, Hana
offers to walk them there. Her dialogue, the node's text, the completion rule and
the XP are all untouched. The mission's *context* — an old lady who lost her
purse — is not just preserved, it is **strengthened**, because she now walks with
you.

### Worked example: the request's own scenario, end to end

1. Player is on `lost_purse_report`, node 2, standing in the park.
2. Player says 「こうばんは どこですか」 to Hana (`old_lady`, town @ `2448,1152`).
3. Keyword match `こうばん` + `どこ` → guide request; +XP for asking in Japanese.
4. Hana: 「はい、ごあんない します。ゆっくりで いいのよ。」 → `Leading` on
   `route.park_to_police`.
5. At `3456,1104` (`crossing: true`) she stops, looks left, looks right, says
   「くるまに きを つけて」, waits until the player is within 5 tiles, crosses.
6. Player stops to talk to someone → she enters `Pausing` at the last waypoint,
   turns, bubbles 「ゆっくりで いいのよ」, arrow points onward. She does not
   continue without the player.
7. At `4621,680` she stops beside `door_police-station`: 「ここから はいります」 and
   waits indefinitely.
8. Player enters. Zone `policeStation` loads; Hana fades in at `spawn:default`
   (`697,487`) one step behind.
9. She walks to `688,420`, gestures at Officer Yamada (`npc_id: "20"` @ `688,384`):
   「つきました。こちらが こうばん です。」
10. Arrival check: 「ここは どこ ですか」 → 「こうばん です」 → +15 XP, +friendship.
11. Node 3 (`talkToNpc`, Officer Yamada) proceeds **exactly as authored today**.

Not one byte of `missions.json` changed.

## 9. Failure modes and their answers

| Failure | Answer |
|---|---|
| Player runs ahead of the guide | Guide keeps its route; if the player reaches the destination first, guide congratulates and dismisses. Never a penalty. |
| Player leads the guide somewhere else | Guide follows (never abandoned), re-routes from wherever they end up. |
| Guide clips a wall / gets stuck | Non-blocking collision + 3 s `Unstick` + off-camera `CatchUp` warp. |
| Zone is level-locked | `VerbalOnly` + explains the gate's `required_level`. |
| Player quits mid-guide | Companion state is session-scoped; on reload the NPC is back on its patrol path, and the offer can be repeated. |
| Two guides requested | Only one active companion of role `guide`; requesting a second politely dismisses the first. |
| Guide NPC also has a patrol path | Patrol is suspended for the session and restored on dismissal. |
| Player asks a guide to a place they've never discovered | Allowed only if it's the active mission's `location_id`; otherwise 「まだ しらない ばしょね」. |

## 10. Phasing

| Phase | Scope |
|---|---|
| C0 | Session-scoped companion entity + nav grid from the `collisions` layer |
| C1 | `guide` role: Leading / Pausing / Resume / Arrived + `npc_capabilities.json` |
| C2 | Gate handoff (`AtGate` → `ZoneHandoff`), crossings, `guide_routes.json` for hero routes |
| C3 | Line packs, turn narration, arrival check, in-language requests |
| C4 | `escort` role (breadcrumb following), stuck detection, guide overlays |
| C5 | Guidance levels (Lead → Verbal+wait → Verbal once), pets |

## 11. Open questions for the team

1. Is there already a session-scoped entity registry that survives zone loads, or
   is every actor rebuilt per zone? C0 depends on the answer.
2. Do NPC `walk.path` loops pause during dialogue today? The same suspend hook is
   what the companion needs.
3. How is "discovered location" tracked in the save file? Guide scope filtering
   (§3) and the "place you've never been" rule depend on it.
4. Should a guide carry the player's items (`can_carry_for_player`, a porter)?
   It ties both systems together nicely, but it needs the carry anchor system on
   NPC atlases too — cheap, since the anchor table is character-agnostic.
