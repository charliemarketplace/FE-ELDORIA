---
name: author-multi-item-or-sequence-item
description: Author a single inventory item that bundles several sub-items into one slot — a Three-Houses-style spell menu (multi_item) or a Warp/Rescue-style item built from steps used in order (sequence_item) — for a designer who wants a composite item instead of one flat effect.
---

## 1. Feature

Two sibling item components let a designer build one item out of several
other, fully-defined items instead of authoring a monolithic set of
components on a single item:

- **`multi_item`** turns the parent into a *menu* — using it opens a
  sub-list of its child items (e.g. one "Tome" item holding several spells,
  each with its own range/damage/uses), and the player picks which child to
  cast.
- **`sequence_item`** turns the parent into a *pipeline* — using it walks
  the player through each child item's targeting step in order (top to
  bottom), then resolves combat once with the whole chain. This is the
  documented way to build complex, multi-stage effects like Warp or Rescue
  out of two composable one-step items.

Both are pure item-authoring: no DB constant gates them, and the engine's
generic item plumbing (inventory scanning, weapon/spell detection, combat
targeting) already understands nested items recursively.

## 2. Details

### 2.1 The components

All in `app/engine/item_components/advanced_components.py`:

| Component | nid | Exposes | Effect |
|---|---|---|---|
| `MultiItem` | `multi_item` | `List[Item]` | Stores child item nids; using the parent lets the player pick and use any one child. |
| `MultiItemHidesUnusableChildren` | `multi_item_hides_unavailable` | (flag, no value) | When present, the child-selection menu filters out children that `item_funcs.available()` currently rejects (e.g. no uses left, out of range). |
| `SequenceItem` | `sequence_item` | `List[Item]` | Stores child item nids; using the parent targets each child in list order, then fires combat once using the parent item with all targets collected. |
| `MultiTarget` | `multi_target` | Int (default `2`) | Item requires this many targets to be selected before combat resolves. |
| `AllowSameTarget` | `allow_same_target` | (flag) | Lets a multi-target item pick the same tile/unit more than once. |
| `AllowLessThanMaxTargets` | `allow_less_than_max_targets` | (flag) | Lets the player confirm early with fewer than the required number of targets (shows a "Press START to confirm targets" pennant). |
| `StoreUnit` | `store_unit` | (none) | On hit, stores the struck unit's nid in `item.data['stored_unit']` and plays a rescue-hit animation — does **not** remove the unit from the map itself (that line is commented out in source). |
| `UnloadUnit` | `unload_unit` | (none) | `target_restrict` only allows empty, traversable tiles; on hit, `Warp`s the stored unit (from a paired `StoreUnit` sub-item) to the target tile and clears the stored slot. |

`StoreUnit`/`UnloadUnit` are the two halves the `sequence_item` docstring
means by "Useful for complex items like Warp or Rescue": author one item
whose `sequence_item` list is `[a "grab" item with store_unit, a "drop" item
with unload_unit]`, and using the composite item asks the player to pick a
unit, then a destination tile, in one combat resolution.

### 2.2 How `multi_item` is created and read

`item_funcs.create_item()` (`app/engine/item_funcs.py:199-231`) recursively
instantiates every nid in `item.multi_item.value` (or
`item.sequence_item.value`) as a real sub-`ItemObject`, parented to the
outer item (`parent=item`, lines 223-229) — so each child has its own full
component set, uses counter, etc.

Recursive helpers that treat a `multi_item` as transparent:

- `get_all_items(unit)` (`item_funcs.py:248-265`) — flattens a unit's
  inventory, replacing each `multi_item` with its children (not itself).
- `get_all_items_with_multiitems(item_list)` (`item_funcs.py:267-283`) —
  same but keeps the parent in the list too.
- `get_all_items_and_abilities(unit)` (`item_funcs.py:285-297`) — adds in
  any items granted by the `Ability`/`extra_ability` skill component
  (see the combat-art skill) on top of `get_all_items`.
- `is_weapon_recursive` / `is_spell_recursive`
  (`item_funcs.py:299-333`) — descend into `item.subitems` to answer
  "is this a weapon/spell" for a `multi_item` whose children are weapons or
  spells.
- `get_all_items_from_multi_item(unit, item)` (`item_funcs.py:335-354`) —
  returns only the leaf (non-multi) children, recursively.

### 2.3 Player-facing flow

**Multi-item menu** — `general_states.py:1072-1088` (the "extra ability"
branch of the unit action menu, but the same code path applies to any
`multi_item` in the regular inventory): if any child `is_weapon_recursive`,
the state transitions to `weapon_choice` with `game.memory['valid_weapons']`
set to the (optionally availability-filtered, per
`multi_item_hides_unavailable`) weapon children; otherwise it checks for
spell children and goes to `spell_choice` instead.

