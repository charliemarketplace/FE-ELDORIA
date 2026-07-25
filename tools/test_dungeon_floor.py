#!/usr/bin/env python3
"""
Execution-based proof for multi-floor dungeon transitions (issue #20) --
driven directly against the LT engine (no browser, no Playwright, no pygbag
rebuild).

Bootstrap mirrors tools/test_capital_completion.py exactly (dummy SDL
drivers, real DB/RESOURCES load, real GameState, engine_sprites.load_images()
quirk workaround, real game_state.start_level()).

Covers:
  - GameState.clean_up(preserve_hp=True) leaves a damaged unit damaged;
    the default (preserve_hp=False) full-heals it, as before this feature.
  - LevelPrefab.preserve_state_on_transition routes through to
    EventState.level_end()'s game.clean_up(preserve_hp=...) call, both when
    True and when False/default.
  - Party composition, inventory, and exp survive a clean_up() either way
    (this was already true before the feature; asserted here as a
    regression guard, not a new behavior).

Run with:
  uv run --no-project --python 3.12 --with pygame-ce --with typing-extensions python tools/test_dungeon_floor.py
"""
import os
import sys

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
from app.events.event_state import EventState
import app.engine.sprites as engine_sprites


FAILURES = []


def check(label, condition, detail):
    status = 'PASS' if condition else 'FAIL'
    print('[%s] %s: %s' % (status, label, detail))
    if not condition:
        FAILURES.append('%s -- %s' % (label, detail))
    return condition


def party_snapshot(g):
    """(unit nids in party, {nid: sorted item nids}, {nid: exp}) -- the three
    things BACKLOG_AUDIT.md says were already preserved across transitions,
    independent of preserve_hp."""
    units = g.get_units_in_party()
    nids = sorted(u.nid for u in units)
    items = {u.nid: sorted(item.nid for item in u.items) for u in units}
    exp = {u.nid: u.exp for u in units}
    return nids, items, exp


print('=' * 78)
print('DUNGEON FLOOR -- EXECUTION-BASED PROOF (real clean_up() / level_end() calls)')
print('=' * 78)

# ---------------------------------------------------------------------------
# 0. Boot DB/RESOURCES, start S1 for real (same quirk-workaround as
#    tools/test_capital_completion.py).
# ---------------------------------------------------------------------------
print('\n--- [0] Boot DB/RESOURCES, game_state.start_level(\'S1\') ---')
RESOURCES.load('lion_throne.ltproj', CURRENT_SERIALIZATION_VERSION)
DB.load('lion_throne.ltproj', CURRENT_SERIALIZATION_VERSION)
engine_sprites.load_images()
game = game_state.start_level('S1')
check('0. start_level(S1)', game.level is not None and game.level.nid == 'S1',
      'game.level.nid = %r (expected S1)' % (game.level.nid if game.level else None))

rowan = game.get_unit('Rowan')
max_hp = rowan.get_max_hp()
check('0. Rowan starts at full HP', rowan.get_hp() == max_hp,
      'rowan.get_hp()=%r, max_hp=%r' % (rowan.get_hp(), max_hp))
check('0. Rowan has more than 1 max HP (so damaging is observable)', max_hp > 1,
      'max_hp = %r' % max_hp)

# ---------------------------------------------------------------------------
# 1. LevelPrefab.preserve_state_on_transition exists and defaults to False.
# ---------------------------------------------------------------------------
print('\n--- [1] LevelPrefab.preserve_state_on_transition defaults to False ---')
s1_level = DB.levels.get('S1')
check('1. S1.preserve_state_on_transition defaults to False',
      s1_level.preserve_state_on_transition is False,
      's1_level.preserve_state_on_transition = %r' % (s1_level.preserve_state_on_transition,))

