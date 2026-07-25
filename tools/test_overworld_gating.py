#!/usr/bin/env python3
"""
Execution-based proof for issues #2 (overworld node unit-count/level entry
requirements) and #6 (Safe/Unsafe revisited nodes) -- driven directly
against the LT engine (no browser, no Playwright, no pygbag rebuild).

Bootstrap mirrors tools/test_capital_completion.py / tools/test_level_reentry.py
exactly (dummy SDL drivers, real DB/RESOURCES load, real GameState).

Run with:
  uv run --no-project --python 3.12 --with pygame-ce --with typing-extensions python tools/test_overworld_gating.py
"""
import os
import sys
import pickle
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import play_harness as harness
harness.boot()

from app.data.resources.resources import RESOURCES
from app.data.database.database import DB

from app.engine import game_state
from app.engine.game_state import GameState
from app.engine.generic_unit import create_generic_unit
from app.utilities import static_random


FAILURES = []


def check(label, condition, detail):
    status = 'PASS' if condition else 'FAIL'
    print('[%s] %s: %s' % (status, label, detail))
    if not condition:
        FAILURES.append('%s -- %s' % (label, detail))
    return condition


print('=' * 78)
print('OVERWORLD GATING -- EXECUTION-BASED PROOF (real DB / GameState / RNG calls)')
print('=' * 78)

# ---------------------------------------------------------------------------
# 1. Boot DB/RESOURCES, start S1 for real, build an OverworldManager for the
#    real "0" overworld out of overworlds.json.
# ---------------------------------------------------------------------------
print('\n--- [1] Boot DB/RESOURCES, game_state.start_level(\'S1\'), build OverworldManager ---')
# RESOURCES/DB already loaded and engine-chrome sprites/fonts already
# initialized by harness.boot() above.
game = game_state.start_level('S1')
check('1. start_level(S1)', game.level is not None and game.level.nid == 'S1',
      'game.level.nid = %r (expected S1)' % (game.level.nid if game.level else None))

from app.engine.overworld.overworld_manager import OverworldManager

overworld_obj = game.overworld_registry.get('0')
check('1. overworld "0" present in registry', overworld_obj is not None,
      'game.overworld_registry.keys() = %s' % list(game.overworld_registry.keys()))

manager = OverworldManager(overworld_obj, cursor=None, next_level='S1', camera=None)
check('1. OverworldManager built with real nodes', 'S3' in manager.nodes and 'S1' in manager.nodes,
      'manager.nodes.keys() = %s' % list(manager.nodes.keys()))


def clear_party():
    """Empties the party as far as get_units_in_party()/node_requirement_met()
    (both party == current_party filtered, per app/engine/game_state.py and
    app/engine/overworld/overworld_manager.py) are concerned, so each
    req_unit_count/req_unit_level probe below starts from a precisely
    controlled, empty party.

    Reassigns `.party` rather than deleting from game.unit_registry: S1's
    own level-authored units (Rowan/Iska) are never referenced by nid
    anywhere in this file -- they're incidental to loading a real level to
    get a real OverworldManager, not part of what's under test -- but they
    DO count towards get_units_in_party() like any other player unit, so
    leaving them at the real current_party would silently satisfy a low
    req_unit_level (e.g. the bug-3 fix's req_unit_level: 2 -- both start at
    internal level 2) without this test ever adding a single unit itself.
    Deleting them outright instead would crash the save/pickle/load round
    trip in section 8 below (LevelObject.restore() resolves game._current_level
    .units back through game.get_unit(), which needs them to still exist).
    """
    for unit in list(game.unit_registry.values()):
        if unit.team == 'player' and getattr(unit, '_test_added', False):
            del game.unit_registry[unit.nid]
    for unit in game.unit_registry.values():
        if unit.team == 'player':
            unit.party = '_test_bench'


def add_party_unit(nid, klass, level, internal_level_note=''):
    """Builds a real UnitObject (via the same GenericUnit -> UnitObject.from_prefab
    path app.engine.enemy_pool uses) at the given raw klass/level, then adjusts
    it to look like a player-party member (generic squad units aren't
    persistent by default) and registers it."""
    unit = create_generic_unit(nid, klass, level, 'player')
    unit.persistent = True
    unit.party = game.current_party
    unit.dead = False
    unit._test_added = True
    game.register_unit(unit)
    return unit


