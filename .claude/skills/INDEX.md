# Eldoria capability skills — index

One skill per authorable capability. Each answers: what the feature is, how to
add one, which files it touches, a working example already in this repo, and a
test that proves it works.

Discovery runs in rounds. Each round excludes everything already listed here
and hunts the codebase for capabilities not yet documented. Add a row the
moment a skill lands so the next round doesn't rediscover it.

## Skill template

Every `SKILL.md` under `.claude/skills/<name>/` must carry YAML frontmatter
with `name` and `description`, then these five sections:

1. **Feature** — one paragraph. What it lets a designer do.
2. **Details** — the full option surface. Every field, flag, and variant, with
   defaults and what happens when you leave something out.
3. **Code files** — exact paths, with the line ranges that matter and what each
   one contributes.
4. **Working example in this repo** — a real nid/file/line you can go read.
   Never a hypothetical.
5. **Test** — the command that proves it works, and what the assertion actually
   checks. If nothing covers it, say so and name the test that should exist.

## Documented

| Skill | Capability |
|---|---|
| `add-custom-playable-character` | Author a new unique character (`UnitPrefab`) and place them on the map via static level data or the `load_unit`/`add_unit` event commands |
| `add-class-with-promotion-path` | Define a class and wire it into a promotion chain (`turns_into`/`promotion` stat-gain sentinels, auto-promote vs. promotion item, skill inheritance) |
| `author-support-affinity-relationship` | Declare a support pair and/or character affinity with per-rank combat bonuses, rank thresholds, and the constants governing how they're earned/combined |
| `add-weapon-type-or-rank` | Add a new weapon type (triangle advantage/disadvantage, rank bonus) or extend the weapon-rank ladder |
| `configure-difficulty-mode` | Author a difficulty mode: permadeath/growth/RNG policy, per-team (player/enemy/boss) stat bonuses, unlock gating |
| `author-terrain-effects` | Give a terrain type a movement-cost key (`mtype`), an LOS-blocking flag (`opaque`), and a passive on-tile status skill (`status`) |
| `configure-movement-cost-grid` | Edit the `mcost.json` movement-type × terrain cost grid and per-class `movement_group` assignment |
| `configure-ai-presets-and-groups` | Author `ai.json` behavior presets (targeting, view range, offense bias) and link units via `ai_group` so a squad reacts together |
| `author-rescue-and-pairup` | Enable classic Rescue/Drop/Give/Take carrying, or switch to Fates-style Pair-Up (guard stance/gauge), via the shared `traveler` slot |
| `configure-turnwheel-rewind-limits` | Cap Turnwheel rewinds per chapter, force a rewind after a scripted death, or permanently lock in history |
| `configure-fatigue-system` | Turn on per-unit fatigue (deployment blocking or stat-penalty status skills) via `fatigue`/`reset_fatigue` constants and the `_fatigue` game_var |
| `configure-bexp-economy` | Grant a party pooled Bonus Experience and let the player spend it in base to hand-pick level-ups (`bexp`/`rd_bexp_lvl` constants, `give_bexp`/`open_bexp_menu` commands) |
| `configure-initiative-turn-order` | Replace team-phase turns with a per-unit initiative queue (`initiative` constant, `InitiativeTracker`, per-unit upkeep timing) |
| `configure-fog-of-war` | Activate level-wide fog of war via event commands and layer `fog`/`vision` map regions on top for local overrides |
| `author-persistent-records-and-achievements` | Author cross-save persistent records and player-facing achievements via event commands, distinct from the automatic Recordkeeper |
| `author-effective-damage-weapon` | Author an item that deals bonus/multiplied damage against unit tags (`effective_damage` component), with its icon/reticle tells and the `negate`/`negate_tags` counter |
| `author-multi-item-or-sequence-item` | Author a composite item: a `multi_item` picker menu (Three-Houses-style spell list) or a `sequence_item` step pipeline (Warp/Rescue-style), plus `multi_target`/`allow_same_target`/`allow_less_than_max_targets` |
| `author-combat-art-or-proc-skill` | Author a player-selectable Combat Art or an automatic proc skill (chance- or charge-gated), including the `build_charge`/`drain_charge`/mana resource layer |
| `author-aura-skill` | Author a passive radius buff/debuff (`aura`/`aura_range`/`aura_target`) that auto-attaches a child skill to nearby units, with LOS gating and map highlighting |
| `author-movement-granting-skill` | Author a move-again skill (Canto/Canter/CantoSharp), Pass-through, or a Witch Warp teleport, plus Galeforce's kill-to-move-again |
| `author-shop-and-armoury` | Author a `shop` event: item list, `ShopFlavor` (vendor/armory/custom), `StockList` with cross-visit persistence via `ShopId` |
| `configure-convoy-and-storage` | Turn on the party's shared convoy (`enable_convoy`/`_convoy`), route items into a specific party's convoy via `give_item;convoy`/`Party`, and the `long_range_storage`/`convoy_on_death` constants |
| `author-camera-and-screen-transitions` | Direct cutscene camera/screen: `transition` fades, `change_background` panoramas, `move_cursor`/`center_cursor`/`flicker_cursor` pans, and `screen_shake` |
| `author-overworld-nodes-roads-and-entities` | Progressively reveal overworld nodes/roads, toggle a node's custom menu options, and spawn/move standalone cinematic or reinforcement entities distinct from the automatic party entity |
| `author-portrait-and-sprite-presentation` | Stage dialogue portraits beyond a bare add/remove: screen slots and auto-mirroring, slide vs. fade transitions, `move_portrait`/`bop_portrait`/`mirror_portrait`, and manual `expression` control |

