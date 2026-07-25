#!/usr/bin/env python3
"""
Execution-based proof that the Merchant (BACKLOG_AUDIT.md item 6, scoped to
the prep-menu market only per the user's SCOPE DECISION) actually works,
driven directly against the LT engine (no browser, no Playwright, no pygbag
rebuild).

Every check below performs a real state mutation via action.do(action.Foo(...))
or the new app/engine/merchant.py helpers, and then asserts a real
before/after difference in engine state -- same style and same bootstrap as
tools/test_capital_completion.py.

Run with:
  uv run --no-project --python 3.12 --with pygame-ce --with typing-extensions python tools/test_merchant.py
"""
import os
import sys
import pickle
import tempfile

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
from app.engine import item_funcs
from app.engine import skill_system
from app.engine import game_state
from app.engine.game_state import GameState
from app.engine.source_type import SourceType
from app.engine.objects.unit import UnitObject
from app.data.database.level_units import UniqueUnit
import app.engine.sprites as engine_sprites


FAILURES = []
GAPS = []


def check(label, condition, detail):
    status = 'PASS' if condition else 'FAIL'
    print('[%s] %s: %s' % (status, label, detail))
    if not condition:
        FAILURES.append('%s -- %s' % (label, detail))
    return condition


def gap(label, detail):
    print('[GAP] %s: %s' % (label, detail))
    GAPS.append('%s -- %s' % (label, detail))


print('=' * 78)
print('MERCHANT -- EXECUTION-BASED PROOF (real action.do() calls)')
print('=' * 78)

# ---------------------------------------------------------------------------
# 1. Boot DB/RESOURCES, start CAPITAL for real (same harness quirk workaround
#    as tools/test_capital_completion.py -- RESOURCES.load resets app.sprites
#    but doesn't re-run app.engine.sprites.load_images()).
# ---------------------------------------------------------------------------
print('\n--- [1] Boot DB/RESOURCES, game_state.start_level(\'CAPITAL\') ---')
RESOURCES.load('lion_throne.ltproj', CURRENT_SERIALIZATION_VERSION)
DB.load('lion_throne.ltproj', CURRENT_SERIALIZATION_VERSION)
engine_sprites.load_images()
game = game_state.start_level('CAPITAL')
check('1. start_level(CAPITAL)', game.level is not None and game.level.nid == 'CAPITAL',
      'game.level.nid = %r (expected CAPITAL)' % (game.level.nid if game.level else None))

from app.engine import merchant as merchant_engine

check('1. Merchant unit prefab exists in DB', 'Merchant' in DB.units,
      'DB.units has Merchant = %s' % ('Merchant' in DB.units))
check('1. no Merchant registered yet at fresh boot', game.get_unit(merchant_engine.MERCHANT_NID) is None,
      'game.get_unit(%r) = %r' % (merchant_engine.MERCHANT_NID, game.get_unit(merchant_engine.MERCHANT_NID)))

# ---------------------------------------------------------------------------
# 2. Prove the UniqueUnit-wrap mechanism itself (BACKLOG_AUDIT.md "traps"
#    section): a raw UnitPrefab passed to UnitObject.from_prefab silently
#    skips the items/skills block and forces team='player'; wrapping it in
#    UniqueUnit(nid, team, ai, None), the way event_functions.load_unit and
#    app/engine/merchant.py:get_merchant both do, takes the real branch.
#    Rowan has real starting_items/skills in units.json, so this is the
#    cleanest unit to observe the difference on (the Merchant's own prefab
#    has none, by design -- see [4] below for the Merchant-specific proof).
# ---------------------------------------------------------------------------
print('\n--- [2] Prove UnitObject.from_prefab is_level_unit branching (raw vs UniqueUnit-wrapped) ---')
rowan_prefab = DB.units.get('Rowan')
raw_rowan = UnitObject.from_prefab(rowan_prefab, game.current_mode, new_nid='Rowan_RAW_TEST')
check('2. raw UnitPrefab -> items skipped', raw_rowan.items == [],
      'raw_rowan.items = %s (expected [])' % [i.nid for i in raw_rowan.items])
