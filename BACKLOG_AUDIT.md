# Backlog audit — verified findings

Produced by a multi-agent pass over issues #2–#23: ten planning agents read the source and
proposed diffs, then two independent reviewers attacked those plans and re-verified every
load-bearing claim against the code. Several findings were **refuted** during review; this
document records what survived, with the refutations kept visible so they aren't rediscovered.

Every claim below was checked against source or proven by executing the engine headlessly.
Line numbers were accurate at the time of writing — re-verify before relying on one.

---

## 1. Things that already work (no engine code needed)

| Believed missing | Reality |
|---|---|
| Branching dialogue | `Choice`/`Unchoice` fully support it. The `expression` flag makes an option list a live closure re-evaluated every frame (`event.py:769-784`, `player_choice.py:175-182`). Shipping in `CAPITAL Intro` (events.json ~1019-1249). |
| Compound win conditions | `win_game` is one line (`event_functions.py:658-662`) and trigger-agnostic. An N-of-N condition already ships as `S5 QuenchWin` (three valve `game_var`s). |
| Recruitment / switching sides | `add_talk` → `TalkAbility` → `OnTalk` → `change_team;X;player`. Ships 3× (events.json lines 208, 429, 597). `ChangeTeam` is do/reverse symmetric. |
| Seeded RNG | `app/utilities/static_random.py` — three LCG streams, serializable. `game.get_random(a,b)` (`game_state.py:1531-1547`) is already turnwheel-safe. |
| Free roam | `app/engine/roam/` is complete. The roam→grid-combat transition **works today** — verified empirically by two independent agents. No content uses it. |
| Runtime generic-unit creation | `event_functions.make_generic` (843-870) already does it. It's just bound to an `Event` instance and unreachable elsewhere — extract, don't invent. |
| Conditional reinforcement spawns | `unit_groups` + `add_group`/`spawn_group`/`move_group`/`remove_group` (`event_functions.py:1267-1397`) are complete and wired. Empty on all 7 levels. |

**Consequence:** the three "conditional enemy appearance" triggers (turn count / attacked an NPC /
wrong dialogue choice) are **one system**, not three features — an ordinary event `trigger` +
`condition` pair. All three trigger nids already fire.

---

## 2. Traps — things that look right and aren't

**`static_random.get_randint()` draws from `combat_random`.** It reads like a neutral utility.
Using it for a non-combat roll shifts every subsequent combat roll and desyncs turnwheel replay.
Its only existing caller wraps it in `action.RecordRandomState` deliberately. Use
`game.get_random()` / `get_random_choice()` / `get_random_weighted_choice()` instead — those use
`other_random` and log `RecordOtherRandomState`.

**`UnitObject.from_prefab` silently skips items and skills** for a raw `UnitPrefab`. It branches on
`is_level_unit = not isinstance(prefab, UnitPrefab)` (`unit.py:143`); the raw path skips the entire
items/skills block and force-sets `team='player'`. Wrap in `UniqueUnit(...)` as `load_unit` does.
Verified: raw → `items=[]`, wrapped → `items=['Iron Sword','Vulnerary','EMB_EmberCoal']`. No exception.

**`item_funcs.buy_price(None, item)` used to crash** — `sell_price` guarded `if unit:`, `buy_price`
didn't, and `menu_options.py` passes an owner that can be `None`. Fixed; keep them symmetric.

**`ABILITIES[:3]` is a position-dependent slice** (`abilities.py:319-321`). Where a new `Ability`
subclass is *defined in the file* decides whether it lands in the unit menu correctly.

**`GenericUnit` is constructed with 9 positional args** at two sites. Every field has a default, so
inserting a field anywhere but the end shifts `starting_items`/`team`/`ai` **silently, with no
TypeError**. Append only.

**`query_engine`'s `func_dict` is built by scanning `dir(self)`.** Any public class attribute is
exposed to every condition-eval scope, callable or not. Keep helper constants at module scope.

**`clean_up()` restores HP/guard/mana outside every `if full:` block** (`game_state.py:587-590`), so
it fires on any transition. Currently harmless — see §4.

---

## 3. The deploy cap is inert as content stands

