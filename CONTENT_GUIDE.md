# LT content authoring guide (for programmatic / AI editing)

How game content is stored and wired together in a `.ltproj`, verified against
`lion_throne.ltproj` (this repo) and `default.ltproj` (the Sacred Stones demo
shipped with the editor at `../lt_editor/lt_editor/default.ltproj`). Everything
below is plain JSON + PNG — no compilation step; the engine reads it directly.

## 0. Two on-disk layouts

`metadata.json` → `"as_chunks"` decides the layout. **The engine reads both.**

| | Lion Throne (monolithic) | default.ltproj (chunked) |
|---|---|---|
| units | `game_data/units.json` (one array) | `game_data/units/<Nid>.json` (one file each) + `.orderkeys` |
| same for | `levels.json`, `items.json`, `skills.json`, `events.json`, `classes.json` | `levels/`, `events/`, `items/`, `skills/`, `classes/` dirs |

Chunked is friendlier for AI edits (small files, no giant-array surgery).
When editing monolithic files: append to the array; order = display order.
When adding a chunked file: also append its nid to the dir's `.orderkeys`.

Shared singleton files (both layouts): `constants.json`, `equations.json`,
`terrain.json`, `mcost.json`, `ai.json`, `factions.json`, `teams.json`,
`stats.json`, `weapons.json`, `weapon_ranks.json`, `difficulty_modes.json`,
`translations.json`, `tags.json`, `parties.json`, `lore.json`, `supports*`.

## 1. Levels

One entry in `levels.json` per chapter. Anatomy (Lion Throne Chapter I):

```json
{
  "nid": "1", "name": "Chapter I",
  "tilemap": "Chapter 1",            // -> resources/tilemaps
  "party": "Resistance",             // -> parties.json
  "music": {"player_phase": "...", "enemy_phase": "...", ...},
  "objective": {"simple": "Defeat Boss", "win": "Defeat Sidney",
                "loss": "Ophies dies,Any two of your units are defeated"},
  "roam": false, "roam_unit": null,  // free-roam chapters
  "units": [ ...placements... ],
  "regions": [ ...map hotspots... ],
  "unit_groups": [{"nid": "EnemyRein", "units": ["108","109","110"], "positions": {}}],
  "ai_groups": []
}
```

**`objective` is display text only.** Actual win/loss logic lives in events
(`win_game` / `lose_game` commands, see §5).

Unit placements come in two flavors:

- **Unique** (`"generic": false`): references a unit in `units.json` by nid,
  adds only `team`, `ai` (-> `ai.json` presets: None/Attack/Defend/Pursue...),
  `starting_position` `[x, y]`, `starting_traveler` (rescued passenger nid).
- **Generic** (`"generic": true`): defined entirely inline — `klass`, `level`,
  `faction` (-> `factions.json` for name/icon), `starting_items`
  (`[["Willow Bow", false]]`, bool = droppable), `starting_skills`, `team`, `ai`.
  Stats are computed from the class bases/growths at that level. This is how
  all rank-and-file enemies exist; a new enemy needs zero files touched
  besides the level entry.

`unit_groups` name sets of placed units so events can spawn/move them together
(reinforcements). To make a new level: new tilemap (or reuse one), new entry in
`levels.json`, a `level_start` event, and win/loss events.

## 2. Characters (units)

**Unique units** live in `units.json` (28 in Lion Throne). Key fields:

```
nid, name, desc, level, klass          -> classes.json nid
tags: ["Lord"]                         -> tags.json (Lord/Boss/Armor/Mounted...)
bases / growths: {HP, STR, MAG, SKL, SPD, LCK, DEF, RES, CON, MOV}  (growths are %)
starting_items: [["Iron Sword", false]]
learned_skills: [[level, skill_nid], ...]        (personal skills)
wexp_gain: {"Sword": [usable?, amount, cap], ...}  (weapon ranks; amount vs weapon_ranks.json thresholds)
portrait_nid, affinity, variant, alternate_classes, stat_cap_modifiers
```

**Classes** (`classes.json`) carry the rest of a character's identity:
`bases`/`growths`/`max_stats` (unit totals = unit + class contributions per
`constants`), `movement_group` (-> `mcost.json` row), `promotes_from` /
`turns_into` / `promotion` gains, `learned_skills` (class skills, e.g.
Myrmidon: `[[1,"TLT_Riposte"],[5,"TLT_Vantage"],[8,"Feat"]]`), `wexp_gain`,
and crucially the art links: **`map_sprite_nid`** and **`combat_anim_nid`**.

