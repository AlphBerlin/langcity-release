# Carry System — 持ち物 (mochimono)

> Design only. No code or content changes in this document.
> Read [`README.md`](README.md) first — the additive-overlay contract (C1–C5) governs everything here.

## 1. What it is, in one paragraph

The player can physically hold things — an apple in one hand, a ramen bowl in
both arms, a delivery box on the back — and those things are **visible on the
character sprite**, slow them down, can be dropped or spilled, and are handed
over to an NPC with a spoken phrase. Carrying is the game's excuse to teach the
vocabulary Japanese learners are worst at: **object names, counters
(ひとつ / 一杯 / 一本), adjectives of state (おもい・あつい), and the
giving/receiving phrases (どうぞ / おねがいします / おまたせしました)**. It is
not a physics toy bolted onto a language game; it is a vocabulary drill with
legs.

## 2. Why it fits this codebase cheaply

- **No new character art.** Every atlas has only `idle_*` / `walk_*` (+ NPC `talk`).
  Carried objects are **separate sprites attached to the character** with a
  per-direction anchor offset and a per-direction draw order — so one 32×32 item
  sprite works on all 30+ characters, including the player. Bespoke `carry_walk_*`
  rows for the player are a **later polish item, never a dependency**.
- **No new sources.** The town map already has vending machines (`vending_3`,
  `vending_7`), 88 named objects and interior maps for konbini, supermarket, ramen.
- **No new UI kit.** `panels/inventory grid`, `hud/counter_*`, `hud/bar_energy_*`,
  `overlays/toast_*` and `hud/meter_friendship_*` already exist.
- **No mission edits.** Section 6.

## 3. Slots and the carry model

Carried ≠ inventory. **Inventory is abstract storage; carry is a physical,
visible, movement-affecting state.** They are separate systems with one bridge
(`stash`, §5.4).

| Slot | Capacity | Typical items | Notes |
|---|---|---|---|
| `back` | 1 item, bulk ≤ 3 | backpack, delivery box, rice sack, futon | Biggest speed cost, hands stay free |
| `front` | 1 item, bulk ≤ 3 | tray, cardboard box, bouquet, cat carrier | **Occupies both hands** |
| `hand_l`, `hand_r` | 1 item each, bulk ≤ 1 | apple, bottle, umbrella, konbini bag | Either hand; auto-assigned |
| `head` | 1 item, bulk ≤ 2 | tray of ramen bowls | Novelty/stunt: XP bonus, spill ×2 |

Constraint solver (trivial, evaluated on every pick-up attempt):

```
front occupied      => hand_l and hand_r unavailable
hand_l or hand_r occupied => front unavailable
total_bulk = Σ bulk of all carried items
```

Failure to fit is never a silent no — the NPC or the player bubble says
「りょうてが ふさがって います」 ("my hands are full"), which is itself a
teachable phrase.

### 3.1 Draw order (the only rendering rule that matters)

The character is a top-down sprite with `pivot` bottom-center. Item sprites are
children of the character with an anchor per facing:

| Facing | `back` item | `front` item | `hand_*` item | `head` item |
|---|---|---|---|---|
| `down` (toward camera) | behind character | **in front** | in front | in front |
| `up` (away) | **in front** | behind | behind | in front |
| `left` / `right` | behind | in front | in front | in front |

That table plus a 4-entry anchor offset per item is the entire visual
integration. It is why no character sheet has to be redrawn.

## 4. Data shapes (new files, all additive)

### 4.1 `common/content/carry_items.json`

```json
{
  "schema_version": 1,
  "items": [
    {
      "id": "item.apple",
      "vocab_skill_id": "vocab.林檎",
      "display_jp": "りんご", "reading": "ringo", "display_en": "apple",
      "counter": "ko",
      "slots": ["hand_l", "hand_r", "back"],
      "bulk": 1, "weight": 1,
      "traits": ["perishable"],
      "speed_modifier": 0.0,
      "spill_rate": 0.0,
      "sprite": "assets/lang/images/objects/carry/apple.png",
      "anchors": { "down": [6, -20], "up": [-6, -20], "left": [-9, -19], "right": [9, -19] },
      "sfx": { "pickup": "sfx_pickup_soft", "drop": "sfx_drop_soft" }
    },
    {
      "id": "item.ramen_bowl",
      "vocab_skill_id": "vocab.ramen",
      "display_jp": "ラーメン", "reading": "ra-men", "display_en": "bowl of ramen",
      "counter": "hai",
      "slots": ["front", "head"],
      "bulk": 2, "weight": 2,
      "traits": ["hot", "spillable", "perishable", "fragile"],
      "speed_modifier": -0.18,
      "spill_rate": 0.9,
      "freshness_seconds": 240,
      "sprite": "assets/lang/images/objects/carry/ramen_bowl.png",
      "anchors": { "down": [0, -30], "up": [0, -34], "left": [-4, -30], "right": [4, -30] },
      "sfx": { "pickup": "sfx_pickup_dish", "drop": "sfx_break_dish" }
    }
  ]
}
```