# ---------------------------------------------------------------------------
# 2. Backward compatibility: nodes without req_unit_count/req_unit_level in
#    overworlds.json load with req_unit_count == 0 and are always permitted,
#    regardless of party composition (even an empty party).
# ---------------------------------------------------------------------------
print('\n--- [2] Untouched nodes: req_unit_count defaults to 0, always permitted ---')
clear_party()
untouched_node = manager.nodes['S1']
check('2. S1 node req_unit_count defaults to 0',
      untouched_node.prefab.req_unit_count == 0,
      'S1 node.prefab.req_unit_count = %r' % (untouched_node.prefab.req_unit_count,))
check('2. S1 node req_unit_level defaults to 1',
      untouched_node.prefab.req_unit_level == 1,
      'S1 node.prefab.req_unit_level = %r' % (untouched_node.prefab.req_unit_level,))
check('2. S1 node always permitted, even with an empty party',
      manager.node_requirement_met(untouched_node) is True,
      'manager.node_requirement_met(S1) = %r with 0 party units' %
      (manager.node_requirement_met(untouched_node),))

for other_nid in ('CAPITAL', 'S2', 'SHUB', 'S4', 'S5'):
    node = manager.nodes[other_nid]
    check('2. %s node also untouched (req_unit_count 0)' % other_nid,
          node.prefab.req_unit_count == 0,
          '%s node.prefab.req_unit_count = %r' % (other_nid, node.prefab.req_unit_count))

# ---------------------------------------------------------------------------
# 3. S3 node (authored in overworlds.json with req_unit_count: 2,
#    req_unit_level: 2) is refused with one qualifying unit and permitted
#    with two -- proves the field round-trips out of real project JSON.
#
#    req_unit_level was originally shipped as 5, which tools/test_playthrough.py
#    (a real state-machine playthrough) proved unreachable through normal
#    CAPITAL -> S1 -> S2 progression: only the protagonist reliably reaches
#    internal level 5 that early, so the only way to pass this gate was
#    grinding the first fight repeatedly. Lowered to 2 -- comfortably cleared
#    by at least two party members after a normal, non-grinding clear of the
#    first two chapters, per tools/test_playthrough.py's recorded levels --
#    while still requiring the party to have actually fought.
# ---------------------------------------------------------------------------
print('\n--- [3] S3 node requires 2 units at internal level >= 2 ---')
s3_node = manager.nodes['S3']
check('3. S3 node req_unit_count == 2 (round-tripped from overworlds.json)',
      s3_node.prefab.req_unit_count == 2,
      'S3 node.prefab.req_unit_count = %r' % (s3_node.prefab.req_unit_count,))
check('3. S3 node req_unit_level == 2 (round-tripped from overworlds.json, reachable through normal play)',
      s3_node.prefab.req_unit_level == 2,
      'S3 node.prefab.req_unit_level = %r' % (s3_node.prefab.req_unit_level,))

clear_party()
check('3. S3 refused with zero qualifying units',
      manager.node_requirement_met(s3_node) is False,
      'manager.node_requirement_met(S3) = %r with 0 party units' % (manager.node_requirement_met(s3_node),))

add_party_unit('TestGrunt1', 'Mercenary', 5)
check('3. S3 still refused with only ONE qualifying unit',
      manager.node_requirement_met(s3_node) is False,
      'manager.node_requirement_met(S3) = %r with 1 qualifying unit (need 2)' %
      (manager.node_requirement_met(s3_node),))

add_party_unit('TestGrunt2', 'Mercenary', 5)
check('3. S3 permitted with TWO qualifying units',
      manager.node_requirement_met(s3_node) is True,
      'manager.node_requirement_met(S3) = %r with 2 qualifying units' %
      (manager.node_requirement_met(s3_node),))

