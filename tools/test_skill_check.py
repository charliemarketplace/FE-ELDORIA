#!/usr/bin/env python3
"""
Execution-based proof for the non-combat Skill Check feature (issue #17) --
driven directly against the LT engine (no browser, no Playwright, no pygbag
rebuild).

Bootstrap mirrors tools/test_capital_completion.py exactly (dummy SDL
drivers, real DB/RESOURCES load, real GameState, engine_sprites.load_images()
quirk workaround, real game_state.start_level()).

Covers:
  - SkillCheckAbility.targets() is empty with no registered pair, and
    contains exactly the registered target's position once one is added.
  - A pinned seed produces a deterministic pass and a deterministic fail
    across the DC (same natural roll both times; only the DC differs).
  - SkillCheckAbility.do() actually fires the `on_skill_check` trigger
    (triggers.OnSkillCheck), carrying the roll result.
  - action.AddSkillCheck / action.RemoveSkillCheck are turnwheel-reversible
    (do() then reverse() restores the registry exactly).
  - 100 skill checks leave app.utilities.static_random's combat_random state
    byte-for-byte unchanged (roll_d20 must only ever touch other_random).

Run with:
  uv run --no-project --python 3.12 --with pygame-ce --with typing-extensions python tools/test_skill_check.py
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
from app.engine import equations
from app.engine import game_state
from app.engine import abilities
from app.events import triggers
from app.utilities import static_random
import app.engine.sprites as engine_sprites


FAILURES = []


def check(label, condition, detail):
    status = 'PASS' if condition else 'FAIL'
    print('[%s] %s: %s' % (status, label, detail))
    if not condition:
        FAILURES.append('%s -- %s' % (label, detail))
    return condition


print('=' * 78)
print('SKILL CHECK -- EXECUTION-BASED PROOF (real action.do() / DB / trigger calls)')
print('=' * 78)

# ---------------------------------------------------------------------------
# 0. Boot DB/RESOURCES, start S1 for real (same quirk-workaround as
#    tools/test_capital_completion.py -- RESOURCES.load() resets
#    app.sprites.SPRITES without re-running app.engine.sprites.load_images(),
#    so engine-chrome sprites crash on import unless this is re-run first).
# ---------------------------------------------------------------------------
print('\n--- [0] Boot DB/RESOURCES, game_state.start_level(\'S1\') ---')
RESOURCES.load('lion_throne.ltproj', CURRENT_SERIALIZATION_VERSION)
DB.load('lion_throne.ltproj', CURRENT_SERIALIZATION_VERSION)
engine_sprites.load_images()
game = game_state.start_level('S1')
check('0. start_level(S1)', game.level is not None and game.level.nid == 'S1',
      'game.level.nid = %r (expected S1)' % (game.level.nid if game.level else None))

# S1's levels.json placement puts Rowan at (2, 9) and Iska at (3, 9) --
# adjacent, both team='player'.
rowan = game.get_unit('Rowan')
iska = game.get_unit('Iska')
check('0. Rowan and Iska are placed and adjacent',
      bool(rowan and iska and rowan.position and iska.position and
           abs(rowan.position[0] - iska.position[0]) + abs(rowan.position[1] - iska.position[1]) == 1),
      'rowan.position=%r, iska.position=%r' % (rowan.position if rowan else None, iska.position if iska else None))

# ---------------------------------------------------------------------------
# 1. DB.equations has PERSUASION = SKL + LCK, and equations.parser exposes it
#    (lowercased) the same way HIT/AVOID/etc. are exposed.
# ---------------------------------------------------------------------------
print('\n--- [1] PERSUASION equation is registered and computable ---')
check('1. DB.equations has PERSUASION', 'PERSUASION' in DB.equations,
      'DB.equations nids = %s' % [e.nid for e in DB.equations])

rowan_persuasion = equations.parser.persuasion(rowan)
expected_rowan_persuasion = rowan.stats['SKL'] + rowan.stat_bonus('SKL') + rowan.stats['LCK'] + rowan.stat_bonus('LCK')
check('1. equations.parser.persuasion(rowan) == SKL + LCK',
      rowan_persuasion == expected_rowan_persuasion,
      'persuasion=%r, expected SKL+LCK=%r' % (rowan_persuasion, expected_rowan_persuasion))

# ---------------------------------------------------------------------------
# 2. SkillCheckAbility.targets(): absent with no registered pair, present
#    with exactly one once AddSkillCheck registers it.
# ---------------------------------------------------------------------------
print('\n--- [2] SkillCheckAbility.targets(): absent, then present ---')
check('2. no skill check registered yet -> find_skill_check is None',
      action.find_skill_check('Rowan', 'Iska') is None,
      "action.find_skill_check('Rowan', 'Iska') = %r" % (action.find_skill_check('Rowan', 'Iska'),))
check('2. targets(rowan) is empty with nothing registered',
      abilities.SkillCheckAbility.targets(rowan) == set(),
      'targets = %r' % (abilities.SkillCheckAbility.targets(rowan),))

INITIAL_DC = 12
action.do(action.AddSkillCheck('Rowan', 'Iska', INITIAL_DC))
check('2. find_skill_check returns the registered DC',
      action.find_skill_check('Rowan', 'Iska') == INITIAL_DC,
      "action.find_skill_check('Rowan', 'Iska') = %r (expected %r)" % (action.find_skill_check('Rowan', 'Iska'), INITIAL_DC))
check('2. targets(rowan) now contains exactly Iska\'s position',
      abilities.SkillCheckAbility.targets(rowan) == {iska.position},
      'targets = %r (expected {%r})' % (abilities.SkillCheckAbility.targets(rowan), iska.position))
check('2. targets(iska) does NOT contain Rowan (one-directional, like Talk)',
      rowan.position not in abilities.SkillCheckAbility.targets(iska),
      'targets(iska) = %r' % (abilities.SkillCheckAbility.targets(iska),))

# ---------------------------------------------------------------------------
# 3. Turnwheel-reversibility of AddSkillCheck / RemoveSkillCheck, independent
#    of any particular unit pair (registry-level correctness).
# ---------------------------------------------------------------------------
print('\n--- [3] AddSkillCheck / RemoveSkillCheck are turnwheel-reversible ---')
pre_snapshot = action.get_skill_check_options()

add_action = action.AddSkillCheck('Draven', 'S1Soldier1', 15)
add_action.do()
check('3. AddSkillCheck.do() adds the entry',
      action.find_skill_check('Draven', 'S1Soldier1') == 15,
      "find_skill_check('Draven', 'S1Soldier1') = %r (expected 15)" % (action.find_skill_check('Draven', 'S1Soldier1'),))
add_action.reverse()
check('3. AddSkillCheck.reverse() restores the pre-add registry exactly',
      action.get_skill_check_options() == pre_snapshot,
      'post-reverse registry = %r (expected %r)' % (action.get_skill_check_options(), pre_snapshot))

remove_action = action.RemoveSkillCheck('Rowan', 'Iska')
remove_action.do()
check('3. RemoveSkillCheck.do() removes the entry',
      action.find_skill_check('Rowan', 'Iska') is None,
      "find_skill_check('Rowan', 'Iska') = %r (expected None)" % (action.find_skill_check('Rowan', 'Iska'),))
remove_action.reverse()
check('3. RemoveSkillCheck.reverse() restores the removed entry',
      action.find_skill_check('Rowan', 'Iska') == INITIAL_DC,
      "find_skill_check('Rowan', 'Iska') = %r (expected %r)" % (action.find_skill_check('Rowan', 'Iska'), INITIAL_DC))

# ---------------------------------------------------------------------------
# 4. Deterministic pass / fail across the DC under a pinned seed, and the
#    on_skill_check trigger firing with the roll result -- driven through
#    the real SkillCheckAbility.do() (game.cursor + game.board wired up
#    exactly as the real 'targeting' state would leave them).
# ---------------------------------------------------------------------------
print('\n--- [4] Deterministic pass/fail via SkillCheckAbility.do(), on_skill_check fires ---')
SEED = 918273

# Predict the natural this seed produces, via the exact same call shape
# SkillCheckAbility.do() will make (unit=rowan, no dc yet) -- mirrors the
# reproducibility technique in tools/test_alignment_d20_tier.py section 6.
static_random.set_seed(SEED)
game.game_vars['_random_seed'] = SEED
predicted_natural = game.query_engine.roll_d20(unit=rowan)['natural']
predicted_total = predicted_natural + rowan_persuasion

captured_triggers = []
real_trigger = game.events.trigger


def spy_trigger(trig, level_nid=None):
    captured_triggers.append(trig)
    return real_trigger(trig, level_nid)


game.events.trigger = spy_trigger

def run_skill_check(dc):
    action.do(action.RemoveSkillCheck('Rowan', 'Iska'))
    action.do(action.AddSkillCheck('Rowan', 'Iska', dc))
    game.cursor.position = iska.position
    static_random.set_seed(SEED)
    game.game_vars['_random_seed'] = SEED
    abilities.SkillCheckAbility.do(rowan)
    return captured_triggers[-1]

# --- Pass case: DC set exactly at the predicted total -> success (total >= dc).
pass_trigger = run_skill_check(predicted_total)
check('4. on_skill_check fired for the pass case', isinstance(pass_trigger, triggers.OnSkillCheck),
      'captured trigger = %r' % (pass_trigger,))
check('4. pass case: same seed reproduces the same natural roll',
      pass_trigger.result['natural'] == predicted_natural,
      "result['natural'] = %r (expected %r)" % (pass_trigger.result['natural'], predicted_natural))
check('4. pass case: result[\'success\'] is True (total >= dc)',
      pass_trigger.result['success'] is True,
      'result = %r' % (pass_trigger.result,))
check('4. pass case: unit1/unit2/position carried correctly',
      pass_trigger.unit1 is rowan and pass_trigger.unit2 is iska and pass_trigger.position == rowan.position,
      'unit1=%r, unit2=%r, position=%r' % (pass_trigger.unit1, pass_trigger.unit2, pass_trigger.position))

game.state.temp_state.clear()  # SkillCheckAbility.do() calls game.state.back(); keep it from piling up

# --- Fail case: DC one above the predicted total -> fail (total < dc).
fail_trigger = run_skill_check(predicted_total + 1)
check('4. fail case: same seed reproduces the same natural roll',
      fail_trigger.result['natural'] == predicted_natural,
      "result['natural'] = %r (expected %r)" % (fail_trigger.result['natural'], predicted_natural))
check('4. fail case: result[\'success\'] is False (total < dc)',
      fail_trigger.result['success'] is False,
      'result = %r' % (fail_trigger.result,))

game.state.temp_state.clear()
game.events.trigger = real_trigger  # un-spy

# ---------------------------------------------------------------------------
# 5. STREAM ISOLATION -- combat_random must be completely unaffected by 100
#    skill checks (roll_d20 draws only from other_random). Mirrors
#    tools/test_alignment_d20_tier.py section 7.
# ---------------------------------------------------------------------------
print('\n--- [5] STREAM ISOLATION -- combat_random state unchanged by 100 skill checks ---')
action.do(action.RemoveSkillCheck('Rowan', 'Iska'))
action.do(action.AddSkillCheck('Rowan', 'Iska', 10))
combat_state_before = static_random.get_combat_random_state()
for _ in range(100):
    game.cursor.position = iska.position
    abilities.SkillCheckAbility.do(rowan)
    action.do(action.AddSkillCheck('Rowan', 'Iska', 10))  # do() re-fires each loop
    game.state.temp_state.clear()
combat_state_after = static_random.get_combat_random_state()
check('5. combat_random state UNCHANGED by 100 skill checks',
      combat_state_before == combat_state_after,
      'combat_state_before=%r, combat_state_after=%r' % (combat_state_before, combat_state_after))

# ---------------------------------------------------------------------------
# 6. The `add_skill_check`/`remove_skill_check` event commands actually
#    dispatch, end to end, exactly the way a real event does: parse the
#    text line (event_commands.parse_text_to_command), convert its string
#    parameters to typed values (event_commands.convert_parse), camel_to_snake
#    the parameter keys (as Event.run_command does), and look up the
#    implementation in app.events.function_catalog.get_catalog() -- proving
#    the event_functions module-attachment wiring in event_commands.py
#    (_wire_skill_check_dispatch) actually lands the two functions where
#    function_catalog's inspect.getmembers scan will find them.
# ---------------------------------------------------------------------------
print('\n--- [6] add_skill_check / remove_skill_check event commands dispatch end to end ---')
import logging as _logging
from app.events import event_commands
from app.events.function_catalog import get_catalog
from app.utilities import str_utils


class _FakeEventSelf:
    """Just enough of an Event to satisfy _add_skill_check/_remove_skill_check's
    use of self._get_unit and self.logger -- avoids constructing a real
    app.events.event.Event, which needs a live EventPrefab/processor."""
    def __init__(self, g):
        self._game = g
        self.logger = _logging.getLogger('test_skill_check')

    def _get_unit(self, nid):
        return self._game.get_unit(nid)


def dispatch_event_line(line):
    command, err_idx = event_commands.parse_text_to_command(line, strict=True)
    parameters, flags = event_commands.convert_parse(command, None)
    parameters = {str_utils.camel_to_snake(k): v for k, v in parameters.items()}
    get_catalog()[command.nid](_FakeEventSelf(game), **parameters, flags=flags)
    return command


action.do(action.RemoveSkillCheck('Rowan', 'Iska'))

add_command = dispatch_event_line('add_skill_check;Rowan;Iska;13')
check('6. add_skill_check;Rowan;Iska;13 parses to the AddSkillCheck command',
      isinstance(add_command, event_commands.AddSkillCheck),
      'parsed command class = %r' % (type(add_command),))
check('6. add_skill_check event command registers the pair with DC=13 as an int',
      action.find_skill_check('Rowan', 'Iska') == 13,
      "find_skill_check('Rowan', 'Iska') = %r (expected 13)" % (action.find_skill_check('Rowan', 'Iska'),))

remove_command = dispatch_event_line('remove_skill_check;Rowan;Iska')
check('6. remove_skill_check event command removes the pair',
      action.find_skill_check('Rowan', 'Iska') is None,
      "find_skill_check('Rowan', 'Iska') = %r (expected None)" % (action.find_skill_check('Rowan', 'Iska'),))

# DC omitted -> defaults to 12, per add_skill_check's desc.
dispatch_event_line('add_skill_check;Rowan;Iska')
check('6. add_skill_check with DC omitted defaults to 12',
      action.find_skill_check('Rowan', 'Iska') == 12,
      "find_skill_check('Rowan', 'Iska') = %r (expected 12)" % (action.find_skill_check('Rowan', 'Iska'),))
action.do(action.RemoveSkillCheck('Rowan', 'Iska'))

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