`vocab_skill_id` is the hinge: it points at a real curriculum skill id
(`ja/content/curriculum/levels/level_*.json`), so **every second the item is
carried is trackable exposure** and every hand-over is a review event for the
existing SRS. Nothing else in the file is language-specific, so localisation is
a per-pack override of `display_*`/`reading` only.

**Watch-out found while checking the curriculum:** the food nouns this mechanic
wants are split across levels and script forms — `vocab.ramen` (L5),
`vocab.onigiri` (L3), `vocab.mizu` (L3) and `vocab.ocha` (L3) exist in kana, but
apple only exists as **`vocab.林檎` at L15** (reading りんご, gated behind
`kanji.林` / `kanji.檎`). Carry items must not drag a level-15 kanji skill into a
level-2 errand. Two options, pick one before authoring items:

1. add kana-form starter skills (`vocab.ringo`) to the low levels, and let the
   kanji skill list the kana skill as a prerequisite; or
2. let `vocab_skill_id` be a **list** — `["vocab.ringo", "vocab.林檎"]` — and have
   the carry system credit whichever skills the player has unlocked.

Option 2 is less content work and degrades gracefully; option 1 is cleaner data.
Either way, a validator rule (§9) should reject a carry item whose linked skill
sits above the level of any mission that grants it.

### 4.2 `common/content/carry_sources.json`

Where items come from in the world — binds to map objects that already exist:

```json
{
  "schema_version": 1,
  "sources": [
    { "id": "src.vending_3", "zone": "town", "object_name": "vending_3",
      "grants": ["item.tea_bottle", "item.water_bottle"], "cost_coins": 120,
      "respawn_seconds": 0, "prompt_jp": "かいますか？" },
    { "id": "src.ramen_counter", "zone": "ramen", "object_name": "counter_pickup",
      "grants": ["item.ramen_bowl"], "requires_mission_node": true }
  ]
}
```

`requires_mission_node: true` means the source is inert unless an active overlay
(§6) asked for that item — so free-roam players don't drown in props.

### 4.3 `common/content/carry_tuning.json`

One file, no magic numbers in code:

| Key | Default | Meaning |
|---|---:|---|
| `speed_floor` | `0.55` | Multiplier can never drop below this |
| `sprint_block_bulk` | `3` | Total bulk at which sprint is disabled |
| `sprint_block_traits` | `["spillable","fragile"]` | Traits that disable sprint outright |
| `stumble_speed_threshold` | `0.8` | Fraction of max speed above which a collision stumbles |
| `spill_per_stumble` | `18` | Spill % added per stumble |
| `spill_per_second_sprint` | `6` | Spill % while moving fast with a spillable |
| `spill_ruin_at` | `100` | Item ruined at this spill % |
| `energy_drain_per_bulk_min` | `1.5` | Energy points per bulk per minute |
| `pickup_card_seconds` | `1.6` | Vocabulary card shown on pick-up |

Movement: `speed = base × clamp(1 + Σ speed_modifier, speed_floor, 1.0)`.

## 5. Player-facing flow

### 5.1 State machine

```
Empty ──look at source──► PromptPickUp ──confirm──► Carrying
                                                     │
   ┌───────────── stumble / sprint ──────────────────┤
   │                                                 │
Spilling ──spill ≥ 100──► Ruined ──auto-replace──► Carrying
                                                     │
                                       reach recipient│
                                                     ▼
                                                  Handover ──phrase ok──► Delivered ──► Empty
```

- **PromptPickUp** — proximity prompt on a `carry_sources` object or an NPC
  offering an item. Shows slot preview and refuses politely if slots are full.
- **Carrying** — item drawn on the sprite; speed modifier and energy drain active;
  optional furigana label above the item (accessibility/learning setting).
- **Spilling** — spill meter appears (reuse `hud/bar_energy_*` art tinted) only
  once spill > 0, so the HUD stays quiet for non-spillable items.
- **Ruined** — item disappears with a reaction line, is **re-granted at its
  source for free**, and costs a small delivery grade — never mission failure,
  never lost progress (§8).
- **Handover** — the language beat, §5.3.

### 5.2 Pick-up = one vocabulary card

On pick-up, a 1.6 s bubble: item sprite, `display_jp` large, `reading` small,
audio playback, and a "+1 exposure" tick on the linked skill. No quiz, no
blocking — friction here would kill the loop. The quiz is at hand-over.

### 5.3 Hand-over = a `sayPhrase` in disguise

