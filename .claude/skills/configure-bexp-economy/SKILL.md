---
name: configure-bexp-economy
description: Grant a party a pooled Bonus Experience currency and let the player spend it in base to hand-pick who levels up, for a designer wanting an out-of-combat EXP economy alongside normal combat leveling.
---

## 1. Feature

BEXP (Bonus Experience) is a per-party stockpile of "spendable EXP" a
designer grants (usually for clearing a chapter or hitting some milestone)
that the player converts into ordinary unit EXP from a base menu, one point
at a time or via a "fill to next level" quick-fill, capped so a single
session can't push a unit more than one level. It gives players agency over
who gets stronger without touching the combat/growth-rate system at all,
and can optionally guarantee 3 stat-ups per BEXP-granted level (a Radiant
Dawn-style leveling rule) instead of using the unit's normal growth rates.
The full grant → spend → level-up pipeline is implemented and reachable via
one event command each, but nothing in this project currently grants or
opens it.

## 2. Details

### 2.1 Constants

| Constant | Location | Meaning | Default |
|---|---|---|---|
| `bexp` | `constants.py:80` | Master toggle — adds "Bonus EXP" to the base menu | `False` |
| `rd_bexp_lvl` | `constants.py:81` | "Always gain 3 stat-ups when using Bonus Exp." — switches BEXP-driven level-ups to a fixed 3-stat-up roll instead of normal growth-rate rolls | `False` |

Both tagged `ConstantTag.MAJOR_FEATURES`. `bexp` alone gates the base-menu
entry (`app/engine/base.py:77-79`: `if DB.constants.value('bexp'): options.
insert(2, 'Bonus EXP')`); `rd_bexp_lvl` only changes the *leveling formula*
once BEXP is being spent (§2.4), it doesn't gate visibility.

### 2.2 Storage — a per-party integer, not a game_var

BEXP lives on `PartyObject` (`app/engine/objects/party.py:10,36`, default
`0`), included in save data (`party.py:49`, `55`). Accessors on
`GameState` — all operate on **the current party** (there's no
cross-party read without switching `current_party` first, though the
`give_bexp` event command can target any party explicitly):

- `get_bexp()` (`app/engine/game_state.py:1611-1618`)
- `inc_bexp(amount)` (`game_state.py:1620-1621`) — adds, no floor/ceiling
  applied at this level.
- `set_bexp(amount)` (`game_state.py:1623-1624`) — direct overwrite.

### 2.3 Granting BEXP — `give_bexp` event command

`GiveBexp` (nid `give_bexp`, tag `Tags.GAME_VARS`,
`app/events/event_commands.py:1902-1918`):

