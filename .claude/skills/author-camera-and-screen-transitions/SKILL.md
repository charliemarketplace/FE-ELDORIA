---
name: author-camera-and-screen-transitions
description: Author cutscene camera work — fade transitions, background panoramas, cursor pans/centers/flickers, and screen shake — for scripted events, distinct from dialogue/portrait content.
---

## 1. Feature

A family of `event_commands.py` "BG_FG"/"CURSOR_CAMERA" commands let a
designer direct the *screen itself* during an event: fade a scene to black
and back (`transition`), swap or scroll the backdrop panorama
(`change_background`, `pause_background`/`unpause_background`), move or
snap the map camera and cursor to a location (`move_cursor`,
`center_cursor`, `flicker_cursor`), toggle whether the cursor is drawn at
all (`disp_cursor`), and shake the whole screen for impact
(`screen_shake`/`screen_shake_end`). Each has an `immediate`/`no_block`
flag pair so the designer controls whether the script waits for the effect
to finish or lets it play out in the background while dialogue continues.

## 2. Details

### 2.1 `transition` (`app/events/event_commands.py:668-686`, nickname `t`)

- No required keywords. Calling it with nothing toggles: fades to black if
  a scene is showing, or fades back in if it's already faded out
  (`app/events/event_functions.py:416-424`, tracked via `self.transition_state` on the `Event`).
- `Direction` (optional) explicitly forces `'open'`/`'close'` instead of
  toggling.
- `Speed` (optional, ms) — defaults to `self._transition_speed = 250` ms
  (`app/events/event.py:47,138`); the actual wait is `int(speed * 1.33)`
  when blocking.
- `Color3` (optional) — defaults to black `(0, 0, 0)` (`event.py:48,139`).
- `Panorama` (optional) — swaps in a `PanoramaBackground` to show *during*
  the transition itself (distinct from `change_background`'s persistent
  scene background).
- `no_block` flag — script continues executing while the fade plays; without it, the event pauses for the fade's duration.

### 2.2 `change_background` (`event_commands.py:688-703`, nickname `b`)

- `Panorama` optional — omitting it removes the current background
  entirely rather than changing it (also used to just clear a scene).
- `keep_portraits` flag — normally changing/clearing the background clears
  every currently-displayed portrait (`event_functions.py:451-454`); this
  flag preserves them.
- `scroll` flag — background pans continuously rather than sitting static
  (`background.create_background(panorama, True)` vs. `(panorama, False)`,
  `event_functions.py:446-449`).
- `pause_background`/`unpause_background` (`event_commands.py:705-724`,
  `event_functions.py:456-466`) — freeze/unfreeze an animated (multi-frame)
  panorama; `PauseAt` picks a specific frame to hold on. Logs a warning
  (not an error) and no-ops if there's no current background to pause.

### 2.3 Cursor/camera movement (`Tags.CURSOR_CAMERA`)

- `disp_cursor;ShowCursor` (`event_commands.py:726-736`) — pure visibility
  toggle, `game.cursor.show()`/`hide()`.
- `move_cursor;Position[;Speed]` (`event_commands.py:738-755`, nickname
  `set_cursor`) and `center_cursor;Position[;Speed]`
  (`event_commands.py:758-774`) — the only functional difference is
  `move_cursor` sets the camera's *top-left* target
  (`camera.set_xy`/`force_xy`) while `center_cursor` centers the viewport
  on the position (`camera.set_center`/`force_center`,
  `event_functions.py:474-521`). `Position` accepts a raw `(x, y)` tile
  coordinate or a unit/region reference the `Position` validator resolves.
  `Speed` (optional) switches the camera to `do_slow_pan(duration)`
  (constant-speed, ms-based) instead of the default distance-scaled ease
  (`camera.py:190-192` vs. the default algorithm in `get_next_position`,
  `camera.py:43-60`).
  - `immediate` flag → `camera.force_xy`/`force_center`, an instant snap,
    no travel.
  - `no_block` flag → script continues while the camera pans; otherwise
    the event pushes the `move_camera` state
    (`app/engine/general_states.py:840-848`) and blocks until
    `game.camera.at_rest()`.
- `flicker_cursor;Position` (`event_commands.py:776-787`, nickname
  `highlight`) — a macro, not a separate camera mechanism: it enqueues
  `move_cursor` (with whatever flags were passed through, including
  `immediate`) → `disp_cursor;true` → `wait;1000` →`disp_cursor;false`
  (`event_functions.py:522-533`) — i.e. it moves the camera there and
  blinks the cursor on for one second.

### 2.4 `screen_shake`/`screen_shake_end` (`event_commands.py:789-813`)

- `Duration` required (ms). **Set it to `0` for an indefinite shake** that
  only ends when `screen_shake_end` is explicitly called
  (`camera.set_shake`, `camera.py:194-202`: `if duration > 0: self.shake_end_at = ...` — `0` or negative never sets an end time).
