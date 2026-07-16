#!/usr/bin/env python3
"""
Regression guard: SHUB (Emberhold Waystation), like CAPITAL, is a safe
hub/shop town with no combat -- it should get the same "safe-zone" 5x
player MOVEMENT QoL boost that CAPITAL already has (see
app/engine/equations.py's safe_zone_movement patch, gated on the
game_var 'safe_zone'). SHUB Intro previously never set safe_zone;1 (only
CAPITAL Intro did), so movement in SHUB was stuck at normal (1x) speed
despite being just as safe as Capital.

Checks:
1. SHUB Intro now sets game_var;safe_zone;1 (mirroring CAPITAL Intro).
2. SHUB Depart now resets game_var;safe_zone;0 before win_game (mirroring
   CAPITAL Depart), so the boost doesn't leak into the S3 combat chapter.
3. Live equation check: with game_vars['safe_zone'] set, a player unit's
   MOVEMENT equation actually returns 5x base -- proves the mechanism
   itself works, not just that the JSON text is present.

Run with:
  uv run --no-project --python 3.12 --with pygame-ce --with typing-extensions python tools/verify_safe_zone_movement.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.frozen = True
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import pygame
pygame.init()
pygame.display.set_mode((240, 160))

from app.data.resources.resources import RESOURCES
from app.data.database.database import DB
from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION

FAILURES = []


def check(label, condition, detail):
    status = 'PASS' if condition else 'FAIL'
    print('[%s] %s: %s' % (status, label, detail))
    if not condition:
        FAILURES.append('%s -- %s' % (label, detail))


RESOURCES.load('lion_throne.ltproj', CURRENT_SERIALIZATION_VERSION)
DB.load('lion_throne.ltproj', CURRENT_SERIALIZATION_VERSION)

print('=' * 78)
print('SAFE-ZONE MOVEMENT -- SHUB gets the same 5x QoL boost as CAPITAL')
print('=' * 78)

shub_intro = next(e for e in DB.events if e.nid == 'SHUB Intro')
check("SHUB Intro sets game_var;safe_zone;1",
      'game_var;safe_zone;1' in shub_intro._source,
      '_source[:3] = %s' % shub_intro._source[:3])

shub_depart = next(e for e in DB.events if e.nid == 'SHUB Depart')
check("SHUB Depart resets game_var;safe_zone;0 before win_game",
      shub_depart._source.index('game_var;safe_zone;0') == shub_depart._source.index('win_game') - 1,
      '_source[-3:] = %s' % shub_depart._source[-3:])

capital_intro = next(e for e in DB.events if e.nid == 'CAPITAL Intro')
check("CAPITAL Intro still sets game_var;safe_zone;1 (unchanged reference behavior)",
      'game_var;safe_zone;1' in capital_intro._source,
      '_source[:1] = %s' % capital_intro._source[:1])

# --- Live equation check: does the mechanism actually multiply MOVEMENT? ---
from app.engine.game_state import game
from app.engine import equations

game.build_new()
game.game_vars['safe_zone'] = 0
unit = next((u for u in DB.units if u.nid == 'Rowan'), None) or DB.units.values()[0]

from app.engine.objects.unit import UnitObject
unit_obj = UnitObject.from_prefab(unit, game.unit_registry)
unit_obj.team = 'player'

eq = equations.Parser()

normal_move = eq.movement(unit_obj)
game.game_vars['safe_zone'] = 1
boosted_move = eq.movement(unit_obj)
game.game_vars['safe_zone'] = 0

check("safe_zone game_var actually quintuples player MOVEMENT",
      boosted_move == normal_move * 5,
      'normal_move=%r boosted_move=%r (expected %r)' % (normal_move, boosted_move, normal_move * 5))

print('\n' + '=' * 78)
if FAILURES:
    print('RESULT: %d FAILURE(S)' % len(FAILURES))
    for f in FAILURES:
        print('  - %s' % f)
    sys.exit(1)
else:
    print('RESULT: ALL CHECKS PASSED')
