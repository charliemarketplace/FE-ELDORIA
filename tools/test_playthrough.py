#!/usr/bin/env python3
"""
Real progression test, built on tools/play_harness.py.

Every one of the 12 existing behaviour suites asserts engine state via direct
action.do() calls. None of them ever call game.state.update() -- the actual
state machine that menus, prep screens, event dialogue, and level transitions
run on. This is the "core failure": a player never calls action.do() by hand,
they drive prep_main, Manage, the overworld, and combat through real input
events, and three real player-reported bugs lived entirely in that dispatch
layer:

1. Recruited companions disappear when re-entering an already-cleared level.
2. The prep-menu Market is never reachable in any Manage menu.
3. S3's overworld gate (2 units at internal level 5) is unreachable through
   normal play -- the only way to hit it is grinding the first fight.

This script drives a full campaign start for real: CAPITAL -> S1 -> (re-enter
S1, reproducing bug 1) -> S2, using the real prep menu, real dialogue/choice
screens, real combat (interaction.start_combat, not action.Die), and the real
overworld node-select/transition pipeline. Every assertion below is checked
against LIVE engine state reached by driving game.state.update(), not
re-derived from what the source *should* do.

Run with:
  uv run --no-project --python 3.12 --with pygame-ce --with typing-extensions python tools/test_playthrough.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import play_harness as harness

FAILURES = []
COMPANIONS = ['Kael', 'Elara', 'Ren', 'Briar']


def check(label, condition, detail):
    status = 'PASS' if condition else 'FAIL'
    print('[%s] %s: %s' % (status, label, detail))
    if not condition:
        FAILURES.append('%s -- %s' % (label, detail))
    return condition


def companions_in_party(game):
    party_nids = {u.nid for u in game.get_units_in_party()}
    return {nid: (nid in party_nids) for nid in COMPANIONS}


def companions_deployed(game):
    """A companion is "deployed" if it is actually placed on the level's map
    (unit.position is not None) -- present-in-roster is necessary but NOT
    sufficient; this is the assertion that catches bug 1 (companions sit in
    the registry with position=None forever after a level_reenter that never
    re-places them).
    """
    result = {}
    for nid in COMPANIONS:
        unit = game.get_unit(nid)
        result[nid] = bool(unit is not None and unit.position is not None)
    return result


def print_party_levels(game, label):
    print('--- party levels (%s) ---' % label)
    for u in sorted(game.get_units_in_party(), key=lambda u: u.nid):
        print('    %s: level=%d internal_level=%d exp=%d klass=%s' %
              (u.nid, u.level, u.get_internal_level(), u.exp, u.klass))


print('=' * 78)
print('PLAYTHROUGH -- driving the REAL state machine (prep/menus/events/overworld)')
print('=' * 78)

harness.boot()
from app.engine import game_state
from app.engine.game_state import game

# ---------------------------------------------------------------------------
# 1. Start a new game at CAPITAL, recruit all 4 companions via the REAL
#    dialogue/choice screens (CAPITAL Intro's GreetPick/RecruitX/FeatPick
#    player_choice prompts), not via action.SetGameVar shortcuts. CAPITAL's
#    level_start event never calls `prep` (it's a free-roam hub, not a
#    battle prep screen -- Manage/Market only exist inside S1-S5's prep_main,
#    checked in section 4 below), so this just waits for 'free' roam.
# ---------------------------------------------------------------------------
print('\n--- [1] Boot, start_level(CAPITAL), recruit companions via real choice screens ---')
game_state.start_level('CAPITAL')
harness.run_until(lambda g: harness.top_name() == 'free', max_frames=40000)
check('1. reached free (in-level) state after CAPITAL Intro', harness.top_name() == 'free',
      'state stack = %s' % game.state.state_names())

joined = companions_in_party(game)
check('1. all 4 companions recruited via real CAPITAL Intro choice screens',
      all(joined.values()), 'companions_in_party = %s' % joined)

print_party_levels(game, 'CAPITAL, pre-fight')

# ---------------------------------------------------------------------------
# 3. CAPITAL has no enemies -- win condition is the Depart region event ->
#    real save -> real overworld.
# ---------------------------------------------------------------------------
print('\n--- [3] Clear CAPITAL via its real Depart event, reach overworld ---')
harness.clear_capital(max_frames=40000)
harness.finish_win_and_reach_overworld_or_end(max_frames=40000)
check('3. reached the real overworld after CAPITAL', harness.top_name() == 'overworld',
      'state stack = %s' % game.state.state_names())

post_capital_present = companions_in_party(game)
check('3. all 4 companions still in party after the CAPITAL -> overworld transition',
      all(post_capital_present.values()), 'companions_in_party = %s' % post_capital_present)

# ---------------------------------------------------------------------------
# 4. Travel to S1 (first real combat level), clear via REAL combat.
# ---------------------------------------------------------------------------
print('\n--- [4] Travel to S1, reach prep, clear via real combat ---')
harness.travel_to_level_node('S1', max_frames=40000)
check('4. arrived at S1', game.level.nid == 'S1', 'game.level.nid = %r' % game.level.nid)

harness.goto_prep_main(max_frames=40000)
s1_deployed_before_fight = companions_deployed(game)
s1_present_before_fight = companions_in_party(game)
check('4. companions present in party on FIRST S1 visit (level_start add_unit path)',
      all(s1_present_before_fight.values()), 'companions_in_party = %s' % s1_present_before_fight)
check('4. companions actually deployed on the S1 map on FIRST visit',
      all(s1_deployed_before_fight.values()),
      'companions_deployed = %s' % s1_deployed_before_fight)

s1_manage_select = harness.enter_manage_and_select_unit('Rowan', max_frames=40000)
s1_select_options = [opt.get() for opt in s1_manage_select.select_menu.options]
s1_select_ignore = s1_manage_select.get_ignore()
check('4. Market reachable from S1 prep too',
      not s1_select_ignore[s1_select_options.index('Market')],
      'select_options=%s select_ignore=%s' % (s1_select_options, s1_select_ignore))
harness.back_out_of_prep_manage_select(max_frames=40000)

harness.leave_prep_by_fighting(max_frames=40000)
harness.win_current_level_by_combat()
harness.finish_win_and_reach_overworld_or_end(max_frames=40000)
check('4. reached the real overworld after S1', harness.top_name() == 'overworld',
      'state stack = %s' % game.state.state_names())

post_s1_present = companions_in_party(game)
check('4. all 4 companions still in party after the S1 -> overworld transition',
      all(post_s1_present.values()), 'companions_in_party = %s' % post_s1_present)

print_party_levels(game, 'after S1 clear')

# ---------------------------------------------------------------------------
# 5. Travel to S2 (forward progression continues), clear via real combat.
#    This -- CAPITAL -> S1 -> S2, no extra grinding -- is exactly the "normal
#    play" progression bug 3 asks about.
# ---------------------------------------------------------------------------
print('\n--- [5] Travel to S2, reach prep, clear via real combat ---')
harness.travel_to_level_node('S2', max_frames=40000)
check('5. arrived at S2', game.level.nid == 'S2', 'game.level.nid = %r' % game.level.nid)

harness.goto_prep_main(max_frames=40000)
s2_present = companions_in_party(game)
s2_deployed = companions_deployed(game)
check('5. companions present in party on S2 (level_start add_unit path)',
      all(s2_present.values()), 'companions_in_party = %s' % s2_present)
check('5. companions actually deployed on the S2 map',
      all(s2_deployed.values()), 'companions_deployed = %s' % s2_deployed)

harness.leave_prep_by_fighting(max_frames=40000)
harness.win_current_level_by_combat()
harness.finish_win_and_reach_overworld_or_end(max_frames=40000)
check('5. reached the real overworld after S2', harness.top_name() == 'overworld',
      'state stack = %s' % game.state.state_names())

print_party_levels(game, 'after S1 + S2 cleared normally (no extra grinding)')

# ---------------------------------------------------------------------------
# 6. THE BUG 3 REPRODUCTION: after normal (non-grinding) progression through
#    CAPITAL -> S1 -> S2, is S3's overworld gate actually passable? Checked
#    here, before the bug-1 re-entry detour below, so this reflects a single
#    clean playthrough rather than the extra re-entry fight.
# ---------------------------------------------------------------------------
print('\n--- [6] BUG 3 CHECK: is S3 reachable after NORMAL progression (no grinding)? ---')
s3_node = game.overworld_controller.nodes['S3']
qualifying = [u for u in game.get_units_in_party() if u.get_internal_level() >= s3_node.prefab.req_unit_level]
check('6. S3 node requirement is met after clearing CAPITAL -> S1 -> S2 normally '
      '(req_unit_count=%d, req_unit_level=%d)' % (s3_node.prefab.req_unit_count, s3_node.prefab.req_unit_level),
      game.overworld_controller.node_requirement_met(s3_node),
      'qualifying units (internal_level >= %d) = %s; full party internal levels = %s' %
      (s3_node.prefab.req_unit_level,
       [u.nid for u in qualifying],
       {u.nid: u.get_internal_level() for u in game.get_units_in_party()}))

# ---------------------------------------------------------------------------
# 7. THE BUG 1 REPRODUCTION: from S2's overworld position, travel BACK to
#    S1 (already cleared, next_level is now S2) -- a genuine re-entry, the
#    exact "go back and forth to other levels" the player described -- and
#    assert companions are still actually DEPLOYED on the map, not merely
#    present in the unit registry. This is the assertion that fails on
#    unfixed code: 'S1 Reenter' is bare `prep;0` with none of 'S1 Intro's
#    add_unit calls, so every companion's position stays None forever after
#    the first clean_up(full=True).
# ---------------------------------------------------------------------------
print('\n--- [7] BUG 1 REPRODUCTION: re-enter S1 from the overworld ---')
check('7. S1 is available as a re-entry (already cleared, not next_level)',
      harness.is_reentry_available('S1'),
      "is_level_launchable('S1', %r, %r)" % (game.overworld_controller.next_level, game.game_vars.get('_cleared_levels')))

harness.travel_to_level_node('S1', max_frames=40000)
check('7. re-entered S1', game.level.nid == 'S1', 'game.level.nid = %r' % game.level.nid)

harness.goto_prep_main(max_frames=40000)
reentry_present = companions_in_party(game)
reentry_deployed = companions_deployed(game)
check('7. companions still present in party after RE-ENTERING S1',
      all(reentry_present.values()), 'companions_in_party = %s' % reentry_present)
check('7. companions are actually DEPLOYED on the map after RE-ENTERING S1 '
      '(this is the assertion bug 1 breaks: present in the registry is not enough)',
      all(reentry_deployed.values()),
      'companions_deployed = %s (expected all True -- a companion with position=None '
      'is invisible/unusable even though get_units_in_party() still lists it)' % reentry_deployed)

reentry_options, reentry_ignore, _ = harness.get_prep_main_options()
print('    S1 re-entry prep_main options: %s (ignore=%s)' % (reentry_options, reentry_ignore))

# Re-clear S1 (grinding is an intended feature) to get back to the overworld
# cleanly.
harness.leave_prep_by_fighting(max_frames=40000)
harness.win_current_level_by_combat()
harness.finish_win_and_reach_overworld_or_end(max_frames=40000)
check('7. reached the real overworld after re-clearing S1', harness.top_name() == 'overworld',
      'state stack = %s' % game.state.state_names())

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
