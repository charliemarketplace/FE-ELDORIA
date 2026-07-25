#!/usr/bin/env python3
"""
Execution-based tests for the enemy-pool generator (#4 + #5 -- a pool of
enemy templates keyed by power band, plus a generator that fills
"procedural" marked slots in a level with a squad scaled to the live
party's average effective level), driven directly against the LT engine
(no browser, no Playwright, no pygbag rebuild), using the exact bootstrap
of tools/test_capital_completion.py.

Every check below either validates real content (enemy_pools.json against
the loaded DB) or performs a real state mutation (game.get_random*,
game_state._generate_enemy_squad appending real UnitObjects into a real
LevelObject) and asserts a real before/after difference in engine state.

Run with:
  uv run --no-project --python 3.12 --with pygame-ce --with typing-extensions python tools/test_enemy_pool.py
"""
import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import play_harness as harness
harness.boot()

from app.data.resources.resources import RESOURCES
from app.data.database.database import DB

from app.data.database.level_units import GenericUnit
from app.engine import action
from app.engine import debug_jump
from app.engine import enemy_pool
from app.engine import game_state
from app.engine import power_band
from app.utilities import static_random


FAILURES = []


def check(label, condition, detail):
    status = 'PASS' if condition else 'FAIL'
    print('[%s] %s: %s' % (status, label, detail))
    if not condition:
        FAILURES.append('%s -- %s' % (label, detail))
    return condition


print('=' * 78)
print('ENEMY POOL -- EXECUTION-BASED TESTS')
print('=' * 78)

# ---------------------------------------------------------------------------
# 1. Boot DB/RESOURCES, load the pool, start a real level
# ---------------------------------------------------------------------------
print('\n--- [1] Boot DB/RESOURCES, load enemy_pools.json, start_level(S1) ---')
# RESOURCES/DB already loaded and engine-chrome sprites/fonts already
# initialized by harness.boot() above.

bands = enemy_pool.load_pools()
check('1. enemy_pools.json loads', isinstance(bands, list) and len(bands) > 0,
      'enemy_pool.load_pools() = %d bands' % len(bands))

game = game_state.start_level('S1')
check('1. start_level(S1)', game.level is not None and game.level.nid == 'S1',
      'game.level.nid = %r (expected S1)' % (game.level.nid if game.level else None))

# ---------------------------------------------------------------------------
# 2. Every pool klass/faction/ai resolves; no band is empty; level_range is
#    inside the class's actual max_level
# ---------------------------------------------------------------------------
print('\n--- [2] Content validation: enemy_pools.json against DB ---')
all_templates_ok = True
for band in bands:
    templates = band.get('templates', [])
    if not check('2. band %r non-empty' % band.get('nid'), len(templates) > 0,
                  'templates = %r' % templates):
        all_templates_ok = False
        continue
    for t in templates:
        klass = DB.classes.get(t['klass'])
        ok_klass = klass is not None
        ok_faction = t['faction'] in DB.factions
        ok_ai = t['ai'] in DB.ai
        lo, hi = t['level_range']
        ok_range = klass is not None and 1 <= lo <= hi <= klass.max_level
        detail = 'template %s in band %s (klass=%s faction=%s ai=%s level_range=%s, klass.max_level=%s)' % (
            t['klass'], band.get('nid'), ok_klass, ok_faction, ok_ai, t['level_range'],
            klass.max_level if klass else None)
        if not check('2. template resolves + in-range', ok_klass and ok_faction and ok_ai and ok_range, detail):
            all_templates_ok = False
        for item_nid in t.get('starting_items', []):
            check('2. starting_item %r resolves' % item_nid, item_nid in DB.items,
                  'DB.items has %r: %s' % (item_nid, item_nid in DB.items))

# ---------------------------------------------------------------------------
# 3. 1000 samples per band all land inside the declared level_range
# ---------------------------------------------------------------------------
print('\n--- [3] sample_squad: 1000 samples per band stay inside level_range ---')
for band in bands:
    templates_by_klass = {t['klass']: t for t in band['templates']}
    samples = enemy_pool.sample_squad(band, 1000, game)
    out_of_range = [s for s in samples
                    if not (templates_by_klass[s['klass']]['level_range'][0]
                            <= s['level'] <= templates_by_klass[s['klass']]['level_range'][1])]
    check('3. band %r: 1000 samples in level_range' % band['nid'], len(out_of_range) == 0,
          '%d/1000 out of declared range (examples: %s)' % (len(out_of_range), out_of_range[:5]))

