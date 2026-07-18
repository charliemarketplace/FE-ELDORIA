# LT content authoring guide — for programmatic / AI editing

**Audience: an LLM (or human) starting with zero context.** This document is
self-contained: it explains what this repo is, where every kind of game data
lives, how the pieces reference each other, how to verify your changes, and
how to discover valid values instead of guessing. All facts below were
verified against the actual files on 2026-07-08; paths are given so you can
re-verify anything.

> ⚠️ **This doc predates the Eldoria fork and describes the sibling `lt_web`
> project (running *The Lion Throne*), which this repo (`Eldoria/`) was
> cloned from.** The JSON data model, cross-reference rules, and
> edit→test→rebuild workflow described here apply unchanged. But concrete
> Lion-Throne-specific facts and numbers (13 levels, 243 events, the demo
> chapters `DEBUG`/`TRIAL`/`TOWN`/`RIVER`, `title`/`game_nid`) describe the
> *other* project's content, not Eldoria's. Eldoria has 7 levels (`CAPITAL`,
> `S1`, `S2`, `SHUB`, `S3`, `S4`, `S5`) and 54 events — re-verify any number
> against the live files in `lion_throne.ltproj/game_data/` rather than
> trusting this doc.

## 0. Orientation — what you are looking at

This repo (`lt_web/`) is a **browser (WebAssembly) build of the Lex Talionis
(LT) engine** — a Python/pygame Fire-Emblem-style tactics engine — running a
complete custom fangame, *The Lion Throne*. The project goal: game content
that an AI can create/edit by writing JSON, playable in a browser.

Layout of this repo:

| path | what it is |
|---|---|
| `main.py` | pygbag entry point + WASM shims (threading, save persistence, boot logging, `?level=` jump) |
| `app/` | engine source (LT-Maker build 83ddbf13 = release 2025.03.13a); no editor code |
| `lion_throne.ltproj/` | **the game — all content you would edit lives here** |
| `lt.tmpl` | custom pygbag HTML template (controls card, save export buttons) |
| `web_config.json` | `music_base_url` (null = silent; audio is stripped from this build) |
| `smoke_test.py` | native headless load test — run this after any data edit |
| `README.md` | build/run commands and web-specific engine modifications |
| `AUTHORING_CASE_STUDY.md` | the verified end-to-end authoring process (discover → author → smoke test → rebuild → headless verify → commit), with worked examples and a pattern catalog |

Sibling directories on this machine (outside this git repo, useful for
comparison but do not edit them as part of web work):

- `../lt_editor/lt_editor/` — the LT editor distribution, including
  `default.ltproj` (the Sacred Stones demo game, 7 levels). Same engine,
  different game, and stored in the *chunked* layout (see §1).
- `../LT_Engine/lion-throne/lt_engine/` — the desktop distribution
  `lion_throne.ltproj` was copied from (that copy still has its audio).

**Key architectural fact:** a game is pure data — JSON manifests + PNG
sheets + (optional) OGG audio inside a `.ltproj` directory. There is no
compile step for content. The engine loads it at boot via
`app/data/resources/resources.py` (`RESOURCES.load`) and
`app/data/database/database.py` (`DB.load`); see `main.py` lines ~160-195
for the exact boot sequence.

## 1. The .ltproj data model

### 1.1 Two on-disk layouts

`lion_throne.ltproj/metadata.json` contains `"as_chunks": false` →
**monolithic**: each data type is one JSON array file. The demo
`default.ltproj` uses `"as_chunks": true` → **chunked**: a directory per data
type, one JSON file per entity, plus a `.orderkeys` file listing nids in
display order. **The engine reads both layouts.**

| data | monolithic (this game) | chunked (the demo) |
|---|---|---|
| unique characters | `game_data/units.json` | `game_data/units/<Nid>.json` + `units/.orderkeys` |
| classes | `game_data/classes.json` | `game_data/classes/…` |
| items | `game_data/items.json` | `game_data/items/…` |
| skills | `game_data/skills.json` | `game_data/skills/…` |
| levels/chapters | `game_data/levels.json` | `game_data/levels/…` |
| event scripts | `game_data/events.json` | `game_data/events/…` |

Editing rules: in monolithic files, append to the array (array order = menu
display order). In chunked layouts, also append the nid to `.orderkeys`.

