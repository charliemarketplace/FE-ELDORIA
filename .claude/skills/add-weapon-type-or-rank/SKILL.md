---
name: add-weapon-type-or-rank
description: Add a new weapon type (with its own triangle advantage/disadvantage and rank-based bonuses) or a new weapon proficiency rank, for a designer building out combat math beyond the Sword/Lance/Axe/Light/Anima/Dark triangle.
---

## 1. Feature

A designer can define a new weapon type (e.g. a "Bow" that's exempt from
the triangle, or an entirely new type with its own advantage/disadvantage
matchups against existing types) and/or extend the weapon-rank ladder
(D/C/B/A/S…) that gates which items a unit can wield and grants combat
bonuses as proficiency (`wexp`) grows. Both are pure-JSON authoring — no
code changes — because the engine resolves the weapon triangle and rank
bonuses generically off whatever types/ranks exist in the database.

## 2. Details

### 2.1 Weapon type — `WeaponType` (`app/data/database/weapons.py:118-152`)

| Field | Meaning | Default |
|---|---|---|
| `nid`, `name` | Identifier / display name | required |
| `force_melee_anim` | Force the melee combat animation even for a ranged item of this type | `False` |
| `hide_from_display` | Hide this type from UI displays (e.g. an internal-only type) | `False` |
| `rank_bonus` | `CombatBonusList` — flat combat bonus once a unit reaches a given rank *in this type*, independent of any opponent | `[]` |
| `advantage` | `CombatBonusList` — bonus applied when attacking a listed opposing type | `[]` |
| `disadvantage` | `CombatBonusList` — penalty applied when attacked by a listed opposing type | `[]` |
| `icon_nid`/`icon_index` | Display icon | `None`/`(0,0)` |

Each `CombatBonus` entry (`weapons.py:7-45`) pairs a `weapon_type` (for
`advantage`/`disadvantage`) or nothing (for `rank_bonus`, which instead pairs
a `weapon_rank`, or the literal string `"All"` to apply at every rank) with
8 float effects: `damage, resist, accuracy, avoid, crit, dodge,
attack_speed, defense_speed`. A brand-new weapon type created via
`WeaponCatalog.create_new` (`:160-167`) starts with all three lists empty —
no triangle relationships and no rank bonuses until authored.

### 2.2 Weapon rank — `WeaponRank` (`weapons.py:76-91`) and the ladder

| Field | Meaning |
|---|---|
| `rank` | The rank label (its own nid) — any string, not limited to D/C/B/A/S |
| `requirement` | Minimum accumulated `wexp` in a type to hold this rank |

`RankCatalog.get_rank_from_wexp`/`get_next_rank_from_wexp` (`:95-110`) sort
all authored ranks by `requirement` and binary-bucket a unit's wexp into the
highest rank it qualifies for — so adding a new rank is just inserting one
more `{rank, requirement}` entry; there is no hardcoded rank count or
letter scheme.

### 2.3 Wiring a weapon type into an item

Item components (`app/engine/item_components/weapon_components.py`):
- `WeaponType` (nid `weapon_type`, `:12-28`) — declares the item's type;
  `available()` checks the wielder's class actually has non-zero `wexp_gain`
  for that type *and* current `wexp > 0`.
- `WeaponRank` (nid `weapon_rank`, `:30-46`, `requires = ['weapon_type']`) —
  gates the item behind a minimum rank: `available()` compares the
  wielder's `wexp` for the item's weapon type against
  `DB.weapon_ranks.get(self.value).requirement`.

### 2.4 How the bonuses actually apply — `combat_calcs.py`

- `get_weapon_rank_bonus(unit, item)` (`:13-` ) looks up
  `DB.weapons.get(weapon_type).rank_bonus` and returns whichever entry
  matches the unit's current rank (or `"All"`).