# ---------------------------------------------------------------------------
# 4. A PROMOTED unit whose raw `level` reset (post-promotion) to 1 still
#    counts towards the requirement via get_internal_level(). This is the
#    assertion that catches a naive `unit.level >= req_unit_level`
#    implementation, which would wrongly exclude this unit.
# ---------------------------------------------------------------------------
print('\n--- [4] Promoted unit (raw level reset to 1) still counts via get_internal_level() ---')
clear_party()
# Vanguard (tier 2) promotes_from Mercenary (tier 1, max_level 10). A freshly
# promoted unit's raw level resets to 1, but get_internal_level() = level +
# sum of promoted-from tiers' max_level = 1 + 10 = 11.
promoted_unit = add_party_unit('TestPromoted', 'Vanguard', 1)
check('4. promoted unit raw level is 1 (post-promotion reset)',
      promoted_unit.level == 1,
      'promoted_unit.level = %r' % (promoted_unit.level,))
check('4. promoted unit raw level alone would FAIL the req_unit_level=%d check' % s3_node.prefab.req_unit_level,
      promoted_unit.level < s3_node.prefab.req_unit_level,
      'promoted_unit.level = %r (< %r, so a naive unit.level check would wrongly exclude it)' %
      (promoted_unit.level, s3_node.prefab.req_unit_level))
check('4. promoted unit get_internal_level() is >= %d (1 + Mercenary max_level 10 = 11)' % s3_node.prefab.req_unit_level,
      promoted_unit.get_internal_level() >= s3_node.prefab.req_unit_level,
      'promoted_unit.get_internal_level() = %r (expected >= %r)' %
      (promoted_unit.get_internal_level(), s3_node.prefab.req_unit_level))

# Alone, one promoted unit still isn't enough for S3's req_unit_count of 2.
check('4. S3 still refused with only the ONE promoted unit (need 2)',
      manager.node_requirement_met(s3_node) is False,
      'manager.node_requirement_met(S3) = %r with 1 promoted unit' % (manager.node_requirement_met(s3_node),))

add_party_unit('TestGrunt3', 'Mercenary', 5)
check('4. S3 permitted once the promoted unit + one more qualifying unit are both present',
      manager.node_requirement_met(s3_node) is True,
      'manager.node_requirement_met(S3) = %r with promoted unit + 1 more qualifying unit' %
      (manager.node_requirement_met(s3_node),))

clear_party()

# ---------------------------------------------------------------------------
# 5. Safe/Unsafe roll is cached: calling get_node_safety twice for the same
#    level nid returns the same outcome and does NOT re-roll (other_random
#    state is unchanged on the second call).
# ---------------------------------------------------------------------------
print('\n--- [5] Safe/Unsafe roll is cached, does not re-roll on a second call ---')
game.game_vars.pop('_node_safety', None)
game.game_vars.pop('_pending_unsafe_encounter', None)

first_outcome = manager.get_node_safety('S1')
check('5. first roll for S1 produced a Safe/Unsafe outcome',
      first_outcome in ('Safe', 'Unsafe'),
      "manager.get_node_safety('S1') (1st call) = %r" % (first_outcome,))
check('5. outcome cached in game_vars[_node_safety][S1]',
      game.game_vars.get('_node_safety', {}).get('S1') == first_outcome,
      "game_vars['_node_safety'] = %r" % (game.game_vars.get('_node_safety'),))

other_random_state_after_first = static_random.get_other_random_state()
second_outcome = manager.get_node_safety('S1')
other_random_state_after_second = static_random.get_other_random_state()

check('5. second call for the SAME level nid returns the identical cached outcome',
      second_outcome == first_outcome,
      'first=%r, second=%r (must match -- no re-roll)' % (first_outcome, second_outcome))
check('5. second call did NOT advance the other_random stream (no re-roll happened)',
      other_random_state_after_second == other_random_state_after_first,
      'other_random state after 1st call=%r, after 2nd call=%r (must be identical)' %
      (other_random_state_after_first, other_random_state_after_second))

# ---------------------------------------------------------------------------
# 6. combat_random is completely unaffected by 100 safety rolls (fresh level
#    nids each time, to guarantee 100 actual rolls rather than cache hits).
#    Safety rolls MUST go through get_random_weighted_choice (other_random),
#    never static_random.get_randint (combat_random) -- desyncing combat
#    would break turnwheel replay.
# ---------------------------------------------------------------------------
print('\n--- [6] combat_random stream is unchanged by 100 safety rolls ---')
combat_random_state_before = static_random.get_combat_random_state()
for i in range(100):
    manager.get_node_safety('SafetyTestLevel_%d' % i)