### 1.2 Singleton files (same in both layouts), all under `game_data/`

- `constants.json` — ~80 game-rule toggles/values. **Serialized as a list of
  `[key, value]` pairs, not a dict.** Controls mechanics like `crit`,
  `def_double`, `line_of_sight`, `auto_promote`, EXP curve, `game_nid`
  (save namespace), `title`.
- `equations.json` — combat formulas as expressions over stat names (§4).
- `stats.json` — the stat definitions themselves (HP/STR/MAG/SKL/SPD/LCK/DEF/RES/CON/MOV).
- `terrain.json`, `mcost.json` — terrain properties and movement-cost matrix (§5).
- `weapons.json`, `weapon_ranks.json` — weapon types, triangle advantage, rank thresholds.
- `ai.json` — named AI presets (read it to see valid `ai` values for unit placements).
- `factions.json`, `teams.json`, `parties.json`, `tags.json`,
  `difficulty_modes.json`, `translations.json`, `lore.json`, `support_*`.

### 1.3 Cross-reference model

Everything links by string `nid` (namespaced ID). The chain for a character
on a map:

```
levels.json placement (nid) ─→ units.json unit (klass) ─→ classes.json class
                                    │ (portrait_nid)          │ (map_sprite_nid, combat_anim_nid)
                                    ▼                          ▼
              resources/portraits/<nid>.png + portraits.json   resources/map_sprites/<nid>-stand.png etc.
```

A dangling nid usually fails at boot or on first use — `smoke_test.py`
catches boot-time breaks (§7).

## 2. Levels (chapters)

File: `lion_throne.ltproj/game_data/levels.json` — 13 entries. Anatomy of
Chapter I (`nid: "1"`), fields verbatim from the file:

```json
{
  "nid": "1", "name": "Chapter I",
  "tilemap": "Chapter 1",            // nid in resources/tilemaps/tilemap_data/tilemaps.json
  "bg_tilemap": null,
  "party": "Resistance",             // -> parties.json
  "music": {"player_phase": "Airship Thunderchild", "enemy_phase": "...", ...},
  "objective": {"simple": "Defeat Boss", "win": "Defeat Sidney",
                "loss": "Ophies dies,Any two of your units are defeated"},
  "roam": false, "roam_unit": null,
  "go_to_overworld": false, "should_record": true, "tags": [],
  "units": [ ...placements, see below... ],
  "regions": [ ...interaction hotspots, see §5.2... ],
  "unit_groups": [{"nid": "EnemyRein", "units": ["108","109","110"], "positions": {}}],
  "ai_groups": []
}
```

⚠️ **`objective` is display text only.** Actual win/loss logic is implemented
in events (§5.3) — e.g. Chapter I is won by an event with trigger
`combat_end`, condition `game.check_dead('Sidney')`, body `win_game`.

Unit placements (the `units` array) come in two flavors:

- **Unique** (`"generic": false`): `{"nid": "Ophie", "team": "player",
  "ai": "None", "starting_position": [3, 7], "starting_traveler": null, ...}`
  — references `units.json` by nid; stats/items come from there.
- **Generic** (`"generic": true`): self-contained enemy/NPC —
  `{"nid": "101", "klass": "Archer", "level": 1, "faction": "Soldier",
  "starting_items": [["Willow Bow", false]], "starting_skills": [],
  "team": "enemy", "ai": "Defend", "starting_position": [16, 4], ...}`.
  Stats are rolled from the class at that level. The bool in
  `starting_items` pairs = droppable. **All rank-and-file enemies are these;
  adding one touches only the level entry.**

`unit_groups` name sets of placed units so event commands can move/spawn
them together (reinforcements). `team` values come from `teams.json`:
`player`, `enemy`, `enemy2`, `other` (= neutral/green).

**Minimum new level** = a tilemap nid (reuse an existing one to start), a
`levels.json` entry, a `level_start` event, and win/lose events. Chapter
order/flow: the next chapter is set by event command `set_next_chapter` or
follows array order at `win_game`.

## 3. Characters (units, enemies, neutrals)

### 3.1 Unique units — `game_data/units.json` (28 entries)

Verbatim structure (Ophie, the lord):

