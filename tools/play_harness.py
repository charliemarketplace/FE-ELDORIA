#!/usr/bin/env python3
"""
Reusable headless harness for driving the REAL Lex Talionis state machine.

The 12 existing behaviour suites (test_capital_completion.py, test_merchant.py,
etc.) all boot the engine the same way, then call action.do(action.Foo(...))
directly. That proves the underlying Action/DB plumbing works, but it never
touches game.state -- the actual state machine that menus, prep screens, event
dialogue, and level transitions run on. A player never calls action.do(); they
press buttons that a State.take_input() turns into an event string, which the
StateMachine dispatches. Bugs that live entirely in that dispatch layer (a menu
option that's gated off, a scripted re-entry event that doesn't restore unit
positions) are invisible to a test that skips it.

This module extracts the common SDL/DB bootstrap once, and adds a small,
honest driver for the real state machine:

- `boot()`: RESOURCES/DB load, dummy SDL, fonts, sprite chrome.
- `frame(event)`: exactly one real engine frame -- engine.update_time() then
  game.state.update(event, surf), following 'repeat' chains the same way
  app/engine/driver.py's real game loop does.
- `run_until(predicate, choose=None)`: pumps frames, auto-skipping dialogue
  ('event' state -> sends 'START', the real skip button) and auto-answering
  player_choice screens (defaults to whatever is already under the cursor,
  i.e. the first non-ignored option) until predicate(game) is true.
- Prep-menu helpers that read the ACTUAL live option lists
  (PrepMainState.populate_options(), PrepManageSelectState's select_menu +
  get_ignore()) rather than re-deriving what *should* be on screen.
- Level-clear helpers that resolve real combat (interaction.start_combat with
  skip=True -- real hit/damage/exp via SimpleCombat, not a scripted kill) and
  drive the real overworld node-select -> transition -> next-level pipeline.

Every helper here calls into production engine code (action.py Actions,
game.events.trigger*, game.state.update, interaction.start_combat). Nothing
here reimplements engine behaviour by hand.

Run any script built on this with:
  uv run --no-project --python 3.12 --with pygame-ce --with typing-extensions python <file>
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

sys.frozen = True
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
os.makedirs('saves', exist_ok=True)

_booted = False

# How much faster than real wall-clock time the engine's internal clock runs.
# Several real states (TitleSaveState's 1250ms post-SELECT wait, transition
# fades) are paced by app.engine.engine.get_time(), which is wall-clock based.
# app.engine.engine already ships a "fast-forward" multiplier for the web
# build (driver.py's 1/2/5 hotkeys) -- we reuse that same knob instead of
# monkeypatching time, so every wait still actually elapses, just faster.
TIME_SCALE = 40


def boot():
    """Idempotent: RESOURCES/DB load, dummy SDL video/audio, fonts, sprite
    chrome. Every test built on this harness should call this first (in place
    of hand-rolling the ~15 line bootstrap the 12 existing suites duplicate).
    """
    global _booted
    if _booted:
        return
    from app.data.resources.resources import RESOURCES
    from app.data.database.database import DB
    from app.data.serialization.versions import CURRENT_SERIALIZATION_VERSION

    import pygame
    pygame.init()
    pygame.display.set_mode((240, 160))

    RESOURCES.load('lion_throne.ltproj', CURRENT_SERIALIZATION_VERSION)
    DB.load('lion_throne.ltproj', CURRENT_SERIALIZATION_VERSION)

    # Harness quirk (not a gameplay bug), inherited from the existing suites:
    # RESOURCES.load() resets app.sprites.SPRITES without re-running
    # app.engine.sprites.load_images(), so engine-chrome sprites crash on
    # import unless this is re-run. Driving the real state machine also
    # actually calls State.draw(), which the 12 existing suites never did --
    # that additionally requires app.engine.fonts.load_fonts() (draw() reads
    # FONT[...] directly), which none of them needed either.
    import app.engine.sprites as engine_sprites
    engine_sprites.load_images()
    from app.engine import fonts
    fonts.load_fonts()

    from app.engine import engine as engine_mod
    engine_mod.set_time_scale(TIME_SCALE)

    _booted = True


def get_surf():
    from app.constants import WINWIDTH, WINHEIGHT
    from app.engine import engine as engine_mod
    return engine_mod.create_surface((WINWIDTH, WINHEIGHT))


def frame(event=None):
    """Advance exactly one real engine frame: engine.update_time() (advances
    the wall-clock-derived internal timer every real state's fades/waits read)
    then game.state.update(event, surf), following any 'repeat' chain the
    state machine returns -- exactly what app/engine/driver.py's real game
    loop does every tick. Returns the resulting state name stack.
    """
    from app.engine.game_state import game
    from app.engine import engine as engine_mod
    engine_mod.update_time()
    surf = get_surf()
    surf, repeat = game.state.update(event, surf)
    guard = 0
    while repeat and guard < 200:
        surf, repeat = game.state.update([], surf)
        guard += 1
    return game.state.state_names()


def top_name():
    from app.engine.game_state import game
    cur = game.state.current_state()
    return cur.name if cur else None


def default_choose(_state):
    """Default player_choice handler: leaves the cursor wherever it starts
    (idx 0 -- the first non-ignored option) and lets run_until send SELECT.
    Good enough to recruit every CAPITAL companion (each 'Yes'/first-pool
    option is index 0) and to answer S2's Gambit choice.
    """
    return None


# States that present the player with a single confirm-with-SELECT screen
# (a Choice-family menu defaulting to index 0) reached via scripted content
# this harness drives through (CAPITAL Intro's recruit dialogue, its
# per-companion class/feat wizard). Auto-answering these is the same kind of
# "accept the default" auto-pilot as player_choice -- some of these
# (class_change_choice, promotion_choice) need the same state re-entered
# twice in a row (first SELECT opens a Change/Cancel child menu, second
# confirms it), which naturally falls out of run_until re-checking the top
# state name every frame.
AUTO_SELECT_STATES = frozenset({
    'player_choice', 'class_change_choice', 'promotion_choice', 'feat_choice',
})

# States that resolve on their own (fades, exp bars, death animations) given
# enough real time -- but AlertState.take_input specifically only checks its
# auto-dismiss timer when `event` is truthy (app/engine/general_states.py),
# so a purely None-input auto-pilot would stall on it forever. 'INFO' is a
# harmless real input for every other state we might pass through.
NEEDS_NONEMPTY_INPUT_STATES = frozenset({'alert'})


def run_until(predicate, max_frames=20000, choose=None, sleep=0.0002):
    """Pump frames until predicate(game) is true, auto-piloting the kinds of
    state that would otherwise stall a scripted run forever:

    - 'event' (dialogue/cutscene): sends 'START' once per event instance,
      the real skip-dialogue button (Event.skip()), then None afterwards.
    - AUTO_SELECT_STATES (player_choice, class/promotion choice, feat
      choice): invokes `choose(state)` (defaults to a no-op, i.e. "accept
      whatever's under the cursor") then sends 'SELECT'.

    Every other state gets a plain None input -- exactly like a player who
    isn't touching any button, but time (and therefore fades/timers/AI) still
    advances every frame.

    Raises TimeoutError with the current state stack if predicate never
    becomes true within max_frames -- this is the harness surfacing a real
    stuck state, not something to raise max_frames blindly past.

    Deliberately checks the predicate AFTER pumping a frame, never before.
    game.state.change(...)/back()/clear() only ever append to
    StateMachine.temp_state; the visible state stack (and each new state's
    started/begin()) is not updated until the NEXT state.update() call's
    process_temp_state(). Code that queues a state change synchronously
    outside the state machine (e.g. interaction.start_combat(), which calls
    game.state.change('combat') then runs the entire SimpleCombat resolution
    -- damage, death, exp -- in its own constructor before returning) leaves
    the OLD state as game.state.current_state() until frame() is actually
    called. A predicate-first loop can therefore return "satisfied"
    immediately without ever having pumped the frame that would apply those
    queued changes (e.g. finalizing a defeated unit's death via the 'dying'
    state) -- silently skipping the very thing the caller was waiting for.
    """
    from app.engine.game_state import game
    choose = choose or default_choose
    skip_sent = False
    for _ in range(max_frames):
        name = top_name()
        if name == 'event':
            ev = 'START' if not skip_sent else None
            skip_sent = True
        elif name in AUTO_SELECT_STATES:
            skip_sent = False
            choose(game.state.current_state())
            ev = 'SELECT'
        elif name in NEEDS_NONEMPTY_INPUT_STATES:
            skip_sent = False
            ev = 'INFO'
        else:
            skip_sent = False
            ev = None
        frame(ev)
        # A state that was JUST pushed by that frame's change() sits in
        # game.state.state already but hasn't had start()/begin() called yet
        # (StateMachine.update() only does that on the state's own first
        # update() call). Don't report the predicate satisfied on a state
        # that hasn't actually started -- its instance attributes (e.g.
        # PrepManageSelectState.select_menu) may not exist yet.
        cur = game.state.current_state()
        if predicate(game) and (cur is None or cur.started):
            return True
        if sleep:
            time.sleep(sleep)
    raise TimeoutError(
        "run_until: predicate not satisfied after %d frames; state stack=%s"
        % (max_frames, game.state.state_names()))


# ---------------------------------------------------------------------------
# Prep menu helpers -- read the ACTUAL live option lists, not a re-derivation
# of what should be there.
# ---------------------------------------------------------------------------

def goto_prep_main(max_frames=20000, choose=None):
    """Pumps until 'prep_main' is top of stack (works from level boot, from
    mid-event, or from anywhere else -- run_until's auto-pilot handles
    whatever dialogue/choices lead there)."""
    run_until(lambda g: top_name() == 'prep_main', max_frames=max_frames, choose=choose)


def get_prep_main_options():
    """The real PrepMainState.populate_options() output: (options, ignore,
    events), read off the live state instance (must be top of stack)."""
    from app.engine.game_state import game
    state = game.state.current_state()
    assert state.name == 'prep_main', "top state is %r, not prep_main" % (state.name if state else None)
    return state.populate_options()


def select_prep_main_option(label):
    """Selects `label` in the live PrepMainState menu and presses SELECT --
    the real Choice.set_selection()+take_input() path, not a shortcut."""
    from app.engine.game_state import game
    state = game.state.current_state()
    assert state.name == 'prep_main', "top state is %r, not prep_main" % (state.name if state else None)
    state.menu.set_selection(label)
    frame('SELECT')


def enter_manage_and_select_unit(unit_nid, max_frames=20000, choose=None):
    """From prep_main: selects Manage, waits for prep_manage, selects the
    given unit, waits for prep_manage_select, and returns that live State
    instance (its .select_menu / .get_ignore() are the actual menu the player
    would see for that unit)."""
    from app.engine.game_state import game
    select_prep_main_option('Manage')
    run_until(lambda g: top_name() == 'prep_manage', max_frames=max_frames, choose=choose)
    manage_state = game.state.current_state()
    unit = game.get_unit(unit_nid)
    manage_state.menu.set_selection(unit)
    frame('SELECT')
    run_until(lambda g: top_name() == 'prep_manage_select', max_frames=max_frames, choose=choose)
    return game.state.current_state()


def back_out_of_prep_manage_select(max_frames=20000, choose=None):
    """BACK, BACK: prep_manage_select -> prep_manage -> prep_main."""
    frame('BACK')
    run_until(lambda g: top_name() == 'prep_manage', max_frames=max_frames, choose=choose)
    frame('BACK')
    run_until(lambda g: top_name() == 'prep_main', max_frames=max_frames, choose=choose)


def leave_prep_by_fighting(max_frames=20000, choose=None):
    """Selects 'Fight' in the live prep_main menu and drives forward (through
    whatever post-prep dialogue the level's intro/reenter event still has,
    via run_until's auto-skip) until the level's real 'free' gameplay state is
    reached."""
    select_prep_main_option('Fight')
    run_until(lambda g: top_name() == 'free', max_frames=max_frames, choose=choose)


# ---------------------------------------------------------------------------
# Level clearing -- real event dispatch (CAPITAL's Depart region event) or
# real combat resolution (everywhere else).
# ---------------------------------------------------------------------------

def clear_capital(max_frames=20000, choose=None):
    """CAPITAL has no enemies -- its only win condition is stepping into the
    'Depart' region, which calls win_game (see lion_throne.ltproj/game_data/
    events.json, 'CAPITAL Depart'). Driving an actual player walk onto that
    region tile needs full overworld-style pathing simulation for no payoff
    (the bugs under test are about menus/persistence, not footpath grids), so
    this fires the same named event a real region-step would
    (game.events.trigger_specific_event -- the exact call PrepMainState's own
    custom options and OverworldPartyOptionMenu use), then drives the result
    for real."""
    from app.engine.game_state import game
    assert game.level.nid == 'CAPITAL'
    did = game.events.trigger_specific_event('CAPITAL Depart')
    assert did, "CAPITAL Depart event did not fire"
    run_until(lambda g: top_name() == 'title_save', max_frames=max_frames, choose=choose)


# States a resolving combat can pass through before settling: 'combat'
# itself, 'wait' (WaitState, a single-frame pop), 'dying' (a real-time death
# fade), 'exp' (a level-up bar), and 'alert' (a banner, e.g. a dropped item).
_COMBAT_TRANSIENT_STATES = frozenset({'combat', 'wait', 'dying', 'exp', 'alert'})


def _find_adjacent_free_tile(pos):
    from app.engine.game_state import game
    x, y = pos
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        p = (x + dx, y + dy)
        if game.tilemap.check_bounds(p) and not game.board.get_unit(p):
            return p
    return None


def win_current_level_by_combat(max_attacks=6000, max_stale_passes=200, max_frames_per_combat=1000):
    """Resolves the level's fight through the real combat pipeline
    (interaction.start_combat(..., skip=True), which is app/engine/combat's
    SimpleCombat -- genuine hit/miss rolls, genuine damage, genuine exp gain,
    genuine CombatEnd trigger dispatch) until no enemies remain.

    Simplification made for the harness (not a bypass of combat itself):
    attackers are teleported adjacent to their target instead of walking
    there (grid pathing is orthogonal to the bugs under test), and each
    attacker is healed to full before their strike so a string of kills
    isn't derailed by an earlier round's counter damage compounding into a
    death the player never had a chance to prevent -- a real player fighting
    one battle at a time wouldn't stack chip damage like a scripted loop
    does. Hit chance, damage, and experience are all real.

    Targets the lowest-current-HP enemy first (likeliest to die soonest,
    same instinct a real player has when triaging a fight), and rotates
    through every deployed unit against that target before giving up on it
    for the pass -- a squad's weapon mights vary (an Iron Sword vs a unit
    with matching DEF nets 0-1 damage; a Fighter's Iron Axe against the same
    target might not), so always leading with the same attacker can stall
    forever on a matchup the rest of the squad would have no trouble with.
    """
    from app.engine.game_state import game
    from app.engine import action
    from app.engine.combat import interaction

    attempts = 0
    stale_passes = 0
    while game.get_enemy_units():
        deployed = [u for u in game.get_units_in_party() if u.position and not u.dead and u.get_hp() > 0]
        if not deployed:
            raise RuntimeError("win_current_level_by_combat: no living deployed unit left to attack with")

        enemies_by_hp = sorted(game.get_enemy_units(), key=lambda u: u.get_hp())
        made_progress = False
        for enemy in enemies_by_hp:
            hp_before = enemy.get_hp()
            for attacker in deployed:
                attempts += 1
                if attempts > max_attacks:
                    raise RuntimeError(
                        "win_current_level_by_combat: exceeded %d attack attempts with enemies still alive: %s"
                        % (max_attacks, [u.nid for u in game.get_enemy_units()]))

                weapon = attacker.get_weapon()
                if weapon is None:
                    continue
                action.do(action.SetHP(attacker, attacker.get_max_hp()))
                adj = _find_adjacent_free_tile(enemy.position)
                if adj is None:
                    continue
                action.do(action.Teleport(attacker, adj))
                interaction.start_combat(attacker, enemy.position, weapon, skip=True)
                # Combat doesn't finish settling the instant interaction.
                # start_combat() returns -- a defeated defender's death is
                # finalized by DyingState/game.death.update() (a real-time
                # fade, see app/engine/death.py), which SimpleCombat.
                # clean_up() only QUEUES (state stack ends up ['free',
                # 'wait', 'dying', ...]) rather than applying immediately.
                # Wait until the state machine is out of every transient
                # state that chain can produce -- including 'exp' (a
                # level-up) and 'alert' -- so the death/exp actually lands
                # before we inspect the enemy's hp/liveness below.
                run_until(lambda g: top_name() not in _COMBAT_TRANSIENT_STATES,
                          max_frames=max_frames_per_combat)

                if top_name() in ('title_save', 'title_start') or game.level is None:
                    # Killing this enemy was the last one -- the level's own
                    # WinGame event fired and EventState.level_end() already
                    # cleared the level. Nothing left for this helper to do;
                    # the caller drives the save/overworld transition.
                    return

                if enemy not in game.get_enemy_units():
                    made_progress = True
                    break  # enemy died -- move on to the next target
                if enemy.get_hp() < hp_before:
                    made_progress = True
                    break  # dealt real damage -- let the next pass continue softening it up
                # A 0-hp-change attempt is not necessarily a stalled matchup
                # -- most weapons carry a real (non-100%) hit chance, so a
                # miss looks identical to a genuine 0-damage matchup here.
                # Keep cycling through the rest of the squad this pass
                # before concluding anything.
            if made_progress:
                break  # re-sort enemies by HP and start the next pass
        if made_progress:
            stale_passes = 0
        else:
            stale_passes += 1
            if stale_passes > max_stale_passes:
                raise RuntimeError(
                    "win_current_level_by_combat: no deployed unit dealt any damage to any "
                    "remaining enemy (%s) in %d consecutive passes over the whole squad (%s) -- "
                    "this looks like a genuinely un-damageable matchup, not bad luck"
                    % ([u.nid for u in game.get_enemy_units()], max_stale_passes, [u.nid for u in deployed]))

    # Not every level's win condition is "combat_end with zero enemies left"
    # (S2's only scripted win path is the project-wide 'Global Escape' event,
    # a retreat map -- defeating every enemy on the field does not, by
    # itself, trigger anything). If we're still mid-level after clearing the
    # field, fall back to the same escape path a player retreating off the
    # map would use.
    if game.level is not None and top_name() not in ('title_save', 'title_start'):
        escape_all_units()


def escape_all_units(max_frames_per_escape=2000):
    """Mirrors the project-wide 'Global Escape' event (level_nid: null,
    trigger: 'Escape', fired by stepping a unit onto an Escape-type region):
    remove each remaining player unit from the field and re-fire that named
    event with it bound as `unit`, exactly like `trigger_specific_event`'s
    real templating does for any other custom-triggered event. The event's
    own condition (`not any(unit.team == 'player' for unit in game.units if
    unit.position)`) calls win_game once the last one is gone -- same
    real event dispatch as every other win path in this module, just without
    needing to simulate walking each unit onto the escape tile.
    """
    from app.engine.game_state import game

    while True:
        on_field = [u for u in game.get_units_in_party() if u.position]
        if not on_field:
            break
        unit = on_field[0]
        # The event itself runs `remove_unit;{unit}` as its first command --
        # don't remove it here too, that would just make the real command
        # log a harmless-but-noisy "Unit not on map!" error.
        did = game.events.trigger_specific_event('Global Escape', unit=unit)
        if not did:
            raise RuntimeError(
                "escape_all_units: 'Global Escape' event did not fire for %r" % unit.nid)
        run_until(lambda g: top_name() not in _COMBAT_TRANSIENT_STATES.union({'event'}),
                  max_frames=max_frames_per_escape)
        if top_name() in ('title_save', 'title_start') or game.level is None:
            return


def finish_win_and_reach_overworld_or_end(max_frames=20000, choose=None):
    """After a level-ending win_game (either clear_capital's Depart event or
    win_current_level_by_combat's last kill) has fired, EventState.level_end()
    clears the state stack and pushes 'title_save'. Drives the real save-slot
    SELECT (TitleSaveState.take_input) and then the timed auto-transition
    (TitleSaveState.update(), paced by the same real-time clock sped up by
    TIME_SCALE) into 'overworld' -- or 'title_start' if this was the last
    level (S5's go_to_overworld is False and it's the final entry in
    levels.json, matching EventState.level_end()'s "No more levels!" branch).
    """
    run_until(lambda g: top_name() == 'title_save', max_frames=max_frames, choose=choose)
    frame('SELECT')  # choose the current save slot, starts TitleSaveState's real wait timer
    run_until(lambda g: top_name() in ('overworld', 'title_start'), max_frames=max_frames, choose=choose)


# ---------------------------------------------------------------------------
# Overworld navigation -- real node-select -> real transition.
# ---------------------------------------------------------------------------

def travel_to_level_node(level_nid, max_frames=20000, choose=None):
    """From the 'overworld' state: teleports the cursor onto the node for
    `level_nid` (game.cursor.set_pos -- the same call OverworldFreeState's
    own BACK handler uses to flick the cursor to the party, i.e. a real
    supported cursor operation, not a private field write) and presses
    SELECT, which is OverworldFreeState.take_input's real branch for both
    "launch next level" and "re-enter a cleared level". Then drives the real
    OverworldMovement -> OverworldLevelTransition -> start_level_asset_loading
    pipeline until game.level.nid == level_nid.
    """
    from app.engine.game_state import game
    run_until(lambda g: top_name() == 'overworld', max_frames=max_frames, choose=choose)
    node = game.overworld_controller.node_by_level(level_nid)
    assert node is not None, "no overworld node found for level %r" % level_nid
    game.cursor.set_pos(node.position)
    frame('SELECT')
    run_until(lambda g: g.level is not None and g.level.nid == level_nid, max_frames=max_frames, choose=choose)


def is_reentry_available(level_nid):
    """Whether `level_nid` is currently selectable as a re-entry (i.e. it is
    cleared and is not the story's next level) -- the exact predicate
    OverworldFreeState.take_input uses."""
    from app.engine.game_state import game
    from app.engine.overworld.overworld_states import is_level_launchable
    return is_level_launchable(
        level_nid, game.overworld_controller.next_level,
        game.game_vars.get('_cleared_levels', set()))