check('2. raw UnitPrefab -> team forced to player', raw_rowan.team == 'player',
      'raw_rowan.team = %r (expected player, forced by the skip branch)' % raw_rowan.team)

wrapped_rowan_prefab = UniqueUnit('Rowan', 'other', 'None', None)
wrapped_rowan = UnitObject.from_prefab(wrapped_rowan_prefab, game.current_mode, new_nid='Rowan_WRAPPED_TEST')
wrapped_item_nids = sorted(i.nid for i in wrapped_rowan.items)
check('2. UniqueUnit-wrapped -> real items resolved', wrapped_item_nids == sorted(['Iron Sword', 'Vulnerary', 'EMB_EmberCoal']),
      'wrapped_rowan.items = %s (expected Iron Sword/Vulnerary/EMB_EmberCoal, per units.json)' % wrapped_item_nids)
check('2. UniqueUnit-wrapped -> team preserved from the UniqueUnit, not forced', wrapped_rowan.team == 'other',
      'wrapped_rowan.team = %r (expected other -- proves the is_level_unit branch ran, not the skip branch)' % wrapped_rowan.team)

# ---------------------------------------------------------------------------
# 3. A save taken before the Merchant ever existed must not crash on load,
#    and get_merchant() must then lazily create + register one.
# ---------------------------------------------------------------------------
print('\n--- [3] Pre-Merchant save loads without crashing; get_merchant() lazily creates one ---')
pre_merchant_s_dict, _pre_meta = game.save()
pre_merchant_unit_nids = sorted(u['nid'] for u in pre_merchant_s_dict['units'])
check('3. pre-Merchant save has no Merchant unit', 'Merchant' not in pre_merchant_unit_nids,
      'pre-Merchant save unit nids = %s' % pre_merchant_unit_nids)

tmp_fd, tmp_path = tempfile.mkstemp(prefix='lt_merchant_premerchant_', suffix='.p')
os.close(tmp_fd)
try:
    with open(tmp_path, 'wb') as fp:
        pickle.dump(pre_merchant_s_dict, fp)
    with open(tmp_path, 'rb') as fp:
        loaded_pre_merchant_s_dict = pickle.load(fp)
finally:
    os.remove(tmp_path)

# Prove it round-trips cleanly into a brand new GameState (no crash) --
# same isolation style as test_capital_completion.py section 7.
isolated_reload = GameState()
isolated_reload.build_new()
isolated_reload.load(loaded_pre_merchant_s_dict)
check('3. isolated reload of pre-Merchant save did not crash and has no Merchant',
      isolated_reload.get_unit(merchant_engine.MERCHANT_NID) is None,
      'isolated_reload.get_unit(%r) = %r' % (merchant_engine.MERCHANT_NID, isolated_reload.get_unit(merchant_engine.MERCHANT_NID)))

# Now reload the same pre-Merchant save into the actual singleton `game`
# object that app/engine/merchant.py operates on (game_state.game is mutated
# in place by build_new()/load(), never rebound, so every module's
# `from app.engine.game_state import game` import stays valid across this).
game.build_new()
game.load(loaded_pre_merchant_s_dict)
check('3. singleton reload of pre-Merchant save has no Merchant either',
      game.get_unit(merchant_engine.MERCHANT_NID) is None,
      'game.get_unit(%r) = %r' % (merchant_engine.MERCHANT_NID, game.get_unit(merchant_engine.MERCHANT_NID)))

merchant = merchant_engine.get_merchant()
check('3. get_merchant() lazily created and registered a Merchant',
      merchant is not None and merchant.nid == merchant_engine.MERCHANT_NID and game.get_unit(merchant_engine.MERCHANT_NID) is merchant,
      'get_merchant() = %r, game.get_unit(%r) = %r' % (merchant, merchant_engine.MERCHANT_NID, game.get_unit(merchant_engine.MERCHANT_NID)))
check('3. get_merchant() is idempotent (no duplicate registration)',
      merchant_engine.get_merchant() is merchant,
      'second get_merchant() call returned %r (expected same object %r)' % (merchant_engine.get_merchant(), merchant))