# ---------------------------------------------------------------------------
# 2. clean_up(preserve_hp=True) leaves a damaged unit damaged; the default
#    (preserve_hp=False) full-heals it. Uses full=False so this doesn't also
#    exercise the "remove units from the field" half of clean_up -- HP
#    preservation is the thing under test here.
# ---------------------------------------------------------------------------
print('\n--- [2] clean_up(preserve_hp=True) preserves damage; default full-heals ---')
pre_nids, pre_items, pre_exp = party_snapshot(game)

rowan.set_hp(1)
check('2. Rowan is damaged before clean_up', rowan.get_hp() == 1, 'rowan.get_hp() = %r' % rowan.get_hp())

game.clean_up(full=False, preserve_hp=True)
check('2. clean_up(preserve_hp=True) leaves the damaged unit damaged',
      rowan.get_hp() == 1, 'rowan.get_hp() = %r (expected 1, unchanged)' % rowan.get_hp())

post_preserve_nids, post_preserve_items, post_preserve_exp = party_snapshot(game)
check('2. party composition unchanged by clean_up(preserve_hp=True)',
      post_preserve_nids == pre_nids, 'nids=%r (expected %r)' % (post_preserve_nids, pre_nids))
check('2. inventory unchanged by clean_up(preserve_hp=True)',
      post_preserve_items == pre_items, 'items=%r (expected %r)' % (post_preserve_items, pre_items))
check('2. exp unchanged by clean_up(preserve_hp=True)',
      post_preserve_exp == pre_exp, 'exp=%r (expected %r)' % (post_preserve_exp, pre_exp))

# Rowan is still damaged (HP=1) here -- now prove the *default* behavior
# (preserve_hp=False) full-heals, restoring pre-feature behavior exactly.
game.clean_up(full=False, preserve_hp=False)
check('2. clean_up(preserve_hp=False) (default) fully heals the damaged unit',
      rowan.get_hp() == max_hp, 'rowan.get_hp() = %r (expected max_hp=%r)' % (rowan.get_hp(), max_hp))

game.clean_up(full=False)  # explicit no-arg call: confirm the default itself still full-heals
rowan.set_hp(1)
game.clean_up(full=False)
check('2. clean_up() with no preserve_hp argument still defaults to full-heal',
      rowan.get_hp() == max_hp, 'rowan.get_hp() = %r (expected max_hp=%r)' % (rowan.get_hp(), max_hp))

post_default_nids, post_default_items, post_default_exp = party_snapshot(game)
check('2. party composition unchanged by clean_up(preserve_hp=False)',
      post_default_nids == pre_nids, 'nids=%r (expected %r)' % (post_default_nids, pre_nids))
check('2. inventory unchanged by clean_up(preserve_hp=False)',
      post_default_items == pre_items, 'items=%r (expected %r)' % (post_default_items, pre_items))
check('2. exp unchanged by clean_up(preserve_hp=False)',
      post_default_exp == pre_exp, 'exp=%r (expected %r)' % (post_default_exp, pre_exp))

# ---------------------------------------------------------------------------
# 3. EventState.level_end() routes preserve_hp from
#    DB.levels.get(game.level.nid).preserve_state_on_transition, both when
#    True and when False/default. Spies on game.clean_up rather than
#    asserting on real HP here, so this section is a targeted proof of the
#    *wiring* in event_state.py, independent of the rest of level_end()'s
#    save/overworld machinery (which section 4 below exercises for real).
#
# level_end() calls clean_up() with the default full=True, which tears the
# level all the way down (GameState.clean_up sets game._current_level = None
# under `if full:`) -- exactly like a real level-to-level transition. So each
# scenario below needs its own fresh game_state.start_level('S1') first;
# reusing one `game`/`event_state` across two level_end() calls would crash
# the second call on `game.level.nid` (game.level is None after the first).
# ---------------------------------------------------------------------------
print('\n--- [3] EventState.level_end() reads preserve_state_on_transition ---')


