---
name: author-rescue-and-pairup
description: Enable classic rescue/drop/give/take carrying or switch on Fates-style pair-up (guard stance, guard gauge, unit fusion) for a designer deciding how allied units can combine on the map.
---

## 1. Feature

Every unit has one `traveler` slot. With the `pairup` constant off (the
default), that slot is filled through classic **Rescue/Drop/Give/Take**: a
unit picks up an adjacent ally (gated by a CON/weight check), carries them
as cargo, and can hand them off or set them down elsewhere. With `pairup` on,
the same slot instead drives **Pair-Up**: the two units fuse into one
active unit with a guard gauge, the passenger backs up the leader in combat
("guard stance"), and they can switch which one leads. Both modes share the
same event-command entry points (`pair_up`/`separate`, nicknamed `rescue`/
`drop`), so a designer can write one event script and let the `pairup`
constant decide which mechanic actually executes.

## 2. Details

### 2.1 The shared carry slot

- `UnitObject.traveler` — the nid of whoever this unit is carrying;
  `UnitObject.lead_unit: bool` marks which paired unit is currently "in
  front" (`app/engine/objects/unit.py`).
- Whether picking someone up is legal at all is governed by two ordinary
  content-defined equations, not hardcoded stats: `equations.parser.
  rescue_aid(unit) >= equations.parser.rescue_weight(target)`
  (`app/engine/abilities.py:161,187,207`; also surfaced to the player at
  `app/engine/general_states.py:1921-1944`).

### 2.2 Rescue/Drop/Give/Take (`pairup = False`, the default)

Player-menu abilities, each vanishing entirely when `pairup` is on
(`if DB.constants.value('pairup'): return set()`):
- `RescueAbility` (`app/engine/abilities.py:151-172`) — pick up an adjacent
  ally with no traveler, if `rescue_aid(unit) >= rescue_weight(ally)`.
- `DropAbility` (`:122-149`) — set the traveler down on an adjacent tile.
- `TakeAbility` (`:174-192`) — take another unit's traveler onto yourself.
- `GiveAbility` (`:194-215`) — hand your traveler to an adjacent ally; also
  respects the `give_and_take` constant (below).
- Backing actions: `Rescue`/`Drop`/`Give`/`Take` (`app/engine/action.py:737,
  783,841,871`).
- **Rescue movement penalty**: `Rescue.do()` (`action.py:754-755`) adds a
  skill named literally `'Rescue'` to the carrier — but only
  `if not skill_system.ignore_rescue_penalty(self.unit) and 'Rescue' in
  DB.skills`. `IgnoreRescuePenalty` is a real skill component
  (`app/engine/skill_components/movement_components.py:94-100`, nid
  `ignore_rescue_penalty`) a designer can grant to exempt specific units. If
  no skill named `Rescue` exists in the project's `skills.json`, the whole
  penalty is silently a no-op — the mechanic only works if the project
  authors a `Rescue` skill (typically a movement/stat penalty) matching that
  literal nid.
- `give_and_take` constant (`app/data/database/constants.py:124`, tag
  `OTHER`, default `False`) — lets a unit `Give` in the same turn it already
  `Take`n (checked in `GiveAbility.targets`, `abilities.py:200`).

### 2.3 Pair-Up mode (`pairup = True`)

- Player-menu abilities (mirror-gated the opposite way —
  `if not DB.constants.value('pairup'): return set()`):
  `PairUpAbility`, `SeparateAbility`, `SwitchAbility`, `TransferAbility`
  (`app/engine/abilities.py:217-289`, approx.).