## Seed exclusion list — round 1 must NOT re-document these

These are already covered in `CONTENT_GUIDE.md`, `BACKLOG_AUDIT.md` or `TODO.md`.
They will be converted to skills separately; discovery rounds should look past them.

1. Overworld level gating by roster (`req_unit_count` / `req_unit_level`)
2. Level re-entry and the `level_reenter` trigger
3. Enemy template pool + party-scaled procedural squad generation
4. Safe/Unsafe revisit rolls
5. Branching dialogue (`Choice` / `Unchoice`, the `expression` flag)
6. Compound win conditions (1-of-N, N-of-M, K-of-N)
7. Recruitment / `change_team` side-switching
8. Alignment axes and `check_alignment()`
9. Declarative deploy caps (`max_deploy` / `min_deploy`)
10. The Merchant: persistent non-roster unit, Donate XP, feat-gated prep market
11. Conditional enemy spawns (`unit_groups` + trigger/condition)
12. Free roam maps and monster engagement
13. Non-combat skill checks (d20 + `DB.equations`)
14. `roll_d20()` resolution
15. Item tiers (`tier` component)
16. Dungeon floor state preservation (`preserve_state_on_transition`)
17. Monster classes via programmatic sprite recolour
18. The state-machine test harness (`tools/play_harness.py`)
19. Switches, layer reveals and gated loot (CONTENT_GUIDE §10)
20. Image-to-tilemap authoring pipeline (AUTHORING_CASE_STUDY.md)

## Round 1 additions — also excluded from round 2 onward

21. Custom playable character authoring + `load_unit`/`add_unit` join mechanics
22. Class definition + promotion chains (`turns_into`/`promotion` sentinels, auto-promote, skill inheritance)
23. Support pairs and affinities (rank thresholds, per-rank combat bonuses, `bonus_method`)
24. Weapon types and weapon ranks (triangle advantage/disadvantage, rank bonus, wexp constants)
25. Difficulty modes (permadeath/growth/RNG policy, per-team stat bonuses, unlock gating)

## Round 2 additions — also excluded from round 3 onward

26. Terrain authoring — `mtype` (movement-cost key), `opaque` (LOS blocking), `status` (on-tile skill effect), and the `RegionType.TERRAIN`/`STATUS` region overrides
27. The `mcost.json` movement-type × terrain cost grid and per-class `movement_group` resolution (including the `MovementType` skill-component override)
28. AI presets (`ai.json` behaviours, priority, offense_bias, view_range codes, roam_ai) and `ai_group` squad coordination (trigger_threshold, the `LevelPrefab.restore()` auto-heal)
29. Rescue/Drop/Give/Take and Pair-Up (guard stance/gauge, the shared `traveler` slot, the `pair_up`/`separate` event commands and their rescue/drop nicknames)
30. Turnwheel rewind limits (`_turnwheel` game_var gate, `_max_turnwheel_uses`/`_current_turnwheel_uses` budget, `activate_turnwheel` forced rewind, `LockTurnwheel`/`clear_turnwheel`/turnwheel-recording toggle)

## Round 3 additions — also excluded from round 4 onward