- Keyword: `Bexp` (Integer, required).
- Optional keywords: `Party` (defaults to the player's current party),
  `String` (custom banner text; default banner reads "Got X BEXP").
- Flag: `no_banner` — suppresses the notification banner entirely.
- Implementation `app/events/event_functions.py:1867-1885` →
  `action.do(action.GiveBexp(party_nid, bexp))`.
- The underlying action, `app/engine/action.py:1805-1821`: clamps the
  **floor at zero** (`if party.bexp + self.bexp < 0: self.bexp =
  -party.bexp`) — a negative `Bexp` argument can spend/remove BEXP via
  events too, but never below 0. Fully turnwheel-reversible.
- Also used internally by `merge_parties()`
  (`event_functions.py:2741-2743`) to transfer one party's BEXP into
  another's when parties merge.
- No automatic per-kill or per-chapter-clear grant exists anywhere in
  combat/chapter-end code — a designer must place `give_bexp` explicitly
  (e.g. on a chapter-clear event).

### 2.4 Spending BEXP — the base-menu flow

Entry point: `open_bexp_menu` event command (nid `open_bexp_menu`, tag
`Tags.MISCELLANEOUS`, `event_commands.py:3101-3114`; optional `Panorama`,
`Music`, `immediate` flag to skip the transition) →
`event_functions.py:3310-3323` → transitions to state `base_bexp_select`.
The base menu itself also exposes "Bonus EXP" directly when `bexp` is on
(§2.1), which goes to the same state.

Two states registered in `app/engine/state_machine.py:143-144`:

- **`BaseBEXPSelectState`** (`app/engine/base.py:1185-1246`) — a unit
  picker (subclass of `prep.PrepManageState`); units already at max level
  are disabled (auto-promote aware, lines 1188-1194). `SELECT` stores the
  unit in `game.memory['current_unit']` and moves to `base_bexp_allocate`.
- **`BaseBEXPAllocateState`** (`app/engine/base.py:1249-1402`) — the spend
  UI, `Choice` menu with **Right = +1 EXP, Left = -1 EXP (undo), Up = fill
  to next level, Down = reset, Select = confirm, Back = cancel**:
  - `determine_needed_bexp(unit)` (`base.py:1292-1298`) — reads
    `equations.parser.get('BONUS_EXP', unit)`; if a project defines a
    `BONUS_EXP` equation greater than 0, that's the EXP-to-next-level
    figure used; otherwise falls back to the hardcoded Radiant Dawn
    formula `max(1, 50 * internal_level + 50)`.
  - `get_bexp_cost_for_an_experience_point()` (`base.py:1300-1318`) —
    interpolates a per-exp-point BEXP cost from the needed-BEXP total, so
    if `bexp_needed > 100` each exp point costs more than 1 BEXP (and less
    than 1 if `bexp_needed < 100`).
  - **Caps**: a single confirm session cannot push a unit's exp past 100
    (`self.new_exp + exp_gain <= 100` gate, line 1340; same bound on the
    `Up` quick-fill loop, lines 1358-1368) and can't spend more BEXP than
    the party has (`self.new_bexp >= bexp_cost`). Reaching exactly 100
    resets exp to 0 and recomputes the needed-BEXP figure for the
    following level — one allocation only ever crosses one level boundary.
  - `Left`/`Down` can only undo back to the exp value the unit had when
    the menu opened (`original_exp`), not below it.
  - On `Select` (lines 1371-1387): if `rd_bexp_lvl` is on, sets
    `game.memory['exp_method'] = 'Bexp'`, queues `(unit, exp_to_gain, None,
    'init')` onto `game.exp_instance`, and transitions to the normal
    `'bonus_exp'` exp/level-up animation state to actually apply it; then
    persists the new BEXP total via `game.set_bexp(...)`.
  - Rendering: `menus.draw_unit_bexp()` (`app/engine/menus.py:74-97`) shows
    current/new EXP and current/new BEXP side by side.

### 2.5 Leveling formula when BEXP-driven

`unit_funcs.get_next_level_up()` checks `game.memory['exp_method'] ==
'Bexp'` (`app/engine/unit_funcs.py:233-234`) — if true, calls
`_rd_bexp_levelup(unit, level)` (`unit_funcs.py:183-213`), which grants
exactly 3 random stat-ups (respecting growth weighting and stat caps),
regardless of the unit's actual growth rates. This path is only taken when
`rd_bexp_lvl` is on; otherwise a BEXP-driven level-up rolls normal
growth-rate-based stat gains like any other level-up.

## 3. Code files

- `app/data/database/constants.py:80-81` — `bexp`, `rd_bexp_lvl` constants.
- `app/engine/objects/party.py:10,36,49,55` — `PartyObject.bexp` field,
  save/restore.
- `app/engine/game_state.py:1611-1624` — `get_bexp`/`inc_bexp`/`set_bexp`.
- `app/engine/action.py:1805-1821` — `GiveBexp` action (floor-at-zero,
  reversible).
- `app/events/event_commands.py:1902-1918,3101-3114` — `give_bexp`,
  `open_bexp_menu` event commands.
- `app/events/event_functions.py:1867-1885,3310-3323,2741-2743` —
  implementations, plus `merge_parties` BEXP transfer.
- `app/engine/base.py:77-79,1185-1246,1249-1402,1292-1318` — base-menu
  gate, `BaseBEXPSelectState`, `BaseBEXPAllocateState`,
  `determine_needed_bexp`/cost-curve.
- `app/engine/state_machine.py:143-144` — `base_bexp_select`/
  `base_bexp_allocate` state registration.
- `app/engine/menus.py:74-97` — `draw_unit_bexp` rendering helper.
- `app/engine/unit_funcs.py:183-213,233-234` — `_rd_bexp_levelup`, the
  `'Bexp'` exp-method branch.
- `app/engine/equations.py:70-73` — generic `EquationParser.get(lhs, unit)`
  fallback-to-0 lookup used for `BONUS_EXP`.

## 4. Working example in this repo

None. `lion_throne.ltproj/game_data/constants.json` sets both `bexp` and
`rd_bexp_lvl` to `false`; its `equations.json` defines 26 equations but no
`BONUS_EXP` (so `determine_needed_bexp` would always fall back to the
hardcoded Radiant Dawn formula if the feature were ever turned on); and a
grep of `events.json` for `give_bexp`/`open_bexp_menu` turns up nothing —
no event ever grants or opens Bonus EXP. The closest analogue authored in
this project is the Merchant's Donate-XP flow (already excluded/documented
separately), which is a different, market-based mechanism for moving EXP
into a unit outside combat, but does not touch `PartyObject.bexp` or the
`bexp` constant at all.

## 5. Test

No `tools/test_*.py` exercises BEXP — a case-insensitive grep across all 13
test files under `tools/` for "bexp" returns nothing. A
`tools/test_bexp.py` should exist that, after `harness.boot()`: calls
`action.do(action.GiveBexp(party_nid, 100))` and asserts `game.get_bexp()
== 100`; calls it again with a negative amount larger than the current
total and asserts the party floors at `0` rather than going negative;
drives `BaseBEXPAllocateState.take_input` (or calls its handlers directly)
through a `Right` sequence and asserts `new_exp` never exceeds 100 in one
session and `new_bexp` is decremented by the interpolated cost; and — with
`rd_bexp_lvl` set True and `game.memory['exp_method'] = 'Bexp'` — asserts
`unit_funcs.get_next_level_up()` returns exactly 3 stat-ups regardless of
the unit's authored growth rates.
