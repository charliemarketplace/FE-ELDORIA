---
name: configure-fog-of-war
description: Turn on level-wide fog of war via event commands, and layer FOG/VISION map regions on top to fog or reveal specific areas independent of the global setting, for a designer building stealth or exploration chapters.
---

## 1. Feature

Fog of war in this engine is not a level-editor checkbox or a DB constant —
it is a **runtime level variable** a designer activates with an event
command, with a configurable radius per team (player/ally/AI) and one of
several visual/mechanical modes (GBA-style, Thracia-style, hybrid). Layered
independently on top of that global setting are two **region types**, `fog`
and `vision`, which a designer paints onto specific tiles in the level
editor: a `fog` region forces its tiles through the fog/line-of-sight check
even when global fog-of-war is off (for a foggy swamp in an otherwise clear
level), while a `vision` region makes its tiles permanently visible to
everyone regardless of sight range or fog (a lit torch clearing, a scripted
"safe" zone). The engine's own event-command docstring makes the
independence explicit: enabling fog of war "does not affect presence of
fog or vision regions."

## 2. Details

### 2.1 Global fog-of-war — level variables, not a level field or constant

There is no `fog_of_war` DB constant and no `fog_of_war` field on
`LevelPrefab` (`app/data/database/levels.py`). It is entirely a `level_var`
set by two event commands (`app/events/event_commands.py`):

- **`enable_fog_of_war`** (`EnableFogOfWar`, lines 933-943, tag
  `Tags.LEVEL_VARS`, keyword `Activated` (Bool)) — its own desc: *"Activates
  or deactivates base level of fog of war. Does not affect presence of fog
  or vision regions."* → `event_functions.py:623-624` →
  `action.do(action.SetLevelVar("_fog_of_war", activated))`.
- **`set_fog_of_war`** (`SetFogOfWar`, lines 945-954) — configures
  `fog_of_war_type`, `radius`, optional `ai_radius`, `other_radius` →
  `event_functions.py:626` sets `_fog_of_war_type`, `_fog_of_war_radius`,
  `_ai_fog_of_war_radius`, `_other_fog_of_war_radius` level_vars.

Read back via `game_state.get_current_fog_info()` (`app/engine/
game_state.py:1342-1349`), which builds a `FogOfWarLevelConfig` from those
level_vars (default `_fog_of_war = False`). `FogOfWarType` (`app/engine/
fog_of_war.py:6-11`) and `FogOfWarLevelConfig` (lines 13-18) live in their
own small module — the enum's exact members should be confirmed in that
file when authoring (verified present: an enum plus a config dataclass
carrying `mode` and radius fields).

Two related DB constants, both independent toggles that only matter *while*
fog-of-war is active (`app/data/database/constants.py:98-99`):

| Constant | Meaning | Default |
|---|---|---|
| `fog_los` | Fog of War also obeys line-of-sight rules (not just radius) | `False` |
| `ai_fog_of_war` | AI decision-making is also restricted by fog of war (otherwise AI sees everything) | `False` |

Both tagged `LINE_OF_SIGHT`/`AI` respectively. Consumed in `app/engine/
game_board.py` — e.g. `ai_fog_of_war` gates whether non-player teams'
`in_vision` checks apply at all (lines 158, 167), `fog_los` gates whether
line-of-sight (not just radius) further restricts what's visible (lines
194, 252, 266).

### 2.2 The `fog` and `vision` region types

`RegionType` enum, `app/events/regions.py:7-14` — full member list:
`NORMAL`, `STATUS`, `EVENT`, `FORMATION`, `FOG`, `VISION`, `TERRAIN`
(values `'normal'`, `'status'`, `'event'`, `'formation'`, `'fog'`,
`'vision'`, `'terrain'`). A region's `sub_nid` field (free-text in the
region editor) is read as an integer **radius** for both `FOG` and
`VISION` regions — it is not a "fog strength" value, just how many extra
tiles around the region's own footprint are affected.

### 2.3 Registration — level start, load, and dynamic add/remove

