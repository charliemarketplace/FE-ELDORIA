---
name: configure-save-slots-and-chapter-cleanup
description: Control the save-slot prompt, mid-battle saving, save deletion, and a non-destructive chapter reset from inside an event script via SkipSave/BattleSave/DeleteSave/ForceChapterCleanUp.
---

## 1. Feature

Four `event_commands.py` "MISCELLANEOUS"/"LEVEL_VARS" commands let a
designer reach into the save system from a script, on top of the engine's
automatic end-of-level save prompt: skip that prompt entirely
(`SkipSave`), offer the player an ad-hoc mid-chapter save
(`BattleSave`), delete a specific save slot or the global suspend file
(`DeleteSave`), and reset the current chapter back to its start-of-turn
state without actually tearing down the level (`ForceChapterCleanUp`).
None of the four are called anywhere in this project's event data — the
only save/suspend paths this project actually exercises are the automatic
numbered-slot prompt at every level clear and the player-driven
Suspend/Save option in the pause menu.

## 2. Details

### 2.1 `skip_save;TrueOrFalse` (`event_commands.py:1020-1030`, `event_functions.py:671-672`)

- Required `Bool` keyword. Turnwheel-safe:
  `action.do(action.SetLevelVar('_skip_save', true_or_false))`.
- Consumed exactly once, at the *next* `level_end()`
  (`event_state.py:72`): `game.memory['_skip_save'] =
  game.level_vars.get('_skip_save', False)` — copied from the
  level-scoped var into the cross-level `game.memory` dict right before
  `game.clean_up()` runs.
- `TitleSaveState.start()` (`title_screen.py:874-881`) checks
  `game.memory.get('_skip_save', False)` first thing: if true, it
  immediately resets the flag to `False` and calls
  `go_to_overworld(make_save=False)` or `go_to_next_level(make_save=False)`
  depending on `game.game_vars['_should_go_to_overworld']`, then
  `return 'repeat'` — the numbered-slot `ChapterSelect` menu is never even
  built. `make_save=False` means `save.suspend_game()` is not called at
  all for that transition, so no save file is written.
- Default (never set, or set `False`): the normal flow runs — the player
  sees the slot-picker menu and a save is written when they confirm or
  press BACK.

### 2.2 `battle_save[;immediately]` (`event_commands.py:1048-1062`, `event_functions.py:677-685`)

- No required keyword; one flag, `immediately`.
- Without the flag: sets `self.battle_save_flag = True` on the running
  `Event`. `EventState.end_event()` (`event_state.py:169-174`) checks this
  flag *after* `_win_game`/`_lose_game`/`_main_menu`/`_enter_level` in a
  fixed priority chain — so a battle save queued in the same event as a
  win/lose/main-menu trigger loses to that trigger and never fires. When
  it does fire, `game.state.back()` pops the event state, sets
  `game.memory['save_kind'] = 'battle'` and `next_state =
  'in_chapter_save'`, and transitions — the save UI appears once the
  *whole event finishes*.
- With `immediately`: skips the flag entirely and jumps straight there
  mid-script — `self.state = 'paused'`,
  `game.memory['save_kind']='battle'`, `next_state='in_chapter_save'`,
  `game.state.change('transition_to')`. The event blocks until the save
  screen resolves before any later commands run.
- `in_chapter_save` and `title_save` are the *same* `TitleSaveState` class
  (`state_machine.py:60-61`); the instance's `.name` (set to whichever
  string was used to push it) is what makes `go_to_next_level`'s
  `if self.name == 'in_chapter_save'` branch treat it as a save mid-level
  rather than an end-of-level transition.

### 2.3 `delete_save[;SaveSlot]` (`event_commands.py:1064-1073`, `event_functions.py:687-691`) — has a live crash bug

- `SaveSlot` is optional. Documented behavior: "If *SaveSlot* is not
  provided, deletes the current save." The literal string `'suspend'`
  (case-insensitive) targets the single global suspend file instead of a
  numbered slot.
