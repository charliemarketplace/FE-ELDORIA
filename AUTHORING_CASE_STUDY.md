# AI content authoring — case study & repeatable process

This documents the actual process used (2026-07-08) to add, verify, and ship
three pieces of content to *The Lion Throne* with zero engine code changes:

| deliverable | commit | what it proved |
|---|---|---|
| Kestrel (unit) + Lionfang (item) + Lionheart (skill) in the DEBUG chapter | `c8e07a9` | entity authoring: units/items/skills from existing components |
| TRIAL — "Kestrel's Trial", minimal new level | `0311455` | level + event wiring: level_start / win / lose |
| TOWN — "Market Day", town level with talk, shops, arena, reach-a-square win | `b34d40e` | interaction systems: regions, on_talk, shop, scripted combat |

Read `CONTENT_GUIDE.md` first — it is the reference for *what* the data
means. This file is the *how*: the loop that took each idea to a verified,
committed change.

## The loop

Every deliverable followed the same five phases:

```
1 DISCOVER   read the real data; never guess a nid, a field shape, or a value
2 AUTHOR     append JSON via a script with byte-identical round-trip guards
3 VALIDATE   native smoke test (seconds) catches bad nids / malformed JSON
4 VERIFY     rebuild web bundle, drive the game headlessly, screenshot proof
5 COMMIT     only after the screenshots show the feature working
```

### Phase 1 — discover

Rules that prevented every "invented value" bug:

- **Copy the shape of the nearest existing entity.** New unit ← copied Nia's
  field-for-field structure. New shop event ← copied `2 Vendor` verbatim and
  changed the item list. The demo project
  (`../lt_editor/lt_editor/default.ltproj`, chunked = one file per entity) is
  a second example pool — the rout condition `len(game.get_enemy_units()) == 0`
  came from its `2_Rout.json` because Lion Throne itself never routs.
- **Component/command vocabulary comes from the source, not memory**: grep
  `nid = '...'` in `app/engine/*_components/`, read `keywords` /
  `optional_keywords` / docstrings in `app/events/event_commands.py`, trigger
  context variables in `app/events/triggers.py` (e.g. `on_talk` exposes
  `unit1`/`unit2` — confirmed before writing conditions on them).
- **Dump the whole level entry before planning positions.** A unit placement
  I hadn't noticed (player Fighter "103" at (10,13) in DEBUG) made a scripted
  move silently no-op — the engine rejects moves onto occupied tiles, which
  looks exactly like dead input. Also render the terrain grid as ASCII
  (`terrain_grid` → one char per tile) to plan walkable paths and check
  movement costs (forest ≠ 1) against unit MOV.
- **Do the combat math up front** from `equations.json` + item/skill
  components + class bases, so every number in the verification screenshots
  has a predicted value. When a number disagrees, something real is going on
  (an enemy forecast showed Hit 0, not the predicted 26 — the defender's
  class skill TLT_Initiative grants +30 avoid on defense; the model of the
  fight was wrong, not the data).

### Phase 2 — author

All edits are made by a small Python script per deliverable (kept in the
session scratchpad, not the repo), never by hand-editing 400 KB JSON files:

- **Round-trip guard first.** The game-data files are exactly reproduced by
  `json.dumps(data, indent=4, ensure_ascii=True).replace('\n', '\r\n')`
  written as UTF-8 bytes with **no trailing newline**. The script asserts
  load→dump equals the original bytes before touching anything, so a diff can
  only ever be the appended entries. If the assert ever fails, stop —
  something about the serialization changed.
- **Append, don't reorder** (array order = menu order). Assert the new nid
  doesn't already exist. Assert target tiles are unoccupied and walkable.
- New entities that need art **reuse existing art**: Kestrel = Mercenary
  class (inherits map sprite + battle anim) + spare portrait `Woman1`;
  the NPCs use `Woman2` / `OldMan1` / `Boy2`; icons are copied
  `icon_nid`/`icon_index` pairs from similar items/skills.

### Phase 3 — validate (native, fast)

