---
name: configure-initiative-turn-order
description: Replace the classic Player-Phase/Enemy-Phase turn structure with a per-unit initiative order (one unit acts at a time, sorted by an initiative value), for a designer who wants a tactics-RPG-style interleaved turn queue instead of team phases.
---

## 1. Feature

Turning on Per Unit Initiative Order replaces the whole team-phase turn
structure (Player Phase → Enemy Phase → Other Phase → repeat) with a single
ordered queue of individual units, sorted once by an initiative value and
then cycled through one unit at a time — closer to a classic tactics-RPG
turn-order strip than Fire Emblem's usual phases. It changes how deeply a
designer needs to think about upkeep/status timing: "start of phase" skill
hooks fire per acting unit instead of once for the whole team, the pause
menu shows a turn-order HUD strip instead of the minimap toggle, and player
units not currently up are drawn "grayed out" like already-acted units. The
entire mechanism is implemented and reachable behind one constant, but the
value that determines *turn order itself* — a project-defined initiative
equation — is absent, so every unit currently ties.

## 2. Details

### 2.1 The constant

`initiative` (`app/data/database/constants.py:71`, BOOL, default `False`,
tag `MAJOR_FEATURES`, display text "Per Unit Initiative Order"). This is
the **only** switch — there is no per-level/per-chapter override. Every
consumer reads the same global `DB.constants.value('initiative')`; `
LevelPrefab` (`app/data/database/levels.py`) has no `initiative` or generic
constants-override field, so a project cannot turn this on for one chapter
and off for another — it's whole-project.

### 2.2 The `InitiativeTracker`

`app/engine/initiative.py`, class `InitiativeTracker` (whole file, ~112
lines):

- State: `unit_line` (ordered list of unit nids), `initiative_line`
  (parallel list of their initiative values), `current_idx`, `draw_me`
  (HUD visibility toggle).
- `start(units)` (lines 30-35) — the one-time sort:
  `sorted(units, key=lambda unit: equations.parser.get_initiative(unit),
  reverse=True)`. **No explicit tie-break** — Python's stable sort means
  units with equal initiative keep whatever order `game.get_all_units()`
  handed them (effectively spawn/registration order).
- `next()`/`back()` (lines 20-28) — advance/retreat `current_idx`, wrapping
  around the line.
- `get_current_unit()`/`get_previous_unit()`/`get_next_unit()` (lines
  37-44) — resolve nids back to live `UnitObject`s via `game.get_unit`.
- `insert_unit()`/`_insort()` (lines 67-69, 97-108) — binary-insert a unit
  back into the middle of the current round (used by the delay skill
  component below).
- `at_start()` — true when `current_idx` is `0` or `-1`; gates whether
  `TurnChange`/`LevelStart` triggers fire (§2.4).
- `toggle_draw()` — flips the HUD strip on/off.

### 2.3 Per-unit initiative value

`equations.parser.get_initiative(unit)` (`app/engine/equations.py:97-101`):
looks for a project equation literally named `initiative`; if none is
defined, always returns `0`. This is the same fallback pattern used
throughout `EquationParser` (compare `get_max_fatigue`, `get_mana`) — a
designer authors an `INITIATIVE` (or however-cased) equation in
`equations.json` to make units actually differ in turn order; without one,
every unit ties and order degenerates to insertion order.

### 2.4 Phase-system rerouting

`app/engine/phase.py`, class `PhaseController` — when
`DB.constants.value('initiative')` is true, every phase query is redirected
to the tracker instead of cycling `DB.teams`:

- `get_current()`/`get_previous()`/`get_next()` (lines 56-69) return
  `game.initiative.get_current_unit().team` etc. instead of a team nid from
  the normal rotation.
- `_next()` (lines 84-85) sets `self.current` from the current initiative
  unit's team.
- `next()` (lines 94-104) skips the "skip empty phases" loop entirely when
  initiative is on (there's no such thing as an "empty phase" in unit-by-
  unit mode).

### 2.5 Turn-change and per-unit upkeep

`app/engine/general_states.py`:

- `TurnChangeState.end()` (lines 113-127) — in initiative mode, does
  `action.do(action.IncInitiativeTurn())`, transitions to a dedicated
  `'initiative_upkeep'` state, and only fires the `TurnChange`/`LevelStart`
  triggers when `game.initiative.at_start()` — i.e. once per full lap of
  the queue, not once per acting unit.
- `InitiativeUpkeep` (lines 175-192) — `begin()`/`end()` call
  `game.phase.next()`, then route to `'free'` (if the current unit's team
  is `player`) or `'ai'`, followed by `'status_upkeep'` and
  `'phase_change'` — **confirming per-unit upkeep/status triggers do fire
  once per unit-turn**, not once per team-phase as in classic mode.
- `PhaseChangeState.begin()` (lines 224-227) — snaps the cursor straight to
  the current initiative unit's position instead of the classic team
  slide-in transition.
- `FreeState` (autoend check ~line 304, SELECT handling ~line 330) —
  autoends the turn once the current initiative unit is `finished`, and
  restricts unit selection in Free move to only that unit.
- START button (~lines 351-353) toggles `game.initiative.toggle_draw()`
  (shows/hides the order HUD) instead of opening the minimap — same
  rebinding applies on the prep screen (`app/engine/prep.py:438-439`).