- **Bug**: the implementation is
  `def delete_save(self: Event, save_slot=None, flags=None): if
  save_slot.lower() == 'suspend': ...`. When `SaveSlot` is omitted, the
  parser never puts a `save_slot` key in `command.parameters` at all —
  `_parse_command` (`event_commands.py:3679-3691`) only adds a key for an
  argument actually supplied, and `convert_parse`
  (`event_commands.py:3740-3761`) only converts keys already present.
  `Event.run_command` (`event.py:426-432`) then calls
  `get_catalog()['delete_save'](self, **parameters, flags=flags)` with no
  `save_slot` kwarg, so the function's own default (`None`) is used, and
  `None.lower()` raises `AttributeError` before `save.delete_save()` is
  ever reached. **The documented "no argument = delete current save" path
  is unreachable — it crashes instead.** Passing an explicit numeric
  `SaveSlot` (a `str` digit, matching how `event_validators` hands string
  args to event functions) works fine, since `'0'.lower()` just returns
  `'0'` and falls through to `save.delete_save(self.game, save_slot)`
  (`save.py:221-238`, which removes the slot's `.p`/`.pmeta`/restart
  files). `'suspend'` also works and calls `save.delete_suspend()`
  (`save.py:217-219`).

### 2.4 `force_chapter_clean_up` (`event_commands.py:996-1018`, `event_functions.py:668-669`)

No keywords. Calls `game.clean_up(full=False)`
(`game_state.py:639-763`). Verified against that method line-by-line:

Always runs, `full` or not:
- `supports.increment_end_chapter_supports()`.
- Reset the turnwheel-uses budget:
  `game_vars['_current_turnwheel_uses'] = game_vars.get('_max_turnwheel_uses', -1)`.
- Every unit: `is_dying = False`; if carrying a traveler and not `full`,
  the traveler is dropped to the nearest open tile instead of forcibly
  un-rescued; full-heal HP/guard-gauge/mana (since `preserve_hp` is not
  exposed by this command and defaults to `False`); sprite reset.
- Every item/skill: `item_system.on_end_chapter`/`skill_system.on_end_chapter`.
- Dead player units: fatigue reset via `ChangeFatigue`; **resurrected**
  (`unit.dead = False`) if the current difficulty mode is *not*
  permadeath (i.e. casual mode), otherwise (permadeath) their tradeable
  items are moved into `self.parties[unit.party].convoy` if
  `convoy_on_death` is truthy (`game_state.py:742-753`).

Because `full=False`, it skips: `game.leave(unit)` for every unit (so
nothing is removed from the field), clearing
`terrain_status_registry`/`region_registry`, pruning non-persistent units
from `unit_registry`, pruning orphaned skills, `self.sweep()`, clearing
`_current_level`/`roam_info`. Instead it takes the `else` branch:
`self.turncount = 1` and `self.action_log.set_first_free_action()` — the
same turnwheel-history reset `clear_turnwheel` performs. This is the whole
of "resets the turnwheel" and "sets turncount to 1" from the command's own
docstring; both are confirmed at `game_state.py:761-762`.

### 2.5 Distinct from the player-facing pause menu

`OptionMenuState._populate_options()` (`general_states.py:423-430`) offers
`Suspend` in permadeath mode or `Save` otherwise; selecting either calls
the plain functions `suspend()` / `battle_save()`
(`general_states.py:391-406`), **not** the `battle_save` event command —
`suspend()` always writes to the single global suspend slot
(`save.suspend_game(game, 'suspend')`), while `battle_save()` (the
function) pushes `in_chapter_save` unconditionally, with no `immediately`
distinction because there's no event to finish first. These two paths
share `save.py`'s save/delete machinery with the event commands above but
are triggered by player input, not script.

### 2.6 Save-kind glossary (`SaveSlot.kind`, `save.py:34`)

