#!/usr/bin/env python3
"""
Regression guard for a real production bug: reveal_overworld_node/road
commands were originally placed in "CAPITAL Depart" (a level event), which
fires while still inside the CAPITAL level, before the game ever transitions
into the overworld state. At that point game.overworld_controller is still
None (see game_state.py's __init__: `self.overworld_controller = None`), so
`game.overworld_controller.nodes[...]` in overworld_event_functions.py's
reveal_overworld_node crashed with an uncaught AttributeError, surfacing to
the player as "Event execution failed with error in command
reveal_overworld_node;CAPITAL".

The fix moves those commands to a Global event bound to the 'overworld_start'
trigger (see app/events/triggers.py's OverworldStart, fired from
app/engine/overworld/overworld_states.py's OverworldFreeState.start() *after*
game.overworld_controller is constructed in set_up_overworld_game_state()).

This script proves the fix two ways:
1. The new "Global Reveal Overworld" event in events.json is wired to trigger
   'overworld_start' (not a level-scoped trigger) and no longer sits in
   CAPITAL Depart's source.
2. Actually constructs a real OverworldManager the same way
   OverworldFreeState.set_up_overworld_game_state() does, then calls the real
   reveal_overworld_node/reveal_overworld_road functions from
   overworld_event_functions.py against it -- proving the exact functions
   that crashed now run cleanly once overworld_controller exists, and that
   all 7 nodes + 6 roads actually end up enabled.

Run with:
  uv run --no-project --python 3.12 --with pygame-ce --with typing-extensions python tools/verify_overworld_reveal_trigger.py
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
print('OVERWORLD REVEAL -- trigger wiring + live function call')
print('=' * 78)

reveal_event = next((e for e in DB.events if e.nid == 'Global Reveal Overworld'), None)
check('Global Reveal Overworld event exists', reveal_event is not None, 'found = %r' % (reveal_event is not None))
check("it's bound to trigger 'overworld_start', not a level event",
      reveal_event.trigger == 'overworld_start' and reveal_event.level_nid is None,
      'trigger=%r level_nid=%r' % (reveal_event.trigger, reveal_event.level_nid))

depart_event = next(e for e in DB.events if e.nid == 'CAPITAL Depart')
depart_source = '\n'.join(depart_event._source)
check("CAPITAL Depart no longer contains reveal_overworld_ commands",
      'reveal_overworld_' not in depart_source,
      'reveal_overworld_ in depart source = %r' % ('reveal_overworld_' in depart_source))

expected_nodes = ['CAPITAL', 'S1', 'S2', 'SHUB', 'S3', 'S4', 'S5']
expected_roads = [('CAPITAL', 'S1'), ('S1', 'S2'), ('S2', 'SHUB'), ('SHUB', 'S3'), ('S3', 'S4'), ('S4', 'S5')]
reveal_source = reveal_event._source
for n in expected_nodes:
    check('reveal event contains reveal_overworld_node;%s' % n,
          ('reveal_overworld_node;%s;immediate' % n) in reveal_source,
          'present = %r' % (('reveal_overworld_node;%s;immediate' % n) in reveal_source))
for a, b in expected_roads:
    check('reveal event contains reveal_overworld_road;%s;%s' % (a, b),
          ('reveal_overworld_road;%s;%s;immediate' % (a, b)) in reveal_source,
          'present = %r' % (('reveal_overworld_road;%s;%s;immediate' % (a, b)) in reveal_source))

# --- Live function call against a *real* OverworldManager, constructed the
#     same way OverworldFreeState.set_up_overworld_game_state() does it ---
from app.engine.game_state import game
from app.engine.overworld.overworld_cursor import OverworldCursor
from app.engine.overworld.overworld_manager import OverworldManager
from app.engine.camera import Camera
from app.events.overworld_event_functions import reveal_overworld_node, reveal_overworld_road

game.build_new()
overworld_nid = DB.overworlds.values()[0].nid
game.camera = Camera(game)
game.cursor = OverworldCursor(game.camera)
game.overworld_controller = OverworldManager(game.overworld_registry[overworld_nid], game.cursor, None, game.camera)

check('overworld_controller constructed with no enabled nodes initially',
      len(game.overworld_controller.revealed_node_nids) == 0,
      'revealed_node_nids = %r' % game.overworld_controller.revealed_node_nids)


class FakeEventSelf:
    """Minimal stand-in for the real Event object -- only what
    reveal_overworld_node/road actually touch (self.logger, self.do_skip,
    self.wait_time, self.state)."""
    def __init__(self):
        import logging
        self.logger = logging.getLogger()
        self.do_skip = True
        self.wait_time = 0
        self.state = None


fake_self = FakeEventSelf()
crash = None
try:
    for n in expected_nodes:
        reveal_overworld_node(fake_self, n, flags={'immediate'})
    for a, b in expected_roads:
        reveal_overworld_road(fake_self, a, b, flags={'immediate'})
except Exception as e:
    crash = e

check('reveal_overworld_node/road ran with no exception against a real OverworldManager',
      crash is None, 'crash = %r' % crash)

if crash is None:
    check('all 7 nodes actually enabled',
          set(game.overworld_controller.revealed_node_nids) == set(expected_nodes),
          'revealed_node_nids = %r' % game.overworld_controller.revealed_node_nids)
    check('all 6 roads actually enabled',
          len(game.overworld_controller.revealed_roads) == len(expected_roads),
          'revealed_roads = %r' % [r.nid for r in game.overworld_controller.revealed_roads])

print('\n' + '=' * 78)
if FAILURES:
    print('RESULT: %d FAILURE(S)' % len(FAILURES))
    for f in FAILURES:
        print('  - %s' % f)
    sys.exit(1)
else:
    print('RESULT: ALL CHECKS PASSED')
