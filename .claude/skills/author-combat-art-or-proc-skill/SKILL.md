---
name: author-combat-art-or-proc-skill
description: Author a skill that grants a player-selectable Combat Art (an extra attack option that applies a bonus effect for one fight) or an automatic proc skill (a chance-based or charge-based trigger like Miracle/Astra/Luna), including the charge/mana resource system that gates how often it can fire.
---

## 1. Feature

This is the FE-style "activated ability" layer built on top of ordinary
combat: a skill can either (a) show up as a selectable option in the unit
action menu that temporarily attaches a bonus-effect child skill to the next
attack (a **Combat Art**), or (b) silently roll to attach that child skill
on its own, at a fixed point in combat resolution (a **proc skill** —
on-attack, on-defense, or unconditional survival effects like Miracle).
Both flavors share the same "resource" layer: a skill can be gated behind a
charge counter that fills over time or per stat point, or a mana cost,
so a designer can make an ability usable every few turns instead of every
fight. This project's playable classes each carry exactly one worked
example of nearly every variant (Critical, Cleave, Metamagic, Luna, Sol,
Miracle) — this is one of the most actively-used systems in the whole repo.

## 2. Details

### 2.1 Combat Art vs. automatic vs. proc — four trigger shapes

All in `app/engine/skill_components/advanced_components.py`:

| Component | nid | Trigger | Player-facing? |
|---|---|---|---|
| `CombatArt` | `combat_art` | Player picks it from the "Combat Arts" menu entry before attacking; active for exactly that one combat | Yes — appears as a menu option |
| `AutomaticCombatArt` | `automatic_combat_art` | Applied on `on_upkeep`, removed on `on_endstep` — active the whole turn, no player choice | No (passive that turn) |
| `AttackProc` / `DefenseProc` | `attack_proc` / `defense_proc` | Rolls once per **strike** (`start_sub_combat`) while attacking/defending; lasts one strike | No |
| `AttackPreProc` / `DefensePreProc` | `attack_pre_proc` / `defense_pre_proc` | Rolls once at `start_combat` while attacking/defending; lasts the whole combat | No |
| `ProcGainSkillForTurn` | `proc_turn_skill` | Rolls once at `on_upkeep`; lasts the whole turn | No |

