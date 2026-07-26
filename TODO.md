# TODO

## Shipped

All on `main`. Thirteen behaviour suites plus `smoke_test.py` run in `.github/workflows/behaviour-tests.yml`.

| # | Feature | Where to see it |
|---|---|---|
| 2 | Overworld level gating | S3 requires 2 units at internal level 2 (reachable through normal CAPITAL->S1->S2 play; verified by `tools/test_playthrough.py`) |
| 3 | Level re-entry | Cleared nodes selectable on the overworld; S1-S4 also re-place every recruited companion (including a mid-level recruit like Tamsin/Ysolde) at a real position, not just the CAPITAL four |
| 4, 5 | Enemy pool + party-scaled generator | `enemy_pools.json`, `app/engine/enemy_pool.py` |
| 6 | Safe/Unsafe revisits | Rolls once per node, cached. An Unsafe roll has a real gameplay effect on S1-S4 (places a party-scaled procedural squad via `add_group;<Level>_UnsafeSquad` and reaches a real fight); a Safe roll skips straight to `win_game`. S5's `level_reenter` event still exists but is dead content — S5 is the last level (`go_to_overworld: false`) and clearing it routes straight to `title_start`, never back to the overworld, so it can never actually be re-selected |
| 7, 9, 23 | Dialogue / win conditions / recruitment docs | CONTENT_GUIDE §5.4, §11, §12 |
| 8 | Alignment axes | `check_alignment('good_evil')` and `check_alignment('lawful_chaotic')` both readable in any condition (S1 `AlignmentBlessing`, S3 `AlignmentDiscipline`); both axes move in both directions — S2's `S2Gambit` choice is the first decrementing write (`Push Through` -3, `Make Camp` +3 on `lawful_chaotic`) |
| 10 | Declarative deploy cap | `max_deploy`/`min_deploy` on a level, reachable for real: S2 declares `max_deploy: 3`/`min_deploy: 1` and its Intro/Unsafe-reentry events call `prep;1`, so 'Pick Units' actually appears in the prep menu and the cap actually refuses a 4th unit past it (driven end-to-end by `tools/test_playthrough.py` via the real prep-menu state machine, not just a level_vars assertion) |
| 11, 12, 13 | Merchant, Donate XP, prep-market pricing | Prep menu |
| 14 | Conditional spawns | S2, three trigger kinds |
| 16 | Free roam | SHUB, walk up to the Wraith |
| 17 | Non-combat skill checks | d20 + `PERSUASION` equation |
| 18 | d20 resolution | `roll_d20()` |
| 19 | Item tiers | `tier` item component, gates real stock: SHUB Armory's tier-2 lines (Steel Sword/Lance/Axe) only appear once the Merchant's tier-unlock feat is granted |
| 21 | Monster classes | Ghoul, Wraith, Hellhound — spawned automatically by the party-scaled procedural generator (`S1_UnsafeSquad`/`S2_UnsafeSquad`/`S3_UnsafeSquad`/`S4_UnsafeSquad`) once the party's average level reaches the band that rolls them, in addition to the S2 `S2Monsters` group and the SHUB roam unit |
| 15 | Reusable state-machine test harness | `tools/play_harness.py` (boot, frame-pump, prep/manage/combat/overworld drivers); `tools/test_playthrough.py` drives a full CAPITAL->S1->S2 run through it |

## Open

**#22 — Gemini art pipeline.** Blocked: no API key in the remote environment. Add one via environment config (not a repo `.env` — the pygbag bundle ships wholesale to the browser). `tools/make_monster_sprites.py` already covers palette variants without it.

## Engine-ready, no content

The engine plumbing for these exists and is directly tested, but no
authored content in `lion_throne.ltproj/game_data/` currently exercises it
in real play — moved out of Shipped rather than left claiming reachability
they don't have.

| # | Feature | What actually exists | What's missing |
|---|---|---|---|
| 20 | Dungeon floor state preservation | `LevelPrefab.preserve_state_on_transition`, read by `EventState.level_end()` and passed to `game.clean_up(preserve_hp=...)` — proven directly by `tools/test_dungeon_floor.py` (which sets the flag on a level at runtime to test the plumbing) | No level in `levels.json` sets `preserve_state_on_transition: true`, and no event anywhere calls `set_next_chapter` — the two-floor "no full heal between floors" scenario this field exists for has never been authored |
| 20a | `clean_up(preserve_hp=…)` | The HP/guard/mana-preserving code path itself, same test as above | Same as #20 — this only ever runs with the default (`preserve_hp=False`, full heal) in real play, since #20 above is what would ever set it `True` |

## Known gaps

- **CI does not gate deploys.** `behaviour-tests.yml` runs on push and PR, but Cloudflare's Git integration builds independently and never reads the result. A red build will still deploy.
- **`enemy_pools.json` has no editor UI.** It is a plain sibling file, deliberately outside `DB.save_data_types`. Hand-edit it.
- **Skill-check event dispatch is attached lazily at first parse.** A module-level import hits a real circular import (`database → event_prefab → event_commands → event_functions → database`). Worth revisiting if that area is touched again.
- **S5's `level_reenter` event is dead content.** See row 6 above — authored the same as S1-S4's but structurally unreachable from real play.
