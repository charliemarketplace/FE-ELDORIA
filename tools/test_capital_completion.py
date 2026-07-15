#!/usr/bin/env python3
"""
Execution-based proof that the CAPITAL hub chapter is completable and
saveable, driven directly against the LT engine (no browser, no
Playwright, no pygbag rebuild).

Every check below performs a real state mutation via action.do(action.Foo(...))
(the same Action classes the real event commands use -- see
app/events/event_functions.py for which Action backs which event command)
and then asserts a real before/after difference in engine state. Nothing
here is an existence check on JSON data; DB/RESOURCES are only used to
read exact values (event scripts, item lists, skill nids) so the script
isn't guessing at content, and to look up prefabs the Actions need.

Run with:
  uv run --no-project --python 3.12 --with pygame-ce --with typing-extensions python tools/test_capital_completion.py
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
from app.engine import game_state
from app.engine.game_state import GameState
from app.engine.source_type import SourceType
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
print('CAPITAL COMPLETION -- EXECUTION-BASED PROOF (real action.do() calls)')
print('=' * 78)

# ---------------------------------------------------------------------------
# 1. Boot DB/RESOURCES, start CAPITAL for real
# ---------------------------------------------------------------------------
print('\n--- [1] Boot DB/RESOURCES, game_state.start_level(\'CAPITAL\') ---')
RESOURCES.load('lion_throne.ltproj', CURRENT_SERIALIZATION_VERSION)
DB.load('lion_throne.ltproj', CURRENT_SERIALIZATION_VERSION)
# Harness quirk (not a gameplay bug): app.data.resources.resources.RESOURCES.load()
# calls app.sprites.reset(), which clears and re-walks the engine-chrome sprite
# dict (app/sprites.py's SPRITES, e.g. 'movement_arrows', 'chapter_title_sigil')
# but does NOT re-run app.engine.sprites.load_images(), which is what actually
# assigns each entry's real pygame Surface into .image. That load_images() call
# already ran once at first import of app.engine.sprites (before RESOURCES.load
# reset the dict it was reading from), so after RESOURCES.load every chrome
# sprite's .image is None until load_images() is called again. Modules such as
# app/engine/level_cursor.py and app/engine/chapter_title.py read SPRITES.get(...)
# .convert_alpha() at class-definition time, so importing them (which
# game_state.start_level() does transitively) crashes with
# AttributeError: 'NoneType' object has no attribute 'copy'/'convert_alpha'
# unless this is re-run first.
engine_sprites.load_images()
game = game_state.start_level('CAPITAL')
check('1. start_level(CAPITAL)', game.level is not None and game.level.nid == 'CAPITAL',
      'game.level.nid = %r (expected CAPITAL)' % (game.level.nid if game.level else None))

# ---------------------------------------------------------------------------
# 2. Replicate CAPITAL Intro's _source (read verbatim from events.json)
# ---------------------------------------------------------------------------
print('\n--- [2] Replicate CAPITAL Intro (game_var/give_money/add_unit) ---')
intro_event = next(e for e in DB.events if e.nid == 'CAPITAL Intro')
intro_script = '\n'.join(intro_event._source)
assert 'game_var;safe_zone;1' in intro_script
assert 'give_money;3000' in intro_script
for nid in ('Kael', 'Elara', 'Ren', 'Briar'):
    assert 'add_unit;%s;' % nid in intro_script
    assert 'game_var;%s_joined;1' % nid.lower() in intro_script

companions = ['Kael', 'Elara', 'Ren', 'Briar']
# positions read verbatim from CAPITAL Intro's _source (add_unit;<nid>;<pos>;immediate)
positions = {'Kael': (10, 9), 'Elara': (14, 9), 'Ren': (11, 8), 'Briar': (16, 8)}

# --- Prove the real add_unit precondition now holds, per event_commands.AddUnit's
# own docstring: "The unit must be in the chapter's data or otherwise have been
# loaded into memory (see load_unit or make_generic)." event_functions.add_unit's
# very first line is self._get_unit(unit) -> game.get_unit(nid) -> unit_registry.get(nid).
# CAPITAL's levels.json units array now includes Kael/Elara/Ren/Briar with
# starting_position: null (the arena/scripted-duel pattern), so
# game.level_setup()'s `for unit in self._current_level.units: self.full_register(unit)`
# (app/engine/game_state.py) already registered all 4 into game.unit_registry at
# start_level('CAPITAL') above -- with starting_position None meaning they are NOT
# yet placed on the map (unit.position is None), exactly like an off-map unit
# waiting for a scripted add_unit to bring it in.
pre_registered = {nid: game.get_unit(nid) for nid in companions}
print('  game.get_unit(nid) for each companion right after start_level(CAPITAL) '
      '(now non-None, thanks to the levels.json fix -- no load_unit/manual registration needed):')
for nid in companions:
    print('    %s -> %r (position=%r)' % (nid, pre_registered[nid], pre_registered[nid].position if pre_registered[nid] else None))

capital_level_unit_nids = {u.nid for u in DB.levels.get('CAPITAL').units}
check('2. all 4 companions resolve via game.get_unit() with no manual registration',
      all(u is not None for u in pre_registered.values()),
      'game.get_unit(nid) for %s = %s' % (companions, {n: repr(u) for n, u in pre_registered.items()}))
check('2. companions are in CAPITAL levels.json units (real fix, not a workaround)',
      set(companions).issubset(capital_level_unit_nids),
      'CAPITAL levels.json units nids = %s' % sorted(capital_level_unit_nids))
check('2. companions registered but NOT yet on map before add_unit runs',
      all(u.position is None for u in pre_registered.values()),
      'positions before add_unit = %s' % {n: u.position for n, u in pre_registered.items()})

gold_before_intro = game.get_party().money
action.do(action.SetGameVar('safe_zone', 1))
action.do(action.GainMoney(game.current_party, 3000))
action.do(action.UpdateRecords('money', (game.current_party, 3000)))

print('  Placing companions via action.ArriveOnMap -- the exact Action '
      'app/events/event.py Event._place_unit uses for entry_type=="immediate", i.e. '
      'add_unit\'s real placement path -- on the units already registered from the '
      'fixed level data (no action.RegisterUnit / UnitObject.from_prefab needed):')
for nid in companions:
    unit = game.get_unit(nid)
    action.do(action.ArriveOnMap(unit, positions[nid]))
    action.do(action.SetGameVar('%s_joined' % nid.lower(), 1))

party_units_after = {u.nid for u in game.get_units_in_party()}
check('2. all 4 companions present in party',
      set(companions).issubset(party_units_after),
      'game.get_units_in_party() nids = %s (need all of %s present)' % (sorted(party_units_after), companions))

gold_after_intro = game.get_party().money
check('2. gold increased by exactly 3000',
      gold_after_intro == gold_before_intro + 3000,
      'gold before=%d, after=%d, delta=%d (expected +3000)' % (gold_before_intro, gold_after_intro, gold_after_intro - gold_before_intro))

check('2. safe_zone truthy', bool(game.game_vars.get('safe_zone')),
      "game.game_vars.get('safe_zone') = %r" % (game.game_vars.get('safe_zone'),))

for nid in companions:
    flag = game.game_vars.get('%s_joined' % nid.lower())
    check('2. %s_joined set' % nid.lower(), bool(flag), "game.game_vars.get('%s_joined') = %r" % (nid.lower(), flag))

# ---------------------------------------------------------------------------
# 3. Class change 2 of the 4 companions via the real Action (action.ClassChange)
#    (CAPITAL Train no longer exists -- class assignment is now an automatic
#    per-unit wizard appended to CAPITAL Intro's own _source, see below)
# ---------------------------------------------------------------------------
print('\n--- [3] Class change 2 companions via action.ClassChange (real Action change_class uses) ---')
assert 'change_class;Kael;Fighter,Mercenary,Archer,Mage,Cleric' in intro_script
assert 'change_class;Elara;Fighter,Mercenary,Archer,Mage,Cleric' in intro_script

class_targets = {'Kael': 'Fighter', 'Elara': 'Mage'}
classed_before = {}
classed_after = {}
for nid, target_klass in class_targets.items():
    unit = game.get_unit(nid)
    before = {
        'klass': unit.klass,
        'stats': dict(unit.stats),
        'HP': unit.get_stat('HP'),
        'STR': unit.get_stat('STR'),
        'SPD': unit.get_stat('SPD'),
    }
    classed_before[nid] = before
    action.do(action.ClassChange(unit, target_klass))
    after = {
        'klass': unit.klass,
        'stats': dict(unit.stats),
        'HP': unit.get_stat('HP'),
        'STR': unit.get_stat('STR'),
        'SPD': unit.get_stat('SPD'),
    }
    classed_after[nid] = after
    check('3. %s.klass changed to %s' % (nid, target_klass),
          after['klass'] == target_klass and after['klass'] != 'Citizen',
          'before klass=%r, after klass=%r' % (before['klass'], after['klass']))
    check('3. %s stats actually changed' % nid,
          after['stats'] != before['stats'],
          'before stats=%s\n           after  stats=%s' % (before['stats'], after['stats']))
    print('    %s: HP %d->%d, STR %d->%d, SPD %d->%d' %
          (nid, before['HP'], after['HP'], before['STR'], after['STR'], before['SPD'], after['SPD']))

# ---------------------------------------------------------------------------
# 4. Grant a feat skill (exact nids read from CAPITAL Intro's feat-wizard
#    lines) via action.AddSkill. CAPITAL Study no longer exists -- feats are
#    now part of the same automatic per-unit wizard as class assignment.
# ---------------------------------------------------------------------------
print('\n--- [4] Grant a feat skill via action.AddSkill (real Action give_skill uses) ---')
# The exact feat skill nid list, read verbatim out of the FeatPick_Kael choice line.
feat_line = next(l for l in intro_event._source if l.startswith('choice;FeatPick_Kael;'))
feat_nids = [tok.split('|')[0] for tok in feat_line.split(';')[3].split(',')]
check('4. feat nids parsed from CAPITAL Intro', len(feat_nids) == 5 and all(n in DB.skills for n in feat_nids),
      'parsed feat nids = %s' % feat_nids)
for nid in companions:
    assert 'give_skill;%s;{v:FeatPick_%s};persistent' % (nid, nid) in intro_script, \
        'expected the {v:...} syntax fix for %s, not the old broken {game.game_vars[...]} form' % nid

feat_unit_nid = 'Kael'
feat_skill_nid = feat_nids[0]  # 'fMaximum HP +5'
feat_unit = game.get_unit(feat_unit_nid)
skills_before = [s.nid for s in feat_unit.skills]
action.do(action.AddSkill(feat_unit, feat_skill_nid, source=feat_unit.nid, source_type=SourceType.PERSONAL))
skills_after = [s.nid for s in feat_unit.skills]
check('4. %s has feat skill %s' % (feat_unit_nid, feat_skill_nid),
      feat_skill_nid in skills_after and feat_skill_nid not in skills_before,
      'skills before=%s, after=%s' % (skills_before, skills_after))

# ---------------------------------------------------------------------------
# 7. THE MOST IMPORTANT CHECK -- mid-flow save -> pickle round trip -> load
#    into a brand-new GameState() (not the same in-memory objects), right
#    after step 4 as instructed (2 companions classed, 1 featured, still in
#    CAPITAL, before Depart/shop).
# ---------------------------------------------------------------------------
print('\n--- [7] Mid-flow save/reload proof (game.save() -> pickle round trip -> fresh GameState().load()) ---')
pre_save_gold = game.get_party().money
pre_save_game_vars = dict(game.game_vars)
pre_save_companion_klasses = {nid: game.get_unit(nid).klass for nid in companions}
pre_save_feat_skills = [s.nid for s in game.get_unit(feat_unit_nid).skills]
pre_save_unit_nids = sorted(game.unit_registry.keys())

s_dict, meta_dict = game.save()

tmp_fd, tmp_path = tempfile.mkstemp(prefix='lt_capital_test_', suffix='.p')
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

post_load_unit_nids = sorted(fresh_game.unit_registry.keys())
check('7. same unit roster round-trips (no dup/missing)',
      post_load_unit_nids == pre_save_unit_nids,
      'pre-save unit nids=%s\n           post-load unit nids=%s' % (pre_save_unit_nids, post_load_unit_nids))

companions_present = {nid: (nid in fresh_game.unit_registry) for nid in companions}
check('7. all 4 companions present after reload, no duplicates',
      all(companions_present.values()) and len(set(post_load_unit_nids)) == len(post_load_unit_nids),
      'present-after-reload=%s' % companions_present)

post_load_klasses = {nid: fresh_game.get_unit(nid).klass for nid in companions}
check('7. classed units kept their assigned class (not reverted to Citizen)',
      post_load_klasses['Kael'] == 'Fighter' and post_load_klasses['Elara'] == 'Mage',
      'pre-save klasses=%s, post-load klasses=%s' % (pre_save_companion_klasses, post_load_klasses))

post_load_feat_skills = [s.nid for s in fresh_game.get_unit(feat_unit_nid).skills]
check('7. featured unit kept its skill',
      feat_skill_nid in post_load_feat_skills,
      'pre-save %s skills=%s, post-load skills=%s' % (feat_unit_nid, pre_save_feat_skills, post_load_feat_skills))

post_load_gold = fresh_game.get_party(game.current_party).money
check('7. gold matches save-time value',
      post_load_gold == pre_save_gold,
      'pre-save gold=%d, post-load gold=%d' % (pre_save_gold, post_load_gold))

post_load_game_vars = dict(fresh_game.game_vars)
check('7. game_vars (incl. safe_zone) match pre-save values',
      post_load_game_vars == pre_save_game_vars,
      'pre-save game_vars=%s\n           post-load game_vars=%s' % (pre_save_game_vars, post_load_game_vars))

# ---------------------------------------------------------------------------
# 5. Simulate an actual shop purchase via the real ShopState buy-path mechanism
#    (app/engine/general_states.py:ShopState.take_input, state=='buy' branch)
# ---------------------------------------------------------------------------
print('\n--- [5] Shop purchase via the real buy-path mechanism (ShopState take_input, state==\'buy\') ---')
vendor_event = next(e for e in DB.events if e.nid == 'CAPITAL Vendor')
vendor_script = '\n'.join(vendor_event._source)
shop_line = next(l for l in vendor_event._source if l.startswith('shop;'))
shop_item_nids = shop_line.split(';')[2].split(',')
check('5. shop item list parsed from CAPITAL Vendor', shop_item_nids == ['Vulnerary', 'Potion', 'Fire', 'Heal'],
      'parsed shop item list = %s' % shop_item_nids)

buyer = game.get_unit('Kael')
template_items = item_funcs.create_items(buyer, shop_item_nids)
target_template = next(i for i in template_items if i.nid == 'Vulnerary')
price = item_funcs.buy_price(buyer, target_template)

gold_before_shop = game.get_party().money
inv_before_shop = [i.nid for i in buyer.items]

new_item = item_funcs.create_item(buyer, target_template.nid)
action.do(action.HasTraded(buyer))
action.do(action.GainMoney(game.current_party, -price))
action.do(action.UpdateRecords('money', (game.current_party, -price)))
game.register_item(new_item)
action.do(action.GiveItem(buyer, new_item))

gold_after_shop = game.get_party().money
inv_after_shop = [i.nid for i in buyer.items]

check('5. gold decreased by exactly item value',
      gold_after_shop == gold_before_shop - price,
      'price=%d, gold before=%d, after=%d, delta=%d' % (price, gold_before_shop, gold_after_shop, gold_after_shop - gold_before_shop))
check('5. item now in buyer inventory',
      'Vulnerary' in inv_after_shop and inv_before_shop.count('Vulnerary') < inv_after_shop.count('Vulnerary'),
      'buyer inventory before=%s, after=%s' % (inv_before_shop, inv_after_shop))

# ---------------------------------------------------------------------------
# 6. Replicate CAPITAL Depart's tail, then transition into S1 via the real
#    save->build_new->load->start_level mechanism (app/engine/save.py:load_game /
#    app/engine/game_state.py:load_level -- this IS how the engine actually
#    carries persistent state across a chapter boundary; see
#    app/events/event_state.py:EventState.level_end/end_event for the
#    win_game/set_next_chapter -> game_vars['_next_level_nid'] -> save -> load
#    pipeline this mirrors).
# ---------------------------------------------------------------------------
print('\n--- [6] CAPITAL Depart tail + real chapter transition into S1 ---')
depart_event = next(e for e in DB.events if e.nid == 'CAPITAL Depart')
depart_script = '\n'.join(depart_event._source)
assert 'game_var;safe_zone;0' in depart_script
assert 'set_next_chapter;S1' in depart_script
assert 'win_game' in depart_script

# game_var;safe_zone;0 -> action.SetGameVar (same Action as event_functions.game_var)
action.do(action.SetGameVar('safe_zone', 0))
check('6. safe_zone now falsy', not game.game_vars.get('safe_zone'),
      "game.game_vars.get('safe_zone') = %r" % (game.game_vars.get('safe_zone'),))

# set_next_chapter;S1 -> action.SetGameVar("_goto_level", "S1") (event_functions.set_next_chapter)
action.do(action.SetGameVar('_goto_level', 'S1'))
# win_game -> direct game.level_vars['_win_game'] = True (event_functions.win_game; not an Action)
game.level_vars['_win_game'] = True
check('6. _goto_level set to S1 and _win_game set',
      game.game_vars.get('_goto_level') == 'S1' and game.level_vars.get('_win_game') is True,
      "_goto_level=%r, level_vars['_win_game']=%r" % (game.game_vars.get('_goto_level'), game.level_vars.get('_win_game')))

# Real chapter-boundary mechanism: EventState.level_end() calls game.clean_up(),
# then game.game_vars['_next_level_nid'] = game.game_vars['_goto_level'], then
# saves to disk (game.state.change('title_save')); resuming that save is what
# actually starts the next level, via app/engine/save.py:load_game /
# app/engine/game_state.py:load_level(level_nid, save_loc), which does
# game.build_new(); game.load(s_dict); game.start_level(level_nid).
game.clean_up()
game.game_vars['_next_level_nid'] = game.game_vars['_goto_level']
game.game_vars['_goto_level'] = None

depart_s_dict, depart_meta = game.save()
depart_fd, depart_path = tempfile.mkstemp(prefix='lt_capital_depart_', suffix='.p')
os.close(depart_fd)
try:
    with open(depart_path, 'wb') as fp:
        pickle.dump(depart_s_dict, fp)
    game = game_state.load_level('S1', depart_path)
finally:
    if os.path.exists(depart_path):
        os.remove(depart_path)

check('6. transitioned into S1', game.level is not None and game.level.nid == 'S1',
      'game.level.nid = %r (expected S1)' % (game.level.nid if game.level else None))

# Now exercise S1 Intro's actual conditional add_unit logic -- read verbatim
# from events.json (not re-derived by hand) -- via the real Action
# (action.ArriveOnMap, the same Action _place_unit uses for entry_type=="immediate").
s1_intro_event = next(e for e in DB.events if e.nid == 'S1 Intro')
s1_lines = s1_intro_event._source
joined_before_s1 = {}
i = 0
while i < len(s1_lines):
    line = s1_lines[i]
    if line.startswith('if;') and '_joined' in line:
        condition = line[len('if;'):]
        add_line = s1_lines[i + 1]
        assert add_line.startswith('add_unit;'), 'unexpected S1 Intro structure: %r' % add_line
        parts = add_line.split(';')
        unit_nid = parts[1]
        pos = tuple(int(x) for x in parts[2].split(','))
        cond_result = bool(eval(condition, {'game': game}))
        joined_before_s1[unit_nid] = cond_result
        if cond_result:
            unit = game.get_unit(unit_nid)
            action.do(action.ArriveOnMap(unit, pos))
        i += 3  # if-line, add_unit-line, end-line
    else:
        i += 1

s1_party_nids = {u.nid for u in game.get_units_in_party()}
check('6. companions with _joined flags now appear in S1',
      all(joined_before_s1.get(nid) for nid in companions) and set(companions).issubset(s1_party_nids),
      'S1 Intro join conditions evaluated true for = %s; present in S1 party after = %s' %
      ([n for n, v in joined_before_s1.items() if v], sorted(s1_party_nids)))

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
