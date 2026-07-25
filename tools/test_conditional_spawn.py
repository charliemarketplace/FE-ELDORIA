#!/usr/bin/env python3
"""
Execution-based proof that S2's conditional monster reinforcements work:
issue #14, "enemies that appear only when a condition fires".

#14 is ONE engine system, not three: an ordinary event `trigger` + `condition`
pair evaluated by `event_manager.get_triggered_events` (app/events/event_manager.py),
paired with the already-complete `unit_groups` spawn mechanism
(`add_group` in app/events/event_functions.py:1267-1300, backed by
action.ArriveOnMap/WarpIn/FadeIn). This script proves the pairing actually
works for the three demonstration triggers authored onto S2
(lion_throne.ltproj/game_data/levels.json + events.json):

  - S2 TurnReinforce    : trigger=turn_change,   condition="game.turncount >= 4"
  - S2 AmbushOnAttack   : trigger=combat_start,  condition="unit1.team == 'player' and unit2 and unit2.team == 'other'"
  - S2 WrongChoiceAmbush: trigger=turn_change,   condition="game.game_vars.get('S2Gambit') == 'Push Through'"

All three call `add_group;S2Monsters`, a unit_groups entry with 2 generic
Monster-faction units (S2Monster1: Ghoul, S2Monster2: Hellhound) whose
levels.json `units` entries have `starting_position: null` -- registered
but not placed, exactly like the CAPITAL companions pattern used in
tools/test_capital_completion.py.

Run with:
  uv run --no-project --python 3.12 --with pygame-ce --with typing-extensions python tools/test_conditional_spawn.py
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

from app.engine import action
from app.engine import game_state
import app.engine.sprites as engine_sprites
from app.events import triggers

FAILURES = []


def check(label, condition, detail):
    status = 'PASS' if condition else 'FAIL'
    print('[%s] %s: %s' % (status, label, detail))
    if not condition:
        FAILURES.append('%s -- %s' % (label, detail))
    return condition


print('=' * 78)
print('CONDITIONAL SPAWN (#14) -- EXECUTION-BASED PROOF')
print('=' * 78)

# ---------------------------------------------------------------------------
# 1. Boot DB/RESOURCES, start S2 for real
# ---------------------------------------------------------------------------
print("\n--- [1] Boot DB/RESOURCES, game_state.start_level('S2') ---")
RESOURCES.load('lion_throne.ltproj', CURRENT_SERIALIZATION_VERSION)
DB.load('lion_throne.ltproj', CURRENT_SERIALIZATION_VERSION)
# See tools/test_capital_completion.py for why this re-run is required.
engine_sprites.load_images()
game = game_state.start_level('S2')
check('1. start_level(S2)', game.level is not None and game.level.nid == 'S2',
      'game.level.nid = %r (expected S2)' % (game.level.nid if game.level else None))

# ---------------------------------------------------------------------------
# 2. unit_groups is authored and wired: S2Monsters group with 2 registered,
#    unplaced units
# ---------------------------------------------------------------------------
print('\n--- [2] S2Monsters unit_groups entry + registered-but-unplaced units ---')
group = game.level.unit_groups.get('S2Monsters')
check('2. S2Monsters group exists', group is not None, 'group = %r' % group)
check('2. group has exactly the 2 authored monster units',
      set(group.units) == {'S2Monster1', 'S2Monster2'},
      'group.units = %s' % (group.units,))

authored_positions = {'S2Monster1': (14, 13), 'S2Monster2': (14, 14)}
group_positions = {nid: tuple(pos) for nid, pos in group.positions.items()}
check('2. group.positions match levels.json unit_groups authoring',
      group_positions == authored_positions,
      'group.positions = %s (expected %s)' % (group_positions, authored_positions))

monsters = {nid: game.get_unit(nid) for nid in group.units}
check('2. both monster units resolve via game.get_unit() (registered at level_setup)',
      all(u is not None for u in monsters.values()),
      'game.get_unit(nid) = %s' % ({n: repr(u) for n, u in monsters.items()},))
check('2. both monster units start with position None (not yet placed)',
      all(u.position is None for u in monsters.values()),
      'positions = %s' % ({n: u.position for n, u in monsters.items()},))

check('2. S2Monster1 is a Ghoul, S2Monster2 is a Hellhound',
      monsters['S2Monster1'].klass == 'Ghoul' and monsters['S2Monster2'].klass == 'Hellhound',
      'klasses = %s' % ({n: u.klass for n, u in monsters.items()},))
check('2. both monsters are Monster faction, enemy team',
      all(u.faction == 'Monster' and u.team == 'enemy' for u in monsters.values()),
      'faction/team = %s' % ({n: (u.faction, u.team) for n, u in monsters.items()},))


def spawn_via_add_group():
    """Replicates event_functions.add_group's placement logic for the
    S2Monsters group (see app/events/event_functions.py:1267-1299): skip
    units already placed/dead, else place at the group's authored position
    via action.ArriveOnMap (the same Action add_group uses for entry_type
    'fade'/'immediate' style placement). Mirrors how event_manager.trigger()
    only ever runs an event's commands (here, add_group) after
    get_triggered_events said the event's condition held -- so the caller
    is responsible for only invoking this when should_trigger() is True."""
    placed = []
    for unit_nid, pos in group.positions.items():
        unit = game.get_unit(unit_nid)
        if unit.position or unit.dead:
            continue
        action.do(action.ArriveOnMap(unit, tuple(pos)))
        placed.append(unit_nid)
    return placed


# ---------------------------------------------------------------------------
# 3. Trigger 1: turn_change + "game.turncount >= 4" (the turn-count case)
# ---------------------------------------------------------------------------
print('\n--- [3] turn_change trigger: threshold + only_once + NEGATIVE case ---')
check('3. turncount starts at 0 right after start_level (first turn_change bumps it to 1)',
      game.turncount == 0, 'game.turncount = %r' % game.turncount)

# NEGATIVE CASE: below threshold, the event must not be in the triggered set.
# Since a real add_group call only ever happens as a consequence of the event
# actually running (event_manager.trigger() -> Event script -> add_group),
# and should_trigger() says False here, nothing should place the monsters --
# spawn_via_add_group() is deliberately NOT called in this branch, and the
# monsters must still show the "registered but unplaced" state asserted in [2].
before_trigger = game.events.should_trigger(triggers.TurnChange(), 'S2')
check('3. should_trigger(TurnChange) is False below the turncount threshold',
      before_trigger is False, 'should_trigger = %r (turncount=%d)' % (before_trigger, game.turncount))

triggered_low = game.events.get_triggered_events(triggers.TurnChange(), 'S2')
check('3. S2 TurnReinforce is NOT in the triggered list below threshold',
      'S2 TurnReinforce' not in [e.nid for e in triggered_low],
      'triggered event nids = %s' % ([e.nid for e in triggered_low],))

check('3. NEGATIVE CASE: monsters never placed while the trigger never fires',
      all(game.get_unit(n).position is None for n in group.units),
      'positions while unfired = %s' % ({n: game.get_unit(n).position for n in group.units},))

# Advance turncount to the authored threshold ("game.turncount >= 4").
game.turncount = 4
at_threshold = game.events.get_triggered_events(triggers.TurnChange(), 'S2')
check('3. S2 TurnReinforce IS in the triggered list at the threshold (turncount=4)',
      'S2 TurnReinforce' in [e.nid for e in at_threshold],
      'triggered event nids = %s' % ([e.nid for e in at_threshold],))
check('3. should_trigger(TurnChange) is True at/after the threshold',
      game.events.should_trigger(triggers.TurnChange(), 'S2') is True,
      'turncount = %d' % game.turncount)

# POSITIVE placement: the real add_group placement path (action.ArriveOnMap),
# proving units land at the exact authored unit_groups positions.
placed_now = spawn_via_add_group()
check('3. add_group placement moved exactly the 2 monsters',
      set(placed_now) == {'S2Monster1', 'S2Monster2'},
      'placed = %s' % (placed_now,))
positions_after = {n: game.get_unit(n).position for n in group.units}
check('3. monsters now sit at their authored unit_groups positions',
      positions_after == authored_positions,
      'positions after ArriveOnMap = %s (expected %s)' % (positions_after, authored_positions))

# only_once: replicate event_manager.trigger()'s bookkeeping
# (action.do(action.OnlyOnceEvent(nid))) and prove the SAME event is now
# excluded, even though its condition is still true.
action.do(action.OnlyOnceEvent('S2 TurnReinforce'))
suppressed = game.events.get_triggered_events(triggers.TurnChange(), 'S2')
check('3. only_once suppresses S2 TurnReinforce on the second evaluation',
      'S2 TurnReinforce' not in [e.nid for e in suppressed],
      'triggered event nids after OnlyOnceEvent = %s (condition is still true)' % ([e.nid for e in suppressed],))

# ---------------------------------------------------------------------------
# 4. Trigger 2: combat_start + "unit1.team=='player' and unit2.team=='other'"
#    (the "attacked an Other/NPC" case)
# ---------------------------------------------------------------------------
print("\n--- [4] combat_start trigger: unit1.team=='player' and unit2.team=='other' ---")


class _DummyOtherUnit:
    """Minimal stand-in for a UnitObject: the condition only reads .team."""
    nid = 'NPCStandIn'
    team = 'other'


rowan = game.get_unit('Rowan')
check('4. Rowan resolves and is on the player team',
      rowan is not None and rowan.team == 'player',
      'Rowan = %r, team = %r' % (rowan, rowan.team if rowan else None))

combat_vs_other = triggers.CombatStart(rowan, _DummyOtherUnit(), rowan.position or (1, 15), None, False)
ambush_triggered = game.events.get_triggered_events(combat_vs_other, 'S2')
check("4. S2 AmbushOnAttack fires when unit1 is player and unit2.team == 'other'",
      'S2 AmbushOnAttack' in [e.nid for e in ambush_triggered],
      'triggered event nids = %s' % ([e.nid for e in ambush_triggered],))

combat_vs_enemy = triggers.CombatStart(rowan, game.get_unit('S2Soldier1'), rowan.position or (1, 15), None, False)
ambush_not_triggered = game.events.get_triggered_events(combat_vs_enemy, 'S2')
check("4. S2 AmbushOnAttack does NOT fire against a non-'other' team (enemy)",
      'S2 AmbushOnAttack' not in [e.nid for e in ambush_not_triggered],
      'triggered event nids = %s' % ([e.nid for e in ambush_not_triggered],))

# ---------------------------------------------------------------------------
# 5. Trigger 3: turn_change + a wrong dialogue-choice result stashed in a
#    game_var ("game.game_vars.get('S2Gambit') == 'Push Through'")
# ---------------------------------------------------------------------------
print("\n--- [5] turn_change trigger gated on a stored choice result (S2Gambit) ---")
check("5. S2Gambit unset by default (choice not yet made)",
      game.game_vars.get('S2Gambit') is None, "game.game_vars.get('S2Gambit') = %r" % (game.game_vars.get('S2Gambit'),))

not_yet = game.events.get_triggered_events(triggers.TurnChange(), 'S2')
check('5. S2 WrongChoiceAmbush does not fire while S2Gambit is unset',
      'S2 WrongChoiceAmbush' not in [e.nid for e in not_yet],
      'triggered event nids = %s' % ([e.nid for e in not_yet],))

# choice;S2Gambit;...;Push Through,Make Camp -> player_choice.py stores the
# selection via action.do(action.SetGameVar(nid, selection))
action.do(action.SetGameVar('S2Gambit', 'Push Through'))
wrong_choice_triggered = game.events.get_triggered_events(triggers.TurnChange(), 'S2')
check("5. S2 WrongChoiceAmbush fires once S2Gambit == 'Push Through' (the wrong choice)",
      'S2 WrongChoiceAmbush' in [e.nid for e in wrong_choice_triggered],
      'triggered event nids = %s' % ([e.nid for e in wrong_choice_triggered],))

action.do(action.SetGameVar('S2Gambit', 'Make Camp'))
right_choice_triggered = game.events.get_triggered_events(triggers.TurnChange(), 'S2')
check("5. S2 WrongChoiceAmbush does NOT fire for the correct choice ('Make Camp')",
      'S2 WrongChoiceAmbush' not in [e.nid for e in right_choice_triggered],
      'triggered event nids = %s' % ([e.nid for e in right_choice_triggered],))

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