**Sequence-item pipeline** — `CombatTargetingState`
(`app/engine/general_states.py:1999-2153`):
- `start()` (2007-2015) replaces `self.item` with
  `parent_item.subitems[sequence_item_index]` for the current step.
- `_proceed_to_next_item()` (2144-2153) advances
  `sequence_item_index`, stashes `prev_targets` in `game.memory`, and
  re-enters `combat_targeting` for the next child — until the index
  reaches the end of `parent_item.sequence_item.value`.
- `_engage_combat()` (2097-2116) — once every step's targets are
  collected, slices `self.prev_targets` back up according to each child's
  `item_system.num_targets()`, and calls `interaction.engage()` with the
  **parent** item and the full list of per-step targets, resolving combat
  once for the whole chain.

### 2.4 Multi-target items (independent of multi/sequence)

`num_targets()` (`app/engine/item_system.py:939-947`) reads any component
defining `num_targets` (i.e. `MultiTarget`); if none is present it falls
back to `Defaults.num_targets` (1 target). `allow_same_target()` and
`allow_less_than_max_targets()` (`item_system.py:531-549`) are simple
OR-aggregators over all components defining those hooks — `CombatTargetingState.start()`
(line 2056) shows the "confirm targets" pennant only when
`num_targets() > 1 and allow_less_than_max_targets()`.

### 2.5 What happens if you omit fields

Omit `multi_item`/`sequence_item` entirely: item behaves as a normal single
item — none of this machinery engages. Omit
`multi_item_hides_unavailable`: unusable children still show in the pick
menu (just fail if selected). Omit `allow_same_target`: a multi-target item
cannot reselect a tile/unit already chosen this use. Omit
`allow_less_than_max_targets`: the player must select exactly
`multi_target`'s count before combat can resolve.

## 3. Code files

- `app/engine/item_components/advanced_components.py:1-87` — all eight
  components listed in §2.1.
- `app/engine/item_funcs.py:199-231` — `create_item` (recursive
  sub-item instantiation).
- `app/engine/item_funcs.py:248-354` — `get_all_items`,
  `get_all_items_with_multiitems`, `get_all_items_and_abilities`,
  `is_weapon_recursive`, `is_spell_recursive`,
  `get_all_items_from_multi_item`.
- `app/engine/item_system.py:90-97` — `get_all_components` (also folds in
  skill-granted `item_override` components).
- `app/engine/item_system.py:531-549,939-947` — `allow_same_target`,
  `allow_less_than_max_targets`, `num_targets` aggregators.
- `app/engine/general_states.py:1065-1096` — extra-ability menu branch
  that resolves a `multi_item` ability into `weapon_choice`/`spell_choice`.
- `app/engine/general_states.py:1999-2153` — `CombatTargetingState`,
  the `sequence_item` step-by-step targeting pipeline and
  `_engage_combat()`.

## 4. Working example in this repo

None of `multi_item`, `sequence_item`, `store_unit`, or `unload_unit`
appears in `lion_throne.ltproj/game_data/items.json` (checked every item's
component nid list directly). The closest analogue authored in this
project is the **`Ability`** skill component pattern used by `TLT_Steal`
and `Shove` (`lion_throne.ltproj/game_data/skills.json`: `["ability",
"so_Steal"]` and `["ability", "so_Shove"]`), which grants a unit an extra
item (`so_Steal`, `so_Shove` in `items.json`) usable straight from the
action menu without occupying an inventory slot — the exact same
`get_extra_abilities()`/menu code (`general_states.py:1065-1088`) that
special-cases `item.multi_item` would engage automatically the moment one
of those granted items became a `multi_item` instead of a flat item; it
just isn't authored that way here.

## 5. Test

No `tools/test_*.py` references `multi_item`, `sequence_item`,
`store_unit`, or `unload_unit`. A `tools/test_multi_sequence_item.py`
should exist that, after `harness.boot()`: creates a `multi_item` prefab
with two weapon children via `item_funcs.create_item`, asserts
`item_funcs.get_all_items(unit)` returns both children (not the parent) and
`is_weapon_recursive` is `True`; and separately builds a two-step
`sequence_item` (a `store_unit` item targeting a unit, an `unload_unit`
item targeting a tile), drives `CombatTargetingState` through both steps,
and asserts `_engage_combat()` is reached with a two-element target list and
that the stored unit ends up `Warp`ed to the second step's tile.
