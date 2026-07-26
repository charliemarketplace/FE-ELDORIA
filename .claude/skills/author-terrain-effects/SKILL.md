---
name: author-terrain-effects
description: Author a terrain type's movement-cost key, opaque/LOS-blocking flag, and passive on-tile status effect (regen, avoid, stat bonus) for a designer shaping how tiles feel to stand on, not just how they look.
---

## 1. Feature

A designer can define what a tile *does* to any unit standing on it, independent
of its sprite: which `mcost.json` column it costs to enter (`mtype`), whether it
blocks line-of-sight for the `line_of_sight`/`fog_los` systems (`opaque`), and a
skill it silently grants to any unit that ends its movement there (`status`) —
e.g. an avoid bonus on Ruins, a defense bonus atop a Mountain, or a slow heal-over-
time on a Fort. The status is a normal skill authored in `skills.json`, so its
effect can be anything a skill component can do (stat changes, avoid/crit
modifiers, regeneration, hidden auras) — terrain doesn't have its own def/avoid
fields, it just plugs into the general skill system. A single painted `terrain`-
type region can also locally override which terrain nid a tile counts as,
without repainting the map.

## 2. Details

### 2.1 The terrain record — `Terrain` (`app/data/database/terrain.py:6-19`)

| Field | Meaning | Default |
|---|---|---|
| `nid`, `name` | Identifier / display name shown on the tile-info panel | required |
| `color` | Map-editor swatch `(r,g,b[,a])` (coerced to tuple on load, `:21-26`) | `(0,0,0)` |
| `minimap` | Minimap icon/category key | `None` |
| `platform` | Combat-background "platform" sprite the unit stands on in battle | `None` |
| `background` | Optional combat background override | `None` |
| `mtype` | Row key into `mcost.json`'s `terrain_types` — see the movement-cost-grid skill | `None` |
| `opaque` | Blocks line-of-sight when LOS/fog-LOS is active | `False` |
| `status` | Skill nid granted to any unit that ends a move on this tile | `None` |

`Terrain.create_new` (`:31-39`) seeds a new entry with `color=(0,0,0)`,
`minimap='Grass'`, the first available platform sprite, and `mtype` set to
whatever the *first* row in `mcost.json` happens to be — so a freshly-created
terrain type is immediately walkable (whatever cost that first row assigns) and
carries no status until one is authored.

There is no native `def`/`avoid`/`heal` field: every "terrain bonus" a designer
wants is delivered by pointing `status` at an ordinary skill nid and giving that
skill whatever components it needs (`avoid`, `stat_change`, `regeneration`,
etc.) — terrain-granted skills are usually marked `hidden` so they don't clutter
a unit's skill list display.

### 2.2 How the status is applied/removed at runtime (`app/engine/game_state.py`)

- `arrive(unit, test)` (`:1444-1481`) is called right after a unit's position
  changes; unless `skill_system.ignore_terrain(unit)` is true, it calls
  `add_terrain_status(unit, test)` (`:1483-1510`), which reads the unit's tile
  via `get_terrain_nid`, looks up `DB.terrain.get(terrain_nid)`, lazily creates
  the skill object for `terrain.status` the first time it's needed
  (`item_funcs.create_skill`, cached in `terrain_status_registry` keyed by
  `(x, y, status_nid)` so repeated visits reuse the same skill instance), and
  applies it via `action.AddSkill(..., source_type=SourceType.TERRAIN)`.
- `leave(unit, test)` (`:1394-1426`) calls `remove_terrain_skills` (`:1428-1442`)
  symmetrically, removing the same cached skill on exit.
- A parallel, independent mechanism exists for **`RegionType.STATUS`** regions
  (a painted rectangle granting a skill, not tied to any specific terrain nid):
  `add_region_status`/the status-region branch in `arrive`/`leave` (`:1409-1419`,
  `1467-1471`, `1512-`) — same skill-caching approach, gated by
  `skill_system.ignore_region_status(unit)` instead. Terrain `status` and
  status-*region* `status` are separate authoring surfaces that both funnel
  through the same `_get_terrain_status`/skill-cache plumbing.
- **`RegionType.TERRAIN`** regions are a third, distinct region type: painting
  one over a tile makes `get_terrain_nid` (`game_state.py:1543-1559`) return the
  region's `sub_nid` (a terrain nid) instead of the tilemap's painted terrain —
  i.e. a way to locally override a tile's terrain identity (and therefore its
  `mtype`/`status`/`opaque`) without repainting the base map.
