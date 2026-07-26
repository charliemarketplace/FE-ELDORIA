---
name: configure-fatigue-system
description: Turn on per-unit fatigue (deployment blocking or stat-penalty status skills from overuse) via the fatigue/reset_fatigue constants and the _fatigue game_var, for a designer who wants units to need rest between chapters.
---

## 1. Feature

Fatigue lets a designer make repeatedly deploying the same unit costly: units
accrue a `current_fatigue` counter (from items, hits, or scripted events),
and once that counter reaches a per-unit cap, the unit becomes "fatigued" —
either hard-blocked from deployment, or saddled with a stat-penalty status
skill, depending on which of two modes the designer picks. Benched units can
be configured to recover automatically at the start of the next level. The
mechanical skeleton (unit field, action, equation hook, item/skill
components, event command, three UI surfaces) is fully implemented in the
engine, but every part of it requires explicit authoring to actually turn
on — including a second, easy-to-miss gate that this project's constants
editor does not expose at all.

## 2. Details

### 2.1 The gates — three of them, not one

| Gate | Kind | Meaning | Default |
|---|---|---|---|
| `fatigue` | DB constant (`app/data/database/constants.py:72`) | Master feature toggle | `False` |
| `reset_fatigue` | DB constant (`constants.py:73`) | Auto-clear fatigue to 0 for benched units at level start | `False` |
| `_fatigue` | game_var, author-set only (no constants-editor field) | Which *behavior* fatigue has: `1` = hard deploy-block, `2` = auto status-skill | unset (falsy — behaves as neither) |

`_fatigue` has no dedicated event command; a designer sets it like any
generic game_var (`set_game_var`/`game_var`). It is read, not written,
everywhere in the engine — nothing in `app/engine` or in this project ever
assigns it, so simply flipping the `fatigue` DB constant on is not enough to
see any player-facing effect.

### 2.2 Storage on the unit

`current_fatigue` is a dedicated `int` field on `UnitObject`
(`app/engine/objects/unit.py:93`, default `0`), not a stat, not a skill,
reset on unit creation (`unit.py:246`) and persisted/restored in `save()`/
load (`unit.py:923`, `985`). Accessors:

- `get_fatigue()` (`unit.py:378-383`) — returns `current_fatigue`.
- `set_fatigue(val)` (`unit.py:385-386`) — clamps to a floor of `0` only
  (`max(val, 0)`); there is no upper clamp, a unit's fatigue can exceed its
  max.
- `get_max_fatigue()` (`unit.py:371-376`) — delegates to
  `equations.parser.get_max_fatigue(unit)`.

### 2.3 The max-fatigue equation

`EquationParser.get_max_fatigue` (`app/engine/equations.py:91-95`) looks for
a project equation named `max_fatigue`; if none is defined it falls back to
a hardcoded `10`. No `.ltproj` in this repo defines such an equation, so
every unit's threshold is currently the engine default of 10 wherever
fatigue is read.

### 2.4 Changing fatigue — `ChangeFatigue` action

The only mutator is `action.ChangeFatigue(unit, num)`
(`app/engine/action.py:2336-2368`):

- No-ops entirely if `skill_system.ignore_fatigue(unit)` returns `True` (see
  §2.6) — an increment call on such a unit silently does nothing.
- Otherwise sets `unit.set_fatigue(old_fatigue + num)` (so `num` can be
  negative to reduce fatigue, e.g. resting).
- If `_fatigue == 2`, additionally auto-applies/removes literal skill nids
  `'Fatigued'` (when `get_fatigue() >= get_max_fatigue()`) and `'Rested'`
  (when under it) via `AddSkill`/`RemoveSkill` with
  `source_type=SourceType.FATIGUE` (`source_type.py:15`) — but only if a
  skill with that exact nid exists in `DB.skills`; neither exists in this
  project.
- Fully turnwheel-reversible (`reverse()` undoes the sub-actions and resets
  `current_fatigue`).

