---
name: author-aura-skill
description: Author a skill that projects a passive buff/debuff onto nearby allies, enemies, or all units within a radius (a Charisma/Defense-Aura-style leadership skill), including the map highlight, line-of-sight gate, and how it re-propagates as units move.
---

## 1. Feature

`aura` lets a designer give a unit a passive radius effect that
automatically attaches a hidden child skill to every qualifying unit within
range — no event scripting required. The engine tracks aura coverage on the
board itself and keeps it in sync as units move, are added, are removed, or
die, including an optional line-of-sight requirement and an optional
always-visible colored map highlight. This is a live, actively-used system
in this project (two class-innate leadership auras).

## 2. Details

### 2.1 The five paired components (`app/engine/skill_components/status_components.py:13-53`)

All five carry `paired_with = (...)` listing each other, meaning they're
meant to be authored together on one skill:

| Component | nid | Exposes | Default | Meaning |
|---|---|---|---|---|
| `Aura` | `aura` | Skill (nid) | — | The child skill to grant to units in range. |
| `AuraRange` | `aura_range` | Int | `3` | Radius in tiles (Manhattan shell, not Chebyshev). |
| `AuraTarget` | `aura_target` | MultipleChoice: `ally`/`enemy`/`unit` | `'unit'` | Who the aura affects: only allies of the owner, only enemies, or every unit regardless of team. |
| `AuraShow` | `show_aura` | Color3 | `(128, 0, 0)` | If present, always renders a colored highlight over the aura's tiles on the map (independent of the current unit hover). |
| `HideAura` | `hide_aura` | (flag) | — | Suppresses the hover-triggered aura highlight (the one shown when the mouse/cursor is over the owner) even if `show_aura` isn't set. |

Omitting `aura_range` defaults the radius to `3`; omitting `aura_target`
defaults to `'unit'` (affects everyone, friend or foe); omitting
`show_aura`/`hide_aura` means the aura only highlights while the owning
unit is hovered/selected (the normal case).

### 2.2 Propagation (`app/engine/aura_funcs.py`, full file)

- `propagate_aura(unit, skill, game)` (77-90) — called when a unit with an
  aura skill moves onto the map or the skill is added: resets
  `game.board`'s aura grid entry for the child skill, computes every
  position within `aura_range` via
  `game.target_system.get_shell({unit.position}, range_set,
  game.board.bounds)`, records each as an aura source
  (`game.board.add_aura`), and immediately calls `apply_aura` on any unit
  already standing in one of those tiles.
- `pull_auras(unit, game)` (35-44) — called when a unit moves *into* a
  tile: reads every aura registered at that position from
  `game.board.get_auras(pos)` and applies each (skipping the aura's own
  owner).
- `apply_aura(owner, unit, child_skill, target, test=False)` (46-63) — the
  actual gate: checks `target` (`'enemy'`/`'ally'`/`'unit'`) against
  `skill_system.check_enemy`/`check_ally`, **then**, only if the
  `aura_los` DB constant is `True`, requires
  `line_of_sight.line_of_sight({owner.position}, {unit.position}, 99)`
  before calling `action.AddSkill(unit, child_skill,
  source_type=SourceType.AURA)`. If `aura_los` is left at its default
  (`False`), auras ignore walls/terrain entirely.
- `remove_aura` / `release_aura` (65-117) — the teardown half, called when
  a unit leaves the aura's positions, the owner moves/dies, or the skill is
  removed; `release_aura` walks every position the child skill currently
  occupies (`game.board.get_aura_positions`) and calls `remove_aura` on
  each occupant.
- `repopulate_aura(unit, skill, game)` (92-105) — the load-time-only
  variant of `propagate_aura` that skips the "apply to units already
  standing there" step (that's handled separately during unit placement),
  called once per aura skill when a save/level is loaded
  (`app/engine/game_state.py:630-631`).

### 2.3 Where propagation hooks into unit lifecycle

`app/engine/game_state.py`: a unit **leaving** the map
(`leave(unit, test=False)`, ~1387-1408) removes any auras affecting it at
its old position and releases any auras *it* owns; a unit **arriving**
(`arrive(unit, test=False)`, ~1450-1478) does the reverse — `pull_auras`
first, then `propagate_aura` for each of its own aura skills. `action.py`
mirrors this inside `AddSkill`/`RemoveSkill`/move actions
(`action.py:3610-3728`) so the turnwheel can reverse aura state correctly.