def spy_wiring_scenario(preserve_flag):
    g = game_state.start_level('S1')
    lvl = DB.levels.get('S1')
    lvl.preserve_state_on_transition = preserve_flag
    captured_kwargs = []
    real_clean_up = g.clean_up

    def spy_clean_up(*args, **kwargs):
        captured_kwargs.append(kwargs)
        return real_clean_up(*args, **kwargs)

    g.clean_up = spy_clean_up
    EventState().level_end()
    return captured_kwargs[-1]


kwargs_true = spy_wiring_scenario(True)
check('3. level_end() passes preserve_hp=True through when the flag is True',
      kwargs_true.get('preserve_hp') is True,
      'clean_up kwargs = %r' % (kwargs_true,))

kwargs_false = spy_wiring_scenario(False)
check('3. level_end() passes preserve_hp=False through when the flag is False',
      kwargs_false.get('preserve_hp') is False,
      'clean_up kwargs = %r' % (kwargs_false,))

# ---------------------------------------------------------------------------
# 4. Full end-to-end: a damaged unit stays damaged through a *real*
#    EventState.level_end() call when preserve_state_on_transition is True,
#    and gets healed when it's False -- proving the wiring is live, not just
#    spied-on. game.state.change()/.clear() only append tokens to
#    game.state.temp_state (deferred, no real state is instantiated), so
#    this is safe to call headlessly. Each scenario gets its own fresh
#    start_level('S1') for the same reason as section 3.
# ---------------------------------------------------------------------------
print('\n--- [4] End-to-end level_end() with a real damaged unit ---')


def real_wiring_scenario(preserve_flag):
    g = game_state.start_level('S1')
    lvl = DB.levels.get('S1')
    lvl.preserve_state_on_transition = preserve_flag
    u = g.get_unit('Rowan')
    snapshot = party_snapshot(g)
    u.set_hp(1)
    g.state.temp_state.clear()
    EventState().level_end()
    return g, u, snapshot


game_true, rowan_true, snapshot_true = real_wiring_scenario(True)
check('4. real level_end() with preserve_state_on_transition=True leaves the unit damaged',
      rowan_true.get_hp() == 1, 'rowan.get_hp() = %r (expected 1)' % rowan_true.get_hp())
post_true = party_snapshot(game_true)
check('4. party composition survives the real level_end() (preserve True)',
      post_true[0] == snapshot_true[0], 'nids=%r (expected %r)' % (post_true[0], snapshot_true[0]))
check('4. inventory survives the real level_end() (preserve True)',
      post_true[1] == snapshot_true[1], 'items=%r (expected %r)' % (post_true[1], snapshot_true[1]))
check('4. exp survives the real level_end() (preserve True)',
      post_true[2] == snapshot_true[2], 'exp=%r (expected %r)' % (post_true[2], snapshot_true[2]))

game_false, rowan_false, snapshot_false = real_wiring_scenario(False)
check('4. real level_end() with preserve_state_on_transition=False (default) fully heals',
      rowan_false.get_hp() == rowan_false.get_max_hp(),
      'rowan.get_hp() = %r (expected max_hp=%r)' % (rowan_false.get_hp(), rowan_false.get_max_hp()))
post_false = party_snapshot(game_false)
check('4. party composition survives the real level_end() (preserve False)',
      post_false[0] == snapshot_false[0], 'nids=%r (expected %r)' % (post_false[0], snapshot_false[0]))
check('4. inventory survives the real level_end() (preserve False)',
      post_false[1] == snapshot_false[1], 'items=%r (expected %r)' % (post_false[1], snapshot_false[1]))
check('4. exp survives the real level_end() (preserve False)',
      post_false[2] == snapshot_false[2], 'exp=%r (expected %r)' % (post_false[2], snapshot_false[2]))

game.state.temp_state.clear()

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print('\n' + '=' * 78)
if FAILURES:
    print('FAILURES (%d):' % len(FAILURES))
    for f in FAILURES:
        print('  - %s' % f)
    print('=' * 78)
    sys.exit(1)
else:
    print('ALL CHECKS PASSED')
    print('=' * 78)
