---
name: configure-difficulty-mode
description: Add or tune a difficulty mode — permadeath/growth/RNG policy, per-team (player/enemy/boss) base and growth stat bonuses, and unlock gating — for a designer building Normal/Hard/Lunatic-style game modes.
---

## 1. Feature

A designer can define a named difficulty mode that bundles together: how
permadeath works (or whether the player chooses at new-game), how level-up
growths resolve (Fixed/Random/Dynamic, or player choice), which of five RNG
hit-roll algorithms is used, flat stat bonuses layered onto players/enemies/
bosses separately (both starting bases and per-level growth rates), and
optional autolevel counts. Modes can be locked behind a `RECORDS`-tracked
unlock (e.g. clear the game once to unlock Lunatic) and the new-game flow
automatically skips any choice screen a mode doesn't need.

## 2. Details

### 2.1 The mode record — `DifficultyModePrefab` (`app/data/database/difficulty_modes.py:24-100`)

| Field | Meaning | Default |
|---|---|---|
| `color` | UI color for the mode's label | `'green'` |
| `permadeath_choice` | `PermadeathOption`: `PLAYER_CHOICE` / `CLASSIC` (permadeath on) / `CASUAL` (off) | `PLAYER_CHOICE` |
| `growths_choice` | `GrowthOption`: `PLAYER_CHOICE` / `RANDOM` / `FIXED` / `DYNAMIC` | `PLAYER_CHOICE` |
| `rng_choice` | `RNGOption`: `CLASSIC` / `TRUE_HIT` / `TRUE_HIT_PLUS` / `FATES_HIT` / `GRANDMASTER` | `TRUE_HIT` |
| `player_bases` / `enemy_bases` / `boss_bases` | Flat starting-stat bonus added per team, keyed by stat nid | all-`0` (`init_bases`) |
| `player_growths` / `enemy_growths` / `boss_growths` | Flat per-stat growth-rate bonus added per team | all-`0` (`init_growths`) |
| `player_autolevels` / `enemy_autolevels` / `boss_autolevels` | Extra "free" level-ups applied per team on top of authored level | `0` |
| `promoted_autolevels_fraction` | Fraction of autolevels applied post-promotion instead of pre | `1.0` |
| `start_locked` | If `True`, hidden from new-game selection unless `RECORDS.check_difficulty_unlocked(nid)` says otherwise | `False` |

`get_base_bonus`/`get_growth_bonus`/`get_difficulty_autolevels`
(`:72-94`) all dispatch on the *unit*, not a global setting: allied-team
units get the `player_*` bucket, units tagged `Boss` get the `boss_*`
bucket, everyone else gets `enemy_*` — so a difficulty mode can buff enemy
grunts and boss units by different amounts in the same mode.

### 2.2 What "Player Choice" actually does at the title screen

`app/engine/title_screen.py`'s `TitleModeState` (`:271-`): at New Game,
`available_difficulties` filters out any `start_locked` mode the player
hasn't unlocked (`:298`, mirrored at `:225` for the earlier menu-visibility
check; falls back to `DB.difficulty_modes[0]` with a logged error if *every*
mode is locked, `:227-228`). If more than one mode is available, or the
single available mode has `permadeath_choice`/`growths_choice` set to
`PLAYER_CHOICE`, the game shows the difficulty/permadeath/growth-style menus
in sequence (`:301-337`); otherwise it skips straight past them
(`:237-240`). Each `PLAYER_CHOICE` sub-choice only shows the *other* options
in that enum (`PermadeathOption`/`GrowthOption` members excluding
`PLAYER_CHOICE` itself, `:320`/`:331`) — so a mode that hardcodes
`permadeath_choice: Classic` never shows a permadeath menu at all.

### 2.3 RNG choice → actual hit-roll algorithm (`app/engine/combat/solver.py:413-440`)

| `rng_choice` | Roll formula |
|---|---|
| `CLASSIC` | One raw roll (`static_random.get_combat()`) — classic swingy GBA-style RNG |
| `TRUE_HIT` | Average of two rolls — the modern "double RNG" |
| `TRUE_HIT_PLUS` | Average of three rolls — even less swingy |
| `FATES_HIT` | One roll, then run through `calculate_fates_hit` (`:433-440`), a sigmoid curve that pulls extreme hit% values toward the middle less than a straight average would |
| `GRANDMASTER` | Roll is hardcoded to `0` — i.e. hit% is compared against a roll that always favors the attacker (a "no-variance" competitive mode) |
| anything else | Falls back to True-Hit's two-roll average and logs an error (`:425-427`) |

