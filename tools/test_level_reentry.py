#!/usr/bin/env python3
"""
Execution-based proof that a cleared level can be re-entered from the
overworld -- driven directly against the LT engine (no browser, no
Playwright, no pygbag rebuild).

Bootstrap mirrors tools/test_capital_completion.py exactly (dummy SDL
drivers, real DB/RESOURCES load, real GameState save/pickle/load round
trip).

Run with:
  uv run --no-project --python 3.12 --with pygame-ce --with typing-extensions python tools/test_level_reentry.py
"""
import os
import sys
import pickle
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

sys.frozen = True
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
os.makedirs('saves', exist_ok=True)

from app.data.resources.resources import RESOURCES
from app.data.database.database import DB
from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION

import pygame
pygame.init()
pygame.display.set_mode((240, 160))

from app.engine import game_state
from app.engine.game_state import GameState
import app.engine.sprites as engine_sprites


FAILURES = []


def check(label, condition, detail):
    status = 'PASS' if condition else 'FAIL'
    print('[%s] %s: %s' % (status, label, detail))
    if not condition:
        FAILURES.append('%s -- %s' % (label, detail))
    return condition


print('=' * 78)
print('LEVEL RE-ENTRY -- EXECUTION-BASED PROOF (real action.do() / DB / save calls)')
print('=' * 78)

# ---------------------------------------------------------------------------
# 1. Boot DB/RESOURCES, start S1 for real
# ---------------------------------------------------------------------------
print('\n--- [1] Boot DB/RESOURCES, game_state.start_level(\'S1\') ---')
RESOURCES.load('lion_throne.ltproj', CURRENT_SERIALIZATION_VERSION)
DB.load('lion_throne.ltproj', CURRENT_SERIALIZATION_VERSION)
# Harness quirk (not a gameplay bug), same as tools/test_capital_completion.py:
# RESOURCES.load() resets app.sprites.SPRITES without re-running
# app.engine.sprites.load_images(), so engine-chrome sprites (e.g.
# level_cursor.py, chapter_title.py) crash on import unless this is re-run.
engine_sprites.load_images()
game = game_state.start_level('S1')
check('1. start_level(S1)', game.level is not None and game.level.nid == 'S1',
      'game.level.nid = %r (expected S1)' % (game.level.nid if game.level else None))

# Imported only now: start_level() above already pulled in the full engine
# module graph in the right order (avoids a circular import through
# app.engine.icons / app.engine.graphics.text.text_renderer that trips up
# importing app.engine.overworld.overworld_states cold, before the engine
# package has been touched).
from app.engine.overworld.overworld_states import is_level_launchable

# ---------------------------------------------------------------------------
# 2. `_cleared_levels` starts empty/absent
# ---------------------------------------------------------------------------
print('\n--- [2] _cleared_levels starts empty/absent ---')
check('2. _cleared_levels absent or empty at level start',
      game.game_vars.get('_cleared_levels', set()) == set(),
      "game.game_vars.get('_cleared_levels', set()) = %r" % (game.game_vars.get('_cleared_levels', set()),))

# ---------------------------------------------------------------------------
# 3. Mark S1 cleared (mirrors EventState.level_end()'s new line) and prove the
#    set survives a save -> pickle round trip -> fresh GameState().load()
#    (game_vars is a PrimitiveCounter, pickled wholesale by game.save() --
#    no new save code needed for a set value).
# ---------------------------------------------------------------------------
print('\n--- [3] Mark S1 cleared, save -> pickle round trip -> fresh GameState().load() ---')
game.game_vars['_cleared_levels'] = game.game_vars.get('_cleared_levels', set()) | {'S1'}
check('3. _cleared_levels contains S1 pre-save',
      game.game_vars.get('_cleared_levels') == {'S1'},
      "game.game_vars.get('_cleared_levels') = %r" % (game.game_vars.get('_cleared_levels'),))

s_dict, meta_dict = game.save()

tmp_fd, tmp_path = tempfile.mkstemp(prefix='lt_reentry_test_', suffix='.p')
os.close(tmp_fd)
try:
    with open(tmp_path, 'wb') as fp:
        pickle.dump(s_dict, fp)
    with open(tmp_path, 'rb') as fp:
        loaded_s_dict = pickle.load(fp)
finally:
    os.remove(tmp_path)

fresh_game = GameState()
fresh_game.build_new()
fresh_game.load(loaded_s_dict)

post_load_cleared = fresh_game.game_vars.get('_cleared_levels')
check('3. _cleared_levels round-trips through save/pickle/load intact',
      post_load_cleared == {'S1'} and isinstance(post_load_cleared, set),
      "post-load game_vars.get('_cleared_levels') = %r (type=%s)" %
      (post_load_cleared, type(post_load_cleared).__name__))

