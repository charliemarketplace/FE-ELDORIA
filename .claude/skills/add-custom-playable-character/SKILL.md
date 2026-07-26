---
name: add-custom-playable-character
description: Author a brand-new unique (named) character — stats, growths, personal skills, art, and how/when they physically enter a level — as distinct from generic squad filler or the recruitment/side-switch flow.
---

## 1. Feature

A designer can add a wholly new named character to the roster: a `UnitPrefab`
entry (base stats, growth rates, personal skill list, starting inventory,
portrait/affinity) that exists independently of any level, plus a per-level
placement record that says which team they belong to, where they stand, and
by what mechanism (static level data vs. a scripted event command) they
appear on the map. This is the "new party member" lever — distinct from
*generic* filler units (procedural/enemy-pool squad members, already
excluded) and from the recruitment/`change_team` side-switch mechanic
(already excluded): this skill covers defining the character and getting
them onto the map in the first place, on whichever team they start on.

## 2. Details

### 2.1 The character definition — `UnitPrefab` (one entry per unique unit)

Dataclass `UnitPrefab` in `app/data/database/units.py:12-39`. Fields and what
happens when omitted:

| Field | Meaning | Default / if omitted |
|---|---|---|
| `nid` | Unique id, referenced everywhere (events, level units) | required |
| `name`, `desc` | Display name / roster description | `None` |
| `variant` | Alternate map-sprite/combat-anim skin suffix for the unit's class | `None` (uses class's base art) |
| `level` | Starting internal level | `1` |
| `klass` | Class nid (see the class/promotion skill) | `None` — will crash lookups if unset |
| `tags` | Free-form tags (`Lord`, `Boss`, `AutoPromote`, `NoAutoPromote`, …) | `[]` |
| `bases` / `growths` / `stat_cap_modifiers` | Per-stat starting value / % growth rate / personal cap adjustment, keyed by stat nid from `stats.json` | all-`0` dicts when created via `UnitCatalog.create_new` |
| `starting_items` | `[[item_nid, droppable], ...]` | `[]` |
| `learned_skills` | Personal skills: `[[level, skill_nid], ...]`, granted when unit reaches that level | `[]` |
| `wexp_gain` | Per-weapon-type `WexpGain(usable, starting_wexp, cap)` — `usable=False` means the unit can never wield that type regardless of class | one entry per weapon type, `usable=False` |
| `alternate_classes` | Reclass options exposed to the `class_change` item component | `[]` |
| `portrait_nid` | Links to `resources/portraits/<nid>.png` + manifest entry in `portraits/portraits.json` (`blinking_offset`, `smiling_offset`, `info_offset`) | `None` — no dialogue portrait |
| `affinity` | Affinity nid (see the support/affinity skill) — `None` in every unit in this project | `None` |
| `unit_notes`, `fields` | Free-text designer notes / arbitrary key-value scripting hooks | `[]` |

A boss or a hostile unique character is **not** a separate data type —
it's the same `UnitPrefab`, just placed with `team != "player"` and often
tag `Boss` (see CONTENT_GUIDE §3.1). Making a unique character "recruitable"
mid-story is the excluded `change_team` mechanic — this skill only covers
authoring the character and placing them on whichever team they start on.

### 2.2 Per-level placement — `UniqueUnit` (`app/data/database/level_units.py:79-114`)

Each level's `units` catalog holds a `UniqueUnit` record (or a `GenericUnit`
for squad filler, out of scope here) pointing at a `UnitPrefab` by nid:

| Field | Meaning | Default |
|---|---|---|
| `team` | Which team/allegiance this unit fights for *in this level* | `None` |
| `ai` / `roam_ai` | AI preset nid for combat/free-roam | `None` (no AI script) |
| `ai_group` | Level-local AI coordination group | `None` |
| `starting_position` | `(x, y)` tile — used as the fallback position for `add_unit` (see below) if no explicit position is given | `None` |
| `starting_traveler` | Another unit nid that enters already paired/carried with this one | `None` |

`UniqueUnit.__getattr__` (line 95-102) transparently falls through to the
global `UnitPrefab` for any attribute not defined on the level record
(class, stats, portrait, etc.) — so the level record only needs to override
what's level-specific.

### 2.3 How the character actually enters the map — two mechanisms

**A. Static placement.** If a `UniqueUnit` with a `starting_position` exists
in the level's `units` catalog, the level's built-in unit-placement step
places them automatically when the level starts (no event needed).

**B. Scripted placement via event commands** (`app/events/event_commands.py`,
handlers in `app/events/event_functions.py`) — this is what this project
actually uses for every playable character:

| Command | Nid | What it does | Key defaults |
|---|---|---|---|
| `load_unit` | `load_unit` (`event_commands.py:1170-1183`, handler `event_functions.py:826-842`) | Pulls a `UniqueUnit` into game memory (registers it) without placing it on the map. No-ops if the unit already exists. | `Team` defaults to `'player'`, `AI` defaults to `'None'` |
| `make_generic` | `make_generic` (`event_commands.py:1185-1206`, handler `:844-870`) | Fabricates a brand-new *generic* unit from scratch (out of scope for unique characters, but the closest neighbor) | — |
| `create_unit` | `create_unit` (`event_commands.py:1208-1235`, handler `:872-920`) | Creates a fresh instance of a unit template and optionally places it | `EntryType` defaults `'fade'`, `Placement` defaults `'giveup'` |
| `add_unit` (nickname `add`) | `add_unit` (`event_commands.py:1237-1253`, handler `:922-960`) | Places an already-loaded unit on the map | `Position` falls back to the level's `starting_position`; `EntryType` defaults `'fade'`; `Placement` defaults `'giveup'` |

