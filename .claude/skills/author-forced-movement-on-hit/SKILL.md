---
name: author-forced-movement-on-hit
description: Give an item a forced-movement effect on hit — push the target back (Shove), swap places with it, jump to its far side (Pivot), or shove both combatants apart (Draw Back).
---

## 1. Feature

A family of `ItemTags.SPECIAL` item components move units around the board
as a side effect of combat, independent of damage: `shove` pushes the
defender one or more tiles directly away from the attacker; `swap`
teleports the attacker and defender into each other's tiles; `pivot` moves
the *attacker* to the opposite side of the defender (stepping through
them); `draw_back` pulls both combatants back away from each other by the
same amount. Every one of the four has an `_on_end_combat` variant (applies
after the whole combat round resolves rather than on the triggering hit)
and, for `shove`/`pivot`/`draw_back`, a `_target_restrict` variant that
hides the item from being selectable against a target for which the move
is physically impossible, instead of letting the player pick it and having
it silently fail. This project uses exactly one variant: the spell `Shove`
uses `shove_target_restrict` to push an adjacent ally one tile away.

## 2. Details

### 2.1 Shove (`app/engine/item_components/hit_components.py:179-248`)

- `shove` (`Int` `value`, default `1`): on hit, computes a destination
  tile `magnitude` steps directly away from the attacker along whichever
  of the 8 compass directions the defender already occupies relative to
  the attacker (`_check_shove`, clamps each axis offset to `-1..1` then
  multiplies by `magnitude` — so it always pushes straight, never
  diagonally-scaled). Valid only if the destination is in bounds, unoccupied,
  and the defender's movement cost to it (`movement_funcs.get_mcost`) is
  `<=` their `movement` equation value — i.e. it silently checks the
  defender can "afford" the step, but ignores terrain that blocks entry
  outright versus terrain that's merely expensive. If invalid, nothing
  happens (no damage-independent fizzle message).
- `shove_on_end_combat` (subclasses `Shove`): identical geometry check, but
  applied via `action.do(action.ForcedMovement(...))` in `end_combat`
  instead of `actions.append(...)` in `on_hit` — the push happens once,
  after the round, rather than per-hit, and only fires `if ... and mode`
  (skipped when `mode` is falsy, e.g. a miss-only resolution).
- `shove_target_restrict` (subclasses `Shove`): overrides `on_hit`/
  `end_combat` to no-ops and instead implements `target_restrict`, which
  runs the same `_check_shove` math against the defender **and** every
  splash-hit unit, returning `True` only if at least one of them could
  actually be shoved — this is what removes the item from being targetable
  at all against, say, a unit backed into a wall.
- All three respect `skill_system.ignore_forced_movement(target)` — a unit
  with a skill granting that hook is immune to being shoved (and to
  Pivot/Draw Back's forced movement, see below).

### 2.2 Swap (`hit_components.py:250-269`)

- `swap` (no value): on hit, `action.Swap(unit, target)` — teleports
  attacker and target to each other's exact positions (`action.py:268-293`,
  `game.leave`/`game.arrive` on both, so auras/vision/fog update
  correctly; fully turnwheel-reversible). No range/terrain check at all —
  unlike Shove, a swap always succeeds if not blocked by
  `ignore_forced_movement` on *either* party.
