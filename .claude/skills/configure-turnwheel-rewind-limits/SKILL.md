---
name: configure-turnwheel-rewind-limits
description: Cap how many times the player can rewind with the Turnwheel, force a rewind after a scripted death, or permanently lock in history, for a designer tuning how forgiving mistakes are allowed to be.
---

## 1. Feature

Turning the Turnwheel on is a two-step gate, not one: the `turnwheel` DB
constant only makes the *feature exist*; a separate `_turnwheel` game_var
(set via an event command) has to be switched on before the menu option
actually appears — a project can enable the constant and still never show
the player a Turnwheel. Once genuinely on, a designer can cap total rewinds
per chapter (`_max_turnwheel_uses`), force a mandatory rewind right after a
scripted death (`activate_turnwheel`), permanently lock in everything that
happened up to a point so it can never be undone (`clear_turnwheel`), and
even pause/resume the underlying action recording for a scripted sequence
that shouldn't itself be reversible. The engine also auto-locks rewinding
past the start of the enemy phase, independent of anything an author does.

## 2. Details

### 2.1 The two-part on switch

| Gate | Kind | Meaning | Default |
|---|---|---|---|
| `turnwheel` | DB constant (`app/data/database/constants.py:70`) | Master feature toggle | `False` |
| `_turnwheel` | game_var, author-set | Whether the "Turnwheel" pause-menu option is actually shown | unset (falsy) |

Both must be truthy — checked together at
`app/engine/general_states.py:448-452`
(`if DB.constants.get('turnwheel').value and game.game_vars.get('_turnwheel')
and not game.is_roam():`). `_turnwheel` is set via the event command
`enable_turnwheel` (nid `enable_turnwheel`, `app/events/event_commands.py:
920-931`), whose own description spells out the two-gate design: *"Activates
or deactivates turnwheel. You will also need the Constant checked to see the
turnwheel option in your menu."*

### 2.2 Rewind-uses budget (game_vars, not a DB constant)

- `_max_turnwheel_uses` (int; `-1` = unlimited) — set like any generic game
  var (the `game_var`/`inc_game_var` commands), no dedicated event command
  exists for it.
- `_current_turnwheel_uses` — the remaining counter. Reset to
  `_max_turnwheel_uses` (default `-1`) inside `GameState.clean_up`
  (`app/engine/game_state.py:664-665`) — i.e. **the budget refills every
  level/chapter transition**, it is not a whole-game-long allowance unless an
  author changes `_max_turnwheel_uses` itself between chapters.
- Decremented only on an actual confirmed rewind, and only if not unlimited:
  `if game.game_vars['_current_turnwheel_uses'] > 0:
  game.game_vars['_current_turnwheel_uses'] -= 1` (`app/engine/turnwheel.py:
  563-564`, inside `TurnwheelState.take_input`).
  The pause-menu Turnwheel option itself checks
  `game.game_vars.get('_current_turnwheel_uses', 1) > 0` before letting the
  player enter (`general_states.py:566-573`) — showing an
  `"Turnwheel_empty"` banner and refusing entry once the budget hits `0`.
  `TurnwheelDisplay` draws a "`N` Left" readout whenever
  `_max_turnwheel_uses > 0` (`turnwheel.py:466-472`).

### 2.3 Forced / optional rewind (`activate_turnwheel` event command)

