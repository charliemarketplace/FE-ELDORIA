---
name: author-music-and-sound
description: Direct music (fade in/out, a 4-deep song stack, per-phase/per-battle/per-item overrides) and one-shot sound effects from events, item components, and skill components.
---

## 1. Feature

The engine has a full music/SFX layer: `music`/`music_fade_back`/`music_clear`
fade a track in over the current one and push it onto a 4-channel "song
stack" so a later `music_fade_back` returns to whatever was playing before;
`sound`/`stop_sound` fire one-shot SFX; `change_music` rewrites which track
plays automatically for a given team's turn-phase or in-combat theme for the
rest of the chapter; `change_special_music` sets the title-screen/promotion/
class-change/game-over track. Underneath, every level has a per-team
phase/battle music table, boss units get their own combat-theme override,
and individual items/skills can force a custom battle track via the
`battle_animation_music` component. This project catalogues 51 music tracks
and 218 sound effects, but authors none of them into gameplay: every level's
phase/battle music table is null, and no event or item/skill in this
project's data calls any of the commands or components below.

## 2. Details

### 2.1 Event commands (`event_commands.py:310-393`, implementations `event_functions.py:69-117`)

| Command | Keywords | Default | What it does |
|---|---|---|---|
| `music;Music[;FadeIn]` (`m`) | `Music`, opt. `FadeIn` (ms) | `FadeIn=400` | `get_sound_thread().fade_in(nid, fade_in)`; passing the literal string `"None"` as `Music` fades to a pause instead (`fade_to_pause`) rather than fading in a track named "None". |
| `music_fade_back[;FadeOut]` (`mf`) | opt. `FadeOut` | `400` | Fades out the current song and pops the song stack, resuming whatever track was playing before the most recent `music` call (see §2.2). No-ops if the stack is empty. |
| `music_clear[;FadeOut]` | opt. `FadeOut` | `0` | Fades out **and clears the entire song stack** — `music_fade_back` afterward has nothing to return to. `FadeOut=0` calls `clear()` (instant stop) rather than `fade_clear()`. |
| `sound;Sound[;Volume]` | `Sound`, opt. `Volume` | `Volume=1.0` | `get_sound_thread().play_sfx(nid, volume=volume)`. `Sound` is validated against the SFX catalog (`event_validators.py:404-408`); an unrecognized nid fails validation, not a silent no-op. |
| `stop_sound;Sound` | `Sound` | required | Stops that one SFX if currently playing. |
| `change_music;Phase;Music` | `Phase` (`PhaseMusic` type), `Music` | both required | Rewrites `game.level.music[phase]` via `action.ChangePhaseMusic` (turnwheel-reversible). `Music = "None"` clears that slot to `None` instead of storing the literal string. Persists for the rest of the level (in-memory only — the level's own `music` dict on disk is untouched). |
| `change_special_music;SpecialMusicType;Music` | both required | — | `SpecialMusicType` is one of `title_screen`/`promotion`/`class_change`/`game_over`. `title_screen` writes to the **persistent, cross-save** `RECORDS` store (`RECORDS.replace('_music_title_screen', ...)`); the other three write to session-scoped `game_vars` (`_music_promotion`/`_music_class_change`/`_music_game_over`). |

- During an event skip (`self.do_skip`), `music`/`music_fade_back`/
  `music_clear` all force their fade duration to `0` — skips never wait out
  a music fade.
- `Music` values can be the literal string `"None"` (see table) — this is
  distinct from the Python `None` default; the validator
  (`event_validators.py:392-398`) explicitly special-cases the string.

### 2.2 The song stack (`app/engine/sound.py`)

- `DefaultSoundController` (`sound.py:555-866`) keeps 4 `ChannelPair`s
  (`channel_stack`) and a `song_stack: List[SongObject]` of what's played,
  most-recent last. `fade_in()` (`sound.py:699-769`): if the song is
  already in the stack, pulls it back to the top and reuses/rewinds its
  channel; otherwise pushes a new entry and steals the oldest channel.
  `fade_back()` (`sound.py:771-792`) pops the top of the stack and fades
  into whatever's now on top (or fades to stop if the stack is now empty).
  `DEFAULT_FADE_TIME_MS = 400` (`sound.py:70`) is what all the "default
  400ms" numbers above trace back to.
- `battle_fade_in`/`battle_fade_back` (`sound.py:670-686`) are a
  crossfade variant used specifically for combat music (see §2.3): if the
  target `SongObject.battle` (a separate `-battle.ogg` audio clip loaded
  alongside the main track when a battle variant exists,
  `sounds.py:12-32`) is present, it crossfades on the *same* channel
  instead of pushing a new stack entry; otherwise it falls back to a
  normal `fade_in`. This project's `music.json` catalogue has **zero**
  tracks with a battle variant (checked all 51 entries) and exactly one
  with an intro variant (`'Helms Deep'`, via `intro_full_path`,
  `sounds.py:19,40-41`).

### 2.3 Per-phase and per-battle music — the schema slot the task is pointed at

`LevelPrefab.music` (`app/data/database/levels.py:20`) is an `OrderedDict`
keyed by `DB.music_keys` (`app/data/database/database.py:74-82`): one
`"<team>_phase"` key and one `"<team>_battle"` key per team in `DB.teams`,
plus the fixed key `"boss_battle"`. This project's `constants.json` teams
give 4 phase + 4 battle keys per level; every one of the 7 levels'
`"music"` blocks in `lion_throne.ltproj/game_data/levels.json` sets all
eight to `null` (verified: `player_phase`, `enemy_phase`, `other_phase`,
`enemy2_phase`, `player_battle`, `enemy_battle`, `other_battle`,
`enemy2_battle`, all `null`, in all 7 level entries).

- Phase music: `phase.fade_in_phase_music`/`fade_out_phase_music`
  (`app/engine/phase.py:17-40`) read `game.level.music.get(team +
  '_phase', None)` each time the active team changes. A `null`/missing
  entry means `fade_to_pause` — silence — rather than any fallback track.
  `restart_phase_music` (a DB constant) controls whether re-entering the
  same phase on a later turn restarts the track `from_start` or just
  resumes the fade.
- Battle music: `animation_combat.py:780-798` resolves, in priority
  order, an attacker's own item/skill override (`item_system.battle_music`/
  `skill_system.battle_music`, §2.4) → if the attacker has the `'Boss'`
  tag and no override, `game.level.music.get('boss_battle', None)` → the
  defender's override the same way → finally
  `game.level.music.get('%s_battle' % attacker.team, None)`. `boss_battle`
  is a valid key per `DB.music_keys` even though it isn't one of the eight
  keys this project's levels.json pre-populates — `ChangePhaseMusic`
  (§2.1) writes into a plain dict, so `change_music;boss_battle;Track`
  would add it fresh.