# ---------------------------------------------------------------------------
# 4. Weights respected within tolerance
# ---------------------------------------------------------------------------
print('\n--- [4] sample_squad: weights respected within tolerance ---')
N = 6000
TOL = 0.05
for band in bands:
    templates = band['templates']
    total_weight = sum(t.get('weight', 1) for t in templates)
    samples = enemy_pool.sample_squad(band, N, game)
    counts = {}
    for s in samples:
        counts[s['klass']] = counts.get(s['klass'], 0) + 1
    for t in templates:
        expected_frac = t.get('weight', 1) / total_weight
        observed_frac = counts.get(t['klass'], 0) / N
        check('4. band %r klass %s weight within tolerance' % (band['nid'], t['klass']),
              abs(observed_frac - expected_frac) <= TOL,
              'expected_frac=%.3f observed_frac=%.3f (N=%d, tol=%.2f)' % (expected_frac, observed_frac, N, TOL))

# ---------------------------------------------------------------------------
# 5. party_average_effective_level + pick_band + generated squad mean within
#    LEVEL_TOLERANCE of party mean at ~L3 / ~L10 / ~L18
# ---------------------------------------------------------------------------
print('\n--- [5] Generated squad mean tracks party average effective level ---')


class _FakeUnit:
    def __init__(self, level, klass):
        self.level = level
        self.klass = klass


targets = [
    ('~L3', [_FakeUnit(3, 'Soldier'), _FakeUnit(3, 'Soldier'), _FakeUnit(3, 'Archer')]),
    ('~L10', [_FakeUnit(10, 'Soldier'), _FakeUnit(10, 'Cavalier'), _FakeUnit(10, 'Knight')]),
    ('~L18', [_FakeUnit(8, 'Paladin'), _FakeUnit(8, 'General'), _FakeUnit(8, 'Sniper')]),
]

for label, party in targets:
    avg = enemy_pool.party_average_effective_level(party)
    band = enemy_pool.pick_band(avg, bands)
    squad = enemy_pool.sample_squad(band, 30, game)
    squad_levels = [power_band.effective_level(s['level'], s['klass']) for s in squad]
    squad_mean = sum(squad_levels) / len(squad_levels)
    check('5. %s: party avg=%.2f -> band %r -> squad mean=%.2f within LEVEL_TOLERANCE=%d' % (
              label, avg, band['nid'], squad_mean, enemy_pool.LEVEL_TOLERANCE),
          abs(squad_mean - avg) <= enemy_pool.LEVEL_TOLERANCE,
          'avg=%.2f squad_mean=%.2f diff=%.2f (tolerance=%d)' % (
              avg, squad_mean, abs(squad_mean - avg), enemy_pool.LEVEL_TOLERANCE))

# ---------------------------------------------------------------------------
# 6. Same seed -> same squad; combat_random state UNCHANGED by generation
# ---------------------------------------------------------------------------
print('\n--- [6] Determinism + RNG-stream isolation ---')
band = bands[0]
combat_state_before = static_random.get_combat_random_state()
# "Same seed" for this generator means the other_random stream state -- it's
# the only stream sample_squad/instantiate_squad ever draw from -- so save
# and restore *that* rather than resetting the whole StaticRandom object
# (which would also reseed combat_random, defeating the isolation check
# below).
saved_other_state = static_random.get_other_random_state()

squad_a = enemy_pool.sample_squad(band, 25, game)

static_random.set_other_random_state(saved_other_state)
squad_b = enemy_pool.sample_squad(band, 25, game)

check('6. same seed -> same squad', squad_a == squad_b,
      'squad_a == squad_b: %s (first few: a=%s b=%s)' % (squad_a == squad_b, squad_a[:3], squad_b[:3]))

combat_state_after = static_random.get_combat_random_state()
check('6. combat_random state unchanged by generation', combat_state_before == combat_state_after,
      'combat_random state before=%r after=%r' % (combat_state_before, combat_state_after))

