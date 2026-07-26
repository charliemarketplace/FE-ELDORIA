---
name: author-chapter-title-objectives-and-narration
description: Author the chapter-title interstitial screen, rewrite a level's win/loss/simple objective text mid-chapter, and stage full-screen narration mode for cutscenes.
---

## 1. Feature

Three unrelated presentation systems, all authored from events. `chapter_title`
brings up the full-screen chapter-title interstitial (sigil, ribbon banner,
music) that normally only plays automatically at certain points, letting a
designer replay it with a custom name/track mid-script. `change_objective_simple`/
`change_objective_win`/`change_objective_loss` rewrite the three pieces of a
level's static objective text (the ones shown in the pause menu's Objective
screen and the on-map objective banner) at runtime — useful when a chapter's
win condition changes partway through (a rout chapter that becomes a seize
chapter once a gate opens, for instance). `toggle_narration_mode` phases a
whole-screen narration frame in or out for narrator-style storytelling,
distinct from ordinary dialogue boxes and portraits.

## 2. Details

### 2.1 `chapter_title[;Music][;String]` (`event_commands.py:2960-2969`, `event_functions.py:3115-3123`)

- Both keywords optional. `Music` is any resource nid from the `Music`
  validator, or omitted; `String` is the display name, or omitted.
- Stores `game.memory['chapter_title_music']` (resolved via `self._resolve_nid`,
  so it also accepts a live `SongObject`/`SongPrefab` reference, not just a
  literal nid string) and `game.memory['chapter_title_title']`, ends any
  active event-skip (`self.do_skip = self.super_skip = False` — the title
  screen is never allowed to be skipped through), pushes the `chapter_title`
  state, and pauses the event until the player dismisses it.
- `ChapterTitleState.start()` (`app/engine/chapter_title.py:17-48`) resolves
  the two optionals: `self.title = game.memory.get('chapter_title_title') or
  game.level.name` — omit `String` and it falls back to the *current*
  level's name. Music: tries `game.memory.get('chapter_title_music')` first;
  if that's falsy, fades in the hardcoded fallback track `'Chapter Sound'`
  (`chapter_title.py:38-39`) — there is no "no music" option short of pointing
  `Music` at a silent/empty track.
- The screen runs an unskippable animated sequence (sigil fade-in → ribbon
  grow → 5000ms hold → sigil fade-out → ribbon close) and is dismissed early
  by `START`/`SELECT`/`BACK` (`chapter_title.py:50-56`), which stops the music
  if it was the one that started playing.

### 2.2 `change_objective_simple`/`change_objective_win`/`change_objective_loss;EvaluableString` (`event_commands.py:2585-2616`, `event_functions.py:2636-2643`)

- Each takes one required `EvaluableString` keyword and calls
  `action.do(action.ChangeObjective(key, evaluable_string))`
  (`action.py:3449-3459`, turnwheel-reversible: `reverse()` restores the old
  string) where `key` is `'simple'`/`'win'`/`'loss'` respectively. This just
  overwrites `game.level.objective[key]` — a plain dict on the running
  `LevelObject`, seeded from `LevelPrefab.objective`
  (`app/data/database/levels.py:11,22`, `OBJECTIVE_KEYS = ['simple', 'win',
  'loss']`, each defaulting to `''`).
- `EvaluableString`'s validator (`event_validators.py:389-390`) sets
  `can_preprocess = False`, meaning the raw text is **not** evaluated at
  parse time — it's stored verbatim and only run through
  `TextEvaluator._evaluate_all` when the objective screen is actually drawn
  (`objective_menu.py:79-80,85-86`), so `{tags}` referencing live game state
  (unit names, counts, etc.) resolve fresh every time the player opens the
  menu, not at the moment the event set the string.
- Where each key is displayed: `'win'`/`'loss'` only appear in the full
  Objective screen (`app/engine/objective_menu.py:78-88`, `ObjectiveMenuState`,
  reached via the pause menu's `Objective` option); `'simple'` is the
  one-line always-on-map objective hint (`app/engine/ui_view.py:177,317`).
  There is no single call that updates all three — a chapter whose win
  condition changes needs all three `change_objective_*` calls fired
  together if the on-map hint should match the full screen.
- Omitting a level's objective in its own authoring (leaving the default
  `''`) just shows an empty line in both places; nothing crashes.

### 2.3 `toggle_narration_mode;Direction[;Speed]` (`event_commands.py:3408-3414`, `app/events/overworld_event_functions.py:245-270`)

- Despite living in `overworld_event_functions.py`, this command is not
  overworld-specific — `function_catalog.get_catalog()`
  (`app/events/function_catalog.py:16-19`) merges `event_functions` and
  `overworld_event_functions` into one dispatch table, and the function
  only touches `self.overlay_ui`, which every `Event` has regardless of
  context.
- `Direction` is required and restricted to exactly `"open"`/`"close"`
  (`event_validators.py:557-558`, `class Direction(OptionValidator)`) —
  any other value is rejected at parse time, not silently treated as
  either state.
