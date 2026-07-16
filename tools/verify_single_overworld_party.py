#!/usr/bin/env python3
"""
Regression guard for a real production bug: after beating a chapter and
returning to the overworld, a second, movable "copy" of the player appeared
on the map.

Root cause: lion_throne.ltproj/game_data/parties.json defined two parties --
"Resistance" (leader "Ophie", a unit that doesn't even exist in this
project's roster -- leftover demo-template data) and "Emberwake" (leader
"Rowan", the real party). OverworldObject.from_prefab() unconditionally
creates one OverworldEntityObject per party in the registry (see
app/engine/objects/overworld/overworld.py's `for pnid in
party_registry.keys(): ... overworld.overworld_entities[pnid] = ...`), so
both parties got their own overworld sprite and were both independently
selectable/movable.

Fix: removed the unused "Resistance" party from parties.json.

Run with:
  uv run --no-project --python 3.12 --with pygame-ce --with typing-extensions python tools/verify_single_overworld_party.py
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
print('SINGLE OVERWORLD PARTY -- no leftover duplicate player entity')
print('=' * 78)

party_nids = [p.nid for p in DB.parties.values()]
check('exactly 1 party defined in parties.json', len(party_nids) == 1,
      'party_nids = %r' % party_nids)
check("no leftover 'Resistance' party", 'Resistance' not in party_nids,
      'party_nids = %r' % party_nids)
check("real party 'Emberwake' (leader Rowan) is present", 'Emberwake' in party_nids,
      'party_nids = %r' % party_nids)

from app.engine.game_state import game
from app.engine.objects.overworld import OverworldObject

game.build_new()
overworld_nid = DB.overworlds.values()[0].nid
overworld = OverworldObject.from_prefab(DB.overworlds.get(overworld_nid), game.parties, game.unit_registry)

check('exactly 1 overworld entity constructed (no duplicate "self")',
      len(overworld.overworld_entities) == 1,
      'overworld_entities keys = %r' % list(overworld.overworld_entities.keys()))

entity = list(overworld.overworld_entities.values())[0] if overworld.overworld_entities else None
check("the one overworld entity is Emberwake",
      entity is not None and entity.nid == 'Emberwake',
      'entity.nid = %r' % (entity.nid if entity else None))

print('\n' + '=' * 78)
if FAILURES:
    print('RESULT: %d FAILURE(S)' % len(FAILURES))
    for f in FAILURES:
        print('  - %s' % f)
    sys.exit(1)
else:
    print('RESULT: ALL CHECKS PASSED')
