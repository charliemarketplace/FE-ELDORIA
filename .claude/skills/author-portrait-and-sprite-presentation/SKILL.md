---
name: author-portrait-and-sprite-presentation
description: Author dialogue-scene portrait staging beyond a bare add/remove — screen-position slots, slide-in/fade transitions, mirroring, walking a portrait across the screen, bopping for a reaction beat, and manual blink/mouth expression control.
---

## 1. Feature

`add_portrait`/`remove_portrait` are the two commands every LT dialogue
scene uses to put a character's face on screen, but the underlying
`EventPortrait` object supports a much larger vocabulary: named screen
slots with automatic left/right facing, two distinct transition styles
(darken-fade vs. directional slide), walking a portrait between slots
(`move_portrait`), flipping facing mid-scene (`mirror_portrait`), a
surprise "bop" bounce (`bop_portrait`), adding/removing up to four
portraits in one beat (`multi_add_portrait`/`multi_remove_portrait`), and
manual override of the idle blink/talk-mouth animation via `expression`.
There's also a separate, unit-level `change_portrait` that permanently
swaps which portrait resource a *unit* uses everywhere (not just the
current scene).

## 2. Details

### 2.1 Screen positions (`app/events/screen_positions.py`, full file)

`ScreenPosition` accepts either a named slot or a raw `(x, y)`:

| Horizontal name | x | Horizontal name | x |
|---|---|---|---|
| `OffscreenLeft` | -96 | `CenterRight` | `WINWIDTH-120` |
| `FarLeft` | -24 | `MidRight` | `WINWIDTH-120` |
| `LeftCorner` | -16 | `LevelUpRight` | `WINWIDTH-100` |
| `Left` | 0 | `Right` | `WINWIDTH-96` |
| `MidLeft` | 24 | `RightCorner` | `WINWIDTH-80` |
| `CenterLeft` | 24 | `FarRight` | `WINWIDTH-72` |
| | | `OffscreenRight` | `WINWIDTH` |

Vertical names: `Top` (0), `Middle` (`(WINHEIGHT-80)//2`), `Bottom`
(`WINHEIGHT-80`, the default when only a horizontal name/int is given).
A single unrecognized string resolves to `x=0` silently (`.get(p, 0)`,
`screen_positions.py:33-35`) — no error, the portrait just lands at the
left edge.

**Auto-mirroring**: `parse_screen_position` returns
`position[0] <= horizontal_screen_positions['CenterLeft']` (i.e. `x <= 24`)
as the default mirror flag (`screen_positions.py:46`) — portraits placed
on the left half of the screen face right by default, and vice versa,
without needing the `mirror` flag at all. The `mirror` flag on
`add_portrait` *inverts* whatever this auto-computed default would be
(`event_functions.py:136-137`), it doesn't set an absolute direction.

### 2.2 `add_portrait`/`multi_add_portrait` (`event_commands.py:395-429`, nicknames `u`/`uu`)

- `Portrait`, `ScreenPosition` required.
- `Slide` optional (`normal`/`left`/`right`, `event_validators.py:537-538`)
  — controls how the fade-in renders (§2.3), not the resting position.
- `ExpressionList` optional — initial blink/mouth state (§2.5).
- `SpeedMult` optional, default `1.0` — internally inverted to
  `1 / max(speed_mult, 0.001)` (`event_functions.py:142`), so *larger*
  `SpeedMult` values fade in *faster*.
- Flags: `mirror` (invert auto-facing), `low_priority` (drawn behind other
  portraits — implemented as `priority -= 1000`, `event_functions.py:132-133`),
  `immediate` (no fade), `no_block`.
- Adding a portrait whose `name` is already on screen (and not mid-removal)
  is a no-op — `add_portrait` returns `False` without replacing it
  (`event_functions.py:122-124`); use `remove_portrait` first or
  `change_portrait`/re-add after removing.
- `multi_add_portrait` (2-4 portraits) is a pure macro: it queues
  individual `AddPortrait` commands with `no_block` on all but the last
  (`event_functions.py:158-171`) — there's no true simultaneous variant
  under the hood, just back-to-back non-blocking adds.

### 2.3 Transition rendering — fade vs. slide (`app/events/event_portrait.py`)

