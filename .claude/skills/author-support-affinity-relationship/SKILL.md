---
name: author-support-affinity-relationship
description: Author a support pair or affinity between two characters — rank thresholds, per-rank combat bonuses, and the constants that gate how supports are earned and combined — for a designer who wants relationship-driven combat bonuses.
---

## 1. Feature

A designer can declare a support relationship between two named characters
(a `SupportPair`) that grows from points earned during play (ending a
chapter together, ending turns near each other, fighting together, etc.)
into unlockable "ranks" (C/B/A/S, or any custom rank ladder), each of which
grants a combat stat bonus while the pair is within range on the map. In
parallel, each character can carry an `Affinity` (a `Persona`-style
elemental/personality tag) whose own per-rank bonus table stacks with — or
substitutes for, depending on a constant — the specific-pair bonus.

## 2. Details

### 2.1 Support ranks — `SupportRank` (`app/data/database/supports.py:8-31`)

A flat ordered list of rank nids (e.g. `C`, `B`, `A`, `S`) — there is no
built-in rank naming, `db.support_ranks` is just an ordered
`SupportRankCatalog`; `add_new_default` seeds a rank named `"C"`.
`RankCatalog`-style helpers (`get_highest_rank`, index ordering) treat later
entries in the list as higher rank.

### 2.2 A support pair — `SupportPair` (`supports.py:169-217`)

| Field | Meaning | Default |
|---|---|---|
| `unit1`, `unit2` | The two character nids | `None` |
| `one_way` | If true, only `unit1`'s presence/actions earn points (asymmetric support) | `False` |
| `requirements` | `SupportRankRequirementList` — one `SupportRankRequirement` per rank this pair can reach | `[]` |

Each `SupportRankRequirement` (`:136-157`, extends `SupportRankBonus`) has:

| Field | Meaning |
|---|---|
| `support_rank` | Which rank this entry unlocks |
| `requirement` | Point threshold to unlock it |
| `gate` | Optional game-var name; the rank only counts as usable in combat if `game.game_vars.get(gate)` is truthy (e.g. gating an A-support behind a story flag) |
| `effects` (8 floats: `damage, resist, accuracy, avoid, crit, dodge, attack_speed, defense_speed`) | The combat bonus granted once this rank is active |

### 2.3 Affinities — `Affinity` (`supports.py:81-110`)

| Field | Meaning | Default |
|---|---|---|
| `bonus` | `SupportRankBonusList` — one `SupportRankBonus` (same 8-float `effects` shape as above, but no independent point requirement — it rides on whatever rank the *pair* has reached) per support rank | `[]` |
| `icon_nid`/`icon_index` | Display icon | `None`/`(0,0)` |

A unit's affinity is set per-`UnitPrefab` (`affinity` field, see the
character-authoring skill). `get_bonus` (`app/engine/supports.py:246-` ) looks
up both units' `Affinity.bonus` list for a `SupportRankBonus` matching the
pair's current highest unlocked rank, then combines it with the pair's own
`SupportRankRequirement.effects` per the `bonus_method` constant below.

### 2.4 Constants (`supports.py:115-134`, all in `support_constants.json`)

| Constant | Meaning | Default |
|---|---|---|
| `combat_convos` | Allow support conversations mid-combat | `True` |
| `base_convos` | Allow support conversations at base | `False` |
| `battle_buddy_system` | Let characters swap current support "buddy" at base | `False` |
| `break_supports_on_death` | On permadeath, kill the support along with the unit | `True` |
| `bonus_method` | How affinity bonus combines with the pair bonus: `"No Bonus"` / `"Use Personal Affinity Bonus"` / `"Use Partner's Affinity Bonus"` / `"Use Average of Affinity Bonuses"` / `"Use Sum of Affinity Bonuses"` | `"Use Average of Affinity Bonuses"` |
| `bonus_range` | Map-tile distance within which a support's *combat* bonus applies (`0` = only same-target; `99` = whole map) | `3` |
| `growth_range` | Distance within which a support *earns points* | `1` |
| `chapter_points` / `end_turn_points` / `combat_points` / `interact_points` / `pairup_points` | Points earned per chapter-end / turn-end / combat / dialogue interaction / pair-up combat while in range | `0/1/0/0/0` |
| `bonus_ally_limit` | Max number of active support bonuses stacked at once (`0` = unlimited) | `0` |
| `rank_limit` | Max total support ranks one character can hold across all partners | `5` |
| `highest_rank_limit` | Max number of partners allowed at the *highest* configured rank | `1` |
| `ally_limit` | Max number of distinct partners one character can support with | `0` (unlimited) |
| `point_limit_per_chapter` / `rank_limit_per_chapter` | Caps on how much progress one pair can make within a single chapter | `0` (unlimited) / `1` |