- `swap_on_end_combat`: same swap, but only fires in `end_combat` and only
  `if target and mode == 'attack'` — it explicitly does not trigger on a
  defending hit (i.e. only when the swap-item's owner was the aggressor).

### 2.3 Pivot (`hit_components.py:271-326`, credited to a community contributor "Lord Tweed")

- `pivot` (`Int` `value`, default `1`): moves the **attacker** (not the
  target) to the tile `magnitude` steps beyond the target, on the far
  side, computed as `anchor_pos - offset*-magnitude` where `anchor_pos` is
  the target's position and `offset` is the attacker's direction relative
  to the target — i.e. "step through the target and out the other side."
  Same bounds/occupancy/movement-cost validity check as Shove, and the
  same `ignore_forced_movement` check, but tested against the *attacker*
  (a unit immune to forced movement can't be Pivoted either).
- `pivot_target_restrict`: same suppress-if-invalid pattern as
  `shove_target_restrict`.
- Reuses `pb.ShoveHit` for its playback event — there is no distinct
  "PivotHit" playback effect; visually a Pivot plays the same shove
  animation cue as Shove.

### 2.4 Draw Back (`hit_components.py:328-...`, also "Lord Tweed")

- `draw_back` (`Int` `value`, default `1`): moves **both** combatants
  backward away from each other by `magnitude`, computed once
  (`_check_draw_back`) and only applied `if new_position_user and
  new_position_target` — i.e. it's all-or-nothing; if either combatant's
  destination is invalid (out of bounds, occupied, unaffordable movement
  cost), neither one moves. Checked against `skill_system.ignore_forced_movement(target)`
  only (not the user).
- `draw_back_target_restrict`: same suppress-if-invalid pattern, requiring
  **both** computed destinations to be valid (`all(positions)`) before the
  item is selectable.

### 2.5 What "invalid" means for all four

Every variant's validity check is the same three-part test:
`game.board.check_bounds(new_position)` (on the map),
`not game.board.get_unit(new_position)` (tile unoccupied), and
`movement_funcs.get_mcost(unit, new_position) <=
equations.parser.movement(unit)` (the mover could legally step there this
turn, per their movement type/terrain cost — see
`configure-movement-cost-grid`). None of the four checks whether the
*path* between old and new position is clear — only that the final tile
is legal — so a shove/pivot/draw-back can vault a unit over intervening
terrain in one motion.

## 3. Code files

- `app/engine/item_components/hit_components.py:179-391` — all nine
  components (`Shove`, `ShoveOnEndCombat`, `ShoveTargetRestrict`, `Swap`,
  `SwapOnEndCombat`, `Pivot`, `PivotTargetRestrict`, `DrawBack`,
  `DrawBackTargetRestrict`).
- `app/engine/action.py:254-293` — `ForcedMovement` (sprite transition +
  `game.leave`/`game.arrive`), `Swap`.
- `app/engine/skill_system.py:596-604` — `ignore_forced_movement`.
- `app/engine/item_system.py:206-...` — `target_restrict`, the hook the
  `_target_restrict` variants implement.
- `app/engine/movement_funcs.py` — `get_mcost` (the terrain-cost check
  shared by Shove/Pivot/Draw Back).

## 4. Working example in this repo

**Partially live.** The spell item `so_Shove`
(`lion_throne.ltproj/game_data/items.json`, nid `so_Shove`, name "Shove",
desc "Push an adjacent ally one square away.") is `spell`/`target_ally`,
range 1-1, with `"shove_target_restrict": 1` — a magnitude-1 push that
disappears from the menu if the targeted ally has no valid tile to be
pushed into. This is the **only** forced-movement component used anywhere
in `items.json`: plain `shove`, `shove_on_end_combat`, `swap`,
`swap_on_end_combat`, `pivot`, `pivot_target_restrict`, `draw_back`, and
`draw_back_target_restrict` all appear zero times. Notably this project
only exercises the "restrict" (suppress-if-invalid) half of the family and
never the bare `on_hit`-fires-regardless variant, so the "nothing happens,
no message" silent-failure path described in §2.1 has never actually been
authored here either.

## 5. Test

No `tools/test_*.py` references `Shove`, `Pivot`, `DrawBack`, `Swap`, or
`ForcedMovement` (checked all files under `tools/`). A
`tools/test_forced_movement.py` should exist that: (1) places an attacker
and an adjacent ally with an open tile behind the ally, gives the attacker
`so_Shove`, resolves the hit, and asserts the ally's position moved one
tile further away and the attacker did not move; (2) repeats with a wall
directly behind the ally and asserts `target_restrict` returns `False`
(item not selectable) rather than allowing the hit and silently no-oping;
(3) builds a synthetic `pivot`-bearing item, resolves a hit, and asserts
the *attacker's* position — not the target's — ends up on the opposite
side of the target; (4) grants the target unit a skill implementing
`ignore_forced_movement`, resolves a `swap`-bearing hit, and asserts
neither unit's position changed.
