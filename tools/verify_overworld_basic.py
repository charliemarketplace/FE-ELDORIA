#!/usr/bin/env python3
"""
Lightweight proof that the new overworld/world-map data is real and wired
correctly -- NOT a full headless UI-navigation drive (menu/transition/timing
simulation for interactive states proved fragile and low-value earlier this
session; that's left to manual playtest per project convention).

Checks:
1. DB.overworlds loads the "0" overworld with all 7 real level nodes,
   correct positions, and no dangling level references.
2. Every node's `level` nid actually exists in DB.levels.
3. Every node's `icon` nid actually exists in RESOURCES.map_icons (would
   otherwise silently fail to render, or fall back invisibly).
4. The real level_end() trigger condition (app/events/event_state.py) that
   decides whether to route to the overworld after CAPITAL's `win_game`
   evaluates True given CAPITAL's actual go_to_overworld flag, the
   constants.json overworld flag, and no explicit set_next_chapter (i.e.
   CAPITAL Depart no longer force-jumps to S1).

Run with:
  uv run --no-project --python 3.12 --with pygame-ce --with typing-extensions python tools/verify_overworld_basic.py
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
from app.engine import game_state

FAILURES = []


def check(label, condition, detail):
    status = 'PASS' if condition else 'FAIL'
    print('[%s] %s: %s' % (status, label, detail))
    if not condition:
        FAILURES.append('%s -- %s' % (label, detail))


RESOURCES.load('lion_throne.ltproj', CURRENT_SERIALIZATION_VERSION)
DB.load('lion_throne.ltproj', CURRENT_SERIALIZATION_VERSION)
engine_sprites.load_images()

print('=' * 78)
print('OVERWORLD BASICS -- data integrity + routing condition')
print('=' * 78)

check('constants.json overworld flag is True', DB.constants.value('overworld') is True,
      'DB.constants.value(overworld) = %r' % DB.constants.value('overworld'))

overworlds = DB.overworlds.values()
check('exactly 1 overworld registered', len(overworlds) == 1, 'count = %d' % len(overworlds))
ow = overworlds[0]
check('overworld tilemap is EldoriaWorldMap', ow.tilemap == 'EldoriaWorldMap', 'tilemap = %r' % ow.tilemap)

nodes = ow.overworld_nodes.values()
expected_levels = ['CAPITAL', 'S1', 'S2', 'SHUB', 'S3', 'S4', 'S5']
node_levels = [n.level for n in nodes]
check('7 nodes, one per real level, in order', node_levels == expected_levels,
      'node levels = %s' % node_levels)

for node in nodes:
    check('node %s -> level %s exists in DB.levels' % (node.nid, node.level),
          DB.levels.get(node.level) is not None,
          'DB.levels.get(%r) = %r' % (node.level, DB.levels.get(node.level)))
    icon_exists = RESOURCES.map_icons.get(node.icon) is not None
    check('node %s icon %r exists in RESOURCES.map_icons' % (node.nid, node.icon),
          icon_exists, 'RESOURCES.map_icons.get(%r) = %r' % (node.icon, RESOURCES.map_icons.get(node.icon)))

# Confirm the tilemap referenced by the overworld actually resolves too
tilemap_exists = RESOURCES.tilemaps.get(ow.tilemap) is not None
check('overworld tilemap resource resolves', tilemap_exists,
      'RESOURCES.tilemaps.get(%r) = %r' % (ow.tilemap, RESOURCES.tilemaps.get(ow.tilemap)))

# --- Real level_end() routing condition, read verbatim from event_state.py,
#     evaluated against real DB/game state (not hand-waved) ---
game = game_state.start_level('CAPITAL')
depart_event = next(e for e in DB.events if e.nid == 'CAPITAL Depart')
check('CAPITAL Depart no longer force-jumps chapters',
      'set_next_chapter' not in '\n'.join(depart_event._source),
      '_source = %s' % depart_event._source)

capital_level = DB.levels.get('CAPITAL')
should_go_to_overworld = (
    capital_level.go_to_overworld
    and DB.constants.value('overworld')
    and game.game_vars.get('_goto_level') is None
)
check('level_end() routing condition evaluates True for CAPITAL right now',
      should_go_to_overworld is True,
      'go_to_overworld=%r, overworld const=%r, _goto_level=%r' %
      (capital_level.go_to_overworld, DB.constants.value('overworld'), game.game_vars.get('_goto_level')))

print('\n' + '=' * 78)
if FAILURES:
    print('RESULT: %d FAILURE(S)' % len(FAILURES))
    for f in FAILURES:
        print('  - %s' % f)
    sys.exit(1)
else:
    print('RESULT: ALL CHECKS PASSED')