```json
{
  "nid": "Ophie", "name": "Ophie", "desc": "A strong-hearted renegade...",
  "variant": "", "level": 1, "klass": "Myrmidon", "tags": ["Lord"],
  "bases":   {"HP": 12, "STR": 3, "MAG": 1, "SKL": 5, "SPD": 7, "LCK": 2, "DEF": 1, "RES": 1, "CON": 5, "MOV": 5},
  "growths": {"HP": 105, "STR": 55, ...},        // percent chance per level-up
  "stat_cap_modifiers": {},
  "starting_items": [["Iron Sword", false]],      // [item_nid, droppable]
  "learned_skills": [],                           // personal skills: [[level, skill_nid], ...]
  "wexp_gain": {"Sword": [true, 8, null], "Lance": [false, 0, null], ...},
  "alternate_classes": [], "portrait_nid": "Ophie", "affinity": null,
  "unit_notes": [], "fields": []
}
```

`wexp_gain` per weapon type: `[usable?, starting_wexp, cap]`; wexp thresholds
for ranks D/C/B/A/S are in `weapon_ranks.json`. Enemies/bosses/neutrals are
not a separate concept — a boss is typically a unique unit placed with tag
`Boss` and team `enemy`.

### 3.2 Classes — `game_data/classes.json`

Classes carry the other half of a character: `bases`/`growths`/`max_stats`
contributions, `movement_group` (row in `mcost.json`), promotion data
(`promotes_from`, `turns_into`, `promotion` stat gains, `tier`, `max_level`),
class `wexp_gain`, class `learned_skills` (e.g. Myrmidon:
`[[1, "TLT_Riposte"], [5, "TLT_Vantage"], [8, "Feat"]]`), and the art links:

- `map_sprite_nid` → `resources/map_sprites/<nid>-stand.png` and
  `<nid>-move.png` (team recolors are automatic via palettes)
- `combat_anim_nid` → `resources/combat_anims/<nid>-<WeaponAnim>.png`
  (battle animations; **optional** — if missing, combat resolves on the map,
  no crash)

### 3.3 Art assets for a character (all under `lion_throne.ltproj/resources/`)

| asset | files | manifest |
|---|---|---|
| dialogue portrait | `portraits/<Nid>.png` (96×80-grid sheet: face, chibi, blink+smile mouths) | `portraits/portraits.json` — entry with `blinking_offset`/`smiling_offset` `[x, y]` |
| map sprite | `map_sprites/<Class>-stand.png`, `<Class>-move.png` | `map_sprites/map_sprites.json` |
| battle anim | `combat_anims/<Class>-<Anim>.png` | `combat_anims/combat_anims.json` |
| icons (items/skills) | `icons16/`, `icons32/`, `icons80/` sheets | referenced by `icon_nid` + `icon_index` [col, row] |

**Cheapest new character**: new `units.json` entry using an *existing* class
(inherits map sprite + battle anim) + an existing or new portrait + a
placement in a level. Only genuinely new art requires PNG work.

## 4. Items, skills, and combat math

### 4.1 Items — `game_data/items.json` (102 entries)

An item = `nid/name/desc` + icon ref + **a list of `[component_nid, value]`
pairs**. The complete Iron Sword:

```json
"components": [
  ["weapon", null], ["target_enemy", null], ["level_exp", null],
  ["damage", 3], ["hit", 90], ["weapon_type", "Sword"], ["weapon_rank", "D"],
  ["weight", 3], ["value", 450], ["min_range", 1], ["max_range", 1],
  ["uses", 45], ["uses_options", {"lose_uses_on_miss": false, "one_loss_per_combat": false}]
]
```

Component implementations: `app/engine/item_components/*.py` (181 component
types: weapon, usable, aoe, targeting, exp, special...). Each is a small
class declaring `nid`, a value type, and hook methods the combat engine
calls. A staff, a tome, a potion, a brave/effective/siege weapon are all
just different component combinations. **New items from existing components
= JSON only, zero code.**

### 4.2 Skills & statuses — `game_data/skills.json` (118 entries)

Same component pattern; implementations in `app/engine/skill_components/*.py`.
Real examples from this game:

```json
"Canto":        [["class_skill", null], ["canto", null]]
"TLT_Riposte":  [["dynamic_damage", "3 if (mode == 'defense') else 0"], ["class_skill", null]]
"TLT_Poison":   [["stat_change", [["STR",-2],["MAG",-2],["SKL",-2],["SPD",-2],["DEF",-2],["RES",-2]]],
                 ["unit_anim", "MapPoison"], ["time", 4], ["negative", null]]
"Regeneration": [["regeneration", 0.3], ["class_skill", null]]
```

Note `TLT_Riposte`: component values can be **Python eval strings** with
combat context (`mode`, `unit`, `target`, `item`) — conditional combat
bonuses are pure data. Statuses (poison, stun, buffs) are just skills with
`time`/`negative` components. Skills attach via class `learned_skills`,
unit `learned_skills`, terrain (§5.1), item components (`status_on_hit`),
or the event command `give_skill`.

### 4.3 Combat math — `game_data/equations.json` + `app/engine/combat_calcs.py`

**The stat formulas are data**, evaluated over stat names. Lion Throne:

```json
{"nid": "HIT",   "expression": "SKL*3 + LCK"}
{"nid": "AVOID", "expression": "SPD*3 + LCK"}
{"nid": "DAMAGE","expression": "STR"}   ... etc
```

Resolution pipeline in `compute_hit` (`app/engine/combat_calcs.py:357`):
equation HIT + item `hit` component + item dynamic hooks (effectiveness)
± weapon triangle (`weapons.json` advantage tables) + support bonuses
− defender's AVOID ± skill dynamic hooks (`dynamic_accuracy`/`dynamic_avoid`),
clamped 0-100. `compute_damage` (line ~456) is analogous with
DAMAGE/DEFENSE vs MAGIC_DAMAGE/MAGIC_DEFENSE chosen by the item's components.
Doubling threshold is itself an equation (`SPEED_TO_DOUBLE`). Difficulty
scaling: `difficulty_modes.json` (Hard/Lunatic/Grandmaster enemy bonuses).

## 5. Maps, terrain, interactions, win conditions

### 5.1 Tilemaps & terrain

`resources/tilemaps/tilemap_data/tilemaps.json` — per map: `nid`, `size`
`[w, h]`, `tilesets` used (PNGs in `resources/tilesets/`), and `layers`, each
with a `terrain_grid` (`"x,y": terrain_nid`) plus a sprite grid. Layers can
be shown/hidden by event commands (destroyed bridge, opened wall).
`terrain_nid` → `game_data/terrain.json`: name, avoid/def bonuses, movement
class, and optionally an **attached skill nid** — forts heal because the
terrain grants a regeneration-style skill. Movement costs:
`game_data/mcost.json` matrix (terrain movement class × unit
`movement_group`).

A brand-new map does **not** require per-tile art: a "tileset" can be one
full-map PNG whose sprite grid maps every cell 1:1 (see the Riverhollow
pipeline in `AUTHORING_CASE_STUDY.md`, including generating the image with
an AI image model). ⚠️ The two resource manifests (`tilesets.json`,
`tilemaps.json`) are LF-terminated, unlike `game_data/*.json` (CRLF).

### 5.2 Regions — interaction hotspots (defined per level, in the level entry)

```json
{"nid": "House1", "region_type": "event", "position": [12, 3], "size": [1, 1],
 "sub_nid": "Visit", "condition": "unit.team == 'player'",
 "only_once": true, "interrupt_move": false, "time_left": null}
```

`region_type: "event"` + `sub_nid` = an interaction verb: the engine shows a
menu option named `sub_nid` to a unit standing in the region, and selecting
it fires an event whose `trigger` equals that sub_nid. Sub_nids used in this
game: `Visit`, `Chest`, `Door`, `Switch`, `Search`, `Armory`, `Vendor`,
`Seize`, `Escape`, `Secret`. Other region types: `status` (grants a skill
while inside), `formation` (prep-screen deployment slots), `time` (expires).

### 5.3 Events — the actual game logic

`game_data/events.json` — 243 entries in `lt_web`/Lion Throne, 54 in Eldoria
(re-count via `len(json.load(open(...)))` rather than trusting either number).
Fields:

```
nid, name, trigger, level_nid (null = fires in any chapter),
condition (Python eval string), _source (the script: list of "command;arg;arg" lines),
only_once, priority
```

