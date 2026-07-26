#!/usr/bin/env python3
"""
Execution-based proof for three engine additions:
  - GameQueryEngine.check_alignment (issue #8)
  - GameQueryEngine.roll_d20 (issue #18)
  - item_components.base_components.Tier (issue #19)

Follows the exact headless-bootstrap pattern of tools/test_capital_completion.py
(sys.frozen=True, SDL dummy drivers, RESOURCES.load/DB.load, a real display
surface, engine_sprites.load_images(), then game_state.start_level('CAPITAL')).
Nothing here is an existence check on JSON data -- every assertion drives real
engine state (game_vars, static_random streams, action.do/save/pickle/load,
condition-string evaluation via app.engine.evaluate) and asserts a real
before/after difference or invariant.

Run with:
  uv run --no-project --python 3.12 --with pygame-ce --with typing-extensions python tools/test_alignment_d20_tier.py
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

from app.engine import action
from app.engine import evaluate
from app.engine import game_state
from app.engine.game_state import GameState
from app.utilities import static_random


FAILURES = []


def check(label, condition, detail):
    status = 'PASS' if condition else 'FAIL'
    print('[%s] %s: %s' % (status, label, detail))
    if not condition:
        FAILURES.append('%s -- %s' % (label, detail))
    return condition


print('=' * 78)
print('ALIGNMENT / D20 / TIER -- EXECUTION-BASED PROOF')
print('=' * 78)

# ---------------------------------------------------------------------------
# 0. Boot DB/RESOURCES, start CAPITAL for real (same quirk-workaround as
#    tools/test_capital_completion.py -- RESOURCES.load() resets app.sprites'
#    SPRITES dict, so engine_sprites.load_images() must be re-run before any
#    module that reads SPRITES.get(...).convert_alpha() at import/class-def
#    time gets imported transitively by game_state.start_level()).
# ---------------------------------------------------------------------------
print('\n--- [0] Boot DB/RESOURCES, game_state.start_level(\'CAPITAL\') ---')
# RESOURCES/DB already loaded and engine-chrome sprites/fonts already
# initialized by harness.boot() above.
game = game_state.start_level('CAPITAL')
check('0. start_level(CAPITAL)', game.level is not None and game.level.nid == 'CAPITAL',
      'game.level.nid = %r (expected CAPITAL)' % (game.level.nid if game.level else None))

# ---------------------------------------------------------------------------
# 1. Alignment axes default to 0
# ---------------------------------------------------------------------------
print('\n--- [1] Alignment axes default to 0 ---')
lc_default = game.query_engine.check_alignment('lawful_chaotic')
ge_default = game.query_engine.check_alignment('good_evil')
check('1. lawful_chaotic defaults to 0', lc_default == 0, 'check_alignment(\'lawful_chaotic\') = %r' % lc_default)
check('1. good_evil defaults to 0', ge_default == 0, 'check_alignment(\'good_evil\') = %r' % ge_default)

# ---------------------------------------------------------------------------
# 2. Setting the game_var moves check_alignment, AND is reachable from a raw
#    condition string via app.engine.evaluate.evaluate -- this is the proof
#    that GameQueryEngine.check_alignment actually reaches the func_dict merge
#    at evaluate.py's get_context() (temp_globals.update(game.query_engine.func_dict)),
#    not just as a directly-called Python method.
# ---------------------------------------------------------------------------
print('\n--- [2] check_alignment reachable from raw condition string via evaluate.evaluate ---')
action.do(action.SetGameVar('alignment_good_evil', 3))
direct_value = game.query_engine.check_alignment('good_evil')
check('2. direct call reflects the written game_var', direct_value == 3,
      'check_alignment(\'good_evil\') = %r (expected 3)' % direct_value)

eval_result = evaluate.evaluate("check_alignment('good_evil') >= 3", game=game)
check('2. evaluate.evaluate("check_alignment(\'good_evil\') >= 3") is True',
      eval_result is True,
      'evaluate.evaluate(...) = %r' % eval_result)

eval_result_false = evaluate.evaluate("check_alignment('good_evil') >= 4", game=game)
check('2. evaluate.evaluate("check_alignment(\'good_evil\') >= 4") is False',
      eval_result_false is False,
      'evaluate.evaluate(...) = %r' % eval_result_false)

# ---------------------------------------------------------------------------
# 3. Clamping at +10/-10, and in-range passthrough
# ---------------------------------------------------------------------------
print('\n--- [3] Clamping behavior ---')
action.do(action.SetGameVar('alignment_good_evil', 999))
clamped_high = game.query_engine.check_alignment('good_evil')
check('3. clamps at +10', clamped_high == 10, 'check_alignment(\'good_evil\') = %r (expected 10)' % clamped_high)

action.do(action.SetGameVar('alignment_good_evil', -999))
clamped_low = game.query_engine.check_alignment('good_evil')
check('3. clamps at -10', clamped_low == -10, 'check_alignment(\'good_evil\') = %r (expected -10)' % clamped_low)

action.do(action.SetGameVar('alignment_lawful_chaotic', -7))
in_range = game.query_engine.check_alignment('lawful_chaotic')
check('3. in-range value passes through unchanged', in_range == -7,
      'check_alignment(\'lawful_chaotic\') = %r (expected -7)' % in_range)

# ---------------------------------------------------------------------------
# 4. Unknown axis raises ValueError, both directly and through evaluate
# ---------------------------------------------------------------------------
print('\n--- [4] Unknown axis raises ValueError ---')
raised_direct = False
try:
    game.query_engine.check_alignment('chaos_evil_typo')
except ValueError:
    raised_direct = True
check('4. direct call raises ValueError on unknown axis', raised_direct,
      'raised_direct = %r' % raised_direct)

raised_via_eval = False
try:
    evaluate.evaluate("check_alignment('chaos_evil_typo')", game=game)
except ValueError:
    raised_via_eval = True
check('4. evaluate.evaluate(...) raises ValueError on unknown axis', raised_via_eval,
      'raised_via_eval = %r' % raised_via_eval)

# ---------------------------------------------------------------------------
# 5. Alignment survives a save/pickle/load round trip into a fresh GameState
#    (same pattern as tools/test_capital_completion.py section 7).
# ---------------------------------------------------------------------------
print('\n--- [5] Alignment survives save -> pickle round trip -> fresh GameState().load() ---')
action.do(action.SetGameVar('alignment_good_evil', 6))
action.do(action.SetGameVar('alignment_lawful_chaotic', -4))
pre_save_good_evil = game.query_engine.check_alignment('good_evil')
pre_save_lawful_chaotic = game.query_engine.check_alignment('lawful_chaotic')

s_dict, meta_dict = game.save()

tmp_fd, tmp_path = tempfile.mkstemp(prefix='lt_alignment_test_', suffix='.p')
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

post_load_good_evil = fresh_game.query_engine.check_alignment('good_evil')
post_load_lawful_chaotic = fresh_game.query_engine.check_alignment('lawful_chaotic')
check('5. good_evil axis round-trips', post_load_good_evil == pre_save_good_evil == 6,
      'pre-save=%r, post-load=%r (expected 6)' % (pre_save_good_evil, post_load_good_evil))
check('5. lawful_chaotic axis round-trips', post_load_lawful_chaotic == pre_save_lawful_chaotic == -4,
      'pre-save=%r, post-load=%r (expected -4)' % (pre_save_lawful_chaotic, post_load_lawful_chaotic))

# ---------------------------------------------------------------------------
# 6. roll_d20 reproducibility under a pinned seed, and 1..20 range over many draws
# ---------------------------------------------------------------------------
print('\n--- [6] roll_d20 reproducibility and range ---')
static_random.set_seed(12345)
game.game_vars['_random_seed'] = 12345
seq_a = [game.query_engine.roll_d20()['natural'] for _ in range(50)]

static_random.set_seed(12345)
game.game_vars['_random_seed'] = 12345
seq_b = [game.query_engine.roll_d20()['natural'] for _ in range(50)]

check('6. roll_d20 reproducible under pinned seed', seq_a == seq_b,
      'seq_a[:10]=%s, seq_b[:10]=%s' % (seq_a[:10], seq_b[:10]))

naturals_500 = [game.query_engine.roll_d20()['natural'] for _ in range(500)]
in_range = all(1 <= n <= 20 for n in naturals_500)
check('6. natural always in 1..20 over 500 draws', in_range,
      'min=%r, max=%r' % (min(naturals_500), max(naturals_500)))
check('6. both 1 and 20 occur over 500 draws', 1 in naturals_500 and 20 in naturals_500,
      '1 in results = %r, 20 in results = %r' % (1 in naturals_500, 20 in naturals_500))

# Spot-check band/success/total semantics
crit_fail_roll = next(r for r in (game.query_engine.roll_d20(dc=15) for _ in range(2000)) if r['natural'] == 1)
check('6. natural 1 bands as crit_fail', crit_fail_roll['band'] == 'crit_fail',
      'roll = %r' % crit_fail_roll)
crit_success_roll = next(r for r in (game.query_engine.roll_d20(dc=15) for _ in range(2000)) if r['natural'] == 20)
check('6. natural 20 bands as crit_success', crit_success_roll['band'] == 'crit_success',
      'roll = %r' % crit_success_roll)

no_dc_roll = game.query_engine.roll_d20(modifier=3)
check('6. success is None when dc is None', no_dc_roll['success'] is None,
      'roll = %r' % no_dc_roll)
check('6. total == natural + modifier', no_dc_roll['total'] == no_dc_roll['natural'] + 3,
      'roll = %r' % no_dc_roll)

# Previously-contradictory combinations: a natural 1 must always fail (even
# when a huge modifier would otherwise beat the DC), and a natural 20 must
# always succeed (even against a DC no modifier could realistically beat).
# 'success' and 'band' must always agree.
nat1_huge_modifier = next(r for r in (game.query_engine.roll_d20(modifier=100, dc=15) for _ in range(4000)) if r['natural'] == 1)
check('6. natural 1 with a huge modifier still fails (tabletop crit-fail overrides the DC)',
      nat1_huge_modifier['success'] is False and nat1_huge_modifier['band'] == 'crit_fail',
      'roll = %r' % nat1_huge_modifier)

nat20_impossible_dc = next(r for r in (game.query_engine.roll_d20(modifier=0, dc=1000) for _ in range(4000)) if r['natural'] == 20)
check('6. natural 20 against an impossible DC still succeeds (tabletop crit-success overrides the DC)',
      nat20_impossible_dc['success'] is True and nat20_impossible_dc['band'] == 'crit_success',
      'roll = %r' % nat20_impossible_dc)

# ---------------------------------------------------------------------------
# 7. STREAM ISOLATION -- roll_d20 must draw exclusively from the other_random
#    (turnwheel-safe) stream, and must NEVER touch combat_random. This is the
#    critical assertion: using static_random.get_randint / game.get_random
#    against the wrong stream would silently desync combat replay.
# ---------------------------------------------------------------------------
print('\n--- [7] STREAM ISOLATION -- combat_random state unchanged by roll_d20 ---')
combat_state_before = static_random.get_combat_random_state()
for _ in range(100):
    game.query_engine.roll_d20()
combat_state_after = static_random.get_combat_random_state()
check('7. combat_random state UNCHANGED by 100 roll_d20 calls',
      combat_state_before == combat_state_after,
      'combat_state_before=%r, combat_state_after=%r' % (combat_state_before, combat_state_after))

# ---------------------------------------------------------------------------
# 8. DB.items loads and a Tier component can be attached without raising
# ---------------------------------------------------------------------------
print('\n--- [8] Tier item component attaches without raising ---')
import app.engine.item_component_access as ICA

items_loaded = len(DB.items) > 0
check('8. DB.items loads with at least one item', items_loaded, 'len(DB.items) = %r' % len(DB.items))

tier_attach_ok = False
tier_error = None
target_item = None
try:
    # Pick an item that doesn't already carry a tier component -- content now
    # authors `tier` on many items (item tiers, see CONTENT_GUIDE.md), so
    # DB.items.values()[0] is no longer guaranteed tier-less the way it was
    # when this test was written. Data.append() (app/utilities/data.py)
    # warns-and-skips on a duplicate nid rather than overwriting, so
    # add_component-ing a second 'tier' onto an item that already has one
    # would leave target_item.tier pointing at an object never actually
    # inserted into target_item.components -- a real, pre-existing sharp
    # edge in ItemPrefab.add_component, not something to work around by
    # weakening this assertion.
    target_item = next((it for it in DB.items.values() if not getattr(it, 'tier', None)), None)
    assert target_item is not None, 'every item already carries a tier component'
    tier_component = ICA.get_component('tier')
    assert tier_component is not None, 'ICA.get_component(\'tier\') returned None -- Tier not registered'
    tier_component.value = 3
    target_item.add_component(tier_component)
    tier_attach_ok = (target_item.tier.value == 3)
except Exception as e:
    tier_error = repr(e)

check('8. Tier component attaches to an item without raising, value round-trips',
      tier_attach_ok,
      'target_item=%r, tier_error=%r' % (getattr(target_item, 'nid', None), tier_error))

if target_item is not None and tier_attach_ok:
    target_item.remove_component(target_item.tier)

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