# ---------------------------------------------------------------------------
# 7. Empty / one-unit party does not crash
# ---------------------------------------------------------------------------
print('\n--- [7] Empty / one-unit party does not crash ---')
try:
    avg_empty = enemy_pool.party_average_effective_level([])
    band_empty = enemy_pool.pick_band(avg_empty, bands)
    enemy_pool.sample_squad(band_empty, 5, game)
    check('7. empty party does not crash', True, 'avg=%.2f -> band=%r' % (avg_empty, band_empty['nid']))
except Exception as e:
    check('7. empty party does not crash', False, 'raised %r' % (e,))

try:
    avg_one = enemy_pool.party_average_effective_level([_FakeUnit(5, 'Soldier')])
    band_one = enemy_pool.pick_band(avg_one, bands)
    enemy_pool.sample_squad(band_one, 5, game)
    check('7. one-unit party does not crash', True, 'avg=%.2f -> band=%r' % (avg_one, band_one['nid']))
except Exception as e:
    check('7. one-unit party does not crash', False, 'raised %r' % (e,))

# ---------------------------------------------------------------------------
# 8. debug_jump medians unchanged (S1=2, S2=3, S3=5, S4=5, S5=7)
# ---------------------------------------------------------------------------
print('\n--- [8] debug_jump power-band medians unchanged after power_band refactor ---')
expected_medians = {'S1': 2, 'S2': 3, 'S3': 5, 'S4': 5, 'S5': 7}
for level_nid, expected in expected_medians.items():
    level_prefab = DB.levels.get(level_nid)
    actual = debug_jump._target_level(level_prefab)
    check('8. %s median == %d' % (level_nid, expected), actual == expected,
          'debug_jump._target_level(%s) = %r (expected %r)' % (level_nid, actual, expected))

# ---------------------------------------------------------------------------
# 9. End-to-end: game_state._generate_enemy_squad fills a procedural slot
# ---------------------------------------------------------------------------
print('\n--- [9] game_state._generate_enemy_squad fills procedural slots end-to-end ---')

slot = GenericUnit('ProcSlotTest1', None, None, None, None, [], [], 'enemy', None)
slot.ai_group = 'ProcTestGroup'
slot.starting_position = (5, 6)
slot.procedural = True

fake_level_prefab = types.SimpleNamespace(units=[slot])

units_before = len(game._current_level.units)
game._generate_enemy_squad(fake_level_prefab)
units_after = len(game._current_level.units)

check('9. exactly one unit appended', units_after == units_before + 1,
      'units before=%d after=%d' % (units_before, units_after))

generated = game._current_level.units.get('ProcSlotTest1')
check('9. generated unit exists under authored nid', generated is not None,
      'game._current_level.units.get("ProcSlotTest1") = %r' % (generated,))
if generated is not None:
    check('9. klass/level/faction overwritten (not the empty placeholder)',
          bool(generated.klass) and generated.level is not None and bool(generated.faction),
          'klass=%r level=%r faction=%r' % (generated.klass, generated.level, generated.faction))
    check('9. position kept as authored', generated.position == (5, 6),
          'generated.position = %r (expected (5, 6))' % (generated.position,))
    check('9. team kept as authored', generated.team == 'enemy',
          'generated.team = %r (expected enemy)' % (generated.team,))
    check('9. ai_group kept as authored', generated.ai_group == 'ProcTestGroup',
          'generated.ai_group = %r (expected ProcTestGroup)' % (generated.ai_group,))

# A level with no procedural slots is a no-op (every level shipping today).
real_level_prefab = DB.levels.get('S1')
units_before_noop = len(game._current_level.units)
game._generate_enemy_squad(real_level_prefab)
units_after_noop = len(game._current_level.units)
check('9. no-op when the level has no procedural slots', units_after_noop == units_before_noop,
      'units before=%d after=%d (S1 has 0 procedural slots)' % (units_before_noop, units_after_noop))

# ---------------------------------------------------------------------------
print('\n' + '=' * 78)
if FAILURES:
    print('%d FAILURE(S):' % len(FAILURES))
    for f in FAILURES:
        print(' -', f)
    sys.exit(1)
else:
    print('ALL CHECKS PASSED')