- Backing actions: `PairUp` (`action.py:901`), `SwitchPaired` (`:970`),
  `Separate` (`:1016` — comment there: "shamelessly copied from Drop... in
  case a madlad wants Rescue and Pair Up").
- Gate function `unit_funcs.can_pairup(rescuer, rescuee)`
  (`app/engine/unit_funcs.py:489-507`): `pairup` must be on **and**
  `attack_stance_only` must be off; if `player_pairup_only` is also on, both
  units must be on the `'player'` team. **All three of `pairup`,
  `attack_stance_only`, `player_pairup_only` gate the same feature at once**
  — a project can leave `pairup` on but `attack_stance_only` on and pair-up
  will never actually trigger via `can_pairup`.
- Guard gauge / guard-stance combat: `unit.get_guard_gauge()`/
  `set_guard_gauge()` (used in `PairUp.do`, `action.py:927-928`, and
  `SwitchPaired`, `:982-983`); combat integration in
  `app/engine/combat/simple_combat.py` (guard-stance exp, support-point
  increments via `supports.increment_pairup_supports`,
  `app/engine/supports.py:410-411`) and `app/engine/combat/solver.py`
  (`limit_attack_stance` constant caps how many attacks the guard partner
  contributes).
- `PairupBonus` skill component (`app/engine/skill_components/
  status_components.py:56-62`, nid `pairup_bonus`) fires on the
  `on_pairup`/`on_separate` skill hooks — a stat/skill bonus while paired.

### 2.4 One event-command surface for both modes

- `pair_up(unit1, unit2)` event command (nid `pair_up`, **nickname
  `rescue`**, `app/events/event_commands.py:3321-3327`) →
  `event_functions.pair_up` (`app/events/event_functions.py:3590-3609`):
  errors if either unit is already traveling with someone, then calls
  `unit_funcs.can_pairup(leader, follower)` — if true, does `action.PairUp`;
  **if false (including whenever `pairup` is off), transparently falls back
  to `action.Rescue(leader, follower)` instead**. One event command,
  behavior chosen by the constants above.
- `separate(unit)` event command (nid `separate`, **nickname `drop`**,
  `event_commands.py:3330-3335`) → `event_functions.separate`
  (`event_functions.py:3611-3623`): if `pairup` constant is on, does
  `action.Separate`; otherwise does `action.RemovePartner` (a plain
  traveler-clear, distinct from `Drop` which needs a destination tile).
- There is no separate `take`/`give` event command — those two remain
  player-menu-only actions in both modes.

### 2.5 Constants summary (`ConstantTag.PAIR_UP`, `app/data/database/constants.py:75-78`)

| Constant | Meaning | Engine default |
|---|---|---|
| `pairup` | Master switch: Pair-Up mode instead of Rescue/Drop/Give/Take | `False` |
| `limit_attack_stance` | Limit attack stance to the first attack only | `False` |
| `attack_stance_only` | Only attack stance allowed (no guard-fusion) — also blocks `can_pairup` outright when true | `False` |
| `player_pairup_only` | Only player-team units may pair up | `False` |

## 3. Code files

- `app/engine/abilities.py:122-215` (Rescue/Drop/Take/Give),
  `:217-289` approx. (PairUp/Separate/Switch/Transfer) — menu-ability gating.
- `app/engine/action.py:737-782` (`Rescue`), `:783-` (`Drop`), `:841-`
  (`Give`), `:871-` (`Take`), `:901-` (`PairUp`), `:970-` (`SwitchPaired`),
  `:1016-` (`Separate`).
- `app/engine/unit_funcs.py:489-507` — `can_pairup`.
- `app/events/event_commands.py:3321-3335` — `PairUp`/`Separate` commands
  and their `rescue`/`drop` nicknames.
- `app/events/event_functions.py:3590-3623` — `pair_up`/`separate` handlers
  and the rescue-fallback logic.
- `app/engine/skill_components/movement_components.py:94-100` —
  `IgnoreRescuePenalty`.
- `app/engine/skill_components/status_components.py:56-62` —
  `PairupBonus`.
- `app/data/database/constants.py:75-78,124` — the `PAIR_UP`-tagged
  constants plus `give_and_take`.

## 4. Working example in this repo

`lion_throne.ltproj/game_data/constants.json` sets `pairup: false`,
`attack_stance_only: true`, `player_pairup_only: true`, `give_and_take: true`
(so Pair-Up is doubly disabled: even flipping `pairup` on would leave
`can_pairup` returning `False` because `attack_stance_only` is also true) —
only Rescue/Drop/Give/Take is reachable in this project. `equations.json`
authors `RESCUE_AID = "max(0, 25 - CON) if 'Mounted' in unit.tags else
max(0, CON - 1)"` and `RESCUE_WEIGHT = "CON"` (`lion_throne.ltproj/game_data/
equations.json:71-76`) — a real, tuned formula giving mounted units far more
carrying capacity, using the `Mounted` tag (`tags.json`) and per-class `CON`
stat (e.g. `classes.json` cavalry classes). No skill named `Rescue` exists in
`lion_throne.ltproj/game_data/skills.json`, so the carrier's movement penalty
described in §2.2 never actually applies in this project — carrying an ally
here has no drawback beyond occupying the traveler slot. No event script in
`lion_throne.ltproj/game_data/events.json` calls `pair_up`/`rescue`/
`separate`/`drop` — Rescue/Drop/Give/Take is reachable only through the
always-available in-map unit menu (gated purely by adjacency and the
CON-based equations above, not by any level authoring).

## 5. Test

No `tools/test_*.py` exercises `Rescue`/`Drop`/`Give`/`Take`, `PairUp`,
`can_pairup`, or the `rescue_aid`/`rescue_weight` equations. A
`tools/test_rescue.py` should exist that, after `harness.boot()`, builds a
`Mounted`-tagged unit and a non-mounted ally, asserts
`equations.parser.rescue_aid`/`rescue_weight` reproduce the
`lion_throne.ltproj` formula above, calls `action.do(action.Rescue(...))` and
asserts `unit.traveler == ally.nid` and the ally leaves the board
(`ally.position is None`), then asserts calling `action.Rescue.reverse()`
restores the ally's original position — plus a case toggling `DB.constants`
`pairup=True`/`attack_stance_only=False` and asserting
`unit_funcs.can_pairup` flips to `True` only when both are set correctly.