`'start'` (new level begin), `'overworld'`, `'battle'` (mid-chapter,
either menu-driven or event-driven), `'suspend'` (one global file at
`SUSPEND_LOC`, outside the numbered `SAVE_SLOTS` array), and
`'turn_change'`/`'enemy_turn_change'` — an *automatic* per-turn snapshot
written by `TurnChangeState.save_state()` (`general_states.py:255-264`)
for the Turnwheel's own history, unrelated to any of the four commands
above (see `configure-turnwheel-rewind-limits`).

## 3. Code files

- `app/events/event_commands.py:996-1073` — `ForceChapterCleanUp`,
  `SkipSave`, `BattleSave`, `DeleteSave` command definitions.
- `app/events/event_functions.py:665-691` — their four implementations.
- `app/events/event_commands.py:3643-3761` — `_parse_command`/
  `convert_parse`, the parameter-filtering behavior behind the
  `delete_save` bug.
- `app/events/event.py:426-432` (`run_command`), `62-130` (`level_end`),
  `132-186` (`end_event`, the win/lose/main_menu/enter_level/battle_save/
  turnwheel priority chain).
- `app/engine/game_state.py:639-763` — `clean_up(full, preserve_hp)`.
- `app/engine/title_screen.py:862-1001` — `TitleSaveState`
  (`_skip_save` check at 874-881, `go_to_next_level`/`go_to_overworld` at
  912-933).
- `app/engine/general_states.py:391-406` (`suspend`/`battle_save`
  functions), `408-430` (`OptionMenuState._populate_options`),
  `255-264` (`TurnChangeState.save_state`).
- `app/engine/save.py` (full file) — `SaveSlot`, `suspend_game`,
  `delete_save`, `delete_suspend`, `check_save_slots`, `SAVE_SLOTS`.
- `app/data/database/constants.py:128` — `num_save_slots` (default `3`;
  this project's `constants.json:243-245` also sets `3`).

## 4. Working example in this repo

**Unused.** None of `skip_save`, `battle_save`, `delete_save`, or
`force_chapter_clean_up` appear in
`lion_throne.ltproj/game_data/events.json` (checked every event's
`_source` script text, all 72 events, zero matches). Every level clear in
this project goes through the plain automatic path:
`EventState.level_end()` (`event_state.py:62-130`) runs unconditionally
with `game.memory['_skip_save']` always `False` (never set), so the
player always sees the numbered `ChapterSelect` save-slot menu at
`TitleSaveState`. The only save-adjacent thing a player can trigger is the
pause menu's `Suspend` (this project uses whatever `permadeath` the
active `DifficultyMode` sets) via `general_states.py:391-399` — a
different code path from all four commands documented here.

## 5. Test

No `tools/test_*.py` calls `action.SetLevelVar('_skip_save', ...)`,
`event_functions.battle_save`, `event_functions.delete_save`, or
`event_functions.force_chapter_clean_up` — checked all files under
`tools/`. `game.clean_up(full=False, preserve_hp=...)` itself *is*
exercised (`tools/test_dungeon_floor.py:98-133`,
`tools/test_deploy_cap.py:185-220`), but only for the `preserve_hp`
HP-carry behavior; none of those tests touch `force_chapter_clean_up`'s
other `full=False` side effects (`turncount` reset, turnwheel-history
reset, dead-unit resurrection/convoy transfer). A
`tools/test_save_commands.py` should exist that: (1) calls
`event_functions.delete_save(fake_event)` with no `save_slot` argument and
asserts it currently raises `AttributeError` (documenting the bug rather
than silently tolerating it, so a future fix is visible as a test
change); (2) kills a player unit, sets casual mode, calls
`force_chapter_clean_up`'s underlying `game.clean_up(full=False)`, and
asserts `unit.dead is False` and `game.turncount == 1`; (3) does the same
in permadeath mode with `convoy_on_death` true and asserts the dead
unit's tradeable items land in `game.party.convoy` instead of being
resurrected.
