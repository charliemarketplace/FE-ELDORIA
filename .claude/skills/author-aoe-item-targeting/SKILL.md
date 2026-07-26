---
name: author-aoe-item-targeting
description: Give an item an area-of-effect shape (blast radius, line, cleave, all-allies/all-enemies) so it hits units around the targeted tile instead of only the target itself.
---

## 1. Feature

A family of `ItemTags.AOE` item components lets a designer make an item hit
more than one tile: a growing radius around the target (`blast_aoe` and its
enemy-only/ally-only/equation-sized variants), every unit adjacent to the
*user* rather than the target (`enemy_cleave_aoe`), every unit standing on a
straight line between user and target (`line_aoe`/`enemy_line_aoe`), or every
ally/enemy on the whole map regardless of position
(`all_allies_aoe`/`all_allies_except_self_aoe`/`all_enemies_aoe`). Each
component both computes who actually gets hit at resolution time and what to
highlight on the map before the player commits to a target, so the shape is
visible during targeting, not just felt after the fact. This project uses
exactly one of these — the healing staff `Mend` uses `ally_blast_aoe` to heal
everyone in a 1-tile radius of the target ally.

## 2. Details

### 2.1 The two hooks every AOE component implements (`app/engine/item_components/aoe_components.py`)

- `splash(self, unit, item, position) -> (main_target, splash_list)` — called
  at actual resolution time (`item_system.splash`, `item_system.py:249-280`).
  Returns the position that should be treated as the "main" target (or
  `None` if there isn't one — e.g. a pure-splash spell that never
  touches the tile the player pointed at) and a list of the other
  positions hit.
- `splash_positions(self, unit, item, position) -> set` — called only for
  *display*, before the player confirms (`item_system.splash_positions`,
  `item_system.py:282-...`; consumed by `game.highlight.display_possible_attacks`/
  `display_possible_spell_attacks` in `general_states.py:2086-2094` and
  `ai_controller.py:135-142`). This is why enemy-restricted/ally-restricted
  variants filter differently for `splash` (who actually gets hit) vs.
  `splash_positions` (what tiles get highlighted) — see §2.2.
- If an item has **no** AOE component, `item_system.splash` falls back to
  a single target at `position` with an empty splash list — unless the
  attacking *unit* has a skill defining `alternate_splash`
  (`skill_system.alternate_splash`, `skill_system.py:761-770`), in which
  case that skill-level AOE substitutes for the item lacking one. A
  splash component's own radius/shape can also be widened by
  `skill_system.empower_splash` (`skill_system.py:1231-...`, a skill hook
  every `BlastAOE._get_power` calls) — a unit skill can grow every blast
  item that unit wields without touching the item itself.

### 2.2 The shapes

| Component (nid) | Radius/shape source | Who gets hit | Notes |
|---|---|---|---|
| `blast_aoe` | `Int`, default `1` | Everyone in Manhattan range `0..value` of the target tile (spells hit units on those tiles; physical blast excludes the target's own tile from the splash list but still includes it as `main_target`) | Base shape; `_get_power` adds `1 + empowered_splash` to `value` |
| `enemy_blast_aoe` | same as `blast_aoe` | Same shape, filtered to `skill_system.check_enemy` | For display, non-enemy tiles are dropped from the highlight too |
| `ally_blast_aoe` | same | Filtered to `skill_system.check_ally`; `splash` always returns `main_target=None` (there is no "main" target — everyone hit is just splash) | **Live in this project** on `Mend` (§4) |
| `smart_blast_aoe` | same | Delegates to `AllyBlastAOE`/`EnemyBlastAOE`/plain `BlastAOE` depending on whether the *item* also has `target_ally`/`target_enemy` | Lets one component definition serve both an ally-heal and an enemy-nuke version of a "spread" spell family without picking the ally/enemy variant by hand |
| `equation_blast_aoe` | `Equation`-typed `value`, evaluated via `equations.parser.get` at hit time | Same as `blast_aoe` | Radius scales off a unit's stats/equation rather than a fixed int |
| `ally_equation_blast_aoe` | Equation radius + ally-only filter (multiple inheritance of both) | Allies only | Combines the two above |
| `enemy_cleave_aoe` | Fixed: the 8 tiles orthogonally/diagonally adjacent to the **user's own position** (not the target's) | Enemies among those 8 tiles | "Whirlwind"-style — hits everyone next to *you*, regardless of where you aimed |
| `all_allies_aoe` | None (no radius) | Every allied unit on the map, including the user | `splash_positions` highlights the *entire map* (every `(x,y)` in bounds) since any tile could contain a hit |
| `all_allies_except_self_aoe` | same | Every allied unit except the user | |
| `all_enemies_aoe` | same | Every enemy unit on the map | Highlight filters out ally tiles, everything else lights up |
| `line_aoe` | None — traced with `utils.raytrace(unit.position, position)` | Every unit on the ray from user to target, target's own tile excluded from further extension ("never extends past the target") | |
| `enemy_line_aoe` | same ray | Filtered to enemies only | |