At level setup, `GameState.level_setup()` (`app/engine/game_state.py:
302-307`) iterates `self._current_level.regions` and for each region with
`region_type == RegionType.FOG` calls `action.AddFogRegion(region)
.execute()`; `RegionType.VISION` → `action.AddVisionRegion(region)
.execute()`. The same pattern runs again on save-load (~lines 618-623).

Dynamically at runtime, the generic `AddRegion`/`RemoveRegion` actions
(`app/engine/action.py:3029-3059`, `3106-3138`) branch on region type the
same way, dispatching to dedicated actions:

- `AddFogRegion` (lines 3160-3170) — `do()` → `game.board.
  add_fog_region(region)`; `reverse()` → `remove_fog_region(region)`; both
  call `game.boundary.reset_fog_of_war()` to force a redraw.
- `RemoveFogRegion` (3172-3182) — mirror.
- `AddVisionRegion` (3184-3194) / `RemoveVisionRegion` (3196-3206) — same
  shape for vision.

So a designer can add/remove fog or vision regions mid-chapter via any
event command that manipulates regions (e.g. a scripted region add/remove),
not just by placing them at level-build time.

### 2.4 What each region type actually does — `game_board.py`

- **`add_fog_region(region)`** (lines 210-219): reads `fog_range =
  int(region.sub_nid) if region.sub_nid else 0`, expands every tile in
  `region.get_all_positions()` by a manhattan sphere of that radius, and
  adds the region's nid to `self.fog_regions` at each resulting position
  (clipped to map bounds). `remove_fog_region` (221-224) discards it again.
- **`add_vision_region(region)`** (226-236): identical radius/expansion
  logic, but stores into `self.vision_regions`, and — critically —
  **immediately adds every affected position to `self.previously_visited_
  tiles`** ("Anyone can see a vision region", line 235 comment) so terrain
  memory treats it as already-explored. `remove_vision_region` (238-240) is
  the inverse.
- **`in_vision(pos, team='player')`** (lines 242-276) is the actual
  consumer both feed into:
  - Line 245-246: `if self.vision_regions.get(pos): return True` —
    **a VISION region makes a tile visible to any team unconditionally**,
    bypassing sight range, fog, and line-of-sight entirely. Comment in
    source: "Anybody can see things in vision regions no matter what / So
    don't use vision regions with fog line of sight."
  - Line 248: `if game.get_current_fog_info().is_active or
    self.fog_regions.get(pos):` — **a FOG region forces that tile through
    the full fog/LOS visibility algorithm even when the level-wide fog
    toggle is off.** It is OR'd with the global toggle, not a separate
    numeric fog level; whether the tile is actually seen still depends on
    the viewing unit's sight range and (if `fog_los` is on) line of sight.
    If neither region governs a tile and global fog is inactive, the
    function falls through to `True` (normal, fully-visible behavior).