- `compute_advantage(unit1, unit2, item1, item2, advantage=True)`
  (`:75-` ) reads `DB.weapons.get(item1_weapontype).advantage` (or
  `.disadvantage`) and checks whether `item2`'s type is one of the entries —
  this is the entire weapon-triangle implementation; there's no hardcoded
  Sword>Axe>Lance table anywhere in code, it's 100% data.
  `item_system.ignore_weapon_advantage` (component `ignore_weapon_advantage`,
  `app/engine/item_components/extra_components.py:197-` ) lets a specific
  item opt out of triangle effects entirely.
- `weapon_rank_bonus` is folded into every relevant stat function
  (`accuracy` at `:152-156`, `avoid` at `:178-180`, `crit` at `:213-215`,
  `dodge` at `:235-237`, etc.) alongside the support-rank bonus (see the
  support/affinity skill).

### 2.5 Wexp-gain constants (`app/data/database/constants.py:143-145`)

| Constant | Meaning | Default |
|---|---|---|
| `kill_wexp` | Kills grant double weapon exp | `True` |
| `double_wexp` | Each hit while doubling grants wexp (not just the first) | `True` |
| `miss_wexp` | Gain wexp even on a miss | `True` |

## 3. Code files

- `app/data/database/weapons.py:7-186` — `CombatBonus`/`CombatBonusList`,
  `WeaponRank`/`RankCatalog`, `WeaponType`/`WeaponCatalog`, `WexpGain`.
- `app/engine/item_components/weapon_components.py:12-46` — `WeaponType`
  and `WeaponRank` item components (`available()` gating logic).
- `app/engine/combat_calcs.py:13-27` (`get_weapon_rank_bonus`), `:75-`
  (`compute_advantage`), plus every stat function that folds in
  `weapon_rank_bonus`.
- `app/data/database/constants.py:143-145` — `kill_wexp`/`double_wexp`/
  `miss_wexp`.

## 4. Working example in this repo

`lion_throne.ltproj/game_data/weapon_ranks.json` defines a 4-rank ladder:
`D` (requirement 1), `C` (16), `B` (39), `A` (71) — no `S` rank exists in
this project despite the engine supporting an arbitrary number.
`weapons.json` authors the classic two triangles entirely through
`advantage`/`disadvantage`: `Sword` beats `Axe` (`damage +1, accuracy +15`)
and loses to `Lance` (`damage -1, accuracy -15`); `Axe` beats `Lance`, loses
to `Sword`; `Light` beats `Dark`, loses to `Anima`; `Anima` beats `Light`,
loses to `Dark`; `Dark` beats `Anima`, loses to `Light`. `Bow` and `Default`
have empty `advantage`/`disadvantage` (no triangle interaction) and every
type's `rank_bonus` list is empty — the rank-bonus knob (flat bonus for
reaching a rank in a type, independent of the opponent) is fully wired in
`combat_calcs.py` but not exercised anywhere in this project's data.
`constants.json` sets `kill_wexp: false`, `double_wexp: false`,
`miss_wexp: true` (verified in `lion_throne.ltproj/game_data/constants.json`)
— a deliberate slower wexp-gain pace than the engine defaults.

## 5. Test

No `tools/test_*.py` exercises `compute_advantage`, `get_weapon_rank_bonus`,
or wexp-gain constants. A `tools/test_weapon_triangle.py` should exist that,
after `harness.boot()`, builds two units wielding a `Sword` and an `Axe`
respectively, calls `combat_calcs.compute_hit`/`compute_damage` for both
attack directions, and asserts the `Sword` wielder's hit/damage against the
`Axe` wielder is exactly `+15`/`+1` relative to a matchup with
`ignore_weapon_advantage` forced true (isolating the triangle's
contribution from base equation math) — and a second case that gives a unit
enough `wexp` to cross the `C`/`B`/`A` thresholds from `weapon_ranks.json`
and asserts `DB.weapon_ranks.get_rank_from_wexp(unit.wexp['Sword'])` returns
the expected rank at each boundary.
