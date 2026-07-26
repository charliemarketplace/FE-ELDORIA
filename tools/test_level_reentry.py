#!/usr/bin/env python3
"""
Execution-based proof that a cleared level can be re-entered from the
overworld -- driven directly against the LT engine (no browser, no
Playwright, no pygbag rebuild).

Bootstrap mirrors tools/test_capital_completion.py exactly (dummy SDL
drivers, real DB/RESOURCES load, real GameState save/pickle/load round
trip).

Run with:
  uv run --no-project --python 3.12 --with pygame-ce --with typing-extensions python tools/test_level_reentry.py
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


FAILURES = []


def check(label, condition, detail):
    status = 'PASS' if condition else 'FAIL'
    print('[%s] %s: %s' % (status, label, detail))
    if not condition:
        FAILURES.append('%s -- %s' % (label, detail))
    return condition


print('=' * 78)
print('LEVEL RE-ENTRY -- EXECUTION-BASED PROOF (real action.do() / DB / save calls)')
print('=' * 78)

# ---------------------------------------------------------------------------
# 1. Boot DB/RESOURCES, start S1 for real
# ---------------------------------------------------------------------------
print('\n--- [1] Boot DB/RESOURCES, game_state.start_level(\'S1\') ---')
# RESOURCES/DB already loaded and engine-chrome sprites/fonts already
# initialized by harness.boot() above.
game = game_state.start_level('S1')
check('1. start_level(S1)', game.level is not None and game.level.nid == 'S1',
      'game.level.nid = %r (expected S1)' % (game.level.nid if game.level else None))

# Imported only now: start_level() above already pulled in the full engine
# module graph in the right order (avoids a circular import through
# app.engine.icons / app.engine.graphics.text.text_renderer that trips up
# importing app.engine.overworld.overworld_states cold, before the engine
# package has been touched).
from app.engine.overworld.overworld_states import is_level_launchable

# ---------------------------------------------------------------------------
# 2. `_cleared_levels` starts empty/absent
# ---------------------------------------------------------------------------
print('\n--- [2] _cleared_levels starts empty/absent ---')
check('2. _cleared_levels absent or empty at level start',
      game.game_vars.get('_cleared_levels', set()) == set(),
      "game.game_vars.get('_cleared_levels', set()) = %r" % (game.game_vars.get('_cleared_levels', set()),))

# ---------------------------------------------------------------------------
# 3. Mark S1 cleared (mirrors EventState.level_end()'s new line) and prove the
#    set survives a save -> pickle round trip -> fresh GameState().load()
#    (game_vars is a PrimitiveCounter, pickled wholesale by game.save() --
#    no new save code needed for a set value).
# ---------------------------------------------------------------------------
print('\n--- [3] Mark S1 cleared, save -> pickle round trip -> fresh GameState().load() ---')
game.game_vars['_cleared_levels'] = game.game_vars.get('_cleared_levels', set()) | {'S1'}
check('3. _cleared_levels contains S1 pre-save',
      game.game_vars.get('_cleared_levels') == {'S1'},
      "game.game_vars.get('_cleared_levels') = %r" % (game.game_vars.get('_cleared_levels'),))

s_dict, meta_dict = game.save()

tmp_fd, tmp_path = tempfile.mkstemp(prefix='lt_reentry_test_', suffix='.p')
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

post_load_cleared = fresh_game.game_vars.get('_cleared_levels')
check('3. _cleared_levels round-trips through save/pickle/load intact',
      post_load_cleared == {'S1'} and isinstance(post_load_cleared, set),
      "post-load game_vars.get('_cleared_levels') = %r (type=%s)" %
      (post_load_cleared, type(post_load_cleared).__name__))

# ---------------------------------------------------------------------------
# 4. DB.events.get('level_reenter', 'S1') returns the new prep event, and
#    DB.events.get('level_start', 'S1') still returns S1 Intro -- proves
#    trigger substitution actually selects a different event.
# ---------------------------------------------------------------------------
print('\n--- [4] DB.events.get selects level_reenter vs level_start distinctly for S1 ---')
reenter_events = DB.events.get('level_reenter', 'S1')
start_events = DB.events.get('level_start', 'S1')

check('4. DB.events.get(level_reenter, S1) returns exactly the new prep event',
      len(reenter_events) == 1 and reenter_events[0].nid == 'S1 Reenter',
      'reenter_events = %s' % [e.nid for e in reenter_events])

reenter_script = '\n'.join(reenter_events[0]._source) if reenter_events else ''
# S1 Reenter's _source still contains prep;0 (the Manage/Formation/Save entry
# point), reached on an Unsafe revisit -- and leads with the same conditional
# add_unit re-placement blocks S1 Intro uses. Before the bug-1 fix this was
# bare ['prep;0']: a companion recruited earlier never got re-placed on a
# revisited level, so their position stayed None forever after the first
# clean_up(full=True) -- present in game.get_units_in_party() but invisible
# and undeployable. tools/test_playthrough.py proves the effect at runtime
# (a real re-entry with a real party); this proves the fix is actually
# present in the authored content, not just coincidentally working.
#
# As of the Safe/Unsafe fix (BACKLOG_AUDIT.md item 6), prep;0 is no longer
# unconditionally the last line: an Unsafe roll (game_vars['_pending_
# unsafe_encounter'] == 'S1') places the main squad + a generated squad and
# proceeds to prep for a real fight; a Safe roll skips straight to
# win_game with no fight. Check both halves are actually present, rather
# than pinning the old unconditional shape.
#
# S2 (checked further below in the branched_levels loop) carries the
# deploy-cap fix instead (BACKLOG_AUDIT.md item 3 / adversarial-review
# finding 1): its Intro and Unsafe-reentry branch both call `prep;1`
# (pick_units_enabled=True), not the bare `prep;0` every other level's prep
# event still uses -- `_prep_pick` seeded by `max_deploy` on S2's
# levels.json entry would otherwise be immediately stomped back to False by
# an unconditional `prep;0`, exactly the "inert cap" bug BACKLOG_AUDIT.md #3
# describes. (Authored on S2, not S1: tools/test_deploy_cap.py hard-codes
# S1 as its own zero-migration regression fixture, so declaring max_deploy
# on S1 would falsify that suite's premise instead.)
# tools/test_playthrough.py drives the real Pick Units screen and proves
# the cap actually refuses a unit; this only proves the authored content
# actually asks for it.
check('4. S1 Reenter still reaches prep;0 (Manage/Formation/Save entry point) on an Unsafe roll',
      reenter_events and 'prep;0' in reenter_events[0]._source,
      'S1 Reenter _source = %r' % (reenter_events[0]._source if reenter_events else None,))
check('4. S1 Reenter branches on the Safe/Unsafe pending-encounter flag',
      reenter_events and "_pending_unsafe_encounter" in reenter_script and 'win_game' in reenter_events[0]._source,
      'S1 Reenter _source = %r' % (reenter_events[0]._source if reenter_events else None,))
check('4. S1 Reenter now re-places every recruitable companion, mirroring S1 Intro',
      reenter_events and all('add_unit;%s;' % nid in reenter_script for nid in ('Kael', 'Elara', 'Ren', 'Briar')),
      'S1 Reenter _source = %r' % (reenter_events[0]._source if reenter_events else None,))

check('4. DB.events.get(level_start, S1) still includes S1 Intro, unaffected',
      any(e.nid == 'S1 Intro' for e in start_events),
      'start_events = %s' % [e.nid for e in start_events])

# Also assert the analogous events exist for S2-S5, and that hub levels
# (CAPITAL, SHUB) were deliberately NOT given a level_reenter event.
#
# S2/S3/S4 now carry the same Safe/Unsafe branch as S1 (adversarial-review
# finding 2: an Unsafe roll used to be a no-op past S1, and the pending flag
# leaked into saves forever) -- each has its own `<lvl>_UnsafeSquad`
# procedural unit_group (levels.json) added into the Unsafe half via
# add_group, and both halves still end in 'end', not a bare trailing
# 'prep;0'. S5 is a known exception: it is the campaign's last level
# (go_to_overworld: false, last entry in levels.json), so a first clear
# routes straight to 'title_start' and never revisits the overworld --
# 'S5 Reenter' can therefore never actually fire in real play (confirmed by
# tracing EventState.level_end()'s routing and is_level_launchable's
# reentry gate), so it was deliberately left as the original unconditional
# prep;0 rather than authoring dead content for it.
branched_levels = {
    'S2': 'S2_UnsafeSquad',
    'S3': 'S3_UnsafeSquad',
    'S4': 'S4_UnsafeSquad',
}
for lvl, unsafe_group in branched_levels.items():
    lvl_reenter = DB.events.get('level_reenter', lvl)
    lvl_reenter_script = '\n'.join(lvl_reenter[0]._source) if lvl_reenter else ''
    check('4. %s has exactly one level_reenter prep event' % lvl,
          len(lvl_reenter) == 1,
          '%s level_reenter events = %s' % (lvl, [(e.nid, e._source) for e in lvl_reenter]))
    check('4. %s level_reenter branches on the Safe/Unsafe pending-encounter flag' % lvl,
          lvl_reenter and "_pending_unsafe_encounter" in lvl_reenter_script and 'win_game' in lvl_reenter_script,
          '%s level_reenter _source = %r' % (lvl, lvl_reenter[0]._source if lvl_reenter else None))
    check('4. %s level_reenter places a generated Unsafe squad on the Unsafe branch, not a no-op' % lvl,
          lvl_reenter and 'add_group;%s' % unsafe_group in lvl_reenter_script,
          '%s level_reenter _source = %r' % (lvl, lvl_reenter[0]._source if lvl_reenter else None))
    check('4. %s level_reenter re-places its Intro\'s companions too' % lvl,
          lvl_reenter and 'add_unit;Kael;' in lvl_reenter_script,
          '%s level_reenter _source = %r' % (lvl, lvl_reenter[0]._source if lvl_reenter else None))

# S2 carries the deploy-cap fix (see comment above [4]): both its Intro and
# this Unsafe branch call `prep;1`, and its levels.json entry actually
# declares max_deploy/min_deploy -- unlike every other level, which still
# has neither field set.
s2_intro_script = '\n'.join(DB.events.get('level_start', 'S2')[0]._source)
check('4. S2 Intro reaches prep;1 (Pick Units enabled), not the bare prep;0',
      'prep;1' in s2_intro_script,
      'S2 Intro _source = %r' % s2_intro_script)
s2_reenter_unsafe_script = '\n'.join(DB.events.get('level_reenter', 'S2')[0]._source)
check('4. S2 Reenter Unsafe branch also reaches prep;1',
      'prep;1' in s2_reenter_unsafe_script,
      'S2 Reenter _source = %r' % s2_reenter_unsafe_script)
s2_prefab = DB.levels.get('S2')
check('4. S2 levels.json entry actually declares max_deploy/min_deploy (not just seeded at runtime)',
      s2_prefab.max_deploy == 3 and s2_prefab.min_deploy == 1,
      'S2 max_deploy=%r min_deploy=%r' % (s2_prefab.max_deploy, s2_prefab.min_deploy))
for other in ('S1', 'S3', 'S4', 'S5'):
    other_prefab = DB.levels.get(other)
    check('4. %s levels.json entry still has no max_deploy/min_deploy set (only S2 does)' % other,
          other_prefab.max_deploy is None and other_prefab.min_deploy is None,
          '%s max_deploy=%r min_deploy=%r' % (other, other_prefab.max_deploy, other_prefab.min_deploy))

# S3/S2 additionally re-place a mid-level recruit (Ysolde/Tamsin respectively)
# who is NOT part of S1's four CAPITAL companions -- adversarial-review
# finding 3: LevelObject.from_prefab re-places every registered unit at its
# ORIGINAL level-prefab starting_position, so a recruited Tamsin/Ysolde
# (originally placed on the enemy team at a specific tile) would otherwise
# reappear at that old enemy-side tile, amid respawned enemies, on revisit.
s2_reenter_script = '\n'.join(DB.events.get('level_reenter', 'S2')[0]._source)
check('4. S2 level_reenter re-places recruited Tamsin too (not just the CAPITAL four)',
      'add_unit;Tamsin;' in s2_reenter_script,
      'S2 level_reenter _source = %r' % s2_reenter_script)
s3_reenter_script = '\n'.join(DB.events.get('level_reenter', 'S3')[0]._source)
check('4. S3 level_reenter re-places recruited Ysolde too (not just the CAPITAL four)',
      'add_unit;Ysolde;' in s3_reenter_script,
      'S3 level_reenter _source = %r' % s3_reenter_script)

# S5 (unreachable in real play, see comment above) keeps its original,
# unbranched shape -- pin that explicitly so a future edit that silently
# changes it gets noticed.
s5_reenter = DB.events.get('level_reenter', 'S5')
check('4. S5 level_reenter (dead content -- never reachable) is unchanged: still ends in bare prep;0',
      len(s5_reenter) == 1 and s5_reenter[0]._source[-1] == 'prep;0',
      'S5 level_reenter events = %s' % [(e.nid, e._source) for e in s5_reenter])

for hub in ('CAPITAL', 'SHUB'):
    hub_reenter = DB.events.get('level_reenter', hub)
    check('4. hub level %s was NOT given a level_reenter event' % hub,
          len(hub_reenter) == 0,
          '%s level_reenter events = %s' % (hub, [e.nid for e in hub_reenter]))

# ---------------------------------------------------------------------------
# 5. The launchable predicate (app.engine.overworld.overworld_states.
#    is_level_launchable, the exact function OverworldFreeState.take_input
#    uses to decide whether SELECT on a node may launch a level): with
#    _cleared_levels={'S1'} and next_level='S2', an S1 node is launchable
#    AND an uncleared S3 node is not.
# ---------------------------------------------------------------------------
print('\n--- [5] is_level_launchable predicate ---')
cleared = {'S1'}
next_level = 'S2'
check('5. cleared S1 node is launchable even though it is not next_level',
      is_level_launchable('S1', next_level, cleared) is True,
      "is_level_launchable('S1', 'S2', {'S1'}) = %r" % (is_level_launchable('S1', next_level, cleared),))
check('5. next_level S2 node is launchable',
      is_level_launchable('S2', next_level, cleared) is True,
      "is_level_launchable('S2', 'S2', {'S1'}) = %r" % (is_level_launchable('S2', next_level, cleared),))
check('5. uncleared, non-next-level S3 node is NOT launchable',
      is_level_launchable('S3', next_level, cleared) is False,
      "is_level_launchable('S3', 'S2', {'S1'}) = %r" % (is_level_launchable('S3', next_level, cleared),))

# ---------------------------------------------------------------------------
# 6. _next_level_nid survives a re-clear -- driven through the REAL
#    EventState.level_end() (app/events/event_state.py), not a hand-copied
#    simulation. level_end() takes no state from `self`, so it can be called
#    directly on a bare EventState() the same way TurnChangeState's win-game
#    path calls it for real.
#
#    Story progress must never rewind: a first clear of S1 must advance
#    _next_level_nid to the next level in DB.levels order, and a LATER
#    re-clear of S1 (story already past it, _next_level_nid pointing at
#    S4) must leave _next_level_nid exactly where it was -- this is the
#    campaign-progress regression BACKLOG_AUDIT.md records as just fixed
#    (was_already_cleared computed before the cleared-set is updated).
# ---------------------------------------------------------------------------
print('\n--- [6] _next_level_nid via the REAL EventState.level_end() ---')
from app.events.event_state import EventState

event_state = EventState()

# Clean slate for this section, independent of section 3's save-round-trip
# fixture above.
game.game_vars['_cleared_levels'] = set()
game.game_vars['_next_level_nid'] = None
game.game_vars['_goto_level'] = None

s1_index = DB.levels.index('S1')
expected_first_clear_next = DB.levels[s1_index + 1].nid

event_state.level_end()
check('6. first clear of S1 marks it cleared',
      'S1' in game.game_vars.get('_cleared_levels', set()),
      "game_vars['_cleared_levels'] = %r" % (game.game_vars.get('_cleared_levels'),))
check('6. first clear of S1 advances _next_level_nid to the next level in DB.levels order',
      game.game_vars.get('_next_level_nid') == expected_first_clear_next,
      "game_vars['_next_level_nid'] = %r (expected %r)" %
      (game.game_vars.get('_next_level_nid'), expected_first_clear_next))

# Re-enter S1 for real (the same call an Unsafe overworld revisit makes) and
# simulate story progress having continued past it in the meantime.
game.start_level('S1')
game.game_vars['_next_level_nid'] = 'S4'

event_state.level_end()
check('6. re-clearing an already-cleared S1 does NOT rewind _next_level_nid',
      game.game_vars.get('_next_level_nid') == 'S4',
      "game_vars['_next_level_nid'] = %r (expected unchanged S4)" % (game.game_vars.get('_next_level_nid'),))

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
