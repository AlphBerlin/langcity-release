# Feature Backlog — What Else Would Make LangCity More Interesting

> Design only. Ranked by (player impact ÷ build cost), and every entry is scored
> on **what already exists in this repo** — the cheapest good feature is the one
> whose art and data are already committed.

## Tier A — high impact, assets already in the repo

### A1. Memory Rifts (the map is already full of them)

`tokyo_city.tmj` has a `rifts` object layer with **23 placed rift objects**, and
`images/objects/spr_memory_rift.png` exists. Nothing in the mission data uses
them. That is a whole mechanic sitting unclaimed.

**Design:** a rift is a spaced-repetition spawn point. Walking near one opens a
15-second challenge built from the player's **due SRS items** — words they
learned and are about to forget, drawn from `ja/content/curriculum/levels/*`.
Clear it → the rift closes for its cooldown and the word's interval extends.
Ignore it → the rift visibly darkens over days, and a "haze" shader dims that
block of the city until the player clears it. **The city literally decays where
your vocabulary is decaying**, and it repairs when you review. It is the single
strongest idea available here: it converts an SRS obligation into a place.

*Cost:* low (art + placement done). *Needs:* SRS due-list query, one challenge UI.

### A2. Friendship levels that change how NPCs speak

`hud/meter_friendship_empty|full` already exist and nothing drives them.

**Design:** each NPC has a friendship track (0–5). Level gates **register of
speech**, not just gifts: a stranger speaks formal keigo (〜ですか / いらっしゃいませ),
a friend switches to plain form (〜する？ / うん), and a close friend uses
contractions and slang. Learners get the single hardest thing to teach in a
classroom — **when to switch politeness level** — as an emotional, earned
progression instead of a grammar table. Friendship rises from missions, carry
deliveries (see `carry-system.md` §5.5), gifts, and repeat visits.

*Cost:* low-medium (dialogue variants per NPC — but `npc_content.json` already
has `persona_prompt`, so variants can be prompt-level, not hand-written).

### A3. Daily shifts / part-time jobs (アルバイト)

Interiors exist for konbini, ramen, cafés, supermarket, hospital, office,
and `hud/badge_daily_quest` is in the kit.

**Design:** a repeatable 3-minute shift at a workplace the player has friendship
with. Konbini: listen to a customer's order, pick the right item, state the
price, take payment. Ramen: take orders and carry bowls (**this is where the
carry system pays rent**). Shifts pay coins, are the main money sink/faucet, and
are pure listening-comprehension drills with a diegetic wrapper. Difficulty
scales with the player's curriculum level — customers speak faster and drop the
politeness scaffolding.

*Cost:* medium. *Highest retention-per-yen item on this list* — it is the daily
loop the game currently lacks.

### A4. Time of day, weather and NPC routines

`npc_locations.json` already supports **multiple placements per NPC** and patrol
paths, and `sprites/lighting/` has a cone-light atlas.

**Design:** a 24-minute day cycle. NPCs move between placements by hour (Sato is
at the konbini in the morning, the ramen shop at night). Shops open and close.
Rain changes what NPCs say and makes umbrellas a carryable item people ask you
for. This makes the city feel inhabited rather than staged, and it creates
natural scheduling vocabulary (なんじ / あさ / よる / あめ) plus a reason to return
at a different time.

*Cost:* medium (mostly data + a clock). *Warning:* gate missions so nothing ever
becomes unreachable because of the time — availability windows must be advisory.

## Tier B — strong, moderate cost

### B1. The train line (a listening exam disguised as transport)

The station interior exists and `bgm_station` is referenced.

**Design:** real platform announcements ("つぎは しんじゅく、しんじゅく です")
that the player must parse to pick the right platform and get off at the right
stop. Wrong stop = you're somewhere else in the city, which is a *story*, not a
failure. Ties the map together and doubles as fast travel that the player has to
*earn* comprehension-wise. Fast travel with a spillable item is where the carry
system and this feature collide entertainingly.

### B2. Photo mode — 「これは なんですか」

**Design:** a camera. Point at anything in the world, snap it, and the game asks
you to name it. Correct names go into a personal picture dictionary that fills
up like a Pokédex. Wrong or unknown → an NPC nearby teaches it. It converts the
world art (88 named objects in the town map alone) into a vocabulary surface, and
it is the most shareable thing in the game — a photo album with Japanese captions
is a social object.

### B3. Your apartment, and furnishing it by carrying it home

`apartment`, `townhouse`, `familyHome` maps exist.

**Design:** a home the player decorates with things they buy and **physically
carry home** (see the "Moving day" errand family). Every object placed is a
labelled noun in a room they own; a "label everything" toggle turns the flat into
a self-made vocabulary poster. Home also gives the player a reason to earn coins
and a place to display achievements.

### B4. Festivals and seasons (まつり)

Temple, shrine and stadium maps exist.

**Design:** timed events — hanami in spring, summer matsuri with stalls
(carry the takoyaki!), New Year at the temple. Seasonal vocabulary, limited-time
missions, and the strongest possible reason to reopen the app on a specific day.
Runs on the same content pack pipeline: a festival is a content pack with
`active` windows.

### B5. Mistake replay — 「ことばポケット」

**Design:** every phrase the player got wrong is stored with the *scene* it
happened in. A review session replays that moment — same NPC, same room, same
question — instead of a flashcard. Contextual re-encoding is dramatically more
effective than decontextualised review, and it costs almost nothing to build
because the scenes already exist.

## Tier C — worth doing later

- **Pets** — an animal from `animalCafe` that follows you. Reuses the companion
  component (`role: pet`) at near-zero cost, and gives players a reason to walk.
- **Street notes / graffiti board** — players leave short Japanese messages at
  locations for other players to find (moderated, template-constrained). Cheap
  asynchronous multiplayer that generates learner-authored content.
- **Accent and pitch coach** — the `hud/waveform_empty|active` assets already exist. Show the
  player's pitch contour against a native model for a phrase they just said.
- **Skill tree made real** — 30 skill-tree assets exist in the UI kit and nothing
  drives them; map them to the curriculum's `skill_type` (vocab / grammar /
  listening) so progression is visible.
- **Emergency chains** — hospital + police station + embassy exist. A lost-passport
  or minor-injury chain teaches the highest-stakes real-world Japanese a visitor
  will ever need. Pairs perfectly with the guide system.
- **Bicycle** — a movement upgrade that interacts with carry (basket = +2 bulk,
  can't carry `front` items) and makes the 7776×2304 town feel navigable.

## What I would build first, and why

1. **Carry system, Tier 0 + Tier 1** — visible, cheap, and it makes the existing
   missions feel physical without touching them.
2. **Guide (C1–C3)** — it fixes a real usability problem (players lost in a
   7776 px-wide city) *and* turns it into a listening lesson. Best
   frustration-removed-per-day-of-work on the list.
3. **Memory Rifts (A1)** — the assets are already committed and the mechanic gives
   the whole game a spine: your vocabulary decay is visible in the streets.
4. **Daily shifts (A3)** — the retention loop, and the natural consumer of carry.
5. **Friendship registers (A2)** — teaches the thing textbooks can't.

Everything above composes: shifts need carry, carry needs sources, guides make
shifts findable, rifts make the map worth walking, friendship gates the shifts.
That is one coherent game, not five features.