Each of `CombatArt`/`AutomaticCombatArt`/the proc variants `expose`s
`ComponentType.Skill` — the **child** skill nid to attach (usually a
`hidden` skill carrying the actual stat/damage modifiers, so it doesn't
clutter the unit's skill list under its own name).

### 2.2 Combat Art activation flow (player-facing)

- `skill_system.get_combat_arts(unit)` (`skill_system.py:400-433`) — for
  each of the unit's skills whose `condition()` currently holds and which
  defines `combat_art`, computes which of the unit's items pass every
  `weapon_filter` component (see `AllowedWeapons` below) and, by
  provisionally activating the art and checking
  `game.target_system.get_valid_targets`, still have a valid target at the
  art's (possibly range-modified) range. Only surfaces the art if at least
  one such weapon exists.
- `general_states.py:934-950` — inserted into the action menu right after
  "Attack", either flattened into individual options or (if the
  `combat_art_category` DB constant is `True`) folded into one "Combat
  Arts" sub-menu entry.
- Selecting one calls `skill_system.activate_combat_art(unit, skill)`
  (`skill_system.py:435-438`), which runs every `on_activation` hook —
  `CombatArt.on_activation` (`advanced_components.py:101-107`) does
  `action.do(action.AddSkill(unit, self.value))`, attaching the child skill
  — then transitions to `weapon_choice` restricted to the pre-filtered
  weapon list.
- `CombatArt.end_combat_unconditional` (`advanced_components.py:116-119`)
  fires `action.TriggerCharge` and clears `self.skill.data['active']`
  whether or not the attack actually connected; `deactivate_combat_art`
  removes the child skill if the player backs out without attacking.

### 2.3 `AllowedWeapons` — restricting which items an art/proc can use

nid `allowed_weapons` (`advanced_components.py:137-150`): exposes a
`String` evaluated via `evaluate.evaluate(self.value, unit,
local_args={'item': item})` — an arbitrary Python boolean expression with
`unit`/`item` in scope, e.g.
`"item_system.is_weapon(unit, item) and not item_funcs.is_magic(unit, item)"`
(from `TLT_Critical`). `get_weapon_filter()`
(`advanced_components.py:160-164`) looks up the first component on the
skill defining `weapon_filter` and applies it; every proc variant checks
this before rolling.

### 2.4 `ProcRate` and the roll itself

nid `proc_rate` (`advanced_components.py:295-303`): exposes an
`Equation` nid, resolved via `equations.parser.get(self.value, unit)`.
`get_proc_rate()` (`advanced_components.py:153-157`) looks it up the same
way as the weapon filter; **if no `ProcRate` component is present, the
default proc rate is a hardcoded `100` (always procs)** — this is the
"silent fallback to a hardcoded constant when an expected equation is
absent" pattern: a designer who forgets `proc_rate` gets guaranteed
activation, not a broken skill. The roll itself is
`static_random.get_combat() < proc_rate` (a 0-99 rng draw), used identically
in `AttackProc`, `DefenseProc`, `AttackPreProc`, `DefensePreProc`,
`ProcGainSkillForTurn`, and `AstraProc`.

### 2.5 `AstraProc` — a bundled multi-hit-and-damage-modifier proc

nid `astra_proc` (`advanced_components.py:306-370`), a `NewMultipleOptions`
component (`extra_attacks` int, default `4`; `damage_percent` float,
default `0.5`; `show_proc_effects` bool, default `True`). On a successful
proc during `start_sub_combat`, it both adds `extra_attacks` phases via
`dynamic_multiattacks` and multiplies subsequent strikes' damage by
`damage_percent` via `damage_multiplier`, tracking hit count internally
until it has covered `extra_attacks + 1` strikes, then resets — this is a
purpose-built component for FE's classic Astra/Sacred Dance-style "hits
5 times at half damage" effect; it doesn't compose from smaller pieces the
way the other procs do.

### 2.6 The resource layer — `charge` (`app/engine/skill_components/charge_components.py`)

| Component | nid | Fill behavior | Active when |
|---|---|---|---|
| `BuildCharge` | `build_charge` | Starts at `0`; resets to `0` on use | `charge >= total_charge` (value, default `10`) |
| `DrainCharge` | `drain_charge` | Starts full; `-1` per use | `charge > 0` |
| `ChargesPerTurn` | `charges_per_turn` | Refills to full every `on_endstep` | `charge > 0` |
| `UpkeepChargeIncrease` | `upkeep_charge_increase` | `+value` every `on_upkeep`, clamped `[0, total_charge]` | (pairs with `build_charge`) |
| `CombatChargeIncrease` | `combat_charge_increase` | `+value` after any combat that landed a hit/crit and the skill wasn't already active | (pairs with `build_charge`) |
| `CombatChargeIncreaseByStat` | `combat_charge_increase_by_stat` | Same, but `+unit.stats[stat]+stat_bonus` instead of a flat value (exposes `ComponentType.Stat`, default `SKL`) | (pairs with `build_charge`) |
| `GainMana` / `CostMana` / `CheckMana` | `gain_mana` / `cost_mana` / `check_mana` | Mana-based instead of a charge counter | `unit.current_mana >= value` |

All charge components set `ignore_conditional = True`, meaning
`skill_system.condition()` treats their `condition()` return as
authoritative for gating the *skill itself* (not just an optional
modifier) — this is how "the skill only works once charged" is enforced:
`get_combat_arts()` and `get_extra_abilities()` both call
`condition(skill, unit)` before surfacing anything, and `BuildCharge`/
`DrainCharge`'s `condition()` is exactly the charge check. The actual
decrement/reset only happens when `action.TriggerCharge(unit, skill)`
(`app/engine/action.py:3503-3516`) is explicitly invoked by the
triggering component (`CombatArt.end_combat_unconditional`, each proc's
`end_sub_combat`/`end_combat_unconditional`, or a `combat2` component like
`Miracle`) — a component that procs without also calling `TriggerCharge`
would never consume its charge.

### 2.7 The unconditional "survival" family (`combat2_components.py`)

Not gated by `proc_rate` at all — these always apply once their skill is
present and simply consume charge on trigger: `Miracle` (survive at 1 HP,
`cleanup_combat`), `TrueMiracle` (floor damage at 1 HP,
`after_take_strike`), `IgnoreDamage` (cancel all incoming damage),
`LiveToServe`/`Lifetaker`/`Lifelink` (self-heal off of healing/kills/damage
dealt) — all in `app/engine/skill_components/combat2_components.py:15-140`.
These are typically paired with `drain_charge` (e.g. "once per chapter")
rather than a proc roll.

### 2.8 What happens if you omit fields

Omit both a charge component and `proc_rate`: the skill/art is always
active and always procs at 100% — no cooldown at all. Omit `allowed_weapons`:
every item the unit owns is eligible. Omit `combat_art_category` (DB
constant, default `False`): Combat Arts list flat in the action menu
instead of nesting under one "Combat Arts" entry
(`app/data/database/constants.py:125`).

## 3. Code files

- `app/engine/skill_components/advanced_components.py:16-390` —
  `MultiSkill`, `Ability`, `CombatArt`, `AutomaticCombatArt`,
  `AllowedWeapons`, `get_proc_rate`/`get_weapon_filter`,
  `ProcGainSkillForTurn`, `AttackProc`, `DefenseProc`, `AttackPreProc`,
  `DefensePreProc`, `ProcRate`, `AstraProc`.
- `app/engine/skill_components/charge_components.py:1-190` — all charge
  and mana components in §2.6.
- `app/engine/skill_components/combat2_components.py:15-140` — the
  unconditional survival/self-heal proc family in §2.7.
- `app/engine/skill_system.py:174-181` — `condition()` (AND-aggregates
  every component's `condition`).
- `app/engine/skill_system.py:400-448` — `get_combat_arts`,
  `activate_combat_art`, `deactivate_combat_art`,
  `deactivate_all_combat_arts`.
- `app/engine/skill_system.py:380-389` — `get_extra_abilities` (the
  `Ability` component's consumer, shared menu machinery).
- `app/engine/action.py:3503-3516` — `TriggerCharge` (turnwheel-reversible
  charge consumption/reset).
- `app/engine/general_states.py:920-966,1097-1106` — the action-menu
  Combat Arts listing and selection handling.
- `app/data/database/constants.py:125` — `combat_art_category` constant.

## 4. Working example in this repo

Extensively used. `lion_throne.ltproj/game_data/classes.json` grants:
`Archer` → `TLT_Critical` (`combat_art` + `build_charge:30` +
`combat_charge_increase_by_stat:SKL` + `allowed_weapons` restricting to
non-magic weapons; the child skill `Critical_item_mod` gives `["crit",
1000], ["guaranteed_crit", null]` — a guaranteed-critical Combat Art),
`Fighter`/`Ghoul` → `TLT_Cleave` (`combat_art` + `build_charge:15`,
weapon-filtered to Sword/Axe at range 1; child `Cleave_item_mod` adds
`limit_maximum_range:1`, `cannot_double`, and a splash-damage `Cleave`
component), `Halberdier` → `TLT_Luna` and `Vanguard` → `TLT_Sol` (both
`combat_art` + `build_charge:40`; `Luna_proc` adds the target's defense as
bonus damage via `dynamic_damage`, `Sol_proc` is a `lifelink:1.0`), `Sage`
→ `TLT_Metamagic` (`automatic_combat_art`, no player choice, `build_charge:40`),
and `Cleric` → `TLT_Miracle` (`miracle` + `drain_charge:1`, i.e. once per
chapter — not a `build_charge`/proc-rate skill at all, the pure
unconditional-survival pattern from §2.7). This project sets
`combat_art_category: false` in `constants.json`, so all of the above list
flat in the menu rather than nesting under one submenu.

## 5. Test

No `tools/test_*.py` references `combat_art`, `proc_rate`, `build_charge`,
or `drain_charge` (checked all 13 files under `tools/`). A
`tools/test_combat_art.py` should exist that, after `harness.boot()`: gives
a unit the `TLT_Critical` skill with charge pre-set below `build_charge`'s
threshold and asserts `skill_system.get_combat_arts(unit)` is empty; sets
charge to the threshold and asserts the art now appears and is keyed to
only the unit's non-magic weapons; calls
`skill_system.activate_combat_art` and asserts the `Critical_item_mod`
child skill is attached; and finally calls
`action.do(action.TriggerCharge(unit, skill))` and asserts charge resets to
`0` per `BuildCharge`'s `trigger_charge`.