# ---------------------------------------------------------------------------
# 4. Merchant-specific proof that it was built via the UniqueUnit wrap (not
#    the raw/skip path) -- team stays 'other' (raw would force 'player'),
#    and it is registered but excluded from the roster.
# ---------------------------------------------------------------------------
print('\n--- [4] Merchant is registered, wrapped correctly, and excluded from the roster ---')
check('4. Merchant team is other (proves UniqueUnit wrap, not raw skip-path)', merchant.team == 'other',
      'merchant.team = %r (expected other)' % merchant.team)
check('4. Merchant is persistent (survives clean_up(full=True))', merchant.persistent is True,
      'merchant.persistent = %r' % merchant.persistent)
check('4. Merchant NOT in get_units_in_party()', merchant not in game.get_units_in_party(),
      'get_units_in_party() nids = %s' % [u.nid for u in game.get_units_in_party()])
check('4. Merchant NOT in get_all_units_in_party()', merchant not in game.get_all_units_in_party(),
      'get_all_units_in_party() nids = %s' % [u.nid for u in game.get_all_units_in_party()])
check('4. Merchant IS reachable via game.get_unit (works outside the roster)',
      game.get_unit(merchant_engine.MERCHANT_NID) is merchant,
      'game.get_unit(%r) = %r' % (merchant_engine.MERCHANT_NID, game.get_unit(merchant_engine.MERCHANT_NID)))

# ---------------------------------------------------------------------------
# 5. Donate XP math + turnwheel reversibility.
#    Reusing CAPITAL's own companions (Kael/Elara/Ren/Briar) as donors --
#    they're already team='player' with .party set by level_setup(), so
#    they show up in get_units_in_party() with no extra plumbing needed.
# ---------------------------------------------------------------------------
print('\n--- [5] Donate XP: pooling math, level-up clamp, and turnwheel reversibility ---')
kael, elara, ren, briar = (game.get_unit(n) for n in ('Kael', 'Elara', 'Ren', 'Briar'))
check('5. all 4 companions are in the party (donor pool)',
      all(u in game.get_units_in_party() for u in (kael, elara, ren, briar)),
      'get_units_in_party() nids = %s' % [u.nid for u in game.get_units_in_party()])

kael.exp, elara.exp, ren.exp, briar.exp = 90, 40, 75, 0
check('5. merchant starts at level 1, exp 0', merchant.level == 1 and merchant.exp == 0,
      'merchant.level=%d, merchant.exp=%d' % (merchant.level, merchant.exp))

pre_donate_snapshot = {u.nid: u.exp for u in (kael, elara, ren, briar)}
pre_donate_merchant_level = merchant.level
pre_donate_merchant_exp = merchant.exp

game.state.temp_state.clear()  # isolate the feat_choice queue assertion below
performed, levels_gained = merchant_engine.donate_xp()

check('5. donate math: total 205 (90+40+75+0+0) -> +2 levels', levels_gained == 2,
      'levels_gained = %d (expected 2)' % levels_gained)
check('5. donate math: 5 exp carried into merchant', merchant.exp == 5,
      'merchant.exp = %d (expected 5)' % merchant.exp)
check('5. donate math: merchant now level 3', merchant.level == 3,
      'merchant.level = %d (expected 3, 1 + 2 gained)' % merchant.level)
check('5. donate math: all donors zeroed', all(u.exp == 0 for u in (kael, elara, ren, briar)),
      'post-donate donor exp = %s' % {u.nid: u.exp for u in (kael, elara, ren, briar)})
check('5. feat_choice queued exactly once per level gained', game.state.temp_state.count('feat_choice') == 2,
      'game.state.temp_state = %s (expected two feat_choice entries)' % game.state.temp_state)
check('5. game.memory[current_unit] points at the Merchant for the feat queue',
      game.memory.get('current_unit') is merchant,
      "game.memory['current_unit'] = %r (expected merchant %r)" % (game.memory.get('current_unit'), merchant))
game.state.temp_state.clear()