### 2.4 Rendering

- `game.board` (`app/engine/game_board.py:41-44,326-364`) keeps
  `aura_grid: Dict[Pos, Set[(SkillUid, target)]]` and a reverse index
  `known_auras: Dict[SkillUid, Set[Pos]]` — this is the source of truth
  `get_auras`/`get_aura_positions` read from.
- `game.boundary` (`app/engine/boundary.py:47-54,116-130,224-238`) tracks
  only the subset of auras with `show_aura` set
  (`register_unit_auras`/`unregister_unit_auras`), and
  `draw_auras()` blits a colored tile overlay for each — this is the
  "always visible" highlight, independent of cursor hover.
- `game.highlight.display_aura_highlights(unit)`
  (`app/engine/highlight.py:100-107`) is the hover-triggered version: for
  every aura skill the hovered unit owns that is not `hide_aura`, it looks
  up the child skill's current positions (respecting `aura_los` the same
  way) and highlights them with the generic purple `'aura'` highlight
  sprite. Called from the free-roam and menu states
  (`general_states.py:705,963`).

### 2.5 What happens if you omit fields

Omit `aura` itself: no aura at all (the other four components do nothing
without it — they're keyed off `skill.aura`/`skill.aura_range`/etc. being
truthy, e.g. `aura_funcs.get_all_aura_info` line 26 `if skill.aura:`).
Omit the child skill referenced by `aura` (typo/missing nid): every
propagation function logs `"Aura skill %s has no subskill... skipping
propagation"` and does nothing — silent no-op, not a crash. Leave
`aura_los` (DB constant, default `False`,
`app/data/database/constants.py:97`) off: auras see through walls.

## 3. Code files

- `app/engine/skill_components/status_components.py:13-53` — the five
  components in §2.1.
- `app/engine/aura_funcs.py` (full file, 118 lines) — `get_all_aura_info`,
  `pull_auras`, `apply_aura`, `remove_aura`, `propagate_aura`,
  `repopulate_aura`, `release_aura`.
- `app/engine/game_board.py:41-44,326-364` — the aura grid storage.
- `app/engine/boundary.py:47-54,116-130,224-238` — always-visible aura
  rendering (`show_aura`).
- `app/engine/highlight.py:100-107` — hover-triggered aura highlight.
- `app/engine/game_state.py:524,630-631,1387-1408,1450-1478` —
  lifecycle hooks (load-time repopulate, leave/arrive propagation).
- `app/engine/action.py:3610-3728` — turnwheel-safe propagate/release on
  `AddSkill`/`RemoveSkill`/movement actions.
- `app/data/database/constants.py:97` — `aura_los` DB constant.
- `app/engine/source_type.py:8` — `SourceType.AURA`.

## 4. Working example in this repo

Live. `lion_throne.ltproj/game_data/classes.json` grants `Paladin` →
`TLT_Charisma` and `Sentinel` → `TLT_Defense_Aura`
(`lion_throne.ltproj/game_data/skills.json`):
`TLT_Defense_Aura` = `["aura", "Aura_Defense_Child"], ["aura_range", 3],
["aura_target", "ally"]` (child `Aura_Defense_Child` = `["stat_change",
[["DEF", 2]]]`, hidden); `TLT_Charisma` = `["aura",
"Aura_Charisma_Child"], ["aura_range", 3], ["aura_target", "ally"]`
(child `Aura_Charisma_Child` = `["hit", 15], ["avoid", 15]`, hidden).
Neither sets `show_aura`, so both rely on the default hover-triggered
purple highlight. This project's `constants.json` sets `aura_los: true`
(the constant's default is `false`) — a deliberate authoring choice that
these two auras respect line of sight, unlike the engine default.

## 5. Test

No `tools/test_*.py` references `aura`, `aura_range`, `aura_target`, or
`aura_los` (checked all 13 files under `tools/`). A
`tools/test_aura_skill.py` should exist that, after `harness.boot()`:
places a unit with `TLT_Defense_Aura` and an ally within range 3, calls
`arrive()`/`pull_auras` (or moves the ally in via `action.Move`), and
asserts the ally gains `Aura_Defense_Child` and its `DEF` stat reflects
the `+2` `stat_change`; moves the ally out of range and asserts the child
skill is removed; and a second case with `aura_los` forced `True` and a
wall between owner and ally, asserting the aura does **not** apply despite
being in range.