- `ignore_terrain(unit)` — true only for units with the `IgnoreTerrain` skill
  component (`app/engine/skill_components/movement_components.py:83-92`, nid
  `ignore_terrain`), which also sets `ignore_region_status`. A unit with this
  skill never receives *any* terrain- or status-region-granted skill.

### 2.3 Line-of-sight (`opaque`)

`GameBoard.init_opacity_grid`/`get_opacity` (`app/engine/game_board.py:309-324`)
builds a per-tile opacity grid straight from `DB.terrain.get(terrain_nid).opaque`
at level load; this feeds the Bresenham-line LOS check
(`app/engine/line_of_sight.py`) that `line_of_sight`/`aura_los`/`fog_los`
constants gate. If `DB.terrain.get(terrain_nid)` returns nothing for a tile, it
defaults to non-opaque (`False`).

## 3. Code files

- `app/data/database/terrain.py:6-39` — `Terrain` dataclass and
  `TerrainCatalog.create_new` defaults.
- `app/engine/game_state.py:1394-1543` — `leave`, `remove_terrain_skills`,
  `arrive`, `add_terrain_status`, `add_region_status`, `get_terrain_nid` (the
  entire apply/remove/cache lifecycle, plus the `RegionType.TERRAIN` override).
- `app/engine/game_board.py:309-324` — `init_opacity_grid`/`get_opacity`
  (how `opaque` feeds line-of-sight).
- `app/engine/skill_components/movement_components.py:83-92` —
  `IgnoreTerrain` skill component (`ignore_terrain`/`ignore_region_status`).
- `app/engine/movement/movement_funcs.py:22-35` — `get_mcost`, the other
  consumer of `terrain.mtype` (see `configure-movement-cost-grid`).

## 4. Working example in this repo

`lion_throne.ltproj/game_data/terrain.json`: `Mountain` (around line 402-417)
sets `mtype: "Mountain"`, `status: "Peak"`; `Fort`/`Throne`/`Gate` (lines
419-465) set `status: "Fort"`; `Forest` (lines 338-353) sets `status: "Forest"`.
The referenced skills live in `lion_throne.ltproj/game_data/skills.json`:
`Peak` grants `avoid +40` and `stat_change DEF +2`; `Fort` grants
`regeneration 0.2` (20% max-HP heal per turn) plus `avoid +20`/`DEF +2`; `Forest`
grants `avoid +20`/`DEF +1`; the plain `Avoid10`/`Avoid-5`/`Avoid5` skills
(used by `Ruins`, `Bank`/`River`/`Rapids`/`Snow`, `Desert` respectively) are
flat avoid modifiers with no stat change. These tiles are actually painted onto
levels — e.g. Chapter S1/S2's tilemaps use `Mountain`, `Forest`, and Capital/S5
use `Fort`/`Village`/`Vendor`/`Armory` (`lion_throne.ltproj/resources/tilemaps/
tilemap_data/tilemaps.json`), so the Mountain→`Peak` and Fort→`regeneration`
effects are live in actual play. `Wall`/`Door`/`Mast` set `opaque: true`, but
since `fog_los` is `false` in this project's `constants.json`, opacity is
authored but not currently exercised for LOS-blocking. No level in this project
uses a `RegionType.TERRAIN` override region — the closest analogue is the
`RegionType.STATUS` regions engine-supported at the same code path, which this
project also does not use (its only region types are `event`/`formation`).

## 5. Test

No `tools/test_*.py` exercises terrain-status application, `get_mcost`, or
`opaque`/LOS. The closest existing test, `tools/test_event_placements.py`
(lines ~37-39, 89-97), only statically checks that scripted `add_unit`/`load_unit`
placements in events.json don't land units on impassable terrain (`Wall`,
`Cliff`, `Lake`, `Fence`, `Sea`, `Pillar`) — it never touches status or LOS. A
`tools/test_terrain_status.py` should exist that, after `harness.boot()`, places
a unit on a `Mountain` tile via `game.arrive`, asserts the unit's `all_skills`
now contains a skill instance for `Peak` and that
`combat_calcs.avoid(unit, ...)` is 40 higher than off-tile, then moves the unit
off and asserts the skill is removed again — plus a second case building a
`RegionType.TERRAIN` region and asserting `game.get_terrain_nid` returns the
override nid instead of the tilemap's painted terrain.