### 2.4 Per-item/per-skill battle music override — also unused here

`BattleAnimationMusic` (item component, `app/engine/item_components/aesthetic_components.py:103-112`,
nid `battle_animation_music`) and `BattleAnimMusic` (skill component,
`app/engine/skill_components/aesthetic_components.py:178-186`, same nid)
both expose a single `Music`-typed `value` and implement `battle_music(...)`
returning it, hooked through `item_system.battle_music`
(`item_system.py:1259-1264`) / `skill_system.battle_music`
(`skill_system.py:1539-1546`) — the highest-priority source checked in
§2.3's combat-music resolution, ahead of `boss_battle` and the team-wide
`_battle` key. **Zero items or skills in this project's `items.json`/
`skills.json` use either component.**

### 2.5 Title/promotion/class-change/game-over screens

- Title screen (`app/engine/title_screen.py:81-82`): fades in
  `RECORDS.get('_music_title_screen')` if the persistent record was ever
  set by `change_special_music;title_screen;...`; otherwise no music plays
  (no DB-constant fallback for the title screen).
- Promotion/class-change (`app/engine/promotion.py:243-253`,
  `PromotionState`/`ClassChangeState` share this via inheritance — `music =
  'music_%s' % self.name` builds `'music_promotion'`/`'music_class_change'`
  at runtime): checks `game.game_vars.get('_' + music)` (the event-set
  override) first, then falls back to the DB constant of the same name
  (`DB.constants.value('music_promotion')`/`music_class_change`, both
  `None` by default, `app/data/database/constants.py:138-139`). This
  project's `constants.json` leaves both `null`, so neither screen plays
  music unless an event calls `change_special_music` first.