⚠️ **The script lives in `_source`** (list of semicolon-delimited command
lines). The `commands` field is a legacy serialization and is typically an
empty list — write `_source`.

Real examples from this game:

```
# Win condition — nid "1 WinGame", trigger: combat_end, level_nid: "1",
#                 condition: game.check_dead('Sidney')
win_game

# Loss condition — trigger: combat_end, condition: len(game.get_units_in_party()) < 3
alert;You have lost too many members of your party.
if;game.game_vars.get('_current_turnwheel_uses', 0) > 0
activate_turnwheel
else
lose_game
end

# House visit — nid "1 House", trigger: Visit (fired by region House1)
transition;Close
change_background;House
multi_add_portrait;Man4;Left;{unit};Right
speak;Man4;Hmmm... You're fighting the Empire?|Take this.
give_item;{unit};Hand Axe
has_attacked;{unit}
```

Trigger vocabulary (~40, defined in `app/events/triggers.py`; counts are this
game's usage): `turn_change` (63), `unit_death` (30), `combat_start` (22),
`combat_end` (16), `level_start` (14), `level_end` (11), region sub_nids
(`Visit` 12, `Door` 9, ...), `on_talk` (7), `on_base_convo`, `on_turnwheel`,
`unit_wait`, `unit_level_up`, `on_startup`, etc. Conditions and `{brace}`
interpolations eval with `game`, `unit`, and helpers like `check_pair(...)`
in scope.

Event command vocabulary: **208 commands**, defined with docstrings in
`app/events/event_commands.py` — dialogue (`speak`, portraits, backgrounds),
camera, unit spawning/moving (works with level `unit_groups`), map layer
changes, shops, `give_item`/`give_skill`/`give_exp`, variables
(`game_var`/`level_var`), flow control (`if`/`elif`/`else`/`end`), chapter
flow (`win_game`, `lose_game`, `set_next_chapter`, `activate_turnwheel`).

## 6. Discovering valid values (do this instead of guessing)

| you need | where to look |
|---|---|
| all item component nids | grep `nid = '` in `app/engine/item_components/*.py` (181 hits; class docstring/`desc` explains each, `expose` shows the value type) |
| all skill component nids | same pattern in `app/engine/skill_components/*.py` |
| all event commands + arg signatures | `app/events/event_commands.py` — each class: `nid`, `keywords`, `optional_keywords`, docstring |
| all event triggers | `app/events/triggers.py` — each class docstring says when it fires and what's in scope |
| valid AI preset names | `game_data/ai.json` nids |
| valid team / faction / tag / party nids | `game_data/teams.json`, `factions.json`, `tags.json`, `parties.json` |
| valid terrain nids & movement classes | `game_data/terrain.json`, `mcost.json` |
| valid weapon types/ranks | `game_data/weapons.json`, `weapon_ranks.json` |
| existing icon sheets & indices | `resources/icons16/` etc.; copy `icon_nid`/`icon_index` from a similar existing item/skill |
| condition-eval helpers (`game.*`, `check_pair`...) | `app/events/event_functions.py` and `app/engine/query_engine.py`; or copy patterns from existing events |

When in doubt, **find the closest existing entity and copy its shape** — the
demo (`../lt_editor/lt_editor/default.ltproj`) doubles your example pool, in
per-entity chunked files that are easy to read.

## 7. Workflow: make a change and prove it works

1. **Edit** JSON in `lion_throne.ltproj/` (or add PNGs + manifest entries).
2. **Native smoke test** (seconds, catches boot-time breakage — bad nids,
   malformed JSON, missing resources):
   ```sh
   uv run --no-project --python 3.12 --with pygame-ce --with typing-extensions python smoke_test.py
   ```
3. **Rebuild the web bundle** (game data ships inside the pygbag archive —
   the browser will NOT see edits without this):
   ```sh
   uvx pygbag --build --template lt.tmpl .        # from lt_web/; output in build/web/
   uvx pygbag --ume_block 0 --template lt.tmpl .  # or: build + serve at http://localhost:8000
   ```
   (Run from the parent dir as `uvx pygbag --ume_block 0 --template lt_web/lt.tmpl lt_web` if serving alongside other work.)
4. **Jump straight to the level under test**: open
   `http://localhost:8000/?level=<nid>` (e.g. `?level=CAPITAL` or
   `?level=S1` in Eldoria; `?level=DEBUG` in the sibling `lt_web` repo) — boots
   directly into that chapter via `game_state.start_level`, skipping the
   title screen (~9 s page-load to map). Unknown nids log the valid list to
   the JS console and fall back to the title screen. Implemented in
   `main.py` (`get_url_param`).
5. **Verify in-browser, headlessly.** Boot milestones print to the JS console
   as `LT_BOOT:` lines; crashes print full tracebacks as `LT_BOOT: BOOT
   CRASH:`. Boot takes ~7 s to the engine main loop ("entering main loop").
   Drive it with Playwright (`uv run --no-project --python 3.12 --with
   playwright python <script>.py`, `channel='chrome'`, headless) or the
   chrome-devtools MCP tools: navigate, wait for the boot line, send keys,
   screenshot.
   **In-game controls for scripted playthroughs**: arrows move · S/Space/Enter
   confirm · A cancel · W info · Q cycle units · Tab start menu ·
   1/2/5 game speed ×1/×2/×5 · mouse works. Title → press Tab → menu;
   New Game → S through difficulty prompts.
6. Saves/settings persist in browser localStorage (`lt_save:*` keys) — if a
   data change makes old saves incompatible, clear them
   (`localStorage.clear()`) or bump `game_nid` awareness accordingly.

## 8. What requires code/codegen vs. JSON only

| change | needed |
|---|---|
| new/edited units, items, skills, levels, events, equations, constants, terrain — **using existing component types & event commands** | JSON edit + web rebuild. No code. |
| new PNG assets | PNG + manifest entry + rebuild |
| **new component type** or **new event command** | Python class in `app/engine/*_components/` or `app/events/event_commands.py`, then rerun codegen: `python -c "from app.engine.codegen import source_generator; source_generator.generate_all()"` — regenerates `app/engine/skill_system.py`, `item_system.py`, `app/events/python_event_command_wrappers.py`. Required because the web build sets `sys.frozen` (`main.py`) which skips runtime codegen. Then rebuild. |
| engine behavior changes | edit `app/engine/…` directly; keep the web-specific patches listed in `README.md` (async driver loop, sound fallbacks, time_scale, key defaults) intact |

## 9. Demo vs Lion Throne — why the two games feel different (all data!)

Same engine; every behavioral difference is in `game_data`. Verified diffs:

**Layout/scale**: demo is chunked, 7 levels (nids 0-5 + DEBUG), engine-format
version 2025.03.13a. Lion Throne is monolithic, 13 levels (nids 0-11 +
DEBUG), 28 unique units, 102 items, 118 skills (incl. custom `TLT_*` family
— all built from stock components), 243 events, saved by 2024.10.25a (loads
fine in this engine).

**`equations.json` diffs** (demo → Lion Throne):

| nid | demo (GBA-like) | Lion Throne |
|---|---|---|
| HIT | `SKL*2 + LCK//2` | `SKL*3 + LCK` |
| AVOID | `SPD*2 + LCK` | `SPD*3 + LCK` |
| CRIT_HIT | `SKL//2` | `SKL` |
| CRIT_AVOID | `LCK` | `LCK*2` |
| CRIT_MULT | `3` (triple dmg) | `1` (and constant `crit: false` — crits fully off) |

**`constants.json` diffs** (demo → Lion Throne), the notable ones:
`crit` true→false; `def_double` true→false (defenders never double);
`line_of_sight` false→true; `aura_los` false→true; `attack_stance_only`
false→true; `auto_promote` false→true; `enemy_leveling` Dynamic→Fixed;
`give_and_take` false→true; `convoy_on_death` false→true;
`kill_wexp`/`double_wexp` true→false; `attack_zero_dam`/`attack_zero_hit`
true→false; EXP tuning `exp_curve` 0.035→0.22, `default_exp` 11→15,
`kill_multiplier` 3.0→2.5; `overworld` true→false; `game_nid` LT→LionThrone;
`title` → "The Lion Throne".

The takeaway for authoring: **a total-conversion level of behavior change
required zero engine edits** — that is the property this whole pipeline
relies on.

## 10. Switches, layer reveals, and gated progression/loot

A recurring content pattern — "step on a switch, something elsewhere
unlocks" (a wall opens, a door opens, a chest becomes reachable, a boss
event arms) — is not a single engine feature. It's the same three building
blocks from §5.2/§5.3 (region → event → world-state mutation) composed
twice: once for the trigger, once for whatever downstream thing checks the
resulting state. There is no dedicated "Switch" mechanic in the engine;
`Switch` is just a conventional `sub_nid` string, same as `Visit` or
`Search`.