**Art for a character**, all under `resources/`:

- `portraits/<Nid>.png` + entry in `portraits/portraits.json`
  (`blinking_offset`/`smiling_offset` — a 96×80 grid sheet: main face, chibi,
  blink/smile frames). Used in dialogue scenes and info menu. `portrait_nid`
  on the unit picks it; events can also reference any portrait directly.
- `map_sprites/<Class>-stand.png` + `<Class>-move.png` — per class (and team
  recolors are automatic via palettes). A new character in an existing class
  needs no map sprite work; `variant` allows per-character overrides.
- `combat_anims/<Class>-<WeaponType>.png` — battle animation sheets, per class.
  Missing anim ⇒ engine falls back to map combat. So new content can skip
  battle animations entirely.
- `icons16/32/80` — item/skill icons referenced by `icon_nid` + `icon_index`
  (sheet + cell coordinates).

Enemies and neutrals ("other" team) are not special: same units/classes,
different `team` (`teams.json`: player/enemy/enemy2/other) and `ai` preset.
Bosses are usually unique units placed with the `Boss` tag.

## 3. Items

An item is `nid/name/desc + icon + a list of [component_nid, value] pairs`.
The full Iron Sword:

```json
"components": [
  ["weapon", null], ["target_enemy", null], ["level_exp", null],
  ["damage", 3], ["hit", 90], ["weapon_type", "Sword"], ["weapon_rank", "D"],
  ["weight", 3], ["value", 450], ["min_range", 1], ["max_range", 1],
  ["uses", 45], ["uses_options", {"lose_uses_on_miss": false, "one_loss_per_combat": false}]
]
```

Components are tiny classes in `app/engine/item_components/*.py`
(weapon, hit, usable, aoe, exp, target, special, ...). Each declares its
`nid`, value type, and hook methods the engine calls (e.g. `Damage.damage()
-> value` feeds `combat_calcs`). A healing staff is just different
components (`spell`, `target_ally`, `heal`, `weapon_type: Staff`, ...).
Effective-vs-armor, brave, magic, siege range, status-on-hit — all existing
components. **New items from existing components: JSON only, no code.**
A genuinely new component type = new class in `item_components/` + rerun
`source_generator.py` (regenerates `item_system.py`).

## 4. Combat, skills, bonuses, damage/hit

**The stat formulas themselves are data** — `equations.json`, evaluated
against unit stats. This is the single biggest "feel" lever and the clearest
demo-vs-Lion-Throne behavioral diff:

| equation | demo (GBA-like) | Lion Throne |
|---|---|---|
| HIT | `SKL*2 + LCK//2` | `SKL*3 + LCK` |
| AVOID | `SPD*2 + LCK` | `SPD*3 + LCK` |
| CRIT_HIT / CRIT_AVOID | `SKL//2` / `LCK` | `SKL` / `LCK*2` |
| CRIT_MULT | `3` (triple dmg) | `1` — with constant `crit: false`, crits are off entirely |
| SPEED_TO_DOUBLE | 4 | 4 (doubling threshold, also an equation) |

Resolution pipeline (`app/engine/combat_calcs.py`): `compute_hit` =
equation HIT + item's `hit` component + item dynamic hooks (effectiveness)
± weapon triangle (`weapons.json` advantage tables) + support bonuses
− defender AVOID ± skill dynamic hooks, clamped 0–100. `compute_damage`
analogous with DAMAGE/DEFENSE vs MAGIC_* equations chosen by the item.

**Skills** are the same component pattern (`app/engine/skill_components/*.py`):

- `Canto` = `[["class_skill", null], ["canto", null]]`
- `TLT_Riposte` = `[["dynamic_damage", "3 if (mode == 'defense') else 0"], ...]`
  — components can hold **Python eval strings** with combat context
  (`mode`, `unit`, `target`, `item`), so conditional bonuses are pure data.
- Statuses are skills too: `TLT_Poison` = `stat_change` −2 all stats +
  `unit_anim` + `time: 4` turns + `negative`. `Regeneration` = 30%/turn.

Skills attach via class `learned_skills`, unit `learned_skills`, terrain,
items (`status_on_hold`/`status_on_hit`), or the event command `give_skill`.
Lion Throne's 118 skills include a `TLT_*` family of custom behaviors —
all built from stock components, zero engine changes.

