# TODO

## Shipped

All on `main`. Thirteen behaviour suites plus `smoke_test.py` run in `.github/workflows/behaviour-tests.yml`.

| # | Feature | Where to see it |
|---|---|---|
| 2 | Overworld level gating | S3 requires 2 units at internal level 2 (reachable through normal CAPITAL->S1->S2 play; verified by `tools/test_playthrough.py`) |
| 3 | Level re-entry | Cleared nodes selectable on the overworld |
| 4, 5 | Enemy pool + party-scaled generator | `enemy_pools.json`, `app/engine/enemy_pool.py` |
| 6 | Safe/Unsafe revisits | Rolls once per node, cached |
| 7, 9, 23 | Dialogue / win conditions / recruitment docs | CONTENT_GUIDE §5.4, §11, §12 |
| 8 | Alignment axes | `check_alignment('good_evil')` in any condition |
| 10 | Declarative deploy cap | `max_deploy`/`min_deploy` on a level |
| 11, 12, 13 | Merchant, Donate XP, prep-market pricing | Prep menu |
| 14 | Conditional spawns | S2, three trigger kinds |
| 16 | Free roam | SHUB, walk up to the Wraith |
| 17 | Non-combat skill checks | d20 + `PERSUASION` equation |
| 18 | d20 resolution | `roll_d20()` |
| 19 | Item tiers | `tier` item component |
| 20 | Dungeon floor state preservation | `preserve_state_on_transition` |
| 20a | `clean_up(preserve_hp=…)` | HP/guard/mana survive a floor change |
| 21 | Monster classes | Ghoul, Wraith, Hellhound |
| 15 | Reusable state-machine test harness | `tools/play_harness.py` (boot, frame-pump, prep/manage/combat/overworld drivers); `tools/test_playthrough.py` drives a full CAPITAL->S1->S2 run through it |

## Open

**#22 — Gemini art pipeline.** Blocked: no API key in the remote environment. Add one via environment config (not a repo `.env` — the pygbag bundle ships wholesale to the browser). `tools/make_monster_sprites.py` already covers palette variants without it.

## Known gaps

- **CI does not gate deploys.** `behaviour-tests.yml` runs on push and PR, but Cloudflare's Git integration builds independently and never reads the result. A red build will still deploy.
- **`enemy_pools.json` has no editor UI.** It is a plain sibling file, deliberately outside `DB.save_data_types`. Hand-edit it.
- **Skill-check event dispatch is attached lazily at first parse.** A module-level import hits a real circular import (`database → event_prefab → event_commands → event_functions → database`). Worth revisiting if that area is touched again.
- **Nothing spawns the monster classes automatically** outside the S2 group and the SHUB roam unit. Either author `unit_groups` entries or mark slots `procedural: true` to let the generator fill them.
