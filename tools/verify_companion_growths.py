#!/usr/bin/env python3
"""
Regression guard for a real bug found via manual playtest: Kael/Elara/Ren/
Briar shipped with all-zero personal `growths` in units.json. The engine's
stat-gain formula (app/engine/unit_funcs.py's growth_rate()) is
`unit.growths[nid] + unit.growth_bonus(nid) + klass.growth_bonus.get(nid, 0) + ...`
-- a NAMED unit's level-up stats are driven by its OWN growths field, not by
whatever class it's in (klass.growths is never read here). All-zero personal
growths meant these 4 companions could never gain a single stat on level-up,
in any class, which is exactly what the user reported ("leveled up Elara and
Ren to lvl 2 and no stats changed").

This simulates many level-ups via the real unit_funcs.get_next_level_up()
(the same function the actual level-up screen calls) and asserts stats
actually increase over enough iterations -- growth is probabilistic, so a
single level-up isn't a reliable check, but a total of ~0 gained stats across
dozens of level-ups on a real-growth unit would be statistically absurd.

Run with:
  uv run --no-project --python 3.12 --with pygame-ce --with typing-extensions python tools/verify_companion_growths.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.frozen = True
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

from app.data.resources.resources import RESOURCES
from app.data.database.database import DB
from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION

import pygame
pygame.init()
pygame.display.set_mode((240, 160))

import app.engine.sprites as engine_sprites
from app.engine import game_state, action, unit_funcs

FAILURES = []


def check(label, condition, detail):
    status = 'PASS' if condition else 'FAIL'
    print('[%s] %s: %s' % (status, label, detail))
    if not condition:
        FAILURES.append('%s -- %s' % (label, detail))


RESOURCES.load('lion_throne.ltproj', CURRENT_SERIALIZATION_VERSION)
DB.load('lion_throne.ltproj', CURRENT_SERIALIZATION_VERSION)
engine_sprites.load_images()
game = game_state.start_level('CAPITAL')

print('=' * 78)
print('COMPANION GROWTHS -- proving level-up actually grants stats')
print('=' * 78)

# Personal growths must be nonzero now (the real fix -- not klass.growths,
# which is never consulted for named units per unit_funcs.growth_rate()).
for nid in ('Kael', 'Elara', 'Ren', 'Briar'):
    prefab = DB.units.get(nid)
    check('%s has nonzero personal growths' % nid,
          any(v > 0 for v in prefab.growths.values()),
          'growths = %s' % prefab.growths)

# Simulate 60 level-ups each for Elara and Ren (matches the exact units the
# user reported) via the real get_next_level_up(), same function the actual
# level-up screen uses, and confirm real stat gains accumulate.
for nid in ('Elara', 'Ren'):
    unit = game.get_unit(nid)
    action.do(action.ClassChange(unit, 'Mage' if nid == 'Elara' else 'Mercenary'))
    before_stats = dict(unit.stats)
    total_gain = {k: 0 for k in before_stats}
    for level in range(unit.level, unit.level + 60):
        changes = unit_funcs.get_next_level_up(unit, level)
        action.do(action.ApplyStatChanges(unit, changes))
        for stat_nid, amount in changes.items():
            total_gain[stat_nid] += amount
    grand_total = sum(total_gain.values())
    check('%s gains real stats over 60 simulated level-ups' % nid,
          grand_total > 0,
          'total stat gain across all stats = %d (per-stat: %s)' % (grand_total, total_gain))

print('\n' + '=' * 78)
if FAILURES:
    print('RESULT: %d FAILURE(S)' % len(FAILURES))
    for f in FAILURES:
        print('  - %s' % f)
    sys.exit(1)
else:
    print('RESULT: ALL CHECKS PASSED')