### 2.5 Sources of fatigue gain

- **Item component `Fatigue`** (nid `fatigue`, `app/engine/item_components/
  exp_components.py:164-177`, `ComponentType.Int`, default `value = 1`) —
  fatigues the *attacker* by `value` on a successful hit with the item
  (`end_combat`, mode `'attack'`).
- **Item component `FatigueOnHit`** (nid `fatigue_on_hit`,
  `app/engine/item_components/hit_components.py:79-88`, default `value = 1`)
  — fatigues the *target* by `value` when struck by the item (`on_hit`).
- **Event command `add_fatigue`** (nid `add_fatigue`,
  `app/events/event_commands.py:1392-1401`, keywords `Unit`, `Fatigue`
  (int)) — `event_functions.py:1183-1188` resolves the unit and calls
  `action.do(action.ChangeFatigue(actor, fatigue))`. Referenced as the
  canonical example in the `loop_units` docstring
  (`event_commands.py:3280-3281`, "gives all player units 1 fatigue").
- Neither item component is attached to any item in
  `lion_throne.ltproj/game_data/items.json` in this project, nor is
  `add_fatigue` used in `events.json` — a designer must add these
  themselves.

### 2.6 Ignoring fatigue

Skill component `IgnoreFatigue` (nid `ignore_fatigue`,
`app/engine/skill_components/base_components.py:202-208`, tag `BASE`,
desc "Unit cannot gain fatigue") makes `skill_system.ignore_fatigue(unit)`
return `True`, short-circuiting `ChangeFatigue.do()` before anything is
recorded. Wired into the skill-component hook table as
`ResolvePolicy.ALL_DEFAULT_FALSE`
(`app/engine/component_system/compile_skill_system.py:21`) — any one skill
with this component is enough to block fatigue gain entirely.

### 2.7 Gameplay consequence — `_fatigue` mode 1 vs. mode 2

- **Mode 1 (hard deploy block)**: `app/engine/prep.py:292-297` marks a unit
  `is_fatigued = True` when `DB.constants.value('fatigue')` and
  `_fatigue == 1` and `get_fatigue() >= get_max_fatigue()` — treated the same
  as a deploy blacklist, refusing placement with an error sound
  (`prep.py:305,314`). The same check excludes fatigued units from an
  auto-fill candidate pool in `event_functions.py:2754-2756`.
- **Mode 2 (status-skill penalty)**: handled entirely inside
  `ChangeFatigue.do()` (§2.4) — applies `'Fatigued'`/`'Rested'` skills, which
  a designer must author themselves (with whatever stat penalties/bonuses
  desired) since neither exists by default.

### 2.8 Auto-reset for benched units (`reset_fatigue`)

`PhaseChangeState.refresh_fatigue()` (`app/engine/general_states.py:200-203`)
zeroes fatigue (`ChangeFatigue(unit, -unit.get_fatigue())`) for every unit
not currently on the map. It only runs when **all three** are true
(`general_states.py:220-221`): `DB.constants.value('fatigue')`,
`DB.constants.value('reset_fatigue')`, `game.turncount == 1` and
`game.phase.get_current() == 'player'` — i.e., once, at the very start of a
level, for benched units only. Separately, dead units always have their
fatigue fully zeroed unconditionally (`game_state.py:743-745`), regardless
of `reset_fatigue`.

### 2.9 UI surfaces (all additionally gated on `_fatigue` truthiness)

- **Prep/formation screen**: `draw_fatigue_card` (`app/engine/prep.py:
  351-363`), drawn only if `DB.constants.value('fatigue') and
  game.game_vars.get('_fatigue')` (`prep.py:372-373`) — shows
  "Fatigued"/"Ready!"/"Away".