- Game over (`app/engine/game_over.py:24-27`): same override-then-constant
  pattern; `music_game_over` defaults to the track `'Game Over'`
  (`constants.py:140`), and this project's `constants.json` keeps that
  default — the game-over screen does play music even with zero event
  authoring.

## 3. Code files

- `app/events/event_commands.py:310-393` — `Music`, `MusicFadeBack`,
  `MusicClear`, `Sound`, `StopSound`, `ChangeMusic`, `ChangeSpecialMusic`.
- `app/events/event_functions.py:69-117` — all seven implementations.
- `app/events/event_validators.py:392-421` — `Music`/`Sound` nid
  validators, `PhaseMusic` (`DB.music_keys`), `SpecialMusicType`.
- `app/engine/sound.py` (full file) — `SoundController`/
  `DefaultSoundController`, the song stack, `battle_fade_in`/
  `battle_fade_back`, `DEFAULT_FADE_TIME_MS`.
- `app/data/resources/sounds.py` — `SongPrefab`/`SFXPrefab`
  (intro/battle variant paths), `MusicCatalog`/`SFXCatalog`.
- `app/data/database/levels.py:20` — `LevelPrefab.music`.
- `app/data/database/database.py:74-82` — `DB.music_keys`.
- `app/engine/phase.py:17-40` — phase-music fade in/out.
- `app/engine/combat/animation_combat.py:780-798` — battle-music
  resolution priority chain.
- `app/engine/item_components/aesthetic_components.py:103-112`
  (`BattleAnimationMusic`), `app/engine/skill_components/aesthetic_components.py:178-186`
  (`BattleAnimMusic`), hooks at `app/engine/item_system.py:1259-1264` /
  `app/engine/skill_system.py:1539-1546`.
- `app/engine/title_screen.py:81-82`, `app/engine/promotion.py:243-253`,
  `app/engine/game_over.py:24-27` — special-screen music resolution.
- `app/data/database/constants.py:138-140` — `music_promotion`/
  `music_class_change`/`music_game_over` DB constants.

## 4. Working example in this repo

**Not reachable as currently authored.** Checked every event's `_source`
script text across all 72 entries in `lion_throne.ltproj/game_data/events.json`
for `music`, `change_music`, `sound;`, and `chapter_title`'s music
argument — zero calls to any music/sound event command. Every level's
`"music"` block in `levels.json` is null across all eight keys, and
neither `battle_animation_music` (item) nor its skill twin is used by any
entry in `items.json`/`skills.json`. `music_promotion`/`music_class_change`
are `null` in `constants.json`; only `music_game_over` (`'Game Over'`)
carries a track, so the game-over screen is the *one* place music plays
without any authoring. The resources exist and are fully catalogued
(`lion_throne.ltproj/resources/music/music.json`, 51 tracks;
`lion_throne.ltproj/resources/sfx/sfx.json`, 218 sound effects) — a
designer wiring up per-phase music would edit a level's `"music"` block in
`levels.json` directly, or call `change_music;player_phase;<track nid>`
from that level's `level_start` event for a mid-chapter change.

## 5. Test

No `tools/test_*.py` references `get_sound_thread`, `fade_in`,
`ChangePhaseMusic`, `battle_music`, or `song_stack` (checked all files
under `tools/`). A `tools/test_music_system.py` should exist that: (1)
calls `event_functions.music(fake_event, 'Chapter Sound')` then
`event_functions.music(fake_event, 'Game Over')` and asserts
`sound.MUSIC`'s controller's `song_stack` has both songs in order, then
calls `music_fade_back` and asserts the controller is fading back toward
`'Chapter Sound'`; (2) does
`action.do(action.ChangePhaseMusic('player_phase', 'Chapter Sound'))` on a
level whose `music['player_phase']` was `None`, asserts the value updates,
reverses the action, and asserts it's `None` again; (3) gives a unit's
weapon a `battle_animation_music` component with a value, triggers combat,
and asserts `item_system.battle_music(...)` returns that value ahead of
the team's `_battle` key.
