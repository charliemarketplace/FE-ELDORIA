---
name: configure-movement-cost-grid
description: Edit or extend the mcost.json movement-type-by-terrain cost grid for a designer adding a new movement type (e.g. a mounted-only class) or a new terrain that certain movement types can't cross.
---

## 1. Feature

A designer can define exactly how expensive every terrain `mtype` is to cross
for every movement type (`Light Foot`, `Fliers`, `Heavy Cav`, ...), independent
of both the terrain's visuals and any individual class — the whole weapon-
triangle-style genericism the engine uses elsewhere applies here too: there's
no hardcoded "Fliers ignore terrain" rule, it's 100% a lookup table a designer
edits directly. A class then just declares which column of that table it reads
(`movement_group`), and a skill can override that column per-unit at runtime
(e.g. a temporary "become a flier" effect).

## 2. Details

### 2.1 The grid — `McostGrid` (`app/data/database/mcost.py:1-89`)

- Rows = `terrain_types` (must match `Terrain.mtype` values from `terrain.json`
  — see `author-terrain-effects`); columns = `unit_types` (movement-type
  names, referenced by `Klass.movement_group`).
- `default_value = 1` (`:2`) — cost assigned to any newly-added row/column cell
  via `add_row`/`add_column` (`:36-43`).
- `get_mcost(unit_type, terrain_type)` (`:25-28`) is the only query a designer
  needs to reason about: it does `unit_types.index(unit_type)` /
  `terrain_types.index(terrain_type)` and reads `grid[ridx][cidx]` — both are
  plain list lookups, so **every `mtype` used in `terrain.json` must have a
  matching row here, and every `movement_group` used in `classes.json` must
  have a matching column, or `.index()` raises `ValueError` at runtime** (there
  is no validation step or fallback).
- CRUD helpers for editor tooling: `insert_row`/`insert_column`,
  `delete_row`/`delete_column`, `get_row`/`get_column`,
  `set_row`/`set_column`, direct `get`/`set` by `(x, y)` coordinate (`:17-74`).
- `save()`/`restore()` (`:82-89`) round-trip as the exact 3-element
  `[grid, terrain_types, unit_types]` shape stored in `mcost.json`.
- Cost values are plain numbers (int or float) with no engine-enforced
  ceiling; by convention (not code) `99` marks "impassable to this movement
  type" — see `movement_funcs.check_traversable` below, which compares cost
  against the unit's total movement points, so any cost higher than a unit
  could ever have works as "impassable."

### 2.2 Per-unit resolution — `app/engine/movement/movement_funcs.py:16-49`

- `get_movement_group(unit)` (`:16-20`): first asks
  `skill_system.movement_type(unit)` — true only if the unit has a skill with
  the `MovementType` component (`app/engine/skill_components/
  movement_components.py:65-73`, nid `movement_type`) — and only falls back to
  `DB.classes.get(unit.klass).movement_group` if no skill overrides it. This is
  the mechanism for "this skill turns you into a flier for movement purposes."
- `get_mcost(unit_to_move, pos)` (`:22-35`): resolves the tile's terrain via
  `game.get_terrain_nid`, falls back to `DB.terrain[0]` if the tile has no
  registered terrain, then calls `DB.mcost.get_mcost(movement_group,
  terrain.mtype)`. If `DB.terrain` is empty entirely, cost is a flat `1`.
- `check_traversable`/`check_weakly_traversable` (`:37-49`) compare `mcost`
  against `equations.parser.movement(unit)` — `check_weakly_traversable` also
  accepts any tile costing `≤5` regardless of the unit's actual movement,
  which is what witch-warp-style skills use to find "reachable enough" tiles.
- `IgnoreTerrain` (`app/engine/skill_components/movement_components.py:83-92`)
  only suppresses terrain-*status* application (see `author-terrain-effects`)
  — it does **not** bypass the mcost lookup itself; there is no skill
  component in this codebase that grants free/reduced movement cost.
  `Pass` (`:75-81`) lets a unit move through enemy-occupied tiles, which is an
  occupancy rule, not a cost rule.

## 3. Code files

- `app/data/database/mcost.py:1-89` — `McostGrid` and every editor-facing
  mutation method.
- `app/data/database/klass.py:18` — `Klass.movement_group` field;
  `:92` — `create_new` defaults it to `db.mcost.unit_types[0]`.
- `app/engine/movement/movement_funcs.py:16-49` — `get_movement_group`,
  `get_mcost`, `check_traversable`, `check_weakly_traversable`.
- `app/engine/skill_components/movement_components.py:65-92` —
  `MovementType` (movement-group override) and `IgnoreTerrain`.

## 4. Working example in this repo

`lion_throne.ltproj/game_data/mcost.json` stores `[grid, terrain_types,
unit_types]` with 9 movement types (`Light Foot, Armors, Heavy Cav, Light Cav,
Regular, Mages, Fliers, Fleet, Pirates`) across 19 terrain rows (`Cliff, Fence,
Wall, Stairs, Normal, Ruins, Bank, River, Rapids, Desert, Snow, Sea, Forest,
Thicket, Pillar, Hill, Mountain, Fort, Throne`). Sample rows (column order
matches the `unit_types` list above): `Cliff` = `[99, 99, 99, 99, 99, 99, 1,
99, 99]` — impassable to everyone except `Fliers` (cost 1); `Forest` = `[2,
1.0, 3, 3, 2, 2, 1, 1.0, 2]` — cheapest for `Armors`/`Fleet` (1.0), most
expensive for the two cavalry columns (3); `Mountain` = `[99, 99, 99, 99, 99,
99, 1, 2.0, 99]` — impassable except `Fliers` (1) and `Fleet` (2.0). These
`terrain_types` row keys line up exactly with the `mtype` values authored in
`terrain.json` (`Forest`, `Mountain`, `Fort`, etc — see `author-terrain-
effects`), confirming the link is live end-to-end. `classes.json` assigns
`movement_group` per class — e.g. `Citizen` (`classes.json:3-7`) is `"Light
Foot"`, while other classes use `"Regular"`, `"Armors"`, `"Heavy Cav"`,
`"Fleet"`, `"Mages"` (`classes.json:134,815,950,1498,2314`, among others). No
class or skill in this project's content uses the `MovementType` skill
component to override a unit's movement group at runtime — the closest
analogue is the plain class-level assignment above.

## 5. Test

No `tools/test_*.py` exercises `McostGrid.get_mcost`, `get_movement_group`, or
`check_traversable`, and nothing validates that every `terrain.json` `mtype`
has a matching `mcost.json` row or that every `classes.json`
`movement_group` has a matching column — a designer adding a new terrain
`mtype` or class `movement_group` without the matching row/column gets a
runtime `ValueError` from `.index()`, not a load-time error. A
`tools/test_mcost_grid.py` should exist that, after loading `DB`, asserts
every `Terrain.mtype` in `DB.terrain` appears in `DB.mcost.terrain_types` and
every `Klass.movement_group` in `DB.classes` appears in `DB.mcost.unit_types`
(catching the exact class of bug described above), plus a runtime case that
builds a `Fliers`-type unit and a `Light Foot`-type unit and asserts
`movement_funcs.get_mcost` returns `1` vs `99` for the two respectively on a
`Cliff` tile.