- **Unit info menu**: `create_fatigue_surf`/`draw_fatigue_surf`
  (`app/engine/info_menu/info_menu_state.py:992-1008`), gated at lines
  504-508 (`fatigue` constant, player team, `_fatigue` truthy) — draws a
  `fatigue/max_fatigue` bar labeled "Ftg", red text at/over cap.
  Roster/formation entries are colored red the same way in
  `app/engine/game_menus/menu_options.py:543-549`.

Because `_fatigue` is never assigned anywhere in this project, all three UI
surfaces and both gameplay modes are currently unreachable even if a
designer flips the `fatigue` constant alone.

## 3. Code files

- `app/data/database/constants.py:72-73` — `fatigue`, `reset_fatigue` DB
  constants.
- `app/engine/objects/unit.py:93,246,371-386,923,985` — `current_fatigue`
  field, accessors, save/load.
- `app/engine/equations.py:91-95` — `get_max_fatigue` fallback-to-10 hook.
- `app/engine/action.py:2336-2368` — `ChangeFatigue`.
- `app/engine/item_components/exp_components.py:164-177` — `Fatigue` item
  component (attacker gain).
- `app/engine/item_components/hit_components.py:79-88` — `FatigueOnHit`
  item component (target gain).
- `app/engine/skill_components/base_components.py:202-208` — `IgnoreFatigue`.
- `app/engine/component_system/compile_skill_system.py:21` —
  `ignore_fatigue` hook registration.
- `app/events/event_commands.py:1392-1401` — `AddFatigue` event command.
- `app/events/event_functions.py:1183-1188` — `add_fatigue` implementation.
- `app/engine/prep.py:292-297,351-363,372-373` — mode-1 deploy block, prep
  fatigue card.
- `app/events/event_functions.py:2754-2756` — auto-fill exclusion (mode 1).
- `app/engine/general_states.py:200-203,220-221` — `refresh_fatigue`
  (`reset_fatigue` implementation).
- `app/engine/game_state.py:743-745` — unconditional zero-out on death.
- `app/engine/info_menu/info_menu_state.py:101,504-508,992-1008` — info-menu
  fatigue gauge.
- `app/engine/game_menus/menu_options.py:543-549` — roster red-coloring.
- `app/engine/source_type.py:15` — `SourceType.FATIGUE`.

## 4. Working example in this repo

None. `lion_throne.ltproj/game_data/constants.json` sets both `"fatigue"`
and `"reset_fatigue"` to `false` (matching the DB defaults), no `.ltproj`
equation defines `max_fatigue`, no skill named `Fatigued`/`Rested` exists in
`skills.json`, no item in `items.json` carries the `fatigue`/
`fatigue_on_hit` components, no event in `events.json` calls `add_fatigue`,
and the `_fatigue` game_var is never assigned by any event or engine
default. The closest analogue for "resource that gates repeated deployment"
authored in this project is the deploy-cap/blacklist system
(`max_deploy`/`min_deploy`, already documented) — fatigue would layer a
per-unit, chapter-crossing version of the same idea on top of it via
`prep.py:292-297`'s shared `is_fatigued`/blacklist code path.

## 5. Test

No `tools/test_*.py` exercises fatigue in any form — a grep of all 13 test
files under `tools/` for "fatigue" (case-insensitive) returns nothing. A
`tools/test_fatigue.py` should exist that, after `harness.boot()`: sets
`DB.constants` values for `fatigue`/`reset_fatigue` to `True`, sets
`game.game_vars['_fatigue'] = 1`, calls `action.do(action.ChangeFatigue(unit,
15))` against a unit whose `get_max_fatigue()` returns the default `10`, and
asserts `prep`'s deploy-block path marks the unit `is_fatigued`; a second
case should set `_fatigue = 2`, author dummy `Fatigued`/`Rested` skill defs
into `DB.skills` for the test, and assert `ChangeFatigue` attaches/removes
them as the counter crosses the threshold; a third case should call
`general_states.PhaseChangeState.refresh_fatigue()` on a benched unit with
nonzero fatigue and assert it zeroes only when `reset_fatigue` is also on.
