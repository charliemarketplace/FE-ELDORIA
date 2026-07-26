---
name: add-class-with-promotion-path
description: Author a new class and wire it into a tiered promotion chain — stat/skill gains on promotion, auto-vs-item-triggered promotion, and skill inheritance across tiers.
---

## 1. Feature

A designer can define a new class (base stats, growths, movement type,
weapon proficiencies, class-learned skills, art) and slot it into a
promotion chain by pointing an existing tier-1 class's `turns_into` at it.
The new (tier-2+) class's own `promotion` dict defines exactly what stat
bonuses a unit receives the instant they promote into it, independent of
whatever growths/RNG produced their pre-promotion stats. Promotion can
trigger automatically at a class's level cap (`auto_promote` constant or a
per-unit `AutoPromote` tag) or via a promotion item.

## 2. Details

### 2.1 The class record — `Klass` (`app/data/database/klass.py:12-39`)

| Field | Meaning | Default |
|---|---|---|
| `tier` | Numeric promotion tier (1 = base, 2 = first promotion, …) | `1` |
| `movement_group` | Row into `mcost.json`'s movement-cost grid | first entry in `db.mcost.unit_types` |
| `promotes_from` | Nid of the tier below this one that leads here | `None` |
| `turns_into` | List of class nids this class can promote into | `[]` |
| `max_level` | Level cap for this tier; reaching it is what makes auto-promotion eligible | `20` |
| `bases` / `growths` / `max_stats` | Per-stat class contribution / growth / stat cap, keyed by stat nid | all-`0` (bases/growths), `stat.maximum` (max_stats) |
| `growth_bonus` | Flat per-stat growth-rate bonus added on top of the unit's own growths (see §2.3) | all-`0` |
| `promotion` | **Stat gains applied when a unit promotes *into* this class** (see §2.2 — sentinel values) | all-`0` |
| `learned_skills` | Class-wide skills: `[[level, skill_nid], ...]` | `[]` |
| `wexp_gain` | Per-weapon-type `WexpGain(usable, gain, cap)` for units of this class | one all-`usable=False` entry per weapon type |
| `map_sprite_nid` / `combat_anim_nid` | Art links (see character-authoring skill §2.4) | `None` |
| `fields` | Arbitrary designer scripting hooks | `[]` |
| `Klass.promotion_options(db)` (line 55-56) | Returns only the members of `turns_into` whose `tier` is exactly `self.tier + 1` — a designer can list a class in `turns_into` that's the wrong tier and it will silently be excluded from the promotion menu | — |

### 2.2 What actually happens on promotion — `action.Promote` (`app/engine/action.py:1953-2035`)

Stat gain for each stat comes from the **new** class's `promotion` dict.
Each entry supports three sentinel values in addition to a literal integer
gain (`action.py:1970-1984`):

