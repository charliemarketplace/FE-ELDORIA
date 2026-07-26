---
name: author-movement-granting-skill
description: Author a skill that lets a unit move again after acting (Canto/Canter), move and attack in either order, move through enemies (Pass), or warp to an ally's side (Witch Warp) — the family of skill components that modify movement rules rather than combat math.
---

## 1. Feature

A dedicated tag of skill components (`SkillTags.MOVEMENT`) lets a designer
grant mounted-unit-style "move again" behavior (classic Canto), a fixed
bonus movement after any action (Canter), the ability to walk through
enemy-occupied tiles (Pass), immunity to forced movement or terrain, and a
warp-to-ally-side teleport (Witch Warp) usable from the normal move
cursor — all without any event scripting. Canto is one of the most
recognizable Fire Emblem class traits and is live in this project (mounted
classes); Witch Warp and Galeforce are fully wired into pathfinding, the AI,
and the move cursor but unused by any authored skill here.

## 2. Details

### 2.1 The "move again" family — `canto_movement` / `has_canto`

All in `app/engine/skill_components/movement_components.py`:

| Component | nid | `has_canto(unit, target)` | `canto_movement` |
|---|---|---|---|
| `Canto` | `canto` | `True` unless the unit already attacked (and not itself) | remaining `movement_left` |
| `CantoPlus` | `canto_plus` | Always `True`, even after attacking | remaining `movement_left` |
| `CantoSharp` | `canto_sharp` | `True` if not yet attacked, **or** if `movement_left >= equations.parser.movement(unit)` (i.e. hasn't used any movement yet) — lets a unit attack first, then still move a full move | remaining `movement_left` |
| `Canter` | `canter` (Int, default `2`) | Always `True`, after *any* action | a fixed number of tiles (the component's value), not `movement_left` |

`skill_system.has_canto(unit, target)` (`skill_system.py:739-748`)
aggregates every component defining `has_canto` with `any_false_priority`
(`utils.py:61-64` — really `any()`; defaults to `False`, i.e. no canto, if
no skill grants it). `canto_movement(unit, target)`
(`skill_system.py:1220-1228`) aggregates with `utils.maximum` — if a unit
somehow has two canto-granting skills, it gets the larger of the two
movement values, defaulting to `0` if none apply. The action-menu code
(`general_states.py:958-962`) calls both together: if `has_canto`, it does
`action.SetMovementLeft(unit, canto_movement(...))` and shows the move
highlight immediately in the menu, before the player has even chosen to
move again.

### 2.2 Movement-rule modifiers (no charge/resource layer — plain booleans)

- `Pass` (nid `pass`) — `pass_through(unit)` returns `True`; aggregated by
  `skill_system.pass_through()` (`skill_system.py:497-506`,
  `all_false_priority` = plain `all()`, defaults `False`) — lets the unit's
  pathing ignore enemy-occupied tiles as blockers.
  `MovementType` (`nid movement_type`, exposes `ComponentType.MovementType`)
  is already documented under the `mcost.json`/movement-cost-grid skill —
  not covered again here.
- `IgnoreTerrain` (nid `ignore_terrain`) — both `ignore_terrain(unit)` and
  `ignore_region_status(unit)` return `True`: the unit ignores terrain
  movement cost *and* any terrain-region status effect.
- `IgnoreRescuePenalty` (nid `ignore_rescue_penalty`) — removes the
  movement penalty normally applied while carrying a rescued/paired-up
  unit.
- `Grounded` (nid `grounded`) — `ignore_forced_movement(unit)` returns
  `True`: immune to Shove/Pivot/DrawBack/Swap-style forced movement (see
  the item hit-effect components).
- `NoAttackAfterMove` (nid `no_attack_after_move`, also exists as an item
  component with the same nid) — unit can move or attack, never both, in
  a single turn.

### 2.3 Witch Warp — teleport-to-ally-side

Three variants, all producing a set/list of valid destination tiles via
`witch_warp(unit)`:

- `WitchWarp` (nid `witch_warp`) — for every ally on the map, offers the
  four orthogonally-adjacent tiles that are empty and
  `movement_funcs.check_weakly_traversable`.
- `SpecificWitchWarp` (nid `specific_witch_warp`, exposes
  `List[Unit]`) — same, but only around the explicitly listed unit nids.
- `WitchWarpExpression` (nid `witch_warp_expression`, exposes `String`,
  default `'True'`) — same, but the eligible-partner set is every unit for
  which `evaluate.evaluate(self.value, target, unit, target.position)` is
  truthy (arbitrary Python expression with `target`/`unit` in scope).

`skill_system.witch_warp(unit)` (`skill_system.py:871-881`) is
`@lru_cache`d and resolved with `utils.unique` — **not** a union: if a unit
somehow carries two witch-warp-granting skills, only the *last* one's
result is used, the other is silently discarded. Cache is explicitly
cleared (`skill_system.py:1810`, `witch_warp.cache_clear()`) whenever
state that could invalidate it changes. If no skill defines it, the
default is `[]` (`component_system/skill_system_base.py:50-51`) — no warp
destinations.

Consumers: `game.path_system` (`pathfinding/path_system.py:53`),
`ai_controller.py:109`, and the move cursor
(`level_cursor.py:273`, `general_states.py:748-762`) all call
`skill_system.witch_warp(unit)` directly. The cursor code
(`general_states.py:749-762`) is the actual player-facing rule: if the
cursor lands on a witch-warp tile that is *not* also a normal move tile,
the resulting `current_move` is `action.Warp(unit, pos)` instead of
`action.Move`/`action.CantoMove` — and if the unit has already
attacked/traded, it still goes through the `canto_wait` state afterward
(i.e. Witch Warp composes with Canto rather than replacing it).

### 2.4 Galeforce — kill-to-move-again

`Galeforce` (nid `galeforce`, `movement_components.py:185-195`): on
`end_combat`, if the target died and the unit was the overall attacker
(checked via `mark_hit`/`mark_crit`/`mark_miss` playback entries'
`main_attacker`), calls `action.do(action.Reset(unit))`
(`app/engine/action.py:691-704` — restores `movement_left` to a full
`equations.parser.movement(unit)` and clears the unit's acted/attacked
state) and `action.TriggerCharge(unit, self.skill)` (a no-op unless paired
with a charge component from the combat-art/proc-skill system — Galeforce
has no built-in limiter of its own).

### 2.5 What happens if you omit fields

Omit any of these components: default movement rules apply (no re-move,
no pass-through, forced movement works normally, no warp destinations —
per each aggregator's documented empty-list default in §2.1/2.3). `Canter`
omitting its Int value defaults to `2` tiles. `WitchWarpExpression`
omitting its String value defaults to `'True'` (i.e. every unit on the map
is a valid warp anchor) — a designer who adds this component with no
further tuning gets the same reach as `WitchWarp` but expressed as an
eval instead of a team check.

## 3. Code files

- `app/engine/skill_components/movement_components.py` (full file, 196
  lines) — every component in §2.1-2.4.
- `app/engine/skill_system.py:497-506` — `pass_through` aggregator.
- `app/engine/skill_system.py:739-748` — `has_canto` aggregator.
- `app/engine/skill_system.py:871-881,1810` — `witch_warp` aggregator
  (cached, `unique` policy) and its cache-clear call site.
- `app/engine/skill_system.py:1220-1228` — `canto_movement` aggregator
  (`maximum` policy).
- `app/engine/component_system/utils.py:51-64,81-82` — `all_false_priority`,
  `any_false_priority`, `maximum` policy implementations.
- `app/engine/component_system/skill_system_base.py:50-51,86-87` —
  `Defaults.witch_warp` (`[]`), `Defaults.has_canto` (`False`).
- `app/engine/general_states.py:735-763` — move-cursor handling that
  chooses `action.Warp` vs. `action.Move`/`action.CantoMove` based on
  `skill_system.witch_warp(unit)`.
- `app/engine/general_states.py:958-962` — action-menu canto move
  highlight.
- `app/engine/action.py:691-704` — `Reset` (used by `Galeforce`).
- `app/engine/pathfinding/path_system.py:53` — pathfinding's witch-warp
  destination inclusion.
- `app/engine/ai_controller.py:109` — AI's use of witch-warp destinations.
- `app/engine/level_cursor.py:273` — cursor placement validity check.

## 4. Working example in this repo

Partially live. `lion_throne.ltproj/game_data/skills.json` defines `Canto`
= `["class_skill", null], ["canto", null]`
(`lion_throne.ltproj/game_data/classes.json`: granted to `Cavalier`) — a
plain, unmodified Canto. No skill in this project uses `canto_plus`,
`canto_sharp`, `canter`, `pass`, `witch_warp`/`specific_witch_warp`/
`witch_warp_expression`, or `galeforce` (checked every skill's component
list in `skills.json`). The closest analogue for the warp/teleport half is
the `Shove`/`Pivot`/`DrawBack`/`Swap` family of item hit-effect components
(`app/engine/item_components/hit_components.py`), which move a *struck*
unit rather than the acting unit and are also unused by any item in
`items.json` — this project's only forced-repositioning mechanic actually
authored is Rescue/Pair-Up's `traveler` slot (already documented).

## 5. Test

No `tools/test_*.py` references `canto`, `witch_warp`, `canter`, `pass`
(the movement component), or `galeforce` (checked all 13 files under
`tools/`). A `tools/test_movement_skill.py` should exist that, after
`harness.boot()`: gives a unit the `Canto` skill, has it attack (setting
`has_attacked`), and asserts `skill_system.has_canto(unit, unit)` is
`True` and `skill_system.canto_movement(unit, unit)` equals its
`movement_left`; gives a different unit `WitchWarpExpression` with an
always-true expression and one ally elsewhere on the board, and asserts
`skill_system.witch_warp(unit)` includes exactly the tiles adjacent to
that ally; and a third case granting `Galeforce`, defeating an enemy in
combat, and asserting `action.Reset` fires (unit's `has_attacked`/
`finished` flags clear and `movement_left` is restored to full).