`EntryType` (`app/events/event_validators.py:953-954`) is one of
`fade | immediate | warp | swoosh` — the placement animation.
`Placement` (`:956-957`) is one of `giveup | stack | closest | push` —
what to do if the target tile is already occupied. `add_unit` refuses to run
if the unit is already on the map, already dead, or currently being carried
as another unit's traveler (`event_functions.py:928-938`).

### 2.4 Art assets (all under `lion_throne.ltproj/resources/`)

| Asset | Path | Manifest |
|---|---|---|
| Dialogue portrait | `portraits/<nid>.png` | `portraits/portraits.json` |
| Map sprite | `map_sprites/<Class>-stand.png`, `<Class>-move.png` (inherited from the unit's class unless `variant` overrides it) | `map_sprites/map_sprites.json` |
| Battle animation | `combat_anims/<Class>-<WeaponAnim>.png` | `combat_anims/combat_anims.json` (optional — combat resolves on the map with no crash if missing) |

The cheapest new character reuses an existing class (inherits its map
sprite + combat anim) and only needs a new portrait plus a `UnitPrefab`
entry and a placement.

## 3. Code files

- `app/data/database/units.py:11-111` — `UnitPrefab` dataclass and
  `UnitCatalog.create_new` (default field values for a freshly-created unit).
- `app/data/database/level_units.py:79-114` — `UniqueUnit` (per-level
  placement record); `:8-77` `GenericUnit` for contrast (squad filler,
  out of scope).
- `app/events/event_commands.py:1170-1253` — `LoadUnit`, `MakeGeneric`,
  `CreateUnit`, `AddUnit` command declarations (keywords/optional keywords).
- `app/events/event_functions.py:826-960` — the actual handlers; `add_unit`
  fallback-to-`starting_position` and refusal conditions at `:928-957`.
- `app/events/event_validators.py:953-957` — `EntryType`/`Placement` valid
  value lists.

## 4. Working example in this repo

`Elara` — `lion_throne.ltproj/game_data/units.json`, nid `"Elara"`: a
`Citizen`-class unit with no starting items/skills, `portrait_nid: "Elara"`
(art at `resources/portraits/Elara.png`, manifest entry in
`resources/portraits/portraits.json`), and non-combat-oriented growths
(`MAG` 60%, `STR` 20%). She has **no** static `UniqueUnit` entry in level
`S1`'s `units` catalog at all — instead `events.json`'s `"S1 Intro"` event
places her purely via the scripted command
`add_unit;Elara;3,8;immediate` (nid `add_unit`, position `(3,8)`, entry type
`immediate`), alongside `Kael`, `Ren`, and `Briar` — the same command runs
again in `"S1 Reenter"` so she reappears on level re-entry. Later chapters
(`S2`, `S3`, `S4`, `S5`, `CAPITAL`) repeat the same `add_unit;Elara;...`
pattern with new coordinates each time. Contrast: `Tamsin` (nid `"Tamsin"`)
*does* have a static `UniqueUnit` entry in `S2`'s `units` catalog with
`"team": "enemy"` — she starts hostile and must be converted via the
excluded recruitment/`change_team` mechanic before later chapters can
`add_unit` her onto the player's side.

## 5. Test

`tools/test_event_placements.py` statically validates every authored
`add_unit;<nid>;x,y` in `events.json`: it regex-scans every event's
`_source` for the `add_unit` pattern, cross-references each `(x, y)` against
the level's tilemap terrain, and fails loudly if a placement lands on
impassable terrain (`IMPASSABLE = {'Wall', 'Cliff', 'Lake', 'Fence', 'Sea',
'Pillar'}`, line 39) or if two units in the same event are placed on the
same tile. It exists because of two real regressions: Kael placed inside a
Wall tile in `S1`, and two companions once assigned the same tile. Run it
with `uv run --no-project --python 3.12 --with pygame-ce --with
typing-extensions python tools/test_event_placements.py`.

That test is static (source-text + tilemap only) — it does not boot a level
and actually execute `add_unit`/`load_unit`, so it can't catch a bad
`EntryType`/`Placement` value, the `starting_position`-fallback path when
`Position` is omitted, or the "already on map"/"already dead"/"already
traveling" refusal conditions in `event_functions.py:928-938`. No test
covers that execution path; a
`tools/test_add_unit_execution.py` should exist that, after
`harness.boot()` and `game_state.GameState().start_level(...)`, calls
`load_unit` then `add_unit` with no `Position` and asserts the unit lands
exactly on its level's authored `starting_position`, then calls `add_unit`
again on the same now-placed unit and asserts it is refused and not moved.