31. Fatigue system (`fatigue`/`reset_fatigue` DB constants, the `_fatigue` game_var's two modes, `ChangeFatigue`/`add_fatigue`, `ignore_fatigue`, the `Fatigue`/`FatigueOnHit` item components)
32. BEXP economy (`bexp`/`rd_bexp_lvl` constants, `PartyObject.bexp`, `give_bexp`/`open_bexp_menu` event commands, the `BaseBEXPSelectState`/`BaseBEXPAllocateState` spend UI, the `BONUS_EXP` equation hook)
33. Initiative / per-unit turn-order mode (`initiative` constant, `InitiativeTracker`, the `initiative` equation hook, `PhaseController`/`InitiativeUpkeep` rerouting, `DelayInitiativeOrder`)
34. Fog of war plus the `fog`/`vision` region types (`enable_fog_of_war`/`set_fog_of_war` event commands, `fog_los`/`ai_fog_of_war` constants, `RegionType.FOG`/`VISION`, `game_board.in_vision`, `sight_range` skill components)
35. Persistent records and achievements event layer (`create_record`/`update_record`/`replace_record`/`delete_record`/`unlock_difficulty`, `create_achievement`/`update_achievement`/`complete_achievement`/`clear_achievements`, the cross-save `AchievementManager`/`PersistentRecordManager` pickle stores, contrasted with the automatic save-bound Recordkeeper)

## Round 4 additions — also excluded from round 5 onward

36. Effective damage against unit tags (`effective_damage` item component's `effective_tags`/`effective_multiplier`/`effective_bonus_damage`/`weapon_effectiveness_multiplied` options, the icon-flash/danger-reticle tells, and the `negate`/`negate_tags` skill-side counters)
37. Multi-item and sequence-item construction (`multi_item`/`multi_item_hides_unavailable`/`sequence_item`/`multi_target`/`allow_same_target`/`allow_less_than_max_targets`/`store_unit`/`unload_unit`, the recursive `item_funcs` helpers, and the `CombatTargetingState` step-by-step sequence pipeline)
38. Combat Arts and proc skills (`combat_art`/`automatic_combat_art`/`attack_proc`/`defense_proc`/`attack_pre_proc`/`defense_pre_proc`/`proc_rate`/`astra_proc`/`allowed_weapons`, the `build_charge`/`drain_charge`/`charges_per_turn`/`combat_charge_increase(_by_stat)`/mana-cost resource layer, `action.TriggerCharge`, and the unconditional `combat2` survival family (`miracle`/`true_miracle`/`ignore_damage`/`live_to_serve`/`lifetaker`/`lifelink`))
39. Aura skills (`aura`/`aura_range`/`aura_target`/`show_aura`/`hide_aura`, `aura_funcs.py` propagation/pull/release, the `aura_los` DB constant, and the board/boundary/highlight rendering machinery)
40. Movement-granting skills (`canto`/`canto_plus`/`canto_sharp`/`canter`, `pass`/`ignore_terrain`/`ignore_rescue_penalty`/`grounded`, `witch_warp`/`specific_witch_warp`/`witch_warp_expression`, and `galeforce`)

## Round 5 additions — also excluded from round 6 onward

41. Shops and armouries (`shop` event command's `ShopFlavor`/`StockList`/`ShopId`, the flavor-to-translation fallback in `ShopState`, and the `level_vars`-vs-`game_vars` stock-persistence mismatch)
42. Convoy and storage (`enable_convoy`/`_convoy` game_var gate, `open_convoy`, `give_item;convoy;Item;Party` multi-party targeting, `PutItemInConvoy`/`TakeItemFromConvoy`/`TradeItemWithConvoy`, `long_range_storage`/`convoy_on_death` constants, `convoy_funcs.py` auto-equip heuristics)
43. Camera and screen transition control (`transition`, `change_background`/`pause_background`, `move_cursor`/`center_cursor`/`flicker_cursor`, `screen_shake`/`screen_shake_end` and its five `ShakeType` offset patterns)
44. Overworld nodes, roads, and entities (`reveal_overworld_node`/`reveal_overworld_road` ordering dependency, `set_overworld_menu_option_enabled`/`visible`, `create_overworld_entity`/`disable_overworld_entity`/`overworld_move_unit`/`set_overworld_position`, and the automatic `PARTY`-type entity seeded per `parties.json` entry)
45. Portrait and sprite presentation (`add_portrait`/`remove_portrait`'s `Slide`/`ExpressionList`/`SpeedMult`/`mirror`/`low_priority`, screen-position auto-mirroring, `move_portrait`/`bop_portrait`/`mirror_portrait`, `multi_add_portrait`/`multi_remove_portrait`, `expression`, and the unit-level `change_portrait`)