The hand-over reuses the **existing checkpoint mechanism** verbatim — same
`{aiInstruction, hint, matches[]}` shape used by all 65 `sayPhrase` nodes. No new
dialogue technology:

```json
{ "aiInstruction": "ラーメン、まだ あついですか？わたして ください。",
  "hint": "はい、どうぞ",
  "matches": ["どうぞ"] }
```

Progressive difficulty by player level, all data:

| Level band | Required utterance |
|---|---|
| 1–5 | `どうぞ` |
| 6–12 | `ラーメン です。どうぞ` (name the item) |
| 13–20 | `ラーメン **を いっぱい** どうぞ` (name + **counter**) |
| 21+ | `おまたせしました。あつい ので きを つけて ください` (polite + warning) |

**Counters are the killer app of this mechanic.** Carrying two apples and three
bowls is the only natural, non-worksheet way to make ふたつ / さんばい matter.

### 5.4 The one bridge to inventory

`stash` moves a carried item into inventory storage. Allowed unless the item has
`hot`, `spillable`, or `quest_bound`. This keeps "physical carry" meaningful
while letting players put an umbrella away.

### 5.5 Delivery grading

Score = time (30%) + spill/freshness (40%) + phrase accuracy (30%) → **S / A / B / C**.
Rewards: coins, XP, and **friendship** with the recipient (assets:
`hud/meter_friendship_empty|full`). C is still a pass. There is no fail grade.

## 6. Connecting to existing missions — three tiers, zero edits

### Tier 0 — Ambient (no mission involvement)

Carry exists in free roam. Buy tea from a vending machine, carry an apple around,
practise counters at the supermarket. This tier alone justifies the system and
touches nothing.

### Tier 1 — Overlay onto the 68 existing missions

New file `common/content/mission_carry_overlays.json`. It references missions by
id and node index and **never modifies them**:

```json
{
  "schema_version": 1,
  "min_client": "1.7.0",
  "overlays": [
    {
      "mission_id": "lost_purse_report",
      "node_idx": 2,
      "when": "node_enter",
      "grant": { "item_id": "item.report_form", "slot": "hand_r", "from": "npc:old_lady" },
      "carry_hint_jp": "とどけを もって こうばんへ",
      "on_ruin": "respawn_at_source",
      "blocking": false,
      "bonus_xp": 0
    },
    {
      "mission_id": "lost_purse_report",
      "node_idx": 4,
      "when": "node_complete",
      "consume": { "item_id": "item.report_form", "to": "npc:20" },
      "blocking": false,
      "bonus_xp": 20
    }
  ]
}
```

What this does to `lost_purse_report` (a real mission in the repo today): Hana
hands you a form, you can *see* it in your hand while you walk to こうばん, and
Officer Yamada takes it. The mission's own nodes, text and completion rules are
byte-identical. Delete the overlay file → the mission is exactly what it is now.

Guard rails, enforced by a validator (§9):

- `blocking` **must** be `false` in Tier 1. The carry state can never be a
  precondition for `goToLocation` / `talkToNpc` / `sayPhrase` completion.
- Overlays may not add or reorder nodes.
- `bonus_xp` is additive on top of the mission's `xp_reward`, capped at 25% of it.
- If the player somehow has no item at the consume node, the node still completes
  and the bonus is skipped silently.

Good Tier-1 candidates already in the repo: `lost_purse_report` (form),
konbini/ramen missions from `konbini_clerk`, `ramen_chef`, `store_server`
(shopping bag, bowl), `meet_tanaka_shrine` (omiyage gift).

### Tier 2 — New errand missions (new records only)

Appended to `world_missions[]` as `"kind": "errand"`, using two new node types.
The 68 existing missions are untouched; E0 (README) is the prerequisite.

```json
{
  "id": "ramen_delivery_first",
  "kind": "errand", "language": "ja", "min_level": 8, "active": true,
  "min_client": "1.7.0",
  "giver_npc_id": "ramen_chef",
  "title": "Hot Delivery", "summary": "Carry a bowl of ramen to the office without spilling it.",
  "xp_reward": 120, "sort_order": 70,
  "nodes": [
    { "idx": 0, "type": "goToLocation", "location_id": "ramen", "npc_id": null,
      "description": "Go to the ramen shop (ラーメンや).", "checkpoints": [], "ai_instruction": "" },
    { "idx": 1, "type": "pickUpItem", "location_id": "ramen", "npc_id": "ramen_chef",
      "item_id": "item.ramen_bowl", "slot_hint": "front",
      "description": "Take the bowl of ramen.",
      "checkpoints": [{ "aiInstruction": "あついよ！きを つけてね。", "hint": "", "matches": [] }],
      "ai_instruction": "" },
    { "idx": 2, "type": "goToLocation", "location_id": "plaza", "npc_id": null,
      "description": "Carry it to the plaza (ひろば).", "checkpoints": [], "ai_instruction": "" },
    { "idx": 3, "type": "deliverItem", "location_id": "plaza", "npc_id": "36",
      "item_id": "item.ramen_bowl",
      "grade": { "spill_max": 60, "seconds_target": 180 },
      "description": "Hand over the ramen.",
      "checkpoints": [{ "aiInstruction": "おっ、きた！ありがとう。", "hint": "おまたせしました", "matches": ["どうぞ", "おまたせ"] }],
      "ai_instruction": "" }
  ]
}
```