### 2.3 Targeting-time consumers

- `item_system.target_restrict` (`item_system.py:206-...`) is checked
  during target selection; an AOE component can define its own
  `target_restrict` to forbid selecting a tile at all if the shape
  wouldn't hit anything valid (this is how `ShoveTargetRestrict`-style
  "suppress if invalid" components work for the *forced-movement* family,
  not AOE itself — AOE components here don't restrict targeting, they only
  compute the hit set).
- `combat/interaction.py:56-74` (`engage`) calls `item_system.splash` per
  target position to build the actual list of units the combat resolves
  against, separately for a multi-target/sequence item's sub-items.

## 3. Code files

- `app/engine/item_components/aoe_components.py` (full file, 256 lines) —
  all twelve components listed above.
- `app/engine/item_system.py:249-280` (`splash`), `282-...`
  (`splash_positions`), `1259-1264` (unrelated `battle_music` hook, not
  part of this family — see `author-music-and-sound`).
- `app/engine/skill_system.py:761-770` (`alternate_splash`), `1231-...`
  (`empower_splash`).
- `app/engine/combat/interaction.py:40-78` (`engage`) — where `splash` is
  called to build the real target list for combat.
- `app/engine/general_states.py:2086-2094`, `app/engine/ai_controller.py:135-142`
  — `splash_positions` consumed for map highlighting (player targeting UI
  and AI target evaluation, respectively).

## 4. Working example in this repo

**Live.** `Mend` (`lion_throne.ltproj/game_data/items.json`, item nid
`Mend`) is a healing staff with `magic_heal: 10` and
`"ally_blast_aoe": 1` — a radius-1 (`value=1` → range `0..1`) heal that
hits every ally within one tile of the targeted ally, including the
target itself, and shows its area via `map_cast_anim: "AOE_Mend"`. No
other AOE component is used anywhere else in `items.json` — `blast_aoe`,
`enemy_blast_aoe`, `smart_blast_aoe`, `equation_blast_aoe`,
`enemy_cleave_aoe`, `all_allies_aoe`, `all_enemies_aoe`, `line_aoe`, and
`enemy_line_aoe` are all present in the engine and fully wired but appear
zero times in this project's item data. The closest analogue for the line/
cleave/all-map shapes is this same `Mend` entry — swapping its
`ally_blast_aoe` for `line_aoe` or `all_allies_aoe` and keeping the rest of
the item unchanged would produce a "heal everyone on a line" or "heal the
whole army" staff with no other code changes.

## 5. Test

No `tools/test_*.py` references `item_system.splash`, `BlastAOE`,
`LineAOE`, or `aoe_components` (checked all files under `tools/`). A
`tools/test_aoe_targeting.py` should exist that: (1) equips a unit with
`Mend`, calls `item_system.splash(unit, mend_item, target_pos)` against a
cluster of allies one tile apart, and asserts the returned splash list
contains exactly the adjacent allies and not the more-distant ones or any
enemy standing in range; (2) does the same with a synthetic `line_aoe`
item between two units with a third ally standing directly between them,
and asserts that middle ally is in the splash but a unit one tile off the
line is not; (3) asserts `item_system.splash_positions` for
`all_enemies_aoe` returns every board tile (matching the "highlights the
whole map" behavior) while `item_system.splash` for the same item returns
only enemy-occupied positions.
