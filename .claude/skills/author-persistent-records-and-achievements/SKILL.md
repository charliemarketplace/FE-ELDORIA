---
name: author-persistent-records-and-achievements
description: Author cross-save persistent records and player-facing achievements via event commands, for a designer who wants state (unlocked difficulties, meta-progression flags, completion badges) that survives new games and different save slots of the same project.
---

## 1. Feature

Alongside the automatic Recordkeeper (which silently logs combat stats like
kills/damage/turns into the current save file), the engine exposes a
second, author-driven layer: arbitrary-nid **persistent records** (a
key/expression store) and **achievements** (named, completable, optionally
hidden badges), both created/updated/queried entirely through event
commands. The defining trait that makes this genuinely distinct from a
save-bound game_var: both stores are written to their own file the instant
they change, keyed only by the project's `game_nid` — not the save slot —
so they survive starting a new game or switching save slots, and can even
be read on the title screen before any save is loaded. A designer uses this
for things a normal save shouldn't reset: "have you ever beaten this game,"
"which difficulties has this player unlocked," "which secret ending has
been seen across any playthrough."

## 2. Details

### 2.1 Achievement commands (tag `Tags.ACHIEVEMENT`)

All in `app/events/event_commands.py`:

- **`create_achievement`** (`CreateAchievement`, lines 3450-3457) —
  keywords `Nid`, `Name`, `Description` (all required); flags `completed`
  (auto-marks it done on creation), `hidden` (invisible to the player until
  completed). No-op if the nid already exists.
- **`update_achievement`** (`UpdateAchievement`, 3459-3466) — keywords
  `Achievement`, `Name`, `Description`; flag `hidden`. No-op if the nid is
  absent.
- **`complete_achievement`** (`CompleteAchievement`, 3468-3476) — keywords
  `Achievement`, `Completed` (Bool); flag `banner` (shows a pop-up
  notification). Own desc documents the paired check function:
  `check_achievement("nid")`. No effect if the achievement doesn't exist.
- **`clear_achievements`** (`ClearAchievements`, 3478-3481) — no keywords;
  wipes every achievement ("from the player's computer" per its own desc,
  i.e. the persisted file, not just the current save).
- **`open_achievements`** (`OpenAchievements`, 3130-3140, tag
  `MISCELLANEOUS`) — keyword `Background` (Panorama); opens the
  achievements list screen directly from an event.

### 2.2 Persistent record commands (tag `Tags.PERSISTENT_RECORDS`)

- **`create_record`** (`CreateRecord`, 3483-3488) — keywords `Nid`,
  `Expression`; evaluates `Expression` (a normal event expression, so it
  can reference game state) and stores it. No-op if nid already exists.
- **`update_record`** (`UpdateRecord`, 3490-3495) — same keywords;
  overwrites an existing record's value. No-op if the nid is absent.
- **`replace_record`** (`ReplaceRecord`, 3497-3502) — create-or-update in
  one call; the one to reach for by default unless you specifically want
  the no-op-if-missing/no-op-if-present guard the other two give you.
- **`delete_record`** (`DeleteRecord`, 3504-3509) — keyword `Nid`; removes
  it. No-op if absent.
- **`unlock_difficulty`** (`UnlockDifficulty`, 3511-3517) — keyword
  `DifficultyMode`; unlocks a difficulty mode so it becomes selectable at
  new-game creation. Implemented via the *same* persistent-records store
  (`RECORDS.unlock_difficulty`, §2.3) even though it reads like an
  achievement — a designer combining this skill with
  `configure-difficulty-mode`'s unlock gating should know it's this layer,
  not a save-local flag, that has to carry the unlock across playthroughs.
- **`records_screen`** (`RecordsScreen`, 3038-3045, tag `MISCELLANEOUS`) —
  opens the **automatic Recordkeeper's** stats screen (kills/damage/MVP/
  etc, §2.4) — not the persistent-records store despite the similar name.

### 2.3 Storage — a separate pickle file per project, not the save file

Two small modules, each following the same pattern:

- **`app/engine/achievements.py`**: `Achievement` prefab (`nid`, `name`,
  `desc`, `complete`, `hidden`, lines 8-23); `AchievementManager(Data)`
  (25-72) with `add_achievement`/`update_achievement`/`remove_achievement`/
  `check_achievement`/`complete_achievement`/`clear_achievements`. **Every
  mutator calls `persistent_data.serialize(self.location, self.save())`
  immediately** (lines 38, 48, 55, 67, 72) — writes to disk on every
  change, not batched into a save-game write. File location (lines 74-90):
  `'saves/' + str(DB.constants.value('game_nid')) + '-achievements.p'`.
  Module-level singleton `ACHIEVEMENTS` loads this file at import time.
- **`app/engine/persistent_records.py`**: `PersistentRecord` prefab (`nid`,
  `value`, lines 8-11); `PersistentRecordManager(Data)` (13-67) with
  `get`/`create`/`update`/`replace`/`delete`/`unlock_difficulty`/
  `check_difficulty_unlocked`, same immediate-serialize pattern. File:
  `'saves/' + game_nid + '-persistent_records.p'`; singleton `RECORDS`.
- **`app/engine/persistent_data.py`** — the raw pickle helpers both use:
  `serialize(location, data)` (7-15), `deserialize(location)` (17-24,
  returns `None` on `FileNotFoundError`), `clear(location)` (26-29).
- Both singletons are reloaded on project DB load:
  `app/data/database/database.py:177-179`, `Database.load()` calls
  `achievements.reset()` / `persistent_records.reset()`.

**The file lives in the same `saves/` directory as save slots
(`app/engine/save.py:80`, `'saves/' + GAME_NID() + '-' + str(slot) + '.p'`)
but is keyed only by `game_nid`** — one file shared across every save slot
of the project, untouched by starting a new game. Proof it's readable
before any save exists: `app/engine/title_screen.py:81-82` fades in
`RECORDS.get('_music_title_screen')` at the title screen itself, and lines
225/298 filter selectable difficulties via
`RECORDS.check_difficulty_unlocked(difficulty.nid)` at new-game creation —
both run with no save loaded. A real internal use of this exact pattern:
`event_functions.py:106-110`, `change_special_music` calls
`RECORDS.replace('_music_title_screen', music_nid)` with the comment
"title screen must persist past the current game."

### 2.4 Contrast with the automatic Recordkeeper

`app/engine/records.py`, class `Recordkeeper` (lines 74-281) — auto-tracks
kills, damage dealt/received/prevented, healing, hits/crits/misses,
levels/exp gained, Turnwheel uses, deaths, item use, stealing, recruiting,
turns taken, money gained/lost (docstring, lines 75-94), each entry
timestamped with turn/level context. Populated by gameplay code via
`action.UpdateRecords` (`app/engine/action.py:2505-2514`,
`game.records.append(...)`), never by an event author directly. It is
**per-save**, serialized as part of the save dict
(`app/engine/game_state.py:115,220,491,595-596`) — a new game starts a
fresh Recordkeeper. Surfaced via `records_screen`/`BaseRecordsState`
(`app/engine/base.py:997-1028`) and `app/engine/record_book.py`'s
`RecordsDisplay`/`UnitStats`/`MVPDisplay`/`ChapterStats`.

**The distinction that matters for authoring**: Recordkeeper is a fixed-
schema, save-bound stat logger you cannot extend — you only read it.
RECORDS/ACHIEVEMENTS is an open-ended, author-defined, cross-save store
you write to explicitly with event commands.

### 2.5 Surfacing to the player

- **Achievements screen**: `BaseAchievementState`
  (`app/engine/base.py:1404-1454`, `name = 'base_achievement'`) reads
  `ACHIEVEMENTS.values()` (line 1416) into a `menus.Table(..., mode=
  'achievements')`. Reachable from the in-game Base menu ("Achievements"
  option, `base.py:701-702,756-758`, only listed `if ACHIEVEMENTS:`) **and**
  from the Title Screen's Extras menu (`title_screen.py:747,803-806`,
  same `if ACHIEVEMENTS:` gate) — the title-screen path is only possible
  because achievements live outside the save file.
- **Persistent records** have no equivalent list-screen; they're a data
  store, read back only via the `Expression`-based commands or the query
  function below.

### 2.6 Conditional branching

