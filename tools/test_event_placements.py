#!/usr/bin/env python3
"""Static validation of every `add_unit;<nid>;x,y` in events.json.

Two whole classes of bug shipped past every behaviour test here, because a
unit placed badly still ends up with a non-None position and so still counts
as "deployed":

  * Kael was placed inside a Wall tile in S1 (and, once the re-entry events
    mirrored the intro blocks, in S1 Reenter too); Briar likewise in S3.
    `Event._check_placement` validates map bounds and occupancy but never
    terrain, so the placement silently succeeds and the player sees a
    companion standing in a wall.
  * Two companions were then assigned the same tile while fixing the above.
    The engine nudges the second unit to a nearby tile when it can, but that
    silently relocates an authored placement and can fail outright, leaving
    a companion undeployed.

This runs in a second, needs no game loop, and fails loudly on either.

Run with:
  uv run --no-project --python 3.12 --with pygame-ce --with typing-extensions python tools/test_event_placements.py
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import play_harness as harness
harness.boot()

from app.data.database.database import DB
from app.data.resources.resources import RESOURCES
from app.engine.objects.tilemap import TileMapObject

# Terrain a unit must never be authored onto. Taken from terrain.json's
# impassable entries rather than guessed.
IMPASSABLE = {'Wall', 'Cliff', 'Lake', 'Fence', 'Sea', 'Pillar'}

ADD_UNIT = re.compile(r'add_unit;([^;]+);(\d+),(\d+)')

FAILURES = []


def check(label, condition, detail):
    print('[%s] %s: %s' % ('PASS' if condition else 'FAIL', label, detail))
    if not condition:
        FAILURES.append('%s -- %s' % (label, detail))
    return condition


print('=' * 78)
print('EVENT UNIT PLACEMENTS -- terrain and collision validation')
print('=' * 78)

levels = {l.nid: l for l in DB.levels}
tilemaps = {}

on_impassable = []
collisions = []

for event in DB.events:
    level_nid = event.level_nid
    if not level_nid or level_nid not in levels:
        continue
    level = levels[level_nid]
    if level_nid not in tilemaps:
        prefab = RESOURCES.tilemaps.get(level.tilemap)
        tilemaps[level_nid] = TileMapObject.from_prefab(prefab) if prefab else None
    tilemap = tilemaps[level_nid]
    if tilemap is None:
        continue

    # Tiles already claimed by units authored directly into the level, so an
    # event placement landing on one is just as much a collision.
    seen = {}
    for unit in level.units:
        if unit.starting_position:
            seen[tuple(unit.starting_position)] = '%s (levels.json)' % unit.nid

    for line in (event._source or []):
        match = ADD_UNIT.match(line)
        if not match:
            continue
        nid, x, y = match.group(1), int(match.group(2)), int(match.group(3))
        pos = (x, y)

        terrain = DB.terrain.get(tilemap.get_terrain(pos))
        if terrain and terrain.nid in IMPASSABLE:
            on_impassable.append('%s: %s at %s is %s' % (event.nid, nid, pos, terrain.nid))

        if pos in seen and seen[pos] != nid:
            collisions.append('%s: %s and %s both at %s' % (event.nid, seen[pos], nid, pos))
        seen[pos] = nid

check('no event places a unit on impassable terrain',
      not on_impassable,
      '\n    '.join(on_impassable) if on_impassable else 'checked every add_unit in every level-scoped event')

check('no two units are authored onto the same tile within one event',
      not collisions,
      '\n    '.join(collisions) if collisions else 'no duplicate tiles')

print('\n' + '=' * 78)
if FAILURES:
    for f in FAILURES:
        print('  - %s' % f)
    print('RESULT: FAIL')
    sys.exit(1)
print('RESULT: PASS')
sys.exit(0)