### 2.5 Runtime plumbing

`app/engine/supports.py`'s `SupportPair` (runtime object, `:16-84`, distinct
from the database `SupportPrefab`) tracks `points`, `locked_ranks` (earned
but not yet declared active), `unlocked_ranks`. `increment_points` (`:37-49`)
walks the prefab's `requirements` and locks a new rank each time the running
point total crosses a threshold, respecting `point_limit_per_chapter` /
`rank_limit_per_chapter`. `can_support` (`:57-68`) is the actual eligibility
check combat code calls — it enforces `rank_limit`, `ally_limit`,
`highest_rank_limit`, and any per-rank `gate` game-var.
`app/engine/combat_calcs.py`'s `get_support_rank_bonus` (`:30-` ) is called
from every combat-math function (`compute_hit`, `compute_crit`,
`compute_damage`, etc. — e.g. `:156-157`, `:182-183`, `:217-218`) and even
implements a "Three Houses style" attack-only variant (`:389-398`) that only
applies the bonus to the attacker's side.

## 3. Code files

- `app/data/database/supports.py:8-217` — `SupportRank`, `SupportRankBonus`,
  `Affinity`, `SupportRankRequirement`, `SupportPair` (database prefab), and
  the `support_constants` `ConstantCatalog` (`:115-134`).
- `app/engine/supports.py:16-84` — runtime `SupportPair` (points/ranks
  tracking); `:246-` `SupportController.get_bonus` (affinity + pair
  combination per `bonus_method`).
- `app/engine/combat_calcs.py:30-73` — `get_support_rank_bonus`; consumed
  throughout the hit/avoid/crit/dodge/damage functions and the "Three Houses
  style" attacker-only branch (`:389-398`).

## 4. Working example in this repo

**This feature is fully implemented but entirely unused in this project's
content.** `lion_throne.ltproj/game_data/affinities.json`,
`support_pairs.json`, and `support_ranks.json` are all empty JSON arrays
(`[]`) — no affinity, no support rank ladder, and no support pair is
authored anywhere. Every `UnitPrefab.affinity` in `units.json` is `null`
(verified across all entries). `support_constants.json` *is* configured
(non-defaults: `base_convos: 2`, `bonus_method: "Use Sum of Affinity
Bonuses"`, `pairup_points: 1`), but with zero ranks/pairs/affinities
declared, `get_support_rank_bonus` has nothing to iterate over and always
returns an empty bonus. The closest analogue in this project's actual
content is the weapon-triangle `advantage`/`disadvantage` bonus tables in
`weapons.json` (see the weapon-type/rank skill) — same 8-float
`CombatBonus` shape, same `combat_calcs.py` consumption pattern, but keyed
by weapon type instead of by character pair/affinity.

## 5. Test

No `tools/test_*.py` touches `supports.py`, `SupportPair`, or
`get_support_rank_bonus` — unsurprising, since the feature is unreachable
with this project's current data (empty support ranks/pairs/affinities). A
`tools/test_supports.py` should exist that seeds one `SupportRank` (`"C"`),
one `SupportPair` between two real unit nids with a `SupportRankRequirement`
(`requirement=1`, a non-zero `damage`/`accuracy` in `effects`), places both
units within `bonus_range` on a level, calls `action.do` enough turns/combats
to cross the point threshold via `game.supports`, and asserts
`combat_calcs.compute_hit`/`compute_damage` for that unit changes by exactly
the authored bonus once the rank unlocks — proving the currently-dormant
plumbing actually fires when data is supplied.