`app/engine/query_engine.py:392-400` exposes `has_achievement(nid)` to
event `Expression`s (auto-collected into eval scope by
`GameQueryEngine.func_dict` and merged into event-eval globals in
`app/engine/evaluate.py:63`) — `return ACHIEVEMENTS.check_achievement
(nid)`. Use it directly inside an `if;<expression>` event command
(`event_commands.py:157-182`) the same way you'd use any other query
function. **No equivalent exists for persistent records** — there is no
`get_record`/`has_record` query function; branching on a record's value
requires writing the raw expression yourself (e.g. reading through
whatever mechanism the project exposes `RECORDS` through, since the
built-in query layer doesn't wrap it).

## 3. Code files

- `app/events/event_commands.py:32-33,3038-3045,3130-3140,3450-3517` —
  `Tags.ACHIEVEMENT`/`PERSISTENT_RECORDS`; `RecordsScreen`,
  `OpenAchievements`, `CreateAchievement`, `UpdateAchievement`,
  `CompleteAchievement`, `ClearAchievements`, `CreateRecord`,
  `UpdateRecord`, `ReplaceRecord`, `DeleteRecord`, `UnlockDifficulty`.
- `app/events/event_functions.py:19,37,106-110,3244-3246,3338-3345,
  3626-3723` — imports of `ACHIEVEMENTS`/`RECORDS`; command
  implementations; the `_music_title_screen` cross-game persistence
  example.
- `app/engine/achievements.py` (whole file) — `Achievement`,
  `AchievementManager`, module singleton `ACHIEVEMENTS`, `reset()`.
- `app/engine/persistent_records.py` (whole file) — `PersistentRecord`,
  `PersistentRecordManager`, module singleton `RECORDS`, `reset()`.
- `app/engine/persistent_data.py:7-29` — `serialize`/`deserialize`/`clear`
  pickle helpers.
- `app/data/database/database.py:177-179` — reload on `Database.load()`.
- `app/engine/records.py:74-281` — the contrasting automatic
  `Recordkeeper`.
- `app/engine/action.py:2505-2514` — `UpdateRecords` (feeds Recordkeeper).
- `app/engine/game_state.py:115,220,491,595-596` — Recordkeeper's
  save-bound lifecycle.
- `app/engine/base.py:696-702,747-749,756-758,997-1028,1404-1454` —
  `BaseRecordsState`, `BaseAchievementState`, base-menu entries.
- `app/engine/record_book.py:100,169,208,234` — Recordkeeper UI widgets.
- `app/engine/title_screen.py:81-82,225,298,747,803-806` — cross-save
  reads of `RECORDS`/`ACHIEVEMENTS` before any save loads.
- `app/engine/query_engine.py:392-400` — `has_achievement`.
- `app/engine/evaluate.py:63` — merges query-engine functions into event
  eval scope.
- `app/engine/state_machine.py:150,152` — `base_records`/
  `base_achievement` state registration.

## 4. Working example in this repo

None. A grep of `lion_throne.ltproj/game_data/events.json` for every nid
above (`create_achievement`, `update_achievement`, `complete_achievement`,
`clear_achievements`, `create_record`, `update_record`, `replace_record`,
`delete_record`, `unlock_difficulty`, `records_screen`,
`open_achievements`) and for `has_achievement`/`check_achievement` returns
zero matches — this project never uses either layer. The closest
authored analogue is the automatic Recordkeeper's own usage: two direct
`action.do(action.UpdateRecords('money', ...))` calls in
`tools/test_capital_completion.py:116,297` — but that exercises the
save-bound automatic system (§2.4), not this author-facing persistent
layer, and isn't project event content either (it's test code).

## 5. Test

No `tools/test_*.py` exercises `AchievementManager`, `PersistentRecordManager`,
or any of the event commands in §2.1/§2.2 — a grep of all 13 test files
under `tools/` for "record"/"achievement" only turns up the unrelated
Recordkeeper calls noted above and two incidental comment-text matches
(`test_overworld_gating.py:146`, `test_level_reentry.py:281`) unconnected
to either system. A `tools/test_persistent_records.py` should exist that:
calls `ACHIEVEMENTS.add_achievement(...)` and `RECORDS.create(nid, value)`
via a temp `location` (redirecting `persistent_data.serialize`/
`deserialize` to a scratch path so the real `saves/` directory isn't
touched), asserts the file is written immediately after each mutating
call (not just on process exit), then simulates a "new game" by calling
`achievements.reset()`/`persistent_records.reset()` and asserts the
previously-created achievement/record is still present — proving
persistence survives a fresh `GameState` the way a save-bound game_var
would not.