- `MoveState.get_next_unit()` (~lines 2464-2466) — in initiative mode,
  returns only the current initiative unit (or `None` if it's already
  finished/AI-acted), replacing the normal "next un-acted unit on this
  team" logic.

`app/engine/status_upkeep.py:17-19` — when initiative is on, the upkeep
pass processes `[game.initiative.get_current_unit()]` only, so
`skill_system.on_upkeep`/`on_endstep` hooks run for the single acting unit,
not the whole team simultaneously.

### 2.6 State machine, undo/turnwheel, and lifecycle

- `app/engine/state_machine.py:70` registers `'initiative_upkeep':
  general_states.InitiativeUpkeep`.
- `app/engine/game_state.py:320-323` — gated construction: `if
  DB.constants.value('initiative'): self.initiative =
  InitiativeTracker(); self.initiative.start(self.get_all_units())` — the
  order is computed once, at game/level start, from every unit currently
  registered.
- `app/engine/action.py:3517-3564` — `IncInitiativeTurn`, `InsertInitiative`,
  `RemoveInitiative`, `MoveInInitiative` — all implement `do()`/`reverse()`
  so initiative-order changes are Turnwheel-safe; a generic unit-removal
  path wires in `RemoveInitiative` conditionally (~lines 2447-2449,
  2463-2464, 2482-2483) so a unit leaving the map is pulled out of the
  queue.

### 2.7 UI — the order strip

`app/engine/ui_view.py` — draws the HUD only when `DB.constants.
value('initiative')` and `game.initiative.draw_me` (lines ~114-130);
`create_initiative_info()` (~line 207 on) builds the strip from
`game.initiative.unit_line`, blitting the `initiative_platform` sprite per
entry. `app/engine/unit_sprite.py:418-419` grays out player units whose
turn isn't current (same visual treatment as an already-acted unit).

### 2.8 A skill component built for this mode

`DelayInitiativeOrder` (nid `delay_initiative_order`, tag `COMBAT2`,
`app/engine/skill_components/combat2_components.py:591-604`) —
`after_strike` calls `action.MoveInInitiative(target, self.value)` to push
a struck unit back in the turn order by `value` slots. This is a genuine
initiative-aware combat art component that exists in engine code.

## 3. Code files

- `app/data/database/constants.py:71` — the `initiative` constant.
- `app/engine/initiative.py` (whole file) — `InitiativeTracker`.
- `app/engine/equations.py:97-101` — `get_initiative` fallback-to-0 hook.
- `app/engine/phase.py:48,56-69,84-85,94-104` — `PhaseController` rerouting.
- `app/engine/game_state.py:16,137,286,320-323` — construction/lifecycle.
- `app/engine/general_states.py:86,113-127,175-192,200-227,304,330,
  351-353` — `TurnChangeState`, `InitiativeUpkeep`, `PhaseChangeState`,
  `FreeState` special-casing; `MoveState.get_next_unit` ~2464-2466.
- `app/engine/status_upkeep.py:17-19` — per-unit-only upkeep list.
- `app/engine/state_machine.py:70` — `initiative_upkeep` state
  registration.
- `app/engine/action.py:3517-3564,2447-2449,2463-2464,2482-2483` —
  `IncInitiativeTurn`/`InsertInitiative`/`RemoveInitiative`/
  `MoveInInitiative`.
- `app/engine/ui_view.py:25,35,42,114-130,207+` — HUD strip.
- `app/engine/unit_sprite.py:418-419` — grayed-out sprite when not current.
- `app/engine/prep.py:438-439` — prep-screen START rebinding.
- `app/engine/skill_components/combat2_components.py:591-604` —
  `DelayInitiativeOrder`.

## 4. Working example in this repo

None. `lion_throne.ltproj/game_data/constants.json` sets `"initiative"` to
`false` (matching the DB default) — the only `.ltproj` in this repo.
`lion_throne.ltproj/game_data/equations.json` defines 26 equations, none
named `initiative`/`INITIATIVE`, so even if the constant were flipped on,
`get_initiative()` would always return `0` for every unit and turn order
would reduce to insertion order. `lion_throne.ltproj/game_data/events.json`
has no reference to `initiative` at all, and `delay_initiative_order` is
not attached to any skill in `skills.json`. The closest analogue authored
in this project is the classic team-phase system itself (`DB.teams`
cycling in `PhaseController` when the constant is off) — there is no
partial or chapter-scoped use of initiative to point to.

## 5. Test

No `tools/test_*.py` file references "initiative" in any form — a grep of
all 13 test files under `tools/` returns nothing. A
`tools/test_initiative.py` should exist that, after `harness.boot()`, sets
`DB.constants` value for `initiative` to `True`, constructs an
`InitiativeTracker`, calls `start()` with a small set of units having
distinct authored `initiative` equation results (requiring the test to
inject a fake `INITIATIVE` equation), and asserts `unit_line` sorts
descending by that value; a second case should drive
`TurnChangeState`/`InitiativeUpkeep` through two full unit-turns and assert
`status_upkeep` fires only for the single current unit each time (not the
whole team), and that `TurnChange`/`LevelStart` triggers fire only when
`game.initiative.at_start()` is true; a third case should call
`action.do(action.MoveInInitiative(unit, 2))` and assert the unit's
position in `unit_line` shifts back by two and is undone by
`action.reverse()`.