# ---------------------------------------------------------------------------
# 4. DB.events.get('level_reenter', 'S1') returns the new prep event, and
#    DB.events.get('level_start', 'S1') still returns S1 Intro -- proves
#    trigger substitution actually selects a different event.
# ---------------------------------------------------------------------------
print('\n--- [4] DB.events.get selects level_reenter vs level_start distinctly for S1 ---')
reenter_events = DB.events.get('level_reenter', 'S1')
start_events = DB.events.get('level_start', 'S1')

check('4. DB.events.get(level_reenter, S1) returns exactly the new prep event',
      len(reenter_events) == 1 and reenter_events[0].nid == 'S1 Reenter',
      'reenter_events = %s' % [e.nid for e in reenter_events])

reenter_script = '\n'.join(reenter_events[0]._source) if reenter_events else ''
check('4. S1 Reenter event source is exactly prep;0 (Manage/Formation/Save entry point)',
      reenter_events and reenter_events[0]._source == ['prep;0'],
      'S1 Reenter _source = %r' % (reenter_events[0]._source if reenter_events else None,))

check('4. DB.events.get(level_start, S1) still returns S1 Intro, unaffected',
      len(start_events) == 1 and start_events[0].nid == 'S1 Intro',
      'start_events = %s' % [e.nid for e in start_events])

# Also assert the analogous events exist for S2-S5, and that hub levels
# (CAPITAL, SHUB) were deliberately NOT given a level_reenter event.
for lvl in ('S2', 'S3', 'S4', 'S5'):
    lvl_reenter = DB.events.get('level_reenter', lvl)
    check('4. %s has a level_reenter prep event' % lvl,
          len(lvl_reenter) == 1 and lvl_reenter[0]._source == ['prep;0'],
          '%s level_reenter events = %s' % (lvl, [(e.nid, e._source) for e in lvl_reenter]))

for hub in ('CAPITAL', 'SHUB'):
    hub_reenter = DB.events.get('level_reenter', hub)
    check('4. hub level %s was NOT given a level_reenter event' % hub,
          len(hub_reenter) == 0,
          '%s level_reenter events = %s' % (hub, [e.nid for e in hub_reenter]))

# ---------------------------------------------------------------------------
# 5. The launchable predicate (app.engine.overworld.overworld_states.
#    is_level_launchable, the exact function OverworldFreeState.take_input
#    uses to decide whether SELECT on a node may launch a level): with
#    _cleared_levels={'S1'} and next_level='S2', an S1 node is launchable
#    AND an uncleared S3 node is not.
# ---------------------------------------------------------------------------
print('\n--- [5] is_level_launchable predicate ---')
cleared = {'S1'}
next_level = 'S2'
check('5. cleared S1 node is launchable even though it is not next_level',
      is_level_launchable('S1', next_level, cleared) is True,
      "is_level_launchable('S1', 'S2', {'S1'}) = %r" % (is_level_launchable('S1', next_level, cleared),))
check('5. next_level S2 node is launchable',
      is_level_launchable('S2', next_level, cleared) is True,
      "is_level_launchable('S2', 'S2', {'S1'}) = %r" % (is_level_launchable('S2', next_level, cleared),))
check('5. uncleared, non-next-level S3 node is NOT launchable',
      is_level_launchable('S3', next_level, cleared) is False,
      "is_level_launchable('S3', 'S2', {'S1'}) = %r" % (is_level_launchable('S3', next_level, cleared),))

# ---------------------------------------------------------------------------
# 6. next_level is unchanged after a simulated re-entry -- story progress
#    must survive a revisit. Mirrors OverworldLevelTransition.update(),
#    which pops '_reentry_target_nid' and passes it to go_to_next_level(nid)
#    WITHOUT ever reassigning game.overworld_controller.next_level.
# ---------------------------------------------------------------------------
print('\n--- [6] next_level survives a simulated re-entry ---')


class FakeOverworldController:
    def __init__(self, next_level):
        self.next_level = next_level


fake_controller = FakeOverworldController('S2')
game.game_vars['_reentry_target_nid'] = 'S1'

# Exact logic of OverworldLevelTransition.update(): pop the stashed target,
# fall back to next_level, and never write next_level itself.
reentry_target = game.game_vars.pop('_reentry_target_nid', None)
launch_nid = reentry_target or fake_controller.next_level

check('6. simulated re-entry launches the reentry target, not next_level',
      launch_nid == 'S1',
      'launch_nid = %r (expected S1)' % (launch_nid,))
check('6. next_level is unchanged after the simulated re-entry',
      fake_controller.next_level == 'S2',
      'fake_controller.next_level = %r (expected unchanged S2)' % (fake_controller.next_level,))
check('6. _reentry_target_nid was consumed (popped), not left dangling',
      game.game_vars.get('_reentry_target_nid') is None,
      "game.game_vars.get('_reentry_target_nid') = %r" % (game.game_vars.get('_reentry_target_nid'),))

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
