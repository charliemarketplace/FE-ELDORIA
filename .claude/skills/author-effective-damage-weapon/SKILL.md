---
name: author-effective-damage-weapon
description: Author an item that deals hugely bonus damage against units carrying a specific tag (anti-cavalry, anti-armor, anti-dragon weapons), via the effective_damage item component, its icon/targeting tells, and the negate/negate_tags counter a designer can put on the defending side.
---

## 1. Feature

`effective_damage` lets a designer make an item spike its damage against any
unit whose `tags` list intersects a chosen set — the classic "Horseslayer"/
"Hammer" pattern. It is a single, self-contained item component: pick the
tags, the multiplier, and a flat bonus, and the engine handles the math, the
pulsing white icon tell, and the "danger" targeting-reticle icon for free.
The same effect can be negated on the defending side by a skill with
`negate` (blanket immunity) or `negate_tags` (immunity to specific tags),
which is how a designer authors a "Fili Shield"-style ward.

## 2. Details

### 2.1 The component — `EffectiveDamage` (nid `effective_damage`)

`app/engine/item_components/extra_components.py:10-98`. Uses
`ComponentType.NewMultipleOptions`, so it is authored as one component with
five sub-fields, all optional (defaults shown are the constructor defaults
at lines 25-32):

| Field | Type | Default | Meaning |
|---|---|---|---|
| `effective_tags` | List[Tag] | `[]` | Which `DB.tags` this item is effective against. Empty means the component can never trigger (`any(... for tag in [])` is `False`). |
| `effective_multiplier` | Float | `3` | Bonus damage = `(multiplier - 1.0) * might`, added on top of normal damage. |
| `effective_bonus_damage` | Int | `0` | Flat extra damage added after the multiplier. |
| `show_effectiveness_flash` | Bool | `True` | Pulses the item's map icon white when it would be effective against the current target. |
| `weapon_effectiveness_multiplied` | Bool | `True` | If `True`, weapon-triangle advantage/disadvantage damage is folded into `might` before the multiplier is applied (so triangle bonus is also multiplied); if `False`, only the item's base damage is multiplied. |

### 2.2 The math (`dynamic_damage`, lines 87-98)

```
if target has any tag in effective_tags AND not negated:
    might = item_system.damage(unit, item) or 0
    if weapon_effectiveness_multiplied:
        might += triangle advantage/disadvantage damage (both directions)
    return int((multiplier - 1.0) * might + bonus_damage)
else:
    return 0
```

This return value flows into the shared `dynamic_damage` pipeline, not a
special-cased one: `item_system.dynamic_damage()`
(`app/engine/item_system.py:1169-1177`, sums every item component that
defines `dynamic_damage`) and `skill_system.dynamic_damage()`
(`app/engine/skill_system.py:1385-1394`, sums every skill component that
defines it) are both added into `might` in
`combat_calcs.compute_damage()` (`app/engine/combat_calcs.py:460,468-470`).
Any skill-side `dynamic_damage` component (e.g. a proc skill, see the
combat-art skill) stacks additively with an item's `effective_damage`.

### 2.3 Negation — the defender's counter

`_check_negate()` (lines 61-73) checks the *target's* skills, not the
item's own tags list:

- Any skill with the bare `Negate` component (nid `negate`,
  `app/engine/skill_components/attribute_components.py:62-65`, no
  parameters) whose `condition()` currently holds negates *all*
  `effective_damage` items unconditionally.
- Any skill with `NegateTags` (nid `negate_tags`, lines 67-72, exposes
  `List[Tag]`) whose tag list intersects this item's `effective_tags`
  (and whose `condition()` holds) negates just that tag family.

If negated, `_check_effective()` returns `False` and `dynamic_damage`
returns `0` — the item behaves as a plain weapon for that fight, with no
flash and no danger icon either (both call `_check_effective`/`_check_negate`
too).

### 2.4 UI tells (lines 75-85)

- `item_icon_mod`: if `show_flash` and the current hover target is
  effective, the sprite is recolored via
  `image_mods.make_white(sprite, abs(250 - engine.get_time() % 500)/250)`
  — a triangle-wave white pulse, purely cosmetic.
- `target_icon`: returns the string `'danger'` (consumed elsewhere as a
  reticle icon) when the item is `available`, the target is an enemy
  (`skill_system.check_enemy`), and it is currently effective against them.

### 2.5 What happens if you omit fields

Omitting the component entirely: item does normal damage, no icon/reticle
changes. Omitting `effective_tags` only (leaving `[]`): the component is
present but inert — `_check_effective` always returns `False`. Omitting
`effective_multiplier`: defaults to `3` (i.e. triple total might). No DB
constant gates this feature — it is purely item-authoring, always
reachable the moment the component is attached and `effective_tags` is
non-empty.

## 3. Code files

- `app/engine/item_components/extra_components.py:10-98` — `EffectiveDamage`
  component: options, `_check_effective`, `_check_negate`, `item_icon_mod`,
  `target_icon`, `dynamic_damage`.
- `app/engine/skill_components/attribute_components.py:62-72` — `Negate`,
  `NegateTags` (the defender-side counters).
- `app/engine/item_system.py:1169-1177` — `dynamic_damage` aggregator
  (sums all item components' contributions via `utils.numeric_accumulate`,
  i.e. plain `sum()`, `app/engine/component_system/utils.py:72-73`).
- `app/engine/skill_system.py:1385-1394` — the skill-side twin aggregator
  (each component's `ignore_conditional` flag or `condition(skill, unit,
  item)` gates whether it counts).
- `app/engine/combat_calcs.py:460-470` — `compute_damage()`, where both
  aggregators are added into `might` before weapon-triangle math.

## 4. Working example in this repo

None. A repo-wide check of `lion_throne.ltproj/game_data/items.json` shows
no item carries the `effective_damage` component, and no skill in
`skills.json` carries `negate`/`negate_tags`. The closest analogue actually
authored in this project is the **skill**-side twin of the same pipeline:
`Luna_proc` (`lion_throne.ltproj/game_data/skills.json`, granted temporarily
by the `TLT_Luna` combat art on the Halberdier class) carries
`["dynamic_damage", "combat_calcs.defense(unit, target, None, item)"]` — an
eval expression that adds the target's defense stat as bonus damage,
through the exact same `skill_system.dynamic_damage` →
`combat_calcs.compute_damage` (line 470) path `effective_damage` would use
from the item side, just expressed as a formula instead of a
tag-conditional multiplier.

## 5. Test

No `tools/test_*.py` references `effective_damage`, `negate_tags`, or
`dynamic_damage` (grep across all 13 files under `tools/` for these terms
returns nothing). A `tools/test_effective_damage.py` should exist that,
after `harness.boot()`: creates an item prefab with an `effective_damage`
component (`effective_tags=['Cavalry']`, `effective_multiplier=2.0`,
`effective_bonus_damage=5`), a defending unit tagged `Cavalry`, and asserts
`combat_calcs.compute_damage(...)` for that matchup exceeds the same call
against an untagged unit by exactly `might + 5` (i.e. doubled plus flat
bonus); a second case should give the defender a skill with `negate_tags:
['Cavalry']` and assert the bonus drops back to the untagged value.