| `promotion[stat]` value | Effect |
|---|---|
| `-99` | Set stat to the new class's `bases[stat]` outright (`new_klass_bases - current_stats`) |
| `-98` | Same as `-99`, but only if it would be an *increase* (`max(0, ...)`) — never lowers the stat |
| `-97` | Add the *difference* between new-class base and old-class base, clamped so the result stays within `[0, max_stats + stat_cap_modifiers]` |
| any other integer | Add that many points, capped at `new_klass_maxes + unit.stat_cap_modifiers - current_stat` (never exceeds the promoted class's max) |

If constant `unit_stats_as_bonus` is enabled, the unit's *growth rates*
(not just current stats) also shift by `new_klass_growths - old_klass_growths`
per stat (`action.py:1986-1994`) — otherwise growths are untouched by
promotion.

Two more constants change the ceremony itself:
- `promote_level_reset` (`action.py:2015-2017`): if `True`, level resets to 1
  and exp to 0 on promotion; if `False`, level/exp carry over unchanged.
- `promote_skill_inheritance` (`app/engine/unit_funcs.py:384, 391-400`, inside
  `get_starting_skills`): if `True`, a promoted unit's learned-skill list
  also walks back up to 5 tiers through `promotes_from` and re-checks each
  ancestor class's `learned_skills` for anything the unit's level now
  qualifies for — so a promoted unit doesn't lose access to skills it
  would have learned in its base class after the level reset.

### 2.3 Triggering promotion

| Trigger | Mechanism |
|---|---|
| Auto-promote at level cap | `exp_funcs.has_autopromote(unit)` (`app/engine/exp_funcs.py:3-6`): true if constant `auto_promote` is on, **or** the unit has tag `AutoPromote` — and the class actually has `turns_into` entries — **and** the unit does not have tag `NoAutoPromote`. `can_give_exp` (`:8-16`) uses this to keep letting a maxed-level unit gain exp instead of hard-capping it. |
| Promotion item | Item component `promote` (`app/engine/item_components/class_change_components.py:8-37`, nid `promote`): on use, if the target's class has exactly one `turns_into` option it promotes automatically; if more than one, it opens the `promotion_choice` state. `force_promote` (`:39-52`, nid `force_promote`, `expose = ComponentType.Class`) skips the choice and always promotes into a hardcoded class value on the item. |
| Reclassing (not tier promotion) | `class_change`/`force_class_change` components (`:54-95`) reassign class using the unit's `alternate_classes` list instead of the tier-based `turns_into` chain — a sideways move, not a promotion. |

### 2.4 Discovering ranks / gates

None of this project's promotion items use `promote`/`force_promote`
components in `items.json` — promotion in this project is reachable **only**
through the `auto_promote` global constant (see §4).

## 3. Code files

- `app/data/database/klass.py:11-105` — `Klass` dataclass, `promotion_options`,
  and `ClassCatalog.create_new` default values.
- `app/engine/action.py:1953-2035` — `Promote` action: sentinel-value stat
  math (`:1970-1984`), growth carry-over (`:1986-1994`), `do()`/`reverse()`
  (`:2008-2035`) including `promote_level_reset` handling.
- `app/engine/item_components/class_change_components.py:8-95` — `Promote`,
  `ForcePromote`, `ClassChange`, `ForceClassChange` item components.
- `app/engine/exp_funcs.py:3-16` — `has_autopromote`, `can_give_exp`.
- `app/engine/unit_funcs.py:372-410` — `get_starting_skills`, the
  `promote_skill_inheritance` tier-walk-back logic.

## 4. Working example in this repo

`Mercenary → Vanguard`, `lion_throne.ltproj/game_data/classes.json`:
`Mercenary` (`tier: 1`, `max_level: 10`) lists `"turns_into": ["Vanguard"]`;
`Vanguard` (`tier: 2`, `promotes_from: "Mercenary"`) carries
`"promotion": {"HP": 4, "STR": 1, "MAG": 0, "SKL": 2, "SPD": 2, "LCK": 0,
"DEF": 2, "RES": 2, "CON": 2, "MOV": 1}` — plain literal stat gains, no
sentinel values used anywhere in this project. `game_data/constants.json`
sets `auto_promote: true`, `promote_skill_inheritance: true`, and
`promote_level_reset: true` (all three around lines 143-153) — so any
`Mercenary` reaching level 10 promotes automatically into `Vanguard`, resets
to level 1, and its skill list re-derives from both `Mercenary.learned_skills`
and `Vanguard.learned_skills`. No item in `items.json` carries the `promote`,
`force_promote`, or `class_change` components — this project never exposes a
promotion item to the player; auto-promotion is the only reachable path.

## 5. Test

No `tools/test_*.py` exercises `action.Promote`, `has_autopromote`, or the
`-99/-98/-97` sentinel stat math. `tools/test_overworld_gating.py` builds a
unit already sitting in the post-promotion class `Vanguard` (via
`add_party_unit('TestPromoted', 'Vanguard', 1)`, line ~186) to test an
unrelated roster-counting feature — it never calls `action.Promote` and does
not exercise the promotion transition itself. A `tools/test_promotion.py`
should exist that, after `harness.boot()`, builds a level-10 `Mercenary` unit,
calls `action.do(action.Promote(unit, 'Vanguard'))`, and asserts: `unit.klass
== 'Vanguard'`, each stat increased by exactly `Vanguard.promotion[stat]`
(clamped to `Vanguard.max_stats`), and (with `promote_level_reset` true in
this project's constants) `unit.level == 1` and `unit.exp == 0` afterward. A
second case should set a stat's `promotion` value to `-99`/`-98`/`-97` on a
throwaway class and assert each sentinel's distinct behavior, since none of
them are exercised by this project's actual content.