- Default (no `Slide`): `draw()` darkens the portrait toward black as
  `transition_progress` goes 0→1 (`make_black_colorkey`,
  `event_portrait.py:292-296`) — a fade-from-black, not a fade-from-alpha.
- `Slide='left'`/`'right'`: instead renders with alpha translucency
  (`make_translucent`) *and* offsets the draw position by up to 24px
  (`slide_length`) in the given direction, closing to 0 offset as the
  transition completes (`event_portrait.py:300-304`) — the "walks/slides
  into place while fading in" look.
- `base_transition_speed = frames2ms(14)` (~233ms at 60fps,
  `event_portrait.py:30`), scaled by `1/SpeedMult`.

### 2.4 `remove_portrait`/`multi_remove_portrait` (`event_commands.py:431-463`, nicknames `r`/`rr`)

- `Portrait` required; `SpeedMult` (default `1.0`) and `Slide` optional,
  same semantics as add.
- Flags: `immediate` (instant disappear), `no_block`.
- Internally sets `EventPortrait.end()` (`event_portrait.py:311-317`),
  which reverses the transition direction (`self.remove = True` flips the
  fade progress calculation, `update()` lines 237-238) — remove reuses the
  exact same fade/slide machinery as add, just backwards.
- `multi_remove_portrait` (2-4 portraits) — same one-blocking-call-then-
  non-blocking-rest macro pattern as `multi_add_portrait`.

### 2.5 `expression` (`event_commands.py:513-524`, nickname `e`)

Sets the portrait's idle-animation override list. Valid tokens
(`event_validators.py:569-570`): `NoSmile`, `Smile`, `NormalBlink`,
`CloseEyes`, `HalfCloseEyes`, `OpenEyes`, `OpenMouth`. These aren't emotion
icons — they directly select which mouth/eye sub-image
`EventPortrait.create_image()` blits each frame
(`event_portrait.py:177-219`): `OpenMouth` forces the mouth open
regardless of the automatic talk-animation state; `Smile` swaps the
closed/half/open mouth sprites for their "smiling" variants;
`CloseEyes`/`HalfCloseEyes`/`OpenEyes` override the idle blink cycle
(which otherwise runs on its own timer, `blink_counter`,
`event_portrait.py:77,208-213`) — omit all three and the portrait blinks
naturally at random. Passing no list at all (`add_portrait` without
`ExpressionList`) leaves `self.expressions = set()`, i.e. natural blink,
mouth state driven purely by whether the portrait's `talk()` has been
triggered by an active `speak`.

### 2.6 `move_portrait` (`event_commands.py:465-482`)

Animates the portrait sliding from its current position to a new
`ScreenPosition` (not a re-fade — the portrait stays fully visible and
walks). `SpeedMult` default `1.0`; travel time is computed from pixel
distance via `determine_travel_time` (`event_portrait.py:122-129`,
roughly capped step-size per frame) then divided by `speed_mult`
(`event_portrait.py:116-117`). Flags: `immediate` (`quick_move`, instant
teleport, no animation) and `no_block`.

### 2.7 `bop_portrait` (`event_commands.py:484-496`, nickname `bop`)

No position/expression args — just `Portrait`. Bounces the portrait
vertically twice by default (`bop(num=2, height=2)`,
`event_portrait.py:104-108`), each bop lasting `bop_time = frames2ms(8)`.
Only flag is `no_block` (default blocks for `666`ms,
`event_functions.py:282`, a hardcoded duration independent of the actual
bop animation length).

### 2.8 `mirror_portrait` (`event_commands.py:498-511`, nickname `mirror`)

Flips a portrait's facing across the Y axis by constructing a *replacement*
`EventPortrait` with `mirror` inverted (`event_functions.py:237-243`) — it
is not a simple boolean toggle on the existing object. `SpeedMult` default
`1.0`. Flags: `no_block`, and `fade` — without `fade`, the flip is an
instant position-preserving swap (or, if not skipping, a re-fade-in using
the new mirrored image, `event_functions.py:262-269`); with `fade`, it
decomposes into an explicit `remove_portrait` + `add_portrait` pair
(computing the new auto-mirror flag for the re-add based on which half of
the screen the portrait is on, `event_functions.py:250-260`) — the only
one of these commands that expands into other event commands rather than
mutating state directly.