`_prep_slots` is read only inside `PrepPickUnitsState`, reachable only via the "Pick Units" menu
entry, which `prep.py:31-33` adds only `if game.level_vars.get('_prep_pick')`. All six prep events
call `prep;0`, which sets `_prep_pick = False`.

A `max_deploy` field alone would land, pass a naive test asserting `level_vars['_prep_slots'] == N`,
and do nothing in game. Any deploy-cap work must also make the Pick Units screen reachable, and its
test must assert a unit is actually **refused** placement at the cap.

---

## 4. Claims that were refuted during review

Recorded so they don't get rediscovered and acted on.

**Feats do NOT stack.** `AddSkill.do()` dedupes via `add_skill(test=True)`. Granting
`fMaximum HP +5` three times left maxHP at 20. The genuine re-entry concern is different: the player
could pick a *different* feat each visit and accumulate five distinct ones.

**`change_class` is NOT destructive.** `ClassChange` (`action.py:2045-2087`) preserves level and exp
and applies clamped base-stat deltas; `change_class` early-returns when the class is unchanged. The
real unbounded gain in that path is wexp.

**`prep;0` is NOT cosmetic.** It sets `_prep_pick = False`, so re-running it is harmless — but
suppressing `LevelStart` on a revisit removes the player's only route to Manage / Formation / Save.

**There is no shipping multi-floor chain.** S5 is the last level; its `go_to_overworld: False` marks
end-of-campaign, and **no event anywhere uses `set_next_chapter`/`_goto_level`** — independently
confirmed when a stale test assertion for `set_next_chapter;S1` in `CAPITAL Depart` turned out to be
asserting a command that isn't there. So the `clean_up()` heal in §2 is a future obstacle for dungeon
floors, not a live bug. `reset_mana` is also `False`, so the mana line never executes.

**The re-entry exploit surface is latent, not live.** The `== next_level` gate makes revisits
unreachable today. Unlocking re-entry is what would arm it, so any guard must ship in the *same*
change as the unlock, never after.

**`triggers.LevelStart()` does not fire from `start_level()`.** It fires from `TurnChangeState.end()`
(`general_states.py:124` and `:150`, gated on `game.turncount - 1 <= 0`). Only `:150` is live —
`:124` sits behind the `initiative` constant, which is `False` here.

**No Charisma stat exists.** `stats.json` is the ten vanilla FE stats. A persuasion check wants a
`DB.equations` formula, not a new stat.

---

## 5. Testing: what exists and what it's worth

- `smoke_test.py` (62 lines) — data loads, engine modules import, content references resolve. The
  only thing CI runs. Cannot boot a level or assert behaviour.
- `tools/test_capital_completion.py` (430 lines) — a real headless harness: dummy SDL drivers, real
  `GameState`, real `action.do()` mutations with before/after assertions, real save pickling.

**This test was red on `main` and had been for some time.** `CAPITAL Intro` was refactored into a
`for;OutfitTarget` loop and three separate assertion groups rotted against it. Nothing caught it
because the test is not in CI. Its economy assertion was also tautological — it compared the gold
delta against the same value it used as the debit, so it passed under any price multiplier.

**CI gates nothing that ships.** `deploy.yml` is `workflow_dispatch`-only. The production path is
Cloudflare's Git integration, which runs no tests at all. A behaviour-test workflow is worth building,
but only alongside making the deploy path actually gated — otherwise it's motion, not safety.

Also: `pygbag.ini` was bundling `tools/` into the WASM build shipped to browsers. Now excluded.

---

## 6. Recommended order

1. Make CI gate the path that actually deploys. Everything else is downstream of this.
2. Zero-engine-cost work: the documentation patterns in §1, `check_alignment`, `roll_d20`, an item
   `Tier` component.
3. Content authoring against already-complete engine systems: `unit_groups` spawns, free-roam maps.
4. Enemy pool + generator — largest surface, self-contained if `procedural` is appended last.
5. Deploy cap — only with the `_prep_pick` problem solved, or it ships inert.
6. Merchant — after deciding whether its feats price every shop or only the prep market.
7. Level re-entry last. It is the only change that can retroactively break a live save, and its guard
   and its unlock must land together.