### 2.4 Growth-rate composition (`app/engine/unit_funcs.py:22-108`)

`growth_rate(unit, stat)` (`:33-47`) = `unit.growths[stat]` +
`unit.growth_bonus(stat)` (runtime skill/status bonuses) +
`klass.growth_bonus.get(stat, 0)` (see the class/promotion skill) +
`game.mode.get_growth_bonus(unit, DB).get(stat, 0)` — the difficulty mode's
contribution is one clearly separated additive term, and
`growth_contribution` (`:49-76`) exposes each term individually (labeled
`"Difficulty Bonus"` in the UI breakdown) for players to inspect.
`get_leveling_method` (`:22-31`) resolves which algorithm (`Fixed` /
`Random` / `Dynamic` / `Match`) actually applies: player units use
`game.current_mode.growths` directly; non-player units use constant
`enemy_leveling`, except when that constant is literally `'Match'`, in
which case they also use `game.current_mode.growths`.

## 3. Code files

- `app/data/database/difficulty_modes.py:6-113` — `PermadeathOption`,
  `GrowthOption`, `RNGOption` enums; `DifficultyModePrefab` and its
  `get_base_bonus`/`get_growth_bonus`/`get_difficulty_autolevels` dispatch;
  `DifficultyModeCatalog.create_new` default seeding.
- `app/engine/objects/difficulty_mode.py:6-45` — `DifficultyModeObject`, the
  runtime/save-game object (`from_prefab` resolves the `PLAYER_CHOICE`
  enums into concrete booleans/values at new-game time).
- `app/engine/title_screen.py:225-337` — unlock filtering and the
  new-game choice-menu flow.
- `app/engine/combat/solver.py:413-440` — `generate_roll`/
  `calculate_fates_hit`, the RNG-choice → dice-roll mapping.
- `app/engine/unit_funcs.py:22-108` — `get_leveling_method`, `growth_rate`,
  `growth_contribution`, `base_growth_rate`, `difficulty_growth_rate`.

## 4. Working example in this repo

`lion_throne.ltproj/game_data/difficulty_modes.json` defines three modes:
`Hard` (`Player Choice`/`Player Choice`/`True Hit`, all bases/growths at 0 —
i.e. a mode that exists purely to still prompt the permadeath/growth
choice, with no stat modification of its own), `Lunatic` (`Player Choice`/
`Player Choice`/`True Hit+`, `enemy_bases.MAG +1` and `enemy_growths` boosted
across the board — `STR 35, MAG 35, SKL 20, SPD 30, LCK 20`, `HP 5` — while
`player_bases`/`player_growths` stay at 0), and `Grandmaster` (hardcoded
`Classic` permadeath + `Fixed` growths + `Grandmaster` RNG, zero stat
bonuses either side — a fixed, no-variance ruleset with no choice menus
shown at all since neither `permadeath_choice` nor `growths_choice` is
`Player Choice`). None of the three sets `start_locked: true`, so all three
are selectable from a fresh save.

## 5. Test

No `tools/test_*.py` exercises `DifficultyModePrefab`, `generate_roll`'s
RNG-choice branching, or `get_growth_bonus`'s team dispatch.
`tools/test_overworld_gating.py` references `game.current_mode` only
incidentally through its unit-building helper and never varies difficulty. A
`tools/test_difficulty_modes.py` should exist that, after `harness.boot()`,
sets `game.current_mode = DifficultyModeObject.from_prefab(DB.difficulty_modes.get('Lunatic'))`
and asserts an enemy unit's `unit_funcs.growth_rate(unit, 'STR')` is exactly
35 higher than the same unit under the `Hard` mode, that a `Boss`-tagged
unit reads from `boss_growths` rather than `enemy_growths`, and — for the
RNG side — that forcing `game.current_mode.rng_mode = RNGOption.GRANDMASTER`
makes `solver.generate_roll()` return `0` on every call while
`RNGOption.CLASSIC` returns a value drawn from a single `static_random.get_combat()`
call.