### 2.9 `change_portrait` (`event_commands.py:2092+`, `event_functions.py:2088-2097`)

Not a screen-staging command — this permanently changes which portrait
*resource* a **unit** (not an on-screen `EventPortrait` slot) uses from
then on, via `action.ChangePortrait(unit, portrait_nid)`. Errors (logs,
no-ops) if the unit or the target portrait nid don't resolve. Useful for a
mid-story appearance change (injury, disguise reveal) that should persist
in every future scene featuring that unit, not just the current one.

### 2.10 What happens if you omit fields

- No `ExpressionList` → natural blink/talk-driven mouth, no forced state.
- No `Slide` → default black-fade transition, no positional slide.
- No `SpeedMult` on any command → `1.0`, i.e. the base speed for that
  command (233ms fade, hardcoded bop/travel timings, etc.).
- `mirror_portrait`/`move_portrait`/`bop_portrait` on a `Portrait` name
  that isn't currently on screen → all three just `return False` quietly
  (`event_functions.py:176-212,232-233,276-277`), no error logged, no
  crash.

## 3. Code files

- `app/events/event_commands.py:395-524` — all eight portrait commands
  (`AddPortrait` through `Expression`), plus `ChangePortrait` at `:2092+`.
- `app/events/event_functions.py:118-291` — every implementation in
  §2.2-§2.8; `:2088-2097` — `change_portrait`.
- `app/events/screen_positions.py` (full file) — named slot tables and
  `parse_screen_position`'s auto-mirror rule.
- `app/events/event_portrait.py` (full file, 318 lines) — `EventPortrait`:
  transition/slide rendering (`draw`, 283-309), movement math
  (`move`/`quick_move`/`determine_travel_time`, 110-129), bop state
  machine (104-108, 274-279), talk-driven mouth animation
  (`update_talk`, 137-175), and expression-to-subimage mapping
  (`create_image`, 177-219).
- `app/events/event_validators.py:537-538` (`Slide`), `569-581`
  (`ExpressionList`).

## 4. Working example in this repo

Live, but only the plain baseline. Event nid `S1 Intro`
(`lion_throne.ltproj/game_data/events.json`, level `S1`, trigger
`level_start`) opens with `add_portrait;Halvard;Left`, and every one of
this project's roughly 76 `add_portrait`/76 `remove_portrait` calls across
all events uses only the two required keywords — a bare `Portrait` and a
named `ScreenPosition` (`Left`/`Right`/`MidLeft`/`MidRight`), relying
entirely on auto-mirroring and the default fade. **`Slide`,
`ExpressionList`, `SpeedMult`, `mirror`/`low_priority`/`immediate` flags,
`move_portrait`, `bop_portrait`, `mirror_portrait`,
`multi_add_portrait`/`multi_remove_portrait`, `expression`, and
`change_portrait` are never used anywhere in this project's event data** —
every scene is staged with static, non-mirrored, default-speed fades. The
richer half of this system (walking portraits, slide-ins, forced
expressions, reaction bops) is fully implemented and available but
entirely unauthored here.

## 5. Test

No `tools/test_*.py` references `EventPortrait`, `bop_portrait`,
`mirror_portrait`, or `move_portrait` (checked all files under `tools/`).
The bare word "expression" appears in `tools/test_playthrough.py` and
`tools/verify_text_interpolation.py`, but both uses are about Python
expression evaluation in event text/game_vars, unrelated to the
`expression`/`ExpressionList` portrait command. A
`tools/test_portrait_staging.py` should exist that: constructs an `Event` and calls `add_portrait` with
should exist that: constructs an `Event` and calls `add_portrait` with
`ScreenPosition='Left'`, asserting the resulting `EventPortrait.mirror` is
`True` (left-half auto-face-right) without the `mirror` flag, then again
with the `mirror` flag set and asserting it flips to `False`; calls
`bop_portrait` on that portrait and asserts `bops_remaining == 2`; and
calls `move_portrait` to a new position, then steps `update()` until
`moving` is `False`, asserting the final `position` equals the target
exactly (proving the travel-time interpolation actually converges rather
than overshooting or stalling).