```sh
uv run --no-project --python 3.12 --with pygame-ce --with typing-extensions python smoke_test.py
```

Prints entity counts (watch them tick up: 13→15 levels, 28→32 units…) and
crashes on dangling nids or malformed JSON. Seconds, so run after every edit.

### Phase 4 — verify (in the real browser build)

```sh
uvx pygbag --build --ume_block 0 --template lt.tmpl .   # rebuild bundle
```

- **`--ume_block 0` is mandatory** — without it the built page waits for a
  user gesture and a headless boot times out with *zero* console output.
- Game data ships inside the pygbag archive: the browser cannot see JSON
  edits until this runs.

Then drive it with Playwright (`channel='chrome'`, headless), one fresh page
load per scenario so no state leaks between tests:

- Boot signal: wait for console line `LT_BOOT: … entering main loop`
  (~10 s); crashes surface as `LT_BOOT: BOOT CRASH:` + traceback.
- `?level=<nid>` jumps straight into the chapter under test.
- First keypress dismisses the controls overlay — send a harmless `1`
  (speed ×1) so nothing else consumes a real input.
- Keys: send keydown, sleep 0.1 s, keyup. Arrows/Enter/S/A/W/Q all work.
- **Deterministic driving tricks**:
  - `Q` jumps the cursor to the next player unit — with a single player
    unit it is an absolute cursor anchor on scrolling maps.
  - Menu verbs (Attack, Talk, region sub_nids) sort above Item/Wait, so
    Enter picks them; ArrowUp in the action menu wraps to Wait.
  - On a map that exactly fits the 15×10 viewport (e.g. TacticsRoom) the
    camera never scrolls, so mouse clicks are exact:
    tile (x,y) center = (80x+40, 80y+40) on the 1200×800 canvas.
  - The combat flow after a move is: action menu → weapon select →
    target/forecast → combat — one Enter per step.
- **Screenshots are the assertions.** Screenshot after every meaningful
  step and *look at them*, checking against the phase-1 predictions
  (Kestrel's info page had to read Hit 107 / Avoid 32 — base 92/22 plus the
  new skill — and did). When a flow desyncs, rerun with a screenshot after
  every single keypress to find the step that didn't take.
- A `?level=`-jumped chapter with no next chapter returns to the title
  screen on `win_game` — that title screen is the "win fired cleanly" signal.

### Phase 5 — commit

One commit per deliverable, message stating what was added *and* how it was
verified. Never commit before the screenshots exist.

## Pattern catalog (all verified working in this repo)

- **Rout win**: event `combat_end`, condition
  `len(game.get_enemy_units()) == 0`, source `win_game`.
- **Reach-a-square win**: `event` region with a custom `sub_nid` (e.g.
  `Arrive`), condition `unit.team == 'player'`; event with trigger `Arrive`
  → flavor `speak` → `win_game`. The sub_nid string itself is the menu verb.
- **Death lose**: event `unit_death`, condition `unit.nid == '<Name>'`,
  source `lose_game`.
- **Talkable NPCs**: unique Citizen-class units placed on team `other`;
  `add_talk;Hero;NPC` at level_start; `on_talk` events with condition
  `unit2.nid == '<NPC>'` (TALK bubbles render automatically).
- **Shop**: region sub_nid `Armory`/`Vendor` → event runs
  `shop;{unit};Item1,Item2,…[;vendor]`; fund the party via `give_money;900`
  at level_start.
- **Arena / scripted duel**: enemy placed in the level with
  `starting_position: null`, then `add_unit;<nid>;x,y;immediate` +
  `interact_unit;{unit};<nid>;hit1,hit1,end` (the combat script removes hit
  RNG from the outcome) + conditional prize + `has_attacked;{unit}`.

## Known cosmetic quirks (pre-existing, not content bugs)

- Menu help footer can show translation-fallback keys like `Talk_desc`
  (missing entry in `translations.json` — base game does this too).
- Generic portraits (`Woman1` etc.) have no chibi in their sheet, so the
  map-hover name box shows a `?` chibi. Harmless.
