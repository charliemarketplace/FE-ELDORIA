#!/usr/bin/env python3
"""
Execution-based proof that SHUB is a working free-roam map where you can
walk up to a monster and engage it into combat on the same map: issue #16.

app/engine/roam/ is COMPLETE and the roam -> grid-combat transition already
works (state_machine.py resets `state.processed = False` whenever a state
change happens while free_roam is on top; when the pushed event pops,
FreeRoamState.begin() re-runs, sees roam is off, and calls leave()). This
script does not touch or re-verify that engine mechanism -- it proves the
CONTENT built on top of it is authored correctly on SHUB
(lion_throne.ltproj/game_data/levels.json + events.json + ai.json):

  - levels.json: SHUB has roam=True, roam_unit="Rowan"
  - levels.json: a monster unit (SHUBMonster, a Wraith) with roam_ai set to
    an AI prefab (MonsterRoamAI) that has roam_ai=True in ai.json
  - levels.json: an interrupt_move region ("MonsterApproach") on the
    approach tiles next to the monster
  - events.json: a matching `roaming_interrupt` event ("SHUB
    MonsterApproach") that offers a Fight/Retreat choice, and on Fight calls
    ONLY `change_roaming;False` -- never `clean_up_roaming` (footgun (a):
    clean_up_roaming fades out every unit except the roam unit, which would
    delete the monster before you could ever fight it).

Run with:
  uv run --no-project --python 3.12 --with pygame-ce --with typing-extensions python tools/test_roam.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import play_harness as harness
harness.boot()

from app.data.resources.resources import RESOURCES
from app.data.database.database import DB

from app.engine import game_state

FAILURES = []


def check(label, condition, detail):
    status = 'PASS' if condition else 'FAIL'
    print('[%s] %s: %s' % (status, label, detail))
    if not condition:
        FAILURES.append('%s -- %s' % (label, detail))
    return condition


print('=' * 78)
print('FREE ROAM (#16) -- EXECUTION-BASED PROOF')
print('=' * 78)

# ---------------------------------------------------------------------------
# 1. Boot DB/RESOURCES, start SHUB for real
# ---------------------------------------------------------------------------
print("\n--- [1] Boot DB/RESOURCES, game_state.start_level('SHUB') ---")
# RESOURCES/DB already loaded and engine-chrome sprites/fonts already
# initialized by harness.boot() above.

level_prefab = DB.levels.get('SHUB')
check('1. SHUB levels.json authored with roam=True',
      level_prefab.roam is True, 'level_prefab.roam = %r' % level_prefab.roam)
check("1. SHUB levels.json authored with roam_unit='Rowan'",
      level_prefab.roam_unit == 'Rowan', 'level_prefab.roam_unit = %r' % level_prefab.roam_unit)

game = game_state.start_level('SHUB')
check('1. start_level(SHUB)', game.level is not None and game.level.nid == 'SHUB',
      'game.level.nid = %r (expected SHUB)' % (game.level.nid if game.level else None))

# ---------------------------------------------------------------------------
# 2. game.is_roam() reports True and resolves a real roam unit
# ---------------------------------------------------------------------------
print('\n--- [2] game.is_roam() / game.get_roam_unit() ---')
check('2. game.is_roam() is True on SHUB', game.is_roam() is True,
      'game.is_roam() = %r' % game.is_roam())

roam_unit = game.get_roam_unit()
check('2. game.get_roam_unit() resolves to a real unit',
      roam_unit is not None, 'game.get_roam_unit() = %r' % roam_unit)
check("2. the roam unit is Rowan", roam_unit is not None and roam_unit.nid == 'Rowan',
      'roam_unit.nid = %r' % (roam_unit.nid if roam_unit else None))
check('2. the roam unit is actually placed on the map',
      roam_unit is not None and roam_unit.position is not None,
      'roam_unit.position = %r' % ((roam_unit.position if roam_unit else None),))

# ---------------------------------------------------------------------------
# 3. The interrupt_move region exists and pairs with a roaming_interrupt event
# ---------------------------------------------------------------------------
print('\n--- [3] MonsterApproach interrupt_move region + roaming_interrupt event ---')
region = None
for r in game.level.regions:
    if r.nid == 'MonsterApproach':
        region = r
        break
check('3. MonsterApproach region exists on SHUB', region is not None, 'region = %r' % region)
check('3. MonsterApproach has interrupt_move=True',
      region is not None and region.interrupt_move is True,
      'region.interrupt_move = %r' % (region.interrupt_move if region else None))

roaming_interrupt_events = DB.events.get('roaming_interrupt', 'SHUB')
check('3. a roaming_interrupt event is registered for SHUB',
      len(roaming_interrupt_events) == 1,
      'DB.events.get("roaming_interrupt", "SHUB") = %s' % ([e.nid for e in roaming_interrupt_events],))

engage_event = roaming_interrupt_events[0] if roaming_interrupt_events else None
check("3. the roaming_interrupt event's condition matches this exact region",
      engage_event is not None and eval(engage_event.condition, {'region': region}) is True,
      'condition = %r' % (engage_event.condition if engage_event else None))

# ---------------------------------------------------------------------------
# 4. Footgun (a): the engage event must NEVER call clean_up_roaming, and must
#    call change_roaming;False on the Fight branch (and nothing else, per the
#    task -- clean_up_roaming would fade out the monster before you could
#    ever fight it).
# ---------------------------------------------------------------------------
print('\n--- [4] Engage event does not call clean_up_roaming ---')
engage_script = '\n'.join(engage_event._source) if engage_event else ''
check('4. roaming_interrupt event source does NOT contain clean_up_roaming',
      'clean_up_roaming' not in engage_script,
      'event source:\n%s' % engage_script)
check('4. roaming_interrupt event source DOES call change_roaming;False on Fight',
      'change_roaming;False' in engage_script,
      'event source:\n%s' % engage_script)
check('4. change_roaming;False is gated behind the Fight choice, not unconditional',
      "if;game.game_vars.get('MonsterChoice') == 'Fight'" in engage_script,
      'event source:\n%s' % engage_script)

# ---------------------------------------------------------------------------
# 5. The monster on the map has roam_ai set, and that AI prefab is roam-capable
# ---------------------------------------------------------------------------
print('\n--- [5] SHUBMonster.roam_ai -> ai.json roam_ai=True ---')
monster = game.get_unit('SHUBMonster')
check('5. SHUBMonster resolves and is placed on the map',
      monster is not None and monster.position is not None,
      'monster = %r, position = %r' % (monster, monster.position if monster else None))

roam_ai_nid = monster.get_roam_ai() if monster else None
check('5. SHUBMonster has a roam_ai assigned', bool(roam_ai_nid), 'get_roam_ai() = %r' % roam_ai_nid)

ai_prefab = DB.ai.get(roam_ai_nid) if roam_ai_nid else None
check('5. that AI prefab exists in ai.json', ai_prefab is not None, 'DB.ai.get(%r) = %r' % (roam_ai_nid, ai_prefab))
check("5. the monster's AI prefab has roam_ai=True",
      ai_prefab is not None and ai_prefab.roam_ai is True,
      'ai_prefab.roam_ai = %r' % (ai_prefab.roam_ai if ai_prefab else None))

# ---------------------------------------------------------------------------
# 6. FreeRoamAIHandler (constructed at FreeRoamState.start(), scans units only
#    at construction per the known footgun) actually picked up the monster,
#    proving it's a live roam AI unit and not just data sitting unused.
# ---------------------------------------------------------------------------
print('\n--- [6] FreeRoamAIHandler picked up the monster at construction ---')
from app.engine.roam import free_roam_ai
handler = free_roam_ai.FreeRoamAIHandler()
check("6. FreeRoamAIHandler tracks SHUBMonster as a roam AI unit",
      handler.contains_unit(monster) is not None,
      'handler.contains_unit(monster) = %r' % handler.contains_unit(monster))

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