- `ShakeType` optional, one of `default`/`combat`/`kill`/`random`/`celeste`
  (`event_validators.py:704-705`), each a hardcoded list of `(x, y)` pixel
  offsets cycled every frame (`event_functions.py:539-549`):
  - `default`: a small double-bounce, `[(0,-2),(0,-2),(0,0),(0,0)]`.
  - `combat`: a 3px lateral rock, `[(-3,-3),(0,0),(3,3),(0,0)]`.
  - `kill`: an 8-frame violent shake sequence.
  - `random`: 16 frames of `random.randint(-4,4)` per axis.
  - `celeste`: 16 frames of `random.choice([-1,1])` per axis (a tighter,
    "Celeste"-style jitter).
  - An unrecognized `ShakeType` logs an error and the command no-ops
    (`event_functions.py:551-553`) — it does **not** fall back to
    `default`.
- Shake is applied to both `game.camera` and, if present, the current
  event `background` (`event_functions.py:555-558`), so a panorama shakes
  along with the map.
- `no_block` flag — otherwise the event waits out the full `Duration`.
- `screen_shake_end` (`event_commands.py:805-813`) calls
  `camera.reset_shake()`/`background.reset_shake()` — the only way to stop
  a `Duration=0` (indefinite) shake, and also usable to cut a timed shake
  short.

### 2.5 What happens if you omit fields

- `transition` with zero keywords just toggles open/closed using whatever
  speed/color was last set (or the 250ms/black defaults on the very first
  call).
- `move_cursor`/`center_cursor` without `Speed` use the default
  distance-proportional ease, not a fixed duration.
- `screen_shake` without `ShakeType` → `'default'`.
- `screen_shake` with `Duration` omitted is not possible — it's a required
  keyword; a malformed/missing value would fail command parsing before
  reaching `screen_shake()` at all.

## 3. Code files

- `app/events/event_commands.py:668-813` — all nine commands
  (`Transition`, `ChangeBackground`, `PauseBackground`,
  `UnpauseBackground`, `DispCursor`, `MoveCursor`, `CenterCursor`,
  `FlickerCursor`, `ScreenShake`, `ScreenShakeEnd`).
- `app/events/event_functions.py:416-568` — every implementation above.
- `app/events/event.py:47-48,135-139` — default transition speed/color
  and the `Event` instance's live transition state.
- `app/engine/camera.py:43-60,124-202` — the panning algorithm, `set_xy`/
  `force_xy`/`set_center`/`force_center`/`do_slow_pan`, and `set_shake`/
  `reset_shake`.
- `app/engine/general_states.py:840-848` — `MoveCameraState`, the blocking
  state `move_cursor`/`center_cursor` push when not `no_block`.
- `app/events/event_validators.py:704-705` — `ShakeType` valid options.

## 4. Working example in this repo

Live. Event nid `S3 Intro` (`lion_throne.ltproj/game_data/events.json`,
level `S3`, trigger `level_start`) runs:
```
center_cursor;2,2
flicker_cursor;2,2
map_anim;StatUpSpark;2,2;permanent;no_block
move_cursor;Rowan
```
— centering the camera on tile `(2,2)`, flickering the cursor there, then
panning to the unit `Rowan`, all with default (blocking, ease-in) speed.
`transition;Open`/`transition;Close` are used 64 times project-wide (28
`Close` + 36 `Open`) — always the bare toggle form, never with an explicit
`Speed`, `Color3`, or `Panorama`. `change_background` is used 17 times
(e.g. `change_background;House`, `change_background;Cave`) — always with
just a `Panorama`, never `keep_portraits`, `scroll`, `pause_background`, or
`unpause_background`. **`screen_shake`/`screen_shake_end` are never called
anywhere in this project's event data** — the shake system is fully wired
into the engine (`camera.py`, `background.py`) but unused here; the
closest analogue is the combat-hit screen flash/impact system, which is a
separate mechanism from this event command.

## 5. Test

No `tools/test_*.py` references `screen_shake`, `ScreenShakeEnd`,
`move_cursor`, `center_cursor`, or `camera.set_shake` (checked all files
under `tools/`). A `tools/test_camera_commands.py` should exist that:
drives the `Event` object through a `transition;Close` then asserts
`event.transition_state == 'close'`; calls `screen_shake;0` then asserts
`game.camera.shake_end_at == 0` and `game.camera.shake` is the non-default
offset list, then calls `screen_shake_end` and asserts `game.camera.shake
== game.camera.no_shake`; and calls `move_cursor` with `immediate` set and
asserts `game.camera.current_x/current_y` snap directly to the target
tile's pixel position rather than easing toward it over multiple `update()`
ticks.