**Difficulty** (`difficulty_modes.json`): per-mode enemy stat/growth bonuses
(Lion Throne: Hard/Lunatic/Grandmaster with `enemy_leveling: Fixed`).

## 5. Maps, interactions, win conditions

**Tilemaps** (`resources/tilemaps/tilemap_data/tilemaps.json` + tileset PNGs):
`size`, `layers` (each a `terrain_grid` of `"x,y": terrain_nid` + a sprite
grid referencing tileset cells), `tilesets` used. Terrain nids →
`terrain.json` (name, avoid/def bonuses, movement class, optional attached
skill — Forts heal because the terrain grants a skill) and `mcost.json`
(movement cost matrix per movement_group). Layers can be shown/hidden by
events (destroyed bridges, opened walls).

**Regions** (per level, in the level entry): typed rectangles on the map.
`region_type: "event"` + `sub_nid` = interaction verb — the engine surfaces
a menu option with that name when a unit stands there, and fires the
matching event trigger. Lion Throne uses: Visit (houses), Chest, Door,
Switch, Search, Armory, Vendor, Seize, Escape, Secret. Also
`region_type: "status"` (terrain-wide skill), `"formation"` (prep-screen
deploy slots), `"time"` (expiring).

**Events** are the glue and the *actual* game logic. One entry:
`nid, trigger, level_nid (null = global), condition (Python eval), _source`
(list of `command;arg;arg` lines — note the engine parses `_source`; the
`commands` array is a legacy field, often empty). Examples from Lion Throne:

```
# win condition (trigger: combat_end, cond: game.check_dead('Sidney'))
win_game

# house visit (trigger: Visit — fired by the House1 region, cond: unit.team == 'player')
transition;Close
change_background;House
multi_add_portrait;Man4;Left;{unit};Right
speak;Man4;Hmmm... You're fighting the Empire?|Take this.
give_item;{unit};Hand Axe
has_attacked;{unit}
```

Trigger vocabulary (see `app/events/triggers.py`): `level_start`, `level_end`,
`turn_change`, `phase_change`, `combat_start`, `combat_end`, `unit_death`,
`unit_wait`, `on_talk`, `on_support`, `unit_level_up`, `on_base_convo`,
`on_startup`, region sub_nids, and more. ~180 event commands cover dialogue,
camera, movement, spawning (`add_unit`, `move_unit` with unit_groups),
map changes, shops, items, skills, saving, chapter flow (`win_game`,
`lose_game`, `activate_turnwheel`). Loss conditions are just events too —
Lion Throne's "lose if party < 3" is a `combat_end` global-style check with
`lose_game` in the body.

Full command/component reference also ships as the editor's help docs; the
source of truth is `app/events/event_commands.py` docstrings.

## 6. Demo vs Lion Throne — summary of key diffs

- **Layout**: demo chunked, Lion Throne monolithic (`as_chunks`).
- **Scale**: demo 7 levels (0–5 + DEBUG) / Lion Throne 13 levels, 28 units,
  102 items, 118 skills (many custom `TLT_*`), 243 events.
- **Combat feel**: different HIT/AVOID/CRIT equations (table above); crits
  disabled; `def_double: false` (defenders don't double); `attack_stance_only`,
  `line_of_sight: true`, `aura_los: true`; `auto_promote: true`;
  `enemy_leveling: Fixed` vs demo's Dynamic; different EXP curve
  (`exp_curve 0.22` vs `0.035`, `default_exp 15` vs `11`, `kill_multiplier 2.5`).
- **Systems toggled** (all `constants.json`): Lion Throne enables
  give_and_take, convoy_on_death, long_range_storage; disables overworld,
  kill_wexp/double_wexp; `game_nid: LionThrone` (save-file namespace) vs `LT`.
- **Engine data version**: Lion Throne saved by 2024.10.25a, demo by
  2025.03.13a — both load fine in the 2025.03.13a engine used here.

## 7. What needs a rebuild / codegen

| change | needed |
|---|---|
| any JSON edit (units, items, skills, levels, events, equations, constants) | rebuild web bundle (`uvx pygbag --build --template lt.tmpl .`) — data ships inside the .apk |
| new PNG assets + manifest entries | same rebuild |
| new component **type** or event command | edit `app/engine/*_components/` or `app/events/`, rerun `source_generator.generate_all()` (regenerates `skill_system.py` / `item_system.py` / wrappers — the web build runs `sys.frozen`, so generated files must be current), then rebuild |
| new content from **existing** components | JSON only, no codegen |
