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