- `ActivateTurnwheel` (nid `activate_turnwheel`, `app/events/
  event_commands.py:1032-1046`, optional keyword `Force`, `Bool`, default
  `true`) → sets `game.memory['force_turnwheel']` and transitions into the
  `turnwheel` state (`app/events/event_state.py:176-184` reacts to the
  event's turnwheel-activation flag). Typical use: call this right after a
  scripted/plot-critical death so the player is dropped straight into the
  Turnwheel.
- `TurnwheelState.begin()` (`app/engine/turnwheel.py:474-483`) reads
  `self.force = game.memory.get('force_turnwheel', False)`. When `force` is
  true, `take_input`'s `BACK` handling and its no-rewind-selected branch both
  refuse to exit (`turnwheel.py:565-574`) — the player is stuck in the
  Turnwheel until they actually confirm a rewind. `Force: false` makes the
  same interface optional (cancelable).

### 2.4 Locking history (independent of the uses budget)

- `LockTurnwheel` action (`app/engine/action.py:520-522`) marks a point past
  which `ActionLog.can_use()` refuses to rewind (`can_use` =
  `is_turned_back() and not self.locked`, `turnwheel.py:344-348`;
  `get_last_lock()` walks backward through the log for the most recent
  `LockTurnwheel` marker, `turnwheel.py:326-333`).
- **Automatic lock, no authoring needed**: every time the phase changes,
  `action.do(action.LockTurnwheel(game.phase.get_current() != 'player'))`
  fires (`app/engine/general_states.py:219`) — i.e. the engine locks
  rewinding the instant it's no longer the player's phase, which is the
  built-in "can't rewind past the start of the enemy phase" behavior, wholly
  separate from the death-only-forced-rewind pattern in §2.3. Events also
  lock/unlock around their own execution (`app/events/event_state.py:25,138`)
  so a mid-event moment can't be rewound into.
- `ClearTurnwheel` event command (nid `clear_turnwheel`,
  `event_commands.py:1075-1083`) → `ActionLog.set_first_free_action()`
  (`turnwheel.py:368-370` sets the earliest index the wheel will ever show)
  — a *permanent* trim of history, unlike `LockTurnwheel` which just blocks
  further rewinding without discarding the log.
- `StopTurnwheelRecording`/`StartTurnwheelRecording` event commands
  (`event_commands.py:1085-1108`) toggle whether new actions are appended to
  the log at all (`ActionLog.stop_recording`/`start_recording`,
  `turnwheel.py:380-387`) — for wrapping a scripted sequence that must not be
  individually rewindable; the docs warn to always re-enable recording
  afterward, and note the `on_turnwheel` trigger
  (`app/events/triggers.py:301-308`, fired after a rewind completes) starts
  with recording off by default.

## 3. Code files

- `app/data/database/constants.py:70` — the `turnwheel` DB constant.
- `app/engine/general_states.py:219,448-452,566-573` — the enemy-phase
  auto-lock, pause-menu two-gate check, and uses-budget check.
- `app/engine/game_state.py:639,664-665` — `GameState.clean_up`'s
  per-chapter uses-budget reset.
- `app/engine/turnwheel.py:326-348,368-387,466-483,540-574` —
  `ActionLog.can_use`/`get_last_lock`/`set_first_free_action`/
  `stop_recording`/`start_recording`; `TurnwheelState.begin`/`take_input`
  (force handling, uses decrement).
- `app/engine/action.py:520-522` — `LockTurnwheel`.
- `app/events/event_commands.py:920-931,1032-1108` —
  `EnableTurnwheel`, `ActivateTurnwheel`, `ClearTurnwheel`,
  `Stop`/`StartTurnwheelRecording`.
- `app/events/event_state.py:25,138,176-184` — event-triggered
  turnwheel lock/activation.

## 4. Working example in this repo

`lion_throne.ltproj/game_data/constants.json` sets `"turnwheel": true` — but
grepping `lion_throne.ltproj/game_data/events.json` for `enable_turnwheel`,
`activate_turnwheel`, `clear_turnwheel`, or any `_turnwheel`/
`_max_turnwheel_uses` game_var assignment turns up nothing. Since
`_turnwheel` defaults to falsy and nothing in this project's content ever
sets it true, **the Turnwheel pause-menu option never actually appears in
this game as currently authored**, despite the constant being on — a real,
citable gap between "feature flag enabled" and "feature reachable." The
enemy-phase auto-lock (§2.4) is unaffected by any of this — it's unconditional
engine behavior, not authored, so history is always trimmed at phase changes
regardless of whether the Turnwheel UI itself is reachable. There is no
project-authored analogue for the uses-budget, forced-rewind, or manual
lock/clear commands either; the closest comparison is the automatic
per-phase `LockTurnwheel` call, which fires on every level regardless of
authoring.

## 5. Test

No `tools/test_*.py` drives `TurnwheelState`, checks
`_max_turnwheel_uses`/`_current_turnwheel_uses` depletion, or verifies the
`_turnwheel` gate. Existing tests only assert the general principle that
game state changes go through turnwheel-safe `Action` subclasses (e.g.
`tools/test_merchant.py` manually reverses a donate-XP action sequence;
`tools/test_skill_check.py` asserts `AddSkillCheck`/`RemoveSkillCheck` are
reversible) — none exercise the rewind-limiting mechanism itself. A
`tools/test_turnwheel_limits.py` should exist that, after `harness.boot()`,
sets `game.game_vars['_turnwheel'] = True` and
`game.game_vars['_max_turnwheel_uses'] = 2`, calls `GameState.clean_up()` and
asserts `_current_turnwheel_uses == 2`, then simulates two confirmed rewinds
via `TurnwheelState.take_input` and asserts the counter reaches `0` and the
`"Turnwheel_empty"` banner path triggers on a third attempt; a second case
should assert `action.LockTurnwheel` fires automatically on an enemy-phase
transition and that `ActionLog.can_use()` returns `False` for any action
recorded before that lock.