### 10.1 The two gating flavors used in this project

**A. Layer-reveal gating** (terrain literally changes) — worked example:
`S3` ("The Last Reliquary"). The tilemap prefab
(`resources/tilemaps/tilemap.json`, nid `"Chapter 3"`) has extra layers
beyond `base`, each with a `terrain_grid` that overrides specific tiles when
shown: `SwitchWest`/`SwitchNorth`/`SwitchSouth`/`SwitchCenter` (each turns
one or two `Wall` tiles into passable `Floor`/`Stairs` elsewhere on the map,
plus redraws the switch's own tile as "activated"), `DoorWest`/`DoorEast`
(same idea, opens a `Door` tile), and `ChestWest`/`ChestNorth`/`ChestSouth`/
`ChestCenter` (sprite-only, no terrain change — purely a "chest is here"
decoration layer; the underlying `Chest` terrain tile is already part of
`base` and is walkable from level start, it's just unreachable until a wall
opens). All layers start with a `visible` flag in the tilemap prefab; a
level event calls `show_layer;<LayerNid>` to flip it on permanently (there's
also `hide_layer` to flip one off — e.g. for a bridge that burns down).

The region + event pair, once per switch:

```json
// levels.json, S3's "regions" list
{"nid": "SwitchWest", "region_type": "event", "position": [2, 9], "size": [1, 1],
 "sub_nid": "SwitchWest", "condition": "unit.team == 'player'",
 "time_left": null, "only_once": true, "interrupt_move": false}
```
```
# events.json, level_nid "S3", trigger "SwitchWest"
show_layer;SwitchWest
speak;Iska;The wall gave way. There's a path through, west.
```

Then a second, independent region+event sits on the now-reachable chest
tile itself and hands out the loot on visit — it needs no extra gating
condition, because the tile is *physically* unreachable until the switch
fires (see §10.2 on proving that):

```json
{"nid": "ChestWest", "region_type": "event", "position": [2, 12], "size": [1, 1],
 "sub_nid": "ChestWest", "condition": "unit.team == 'player'",
 "time_left": null, "only_once": true, "interrupt_move": false}
```
```
# events.json, level_nid "S3", trigger "ChestWest"
give_item;{unit};Silence
speak;Sable;A relic, still humming. Careful with it.
```

S3 has four independent switch→chest pairs (West/North/South/Center) plus
two separately-authored `Door` layers gating the critical path — read
`S3`'s full `regions` list and its `S3 Switch*`/`S3 Chest*` events for all
four worked examples side by side.

**B. `game_var` gating** (no terrain change, just a flag) — worked example:
`S5`, regions `Valve1`/`Valve2`/`Valve3` (`region_type: "event"`,
`only_once: true`). Each fires an event that sets a boolean
(`game_var;valve1;1`), then checks all three together:

```
game_var;valve1;1
speak;Iska;Valve's open. Pressure's already dropping on this side.
if;game.game_vars.get('valve1') and game.game_vars.get('valve2') and game.game_vars.get('valve3')
speak;Rowan;All three are open. To the core, before Voss cracks it.
end
```

A separate region (`VaultCore`, sub_nid `Quench`) checks the same three
`game_vars` in its own `condition` string to decide whether interacting
with it should succeed. Use this flavor when the "unlock" isn't a physical
wall — a scripted event, a boss becoming vulnerable, a chapter objective
flipping — or when N switches need to jointly gate one thing in an order
-independent way (raw layer-reveals can do this too by all targeting the
same layer, but a shared `game_var` check is clearer to read).

Nothing stops combining both in one switch: `S3`'s `SwitchCenter` region
shows a single layer that breaches two separate walls at once (a `show_layer`
layer can have more than one tile in its `terrain_grid`), and a `game_var`
could additionally be set there if some other event later needs to know
"has the center switch been thrown" without re-deriving it from terrain.

### 10.2 Don't ship an unreachable switch or a soft-lock — prove reachability first

The bug this section exists to prevent: S3 originally shipped with the
`Switch`/`Chest` art layers in place but **zero regions or events** wired
to them — a player could see the switches and chests but nothing happened,
and the chests were unreachable. The fix wasn't guessing at plausible tile
coordinates; it was running an actual reachability simulation over the raw
`terrain_grid` data before authoring a single region, using each tile's
`mtype` from `game_data/terrain.json` (`Wall` = impassable, everything else
= passable for a basic ground unit — good enough for placement purposes;
it ignores movement-type-specific costs, which don't matter for a yes/no
reachability check):

```python
import json
from collections import deque

tm = json.load(open('lion_throne.ltproj/resources/tilemaps/tilemap.json'))
terrain = json.load(open('lion_throne.ltproj/game_data/terrain.json'))
mtype = {t['nid']: t.get('mtype') for t in terrain}
chapter = next(t for t in tm if t['nid'] == '<TilemapNid>')
layers = {l['nid']: l for l in chapter['layers']}
W, H = chapter['size']

def build_grid(active_layers):
    grid = {}
    for lname in ['base'] + active_layers:
        for k, v in layers[lname].get('terrain_grid', {}).items():
            x, y = map(int, k.split(','))
            grid[(x, y)] = v
    return grid

def walkable(grid, pos):
    return grid.get(pos) is not None and mtype.get(grid[pos]) != 'Wall'

def bfs(grid, start):
    seen, q = {start}, deque([start])
    while q:
        x, y = q.popleft()
        for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
            np = (x+dx, y+dy)
            if 0 <= np[0] < W and 0 <= np[1] < H and np not in seen and walkable(grid, np):
                seen.add(np); q.append(np)
    return seen
```

Use it to check, for every switch→gated-thing pair you're about to author:
1. **The switch's own trigger tile is reachable with nothing else
   triggered** (`bfs(build_grid([]), start_pos)` — or whatever's already
   guaranteed shown, e.g. `Door*` layers here since those open
   unconditionally at `level_start`) — otherwise you've authored an
   unreachable switch, a soft-lock.
2. **The gated tile is *not* reachable before the switch fires** — otherwise
   the "puzzle" does nothing and the switch is inert set dressing.
3. **The gated tile *is* reachable once only that one switch's layer is
   shown** — confirms the switch actually controls that gate and isn't
   coincidentally already open some other way, and that you haven't
   accidentally required two switches when you only meant to require one
   (or vice versa — `SwitchCenter` here was deliberately required for
   `ChestCenter` alone, discoverable by noticing its two breach tiles sit
   on both sides of a fully wall-enclosed room, per §10.1).

This is cheap (milliseconds, pure Python, no game boot needed) and it's the
difference between a puzzle and a bug. Do it *before* picking tile
coordinates for regions, not after — let the reachability data tell you
where the trigger and the reward actually are, rather than eyeballing
sprite positions in the layer's `sprite_grid`.

### 10.3 After authoring: verify at runtime, not just at load time

`smoke_test.py`'s content validator (see the top-level `DBChecker` wiring)
catches dangling nid references (an event `give_item`-ing an item that
doesn't exist, a component pointing at a missing skill) but it does **not**
execute events or simulate movement — a region on the wrong tile, a
`show_layer` with a typo'd layer nid, or a wrong item nid in `give_item`
will load fine and only fail when a player actually steps there. There is
currently no automated headless test that drives a level turn-by-turn and
fires region interactions; if you're authoring a new switch/gate, the
verified way to catch this is a throwaway headless script (native, dummy
SDL driver) that boots the level via `game_state.start_level(<nid>)`,
places/moves a unit onto the trigger tile, fires the region's event the
same way the engine's region-interaction menu does (trigger nid
`on_region_interact`, see `app/events/triggers.py`), and re-checks
reachability/inventory afterward. This is slower than the static BFS check
in §10.2 (needs a real engine boot) — use the BFS check to get placement
right the first time, and a runtime script to confirm the wiring (region
sub_nid ↔ event trigger ↔ layer/item nid) actually fires end-to-end.