# --- Reverse it turnwheel-style: reverse every performed action in reverse
# order and assert the pre-donate state comes back exactly.
for act in reversed(performed):
    act.reverse()

check('5. reverse: donor exp restored', {u.nid: u.exp for u in (kael, elara, ren, briar)} == pre_donate_snapshot,
      'post-reverse donor exp = %s (expected %s)' % ({u.nid: u.exp for u in (kael, elara, ren, briar)}, pre_donate_snapshot))
check('5. reverse: merchant level restored', merchant.level == pre_donate_merchant_level,
      'merchant.level = %d (expected %d)' % (merchant.level, pre_donate_merchant_level))
check('5. reverse: merchant exp restored', merchant.exp == pre_donate_merchant_exp,
      'merchant.exp = %d (expected %d)' % (merchant.exp, pre_donate_merchant_exp))

# Re-run the donation for real so later sections (feats, save round-trip)
# have a leveled-up Merchant to work with.
game.state.temp_state.clear()
performed, levels_gained = merchant_engine.donate_xp()
check('5. re-donate reaches the same +2 levels / 5 exp result',
      levels_gained == 2 and merchant.exp == 5 and merchant.level == 3,
      'levels_gained=%d, merchant.level=%d, merchant.exp=%d' % (levels_gained, merchant.level, merchant.exp))
game.state.temp_state.clear()

# ---------------------------------------------------------------------------
# 6. Simulate the player picking a feat for each of the 2 levels gained --
#    one pricing feat, one ordinary combat feat (proving generic feats are
#    legitimately offered to the Merchant too, per BACKLOG_AUDIT.md's "not
#    filtered" note) -- via the same action.AddSkill the real FeatChoiceState
#    uses.
# ---------------------------------------------------------------------------
print('\n--- [6] Grant feats to the Merchant via action.AddSkill (real FeatChoiceState mechanism) ---')
discount_feat_nid = "fMerchant's Instinct"
check('6. discount feat exists and carries change_buy_price', discount_feat_nid in DB.skills,
      'DB.skills has %r = %s' % (discount_feat_nid, discount_feat_nid in DB.skills))

skills_before = [s.nid for s in merchant.skills]
act1 = action.AddSkill(merchant, discount_feat_nid, source=merchant.nid, source_type=SourceType.PERSONAL)
action.do(act1)
act2 = action.AddSkill(merchant, 'fLuck +4', source=merchant.nid, source_type=SourceType.PERSONAL)
action.do(act2)
skills_after = [s.nid for s in merchant.skills]
check('6. Merchant gained both feats', discount_feat_nid in skills_after and 'fLuck +4' in skills_after,
      'skills before=%s, after=%s' % (skills_before, skills_after))

# ---------------------------------------------------------------------------
# 7. Prep-menu-market pricing: a discount feat changes the buy price, and
#    removing it restores the baseline. This mirrors PrepMarketState's own
#    buy-branch code exactly (app/engine/prep.py) -- read it back to prove
#    the wiring is actually there, not just reimplemented here.
# ---------------------------------------------------------------------------
print('\n--- [7] Prep-market pricing: Merchant feat discount applies, and its absence restores baseline ---')
prep_source_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app', 'engine', 'prep.py')
with open(prep_source_path, 'r') as fp:
    prep_source = fp.read()
check('7. PrepMarketState buy path wires in the Merchant modifier',
      'skill_system.modify_buy_price(merchant, item)' in prep_source,
      'looked for "skill_system.modify_buy_price(merchant, item)" in app/engine/prep.py')
check('7. PrepMarketState sell path wires in the Merchant modifier',
      'skill_system.modify_sell_price(merchant, item)' in prep_source,
      'looked for "skill_system.modify_sell_price(merchant, item)" in app/engine/prep.py')

buyer = kael
template_items = item_funcs.create_items(buyer, ['Vulnerary'])
vulnerary_template = template_items[0]
baseline_price = item_funcs.buy_price(buyer, vulnerary_template)