- `check_fog_of_war(unit, pos)` (~lines 300-306) — used by
  `target_system.py`'s `apply_fog_of_war`/`_filter_splash_through_fog_of_
  war` (~lines 147-165) to filter valid attack targets/splash through fog;
  returns true if `pos == unit.position`, `in_vision(pos, unit.team)`, or
  the tile is otherwise a known/explored tile.
- `can_move_through`/`can_move_through_ally_block` (~lines 154-170) also
  route through `in_vision` — a unit can path through a tile it can't see
  an enemy occupying.
- `terrain_known(pos, is_in_vision)` (~278-287) — governs whether terrain
  type itself is revealed, branching on `FogOfWarType` (HYBRID/THRACIA/GBA
  variants differ in how much terrain memory persists after leaving fog).

### 2.5 Per-unit sight range

`action.UpdateFogOfWar` (`app/engine/action.py:633-651`) computes
`sight_range = skill_system.sight_range(unit) + fog_of_war_radius` (the
team's configured radius from `FogOfWarLevelConfig`, §2.1), then calls
`game.board.update_fow(pos, unit, sight_range)`
(`game_board.py:173-187`), which recomputes that unit's personal visible
tile set via manhattan spheres.

`skill_system.sight_range(unit)` (`app/engine/skill_system.py:794-803`)
aggregates any skill component defining `sight_range`, falling back to `0`
if the unit has none (`Defaults.sight_range`, `component_system/
skill_system_base.py:110-111`). Two ready-made skill components
(`app/engine/skill_components/base_components.py`):

- **`SightRangeBonus`** (nid `sight_range_bonus`, lines 171-180,
  `ComponentType.Int`, default `value = 3`) — flat sight-range bonus.
- **`DecreasingSightRangeBonus`** (nid `decreasing_sight_range_bonus`,
  lines 182-200) — starts at `value` (default 3), decrements by 1 each
  upkeep (a "torch burning out" effect), calling `action.do(action.
  UpdateFogOfWar(unit))` on both sides of the decrement so vision updates
  immediately rather than lagging a turn.

## 3. Code files

- `app/data/database/constants.py:98-99` — `fog_los`, `ai_fog_of_war`
  constants.
- `app/events/event_commands.py:933-954` — `EnableFogOfWar`,
  `SetFogOfWar` event commands.
- `app/events/event_functions.py:623-626` — their implementations
  (`_fog_of_war`, `_fog_of_war_type`, `_fog_of_war_radius`,
  `_ai_fog_of_war_radius`, `_other_fog_of_war_radius` level_vars).
- `app/engine/game_state.py:302-307,618-623,1342-1349` — region
  registration at level setup/load; `get_current_fog_info`.
- `app/engine/fog_of_war.py:6-18` — `FogOfWarType`,
  `FogOfWarLevelConfig`.
- `app/events/regions.py:7-14` — `RegionType` enum (`FOG`, `VISION`
  members).
- `app/engine/action.py:633-651,3029-3059,3106-3138,3160-3206` —
  `UpdateFogOfWar`; `AddRegion`/`RemoveRegion` dispatch;
  `AddFogRegion`/`RemoveFogRegion`/`AddVisionRegion`/`RemoveVisionRegion`.
- `app/engine/game_board.py:154-306` — `add_fog_region`,
  `remove_fog_region`, `add_vision_region`, `remove_vision_region`,
  `in_vision`, `check_fog_of_war`, `can_move_through`,
  `terrain_known`, `get_fog_of_war_radius`, `update_fow`.
- `app/engine/skill_system.py:794-803` — `sight_range` aggregation.
- `app/engine/skill_components/base_components.py:171-200` —
  `SightRangeBonus`, `DecreasingSightRangeBonus`.
- `app/engine/target_system.py:~147-165` — fog-filtered targeting/splash.

## 4. Working example in this repo

None. `lion_throne.ltproj/game_data/levels.json` uses only `"event"` (28
occurrences) and `"formation"` (1 occurrence) region types across every
level — `"fog"` and `"vision"` region types are never placed anywhere in
this project. `lion_throne.ltproj/game_data/constants.json` has `fog_los`
and `ai_fog_of_war` both at their default `false`, and a grep of `events.
json` for `enable_fog_of_war`/`set_fog_of_war` turns up nothing — global
fog of war is never activated by any event in this project either. The
closest analogue authored here is the ordinary `event` region type (used
28 times for triggers/dialogue), which shares the same `RegionObject`
base class and region-editor workflow, but carries none of the vision/fog
board-level logic in `game_board.py`.

## 5. Test

No `tools/test_*.py` covers fog of war or fog/vision regions — a grep of
all 13 test files under `tools/` for "fog" or "vision" returns nothing. A
`tools/test_fog_of_war.py` should exist that, after `harness.boot()`:
calls `action.do(action.SetLevelVar("_fog_of_war", True))` and asserts
`game.get_current_fog_info().is_active` reflects it; places a `FOG`-type
region and asserts `game.board.in_vision(pos, 'player')` requires the
routed sight-range check even with the global toggle off (by first
confirming it returns `True` unconditionally when global fog is off and no
region covers `pos`, then `False`/gated once inside the fog region without
adequate sight range); places a `VISION`-type region and asserts `in_vision`
returns `True` for a team with zero sight range/inside active fog, proving
the unconditional override; and asserts `remove_fog_region`/
`remove_vision_region` (or the `Remove*Region` actions' `reverse()`) restore
prior visibility.