The recipient (`npc_id: "36"`) is an NPC that **already has a `town` placement in
`npc_locations.json`** — a new mission may only target NPCs actually placed in the
destination zone, or it must ship the placement alongside it. The gap is real:
`npc_world_manifest.json` lists `"office": ["14", "28"]`, but neither `14` nor `28`
has an entry in `npc_locations.json` — a delivery addressed to them would arrive at
an empty room.

Note that `pickUpItem` and `deliverItem` keep **the exact node envelope** already
in use (`idx`, `type`, `location_id`, `npc_id`, `description`, `checkpoints`,
`ai_instruction`) and only add `item_id` / `grade`. Any tool that reads missions
today keeps working; the new keys are ignorable.

### Tier 2 mission families worth writing

| Family | Item | Route | Language focus |
|---|---|---|---|
| Ramen run | `item.ramen_bowl` | ramen → plaza / apartment | Counters 杯, adjectives あつい |
| Konbini haul | `item.konbini_bag` | konbini → familyHome | Numbers, ぶくろ, おねがいします |
| Fruit for the shrine | `item.apple` ×3 | supermarket → templeMain | Counters つ, giving verbs |
| Moving day | `item.box` on back | apartment → townhouse | おもい, てつだって ください |
| Hospital flowers | `item.bouquet` | florist → hospital | Politeness level, おだいじに |
| Cat to the vet | `item.cat_carrier` (front) | animalCafe → hospital | Living-thing counter ひき |

## 7. Art and audio needed

| Asset | Count | Size | Notes |
|---|---:|---|---|
| Carry item sprites | ~18 to start | 32×32 (48×48 for `front` items) | Top-down, matches UI kit palette, magenta or alpha per repo convention |
| Spill/steam overlay | 2 | 32×32, 4 frames | Reuse for all spillables |
| Carry HUD chip | 3 states | 32×32 | Slot indicator; can be cut from existing `hud` kit |
| SFX | 6 | — | pickup soft/dish, drop soft/break, stumble, handover chime |
| Player `carry_walk_*` rows | 4 dirs × 4 frames | **optional, phase 3** | Polish only — the anchor system ships without it |

## 8. Anti-frustration rules (non-negotiable)

1. Carrying **never** fails a mission or rolls back a node.
2. A ruined item is re-granted free at its source; the player keeps their route.
3. Fast travel with a spillable is allowed — it costs spill %, not the item.
4. No timers on Tier-1 overlays. Timers exist only in Tier-2 errands, where the
   target time is generous (`seconds_target` is for the *grade*, not a fail).
5. Death/knockdown states do not exist; the worst outcome is a C grade.
6. Accessibility: "no-spill" toggle in settings disables spill entirely and
   keeps grading on time + phrase only.

## 9. Validator (CI, `scripts/`)

A content test in `test/scripts/` should assert, on every build:

- every `mission_id` / `node_idx` in an overlay exists in `missions.json`
- every overlay has `blocking: false`
- `bonus_xp ≤ 0.25 × mission.xp_reward`
- every `item_id` referenced anywhere exists in `carry_items.json`
- every `vocab_skill_id` exists in the curriculum for that language pack
- every `sprite` path exists in the pack
- **`missions.json` hash is unchanged from `main`** unless the commit explicitly
  declares a mission edit — the mechanical enforcement of C1

## 10. Phasing

| Phase | Scope | Ships |
|---|---|---|
| P0 | Engine E0 (unknown-node tolerance) | Client only |
| P1 | Slots, anchors, 6 items, vending/konbini sources, pick-up card | Tier 0 ambient carry |
| P2 | Hand-over checkpoints, grading, friendship reward | Tier 1 overlays on 4 existing missions |
| P3 | `pickUpItem` / `deliverItem` node types | 6 Tier-2 errand missions |
| P4 | Counters progression, spill polish, player carry animation rows | — |

## 11. Open questions for the team

1. Does the client already persist a per-session inventory the carry state can
   sit beside, or does carry state need its own save slice?
2. Should carried items survive a zone change through a door? (Design assumes
   **yes**, and that spillables take a small spill hit on stairs.)
3. Is `energy` currently spent by anything? If not, carrying is a good first
   consumer, but the refill loop (food at ramen/konbini) needs to exist first.
