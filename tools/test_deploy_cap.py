#!/usr/bin/env python3
"""
Execution-based tests for the deployment cap feature (#10 -- LevelPrefab
max_deploy/min_deploy seeding _prep_slots/_minimum_deployment/_prep_pick in
game_state.py) and the clean_up(preserve_hp=...) plumbing (#20a), driven
directly against the LT engine (no browser, no Playwright, no pygbag
rebuild), using the exact bootstrap of tools/test_capital_completion.py.

Every check below performs a real state mutation via GameState.start_level()/
clean_up() or action.do(action.Foo(...)) and then asserts a real before/after
difference in engine state.

Run with:
  uv run --no-project --python 3.12 --with pygame-ce --with typing-extensions python tools/test_deploy_cap.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import play_harness as harness
harness.boot()

from app.data.resources.resources import RESOURCES
from app.data.database.database import DB

from app.engine import action
from app.engine import game_state
from app.engine.game_state import GameState


FAILURES = []


def check(label, condition, detail):
    status = 'PASS' if condition else 'FAIL'
    print('[%s] %s: %s' % (status, label, detail))
    if not condition:
        FAILURES.append('%s -- %s' % (label, detail))
    return condition


print('=' * 78)
print('DEPLOY CAP -- EXECUTION-BASED TESTS (real start_level()/clean_up()/action.do() calls)')
print('=' * 78)

# ---------------------------------------------------------------------------
# 0. Boot DB/RESOURCES (identical to tools/test_capital_completion.py)
# ---------------------------------------------------------------------------
print('\n--- [0] Boot DB/RESOURCES ---')
# RESOURCES/DB already loaded and engine-chrome sprites/fonts already
# initialized by harness.boot() above.


def fresh_start_level(level_nid, preset_level_vars=None):
    """
    Replicates the module-level app.engine.game_state.start_level(level_nid)
    wrapper (game.clear() -> game.load_states(...) -> game.build_new() ->
    game.start_level(level_nid)), but with a hook to inject level_vars between
    build_new() (which resets level_vars to an empty PrimitiveCounter via
    GameState.sweep()) and start_level() (which seeds deploy vars from the
    level prefab via GameState._seed_deploy_vars_from_prefab) -- so tests can
    simulate an event (or a loaded save) that already set a level var before
    deploy-cap seeding would run.
    """
    g = game_state.game
    if not g:
        g = GameState()
        game_state.game = g
    else:
        g.clear()  # Need to use old game if called twice in a row
    g.load_states(['start_level_asset_loading'])
    g.build_new()
    if preset_level_vars:
        for key, val in preset_level_vars.items():
            action.do(action.SetLevelVar(key, val))
    g.start_level(level_nid)
    return g


# ---------------------------------------------------------------------------
# 1. Regression -- a level with no deploy fields set behaves exactly as today
# ---------------------------------------------------------------------------
print('\n--- [1] Regression: level with no max_deploy/min_deploy set (existing levels.json) ---')
s1_prefab = DB.levels.get('S1')
check('1. S1 prefab loads with max_deploy unset (zero-migration proof)',
      s1_prefab.max_deploy is None,
      'DB.levels.get("S1").max_deploy = %r (expected None -- no levels.json migration was needed)' % s1_prefab.max_deploy)
check('1. S1 prefab loads with min_deploy unset (zero-migration proof)',
      s1_prefab.min_deploy is None,
      'DB.levels.get("S1").min_deploy = %r (expected None)' % s1_prefab.min_deploy)

game = fresh_start_level('S1')
check('1. start_level(S1) succeeds (existing level loads fine)',
      game.level is not None and game.level.nid == 'S1',
      'game.level.nid = %r (expected S1)' % (game.level.nid if game.level else None))
check('1. _prep_slots not seeded when max_deploy is None',
      game.level_vars.get('_prep_slots') is None,
      "game.level_vars.get('_prep_slots') = %r (expected None)" % game.level_vars.get('_prep_slots'))
check('1. _prep_pick not seeded when max_deploy is None',
      not game.level_vars.get('_prep_pick'),
      "game.level_vars.get('_prep_pick') = %r (expected falsy)" % game.level_vars.get('_prep_pick'))
check('1. _minimum_deployment not seeded when min_deploy is None',
      game.level_vars.get('_minimum_deployment', 0) == 0,
      "game.level_vars.get('_minimum_deployment', 0) = %r (expected 0)" % game.level_vars.get('_minimum_deployment', 0))

# ---------------------------------------------------------------------------
# 2. THE MOST IMPORTANT CHECK -- max_deploy=3 seeds _prep_slots==3 AND
#    _prep_pick=True. Without also seeding _prep_pick, the cap would be
#    INERT: '_prep_slots' is only ever read inside PrepPickUnitsState
#    (app/engine/prep.py), which is only reachable from the prep menu's
#    'Pick Units' entry, which PrepMainState.populate_options() only adds
#    `if game.level_vars.get('_prep_pick')` -- and every existing prep event
#    sets '_prep_pick' False via `prep;0`. So a level could declare
#    max_deploy=3 and the player would never see a screen that enforces it
#    unless seeding also flips '_prep_pick' True.
# ---------------------------------------------------------------------------
print('\n--- [2] max_deploy=3 seeds _prep_slots=3 AND _prep_pick=True (inert-cap regression guard) ---')
s1_prefab.max_deploy = 3
game = fresh_start_level('S1')
check('2. _prep_slots seeded to max_deploy', game.level_vars.get('_prep_slots') == 3,
      "game.level_vars.get('_prep_slots') = %r (expected 3)" % game.level_vars.get('_prep_slots'))
check('2. _prep_pick seeded True so the Pick Units screen is actually reachable',
      game.level_vars.get('_prep_pick') is True,
      "game.level_vars.get('_prep_pick') = %r (expected True)" % game.level_vars.get('_prep_pick'))

# ---------------------------------------------------------------------------
# 3. min_deploy=2 seeds _minimum_deployment==2
# ---------------------------------------------------------------------------
print('\n--- [3] min_deploy=2 seeds _minimum_deployment=2 ---')
s1_prefab.min_deploy = 2
game = fresh_start_level('S1')
check('3. _minimum_deployment seeded to min_deploy', game.level_vars.get('_minimum_deployment') == 2,
      "game.level_vars.get('_minimum_deployment') = %r (expected 2)" % game.level_vars.get('_minimum_deployment'))

# ---------------------------------------------------------------------------
# 4. An event-set level_vars value wins over prefab seeding
# ---------------------------------------------------------------------------
print('\n--- [4] Event-set level_vars value wins over prefab seeding ---')
# s1_prefab still has max_deploy=3 from step 2 -- pre-seed _prep_slots=5 via the
# real Action (action.SetLevelVar, same Action event_functions.py's `level_var`
# event command uses) between build_new() and start_level(), simulating an
# event that already set this level var before deploy-cap seeding would run.
game = fresh_start_level('S1', preset_level_vars={'_prep_slots': 5})
check('4. pre-set _prep_slots is NOT overwritten by prefab seeding',
      game.level_vars.get('_prep_slots') == 5,
      "game.level_vars.get('_prep_slots') = %r (expected 5, the pre-set value)" % game.level_vars.get('_prep_slots'))
# '_prep_pick' was not pre-set, so it should still get seeded True independently.
check('4. _prep_pick still seeded True independent of the _prep_slots override',
      game.level_vars.get('_prep_pick') is True,
      "game.level_vars.get('_prep_pick') = %r (expected True)" % game.level_vars.get('_prep_pick'))

# ---------------------------------------------------------------------------
# 5. min_deploy > max_deploy clamps rather than raising
# ---------------------------------------------------------------------------
print('\n--- [5] min_deploy > max_deploy clamps instead of raising (must not crash at level load) ---')
s1_prefab.max_deploy = 3
s1_prefab.min_deploy = 10
clamp_raised = None
game = None
try:
    game = fresh_start_level('S1')
except Exception as e:
    clamp_raised = e
check('5. start_level does not raise when min_deploy > max_deploy',
      clamp_raised is None,
      ('exception raised: %r' % (clamp_raised,)) if clamp_raised else 'no exception raised')
if game is not None:
    check('5. _minimum_deployment clamped down to max_deploy (not left at the invalid 10)',
          game.level_vars.get('_minimum_deployment') == 3,
          "game.level_vars.get('_minimum_deployment') = %r (expected 3, clamped from authored 10)" % game.level_vars.get('_minimum_deployment'))
    check('5. _prep_slots still seeded to max_deploy',
          game.level_vars.get('_prep_slots') == 3,
          "game.level_vars.get('_prep_slots') = %r (expected 3)" % game.level_vars.get('_prep_slots'))

# Restore S1 prefab to a clean state so it doesn't leak into anything else that
# might run later in this process (DB is a process-wide singleton).
s1_prefab.max_deploy = None
s1_prefab.min_deploy = None

# ---------------------------------------------------------------------------
# 6. clean_up(preserve_hp=True) leaves a damaged unit damaged;
#    clean_up() with no args still full-heals it (default behavior unchanged).
# ---------------------------------------------------------------------------
print('\n--- [6] clean_up(preserve_hp=...) plumbing (#20a) ---')
game = fresh_start_level('S1')
unit = game.get_unit('Rowan')
check('6. Rowan resolves and is on the map in S1',
      unit is not None and unit.position is not None,
      'game.get_unit("Rowan") = %r, position = %r' % (unit, unit.position if unit else None))

max_hp = unit.get_max_hp()
action.do(action.ChangeHP(unit, -(max_hp - 1)))  # damage down to 1 HP
damaged_hp = unit.get_hp()
check('6. Rowan is actually damaged before clean_up (precondition)',
      damaged_hp == 1,
      'unit.get_hp() = %r (expected 1, max_hp=%r)' % (damaged_hp, max_hp))

game.clean_up(full=False, preserve_hp=True)
hp_after_preserve = unit.get_hp()
check('6. clean_up(preserve_hp=True) leaves a damaged unit damaged',
      hp_after_preserve == 1,
      'unit.get_hp() after clean_up(full=False, preserve_hp=True) = %r (expected still 1)' % hp_after_preserve)

# Damage it again and confirm the DEFAULT clean_up() (no preserve_hp arg) still
# full-heals -- i.e. today's behavior for every existing caller is unchanged.
# (unit.set_hp() is still 1 from the preserve_hp step above -- restore to full
# first so the "-(max_hp - 1)" delta lands back on exactly 1 HP again.)
unit.set_hp(unit.get_max_hp())
action.do(action.ChangeHP(unit, -(unit.get_max_hp() - 1)))
damaged_hp_2 = unit.get_hp()
check('6. Rowan damaged again before default clean_up() (precondition)',
      damaged_hp_2 == 1,
      'unit.get_hp() = %r (expected 1)' % damaged_hp_2)

game.clean_up(full=False)
hp_after_default = unit.get_hp()
check('6. clean_up() with no preserve_hp arg still full-heals (default unchanged)',
      hp_after_default == unit.get_max_hp(),
      'unit.get_hp() after clean_up(full=False) = %r, max_hp = %r (expected equal)' % (hp_after_default, unit.get_max_hp()))

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print('\n' + '=' * 78)
print('SUMMARY')
print('=' * 78)
if FAILURES:
    print('\nFAILURES (%d):' % len(FAILURES))
    for f in FAILURES:
        print('  - %s' % f)
    print('\nRESULT: FAIL')
    sys.exit(1)
else:
    print('\nAll executed assertions PASSED.')
    print('RESULT: PASS')
    sys.exit(0)