combat_random_state_after = static_random.get_combat_random_state()

check('6. combat_random state unchanged after 100 safety rolls',
      combat_random_state_after == combat_random_state_before,
      'combat_random state before=%r, after=%r (must be identical)' %
      (combat_random_state_before, combat_random_state_after))

# ---------------------------------------------------------------------------
# 7. An Unsafe outcome sets game_vars['_pending_unsafe_encounter']; a Safe
#    outcome does not (checked via a deterministic seed sweep since the roll
#    is random -- we just need at least one of each across the 100 rolls
#    above, and that pending_unsafe_encounter always names a levels that
#    actually rolled Unsafe).
# ---------------------------------------------------------------------------
print('\n--- [7] _pending_unsafe_encounter reflects an Unsafe roll ---')
node_safety = game.game_vars.get('_node_safety', {})
safety_test_results = {nid: outcome for nid, outcome in node_safety.items() if nid.startswith('SafetyTestLevel_')}
unsafe_nids = [nid for nid, outcome in safety_test_results.items() if outcome == 'Unsafe']
safe_nids = [nid for nid, outcome in safety_test_results.items() if outcome == 'Safe']
check('7. 100 safety rolls produced at least one Safe and one Unsafe result',
      len(unsafe_nids) > 0 and len(safe_nids) > 0,
      'unsafe count=%d, safe count=%d (out of %d)' % (len(unsafe_nids), len(safe_nids), len(safety_test_results)))

if unsafe_nids:
    game.game_vars.pop('_pending_unsafe_encounter', None)
    manager.get_node_safety(unsafe_nids[0])
    check('7. re-selecting a cached Unsafe node sets _pending_unsafe_encounter to that level nid',
          game.game_vars.get('_pending_unsafe_encounter') == unsafe_nids[0],
          "game_vars['_pending_unsafe_encounter'] = %r (expected %r)" %
          (game.game_vars.get('_pending_unsafe_encounter'), unsafe_nids[0]))

if safe_nids:
    game.game_vars['_pending_unsafe_encounter'] = None
    manager.get_node_safety(safe_nids[0])
    check('7. re-selecting a cached Safe node leaves _pending_unsafe_encounter unset',
          game.game_vars.get('_pending_unsafe_encounter') is None,
          "game_vars['_pending_unsafe_encounter'] = %r (expected None)" %
          (game.game_vars.get('_pending_unsafe_encounter'),))

# ---------------------------------------------------------------------------
# 8. `_node_safety` survives a save -> pickle round trip -> fresh
#    GameState().load() (mirrors tools/test_level_reentry.py's proof for
#    `_cleared_levels`).
# ---------------------------------------------------------------------------
print('\n--- [8] _node_safety survives save/pickle/load round trip ---')
game.game_vars['_node_safety'] = {'S1': 'Safe', 'S2': 'Unsafe'}
game.game_vars['_pending_unsafe_encounter'] = 'S2'
pre_save_node_safety = dict(game.game_vars['_node_safety'])

s_dict, meta_dict = game.save()

tmp_fd, tmp_path = tempfile.mkstemp(prefix='lt_overworld_gating_test_', suffix='.p')
os.close(tmp_fd)
try:
    with open(tmp_path, 'wb') as fp:
        pickle.dump(s_dict, fp)
    with open(tmp_path, 'rb') as fp:
        loaded_s_dict = pickle.load(fp)
finally:
    os.remove(tmp_path)

fresh_game = GameState()
fresh_game.build_new()
fresh_game.load(loaded_s_dict)

post_load_node_safety = fresh_game.game_vars.get('_node_safety')
check('8. _node_safety round-trips through save/pickle/load intact',
      post_load_node_safety == pre_save_node_safety,
      "pre-save _node_safety=%r, post-load _node_safety=%r" %
      (pre_save_node_safety, post_load_node_safety))
check('8. _pending_unsafe_encounter round-trips through save/pickle/load intact',
      fresh_game.game_vars.get('_pending_unsafe_encounter') == 'S2',
      "post-load _pending_unsafe_encounter=%r (expected 'S2')" %
      (fresh_game.game_vars.get('_pending_unsafe_encounter'),))

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
