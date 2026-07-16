#!/usr/bin/env python3
"""
Verifies the "wire up the full story" pass: companion carry-through S2-S5,
overworld routing for every non-final chapter, and prep-screen wiring.

Run with:
  uv run --no-project --python 3.12 --with pygame-ce --with typing-extensions python tools/verify_full_story_wiring.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.frozen = True
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

FAILURES = []


def check(label, condition, detail):
    status = 'PASS' if condition else 'FAIL'
    print('[%s] %s: %s' % (status, label, detail))
    if not condition:
        FAILURES.append('%s -- %s' % (label, detail))


# --- 0. Byte-identical JSON round trip for the two files we hand-edited ---
for relpath in ('lion_throne.ltproj/game_data/levels.json', 'lion_throne.ltproj/game_data/events.json'):
    with open(relpath, 'rb') as f:
        raw = f.read()
    data = json.loads(raw.decode('utf-8'))
    rebuilt = (json.dumps(data, indent=4, ensure_ascii=True).replace('\n', '\r\n')).encode('utf-8')
    check('0. %s is byte-identical to canonical dump' % relpath, rebuilt == raw,
          'len(disk)=%d len(rebuilt)=%d' % (len(raw), len(rebuilt)))

from app.data.resources.resources import RESOURCES
from app.data.database.database import DB
from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION

import pygame
pygame.init()
pygame.display.set_mode((240, 160))

import app.engine.sprites as engine_sprites

RESOURCES.load('lion_throne.ltproj', CURRENT_SERIALIZATION_VERSION)
DB.load('lion_throne.ltproj', CURRENT_SERIALIZATION_VERSION)
engine_sprites.load_images()

print('=' * 78)
print('OVERWORLD ROUTING')
print('=' * 78)

expected_overworld = {'CAPITAL': True, 'S1': True, 'S2': True, 'SHUB': True,
                       'S3': True, 'S4': True, 'S5': False}
for nid, expected in expected_overworld.items():
    level = DB.levels.get(nid)
    check('%s.go_to_overworld == %s' % (nid, expected), level.go_to_overworld == expected,
          'actual = %s' % level.go_to_overworld)

check('DB.levels order matches campaign progression',
      [l.nid for l in DB.levels] == ['CAPITAL', 'S1', 'S2', 'SHUB', 'S3', 'S4', 'S5'],
      'order = %s' % [l.nid for l in DB.levels])

no_set_next_chapter = all('set_next_chapter' not in line for event in DB.events for line in event._source)
check('no event still calls set_next_chapter (all routing now via overworld index order)',
      no_set_next_chapter, 'ok' if no_set_next_chapter else 'FOUND a leftover set_next_chapter call')

overworld = DB.overworlds.get('0')
node_order = [n.nid for n in overworld.overworld_nodes]
check('overworld has all 7 nodes in campaign order', node_order == ['CAPITAL', 'S1', 'S2', 'SHUB', 'S3', 'S4', 'S5'],
      'node order = %s' % node_order)
for node in overworld.overworld_nodes:
    level_ok = DB.levels.get(node.level) is not None
    check('overworld node %s -> level %s resolves' % (node.nid, node.level), level_ok, 'level = %s' % node.level)

print('\n' + '=' * 78)
print('COMPANION CARRY-THROUGH (kael/elara/ren/briar) IN EVERY CHAPTER INTRO')
print('=' * 78)

intro_nids = {'S1': 'S1 Intro', 'S2': 'S2 Intro', 'SHUB': 'SHUB Intro', 'S3': 'S3 Intro',
              'S4': 'S4 Intro', 'S5': 'S5 Intro'}
def get_event(event_nid, level_nid):
    matches = [e for e in DB.events if e.nid == event_nid and e.level_nid == level_nid]
    assert len(matches) == 1, (event_nid, level_nid, len(matches))
    return matches[0]

for level_nid, event_nid in intro_nids.items():
    event = get_event(event_nid, level_nid)
    src = '\n'.join(event._source)
    for companion in ('Kael', 'Elara', 'Ren', 'Briar'):
        var = companion.lower() + '_joined'
        has_check = ("game.game_vars.get('%s')" % var) in src
        has_add = ('add_unit;%s;' % companion) in src
        check('%s carries %s (joined-check + add_unit present)' % (event_nid, companion),
              has_check and has_add, 'has_check=%s has_add=%s' % (has_check, has_add))
    # every companion add_unit position should be unique within this event (no stacked spawns)
    positions = []
    for line in event._source:
        if line.startswith('add_unit;'):
            parts = line.split(';')
            positions.append(parts[2])
    check('%s has no duplicate add_unit spawn tiles' % event_nid, len(positions) == len(set(positions)),
          'positions = %s' % positions)

print('\n' + '=' * 78)
print('PREP SCREEN WIRED INTO EVERY CHAPTER INTRO')
print('=' * 78)

for level_nid, event_nid in intro_nids.items():
    event = get_event(event_nid, level_nid)
    has_prep = 'prep;0' in event._source
    check('%s calls prep;0' % event_nid, has_prep, 'source = %s' % event._source)

capital_intro = get_event('CAPITAL Intro', 'CAPITAL')
check('CAPITAL Intro deliberately has no prep call (character-creation flow, not a battle prep)',
      not any(line.startswith('prep;') for line in capital_intro._source), 'ok')

print('\n' + '=' * 78)
if FAILURES:
    print('RESULT: %d FAILURE(S)' % len(FAILURES))
    for f in FAILURES:
        print('  - %s' % f)
    sys.exit(1)
else:
    print('RESULT: ALL CHECKS PASSED')