- `Speed` is optional, in ms; defaults to `1000` (`anim_duration = 1000`
  when `speed` is falsy). Both the top bar and bottom text area of the
  narration frame slide in/out and fade over this duration
  (`narration_dialogue.py:62-82`, the `!enter`/`!exit` named animations).
- First call lazily builds a `NarrationDialogue` child named
  `'event_narration'` on `self.overlay_ui` and disables it; every
  subsequent call reuses that same instance. `open` calls `.enter()` and
  blocks the event (`self.state = 'waiting'`) for `anim_duration`; anything
  else (in practice only `"close"`, since `Direction` rejects other values)
  calls `.exit()` and blocks the same way. There is no `no_block`/`immediate`
  flag — the wait is unconditional (except during a full event skip, where
  `self.do_skip` suppresses the `.enter()`/`.exit()` calls entirely, per the
  `if not self.do_skip:` guard at `overworld_event_functions.py:260`).
- Once open, `narrate;Speaker;String[;no_block]` (`event_commands.py:651-666`,
  `overworld_event_functions.py:273-296`) pushes a line into the narration
  box (`narration_component.push_text`), registers a hurry-up input handler,
  and blocks (`self.state = 'blocked'`) until the box finishes displaying —
  unless `no_block` is set. **`narrate` is tagged `Tags.HIDDEN` in
  `event_commands.py:653`, i.e. deprecated** — its own docstring still
  requires `toggle_narration_mode;open` to have run first, and calling
  `narrate` before that logs an error and no-ops
  (`overworld_event_functions.py:274-276`).

## 3. Code files

- `app/events/event_commands.py:2585-2616` (`ChangeObjectiveSimple`/`Win`/`Loss`),
  `2960-2969` (`ChapterTitle`), `651-666` (`Narrate`, hidden/deprecated),
  `3408-3414` (`ToggleNarrationMode`).
- `app/events/event_functions.py:2636-2643` (objective changes),
  `3115-3123` (`chapter_title`).
- `app/events/overworld_event_functions.py:245-296` (`toggle_narration_mode`,
  `narrate`).
- `app/events/function_catalog.py:9-20` — why an "overworld" function is
  callable from a non-overworld event.
- `app/engine/chapter_title.py` (full file) — `ChapterTitleState`.
- `app/engine/objective_menu.py:16-91` — `ObjectiveMenuState`, win/loss
  rendering via `TextEvaluator`.
- `app/engine/ui_view.py:177,317` — the on-map `'simple'` objective hint.
- `app/engine/action.py:3449-3459` — `ChangeObjective`.
- `app/data/database/levels.py:11,22` — `OBJECTIVE_KEYS`, `LevelPrefab.objective`
  default.
- `app/engine/graphics/dialog/narration_dialogue.py` (full file) —
  `NarrationDialogue`.
- `app/events/event_validators.py:389-390` (`EvaluableString`), `557-558`
  (`Direction`).

## 4. Working example in this repo

**`chapter_title`, `toggle_narration_mode`, and `narrate` are never called**
— checked every event's `_source` script text across all 72 entries in
`lion_throne.ltproj/game_data/events.json`, zero matches for any of the
three. The chapter-title screen the player actually sees is never
triggered by an event in this project at all (there is no other call site
for the `chapter_title` state outside this one event command), so in this
project's current build the sigil/ribbon interstitial never appears.
`change_objective_simple`/`win`/`loss` are likewise never called by any
event, but the underlying `objective` dict they'd rewrite **is** live data
— every one of the 7 levels authors static `simple`/`win`/`loss` text
directly in `lion_throne.ltproj/game_data/levels.json` (e.g. `S3`:
`{"simple": "Seize the sparkling stairs (NW)", "win": "Rowan seizes the,inner
reliquary:,the sparkling stairs,in the northwest", "loss": "Rowan dies"}`)
and that text is what the Objective screen and on-map hint display for the
whole chapter — this project's objectives are simply fixed for the
duration of each level rather than changed mid-chapter.

## 5. Test

No `tools/test_*.py` references `chapter_title`, `ChangeObjective`,
`toggle_narration_mode`, or `NarrationDialogue` (checked all files under
`tools/`). A `tools/test_chapter_presentation.py` should exist that: (1)
calls `event_functions.chapter_title(fake_event, music=None, string=None)`
and asserts `game.memory['chapter_title_title']` is `None` so
`ChapterTitleState.start()` falls back to `game.level.name`, and that
`ChapterTitleState.music_flag` ends up `True` because it fell back to the
`'Chapter Sound'` track; (2) does
`action.do(action.ChangeObjective('win', 'New win text'))` and asserts
`game.level.objective['win'] == 'New win text'`, then reverses the action
and asserts it's restored to the level's original authored string; (3)
calls `toggle_narration_mode(fake_event, 'open')` and asserts
`self.overlay_ui.has_child('event_narration')` becomes `True` and the
component is enabled, then `'close'` and asserts it exits without error.