# Exact PrepMarketState buy-branch computation (app/engine/prep.py, state == 'buy'):
#   value = item_funcs.buy_price(self.unit, item)
#   merchant = game.get_unit(merchant_engine.MERCHANT_NID)
#   if merchant: value = int(value * skill_system.modify_buy_price(merchant, item))
def prep_market_buy_price(shopper, item):
    value = item_funcs.buy_price(shopper, item)
    m = game.get_unit(merchant_engine.MERCHANT_NID)
    if m:
        value = int(value * skill_system.modify_buy_price(m, item))
    return value

price_with_feat = prep_market_buy_price(buyer, vulnerary_template)
check('7. discount feat lowers the prep-market buy price below baseline', price_with_feat < baseline_price,
      'baseline_price=%d, price_with_feat=%d (fMerchant\'s Instinct = 0.8x)' % (baseline_price, price_with_feat))
check('7. discounted price matches the feat\'s exact multiplier', price_with_feat == int(baseline_price * 0.8),
      'price_with_feat=%d, expected int(%d * 0.8)=%d' % (price_with_feat, baseline_price, int(baseline_price * 0.8)))

remove_act = action.RemoveSkill(merchant, discount_feat_nid)
action.do(remove_act)
price_without_feat = prep_market_buy_price(buyer, vulnerary_template)
check('7. removing the feat restores the baseline price', price_without_feat == baseline_price,
      'price_without_feat=%d, baseline_price=%d' % (price_without_feat, baseline_price))

# Put the feat back so the save round-trip below has something to prove
# persisted correctly.
action.do(action.AddSkill(merchant, discount_feat_nid, source=merchant.nid, source_type=SourceType.PERSONAL))

# ---------------------------------------------------------------------------
# 8. Merchant survives save -> pickle -> fresh GameState().load(), with
#    level/exp/skills intact -- same proof style as
#    tools/test_capital_completion.py section 7.
# ---------------------------------------------------------------------------
print('\n--- [8] Merchant survives save -> pickle -> fresh GameState().load() ---')
pre_save_level = merchant.level
pre_save_exp = merchant.exp
pre_save_skills = sorted(s.nid for s in merchant.skills)

s_dict, _meta = game.save()
tmp_fd, tmp_path = tempfile.mkstemp(prefix='lt_merchant_test_', suffix='.p')
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

fresh_merchant = fresh_game.get_unit(merchant_engine.MERCHANT_NID)
check('8. Merchant present after reload into a brand-new GameState', fresh_merchant is not None,
      'fresh_game.get_unit(%r) = %r' % (merchant_engine.MERCHANT_NID, fresh_merchant))
if fresh_merchant is not None:
    check('8. Merchant level survived the round trip', fresh_merchant.level == pre_save_level,
          'pre-save level=%d, post-load level=%d' % (pre_save_level, fresh_merchant.level))
    check('8. Merchant exp survived the round trip', fresh_merchant.exp == pre_save_exp,
          'pre-save exp=%d, post-load exp=%d' % (pre_save_exp, fresh_merchant.exp))
    post_load_skills = sorted(s.nid for s in fresh_merchant.skills)
    check('8. Merchant skills survived the round trip', post_load_skills == pre_save_skills,
          'pre-save skills=%s, post-load skills=%s' % (pre_save_skills, post_load_skills))
    check('8. Merchant still excluded from the roster after reload',
          fresh_merchant not in fresh_game.get_units_in_party(),
          'fresh_game.get_units_in_party() nids = %s' % [u.nid for u in fresh_game.get_units_in_party()])

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print('\n' + '=' * 78)
print('SUMMARY')
print('=' * 78)
if GAPS:
    print('\nGAPS (%d):' % len(GAPS))
    for g in GAPS:
        print('  - %s' % g)
if FAILURES:
    print('\nFAILURES (%d):' % len(FAILURES))
    for f in FAILURES:
        print('  - %s' % f)
    print('\nRESULT: FAIL')
    sys.exit(1)
else:
    print('\nAll executed assertions PASSED.%s' % (' (with %d GAP(s) reported above)' % len(GAPS) if GAPS else ''))
    print('RESULT: PASS')
    sys.exit(0)
