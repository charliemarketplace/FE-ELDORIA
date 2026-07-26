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


def resolve_feat_choice_for(feat_nid, max_frames=2000):
    """Selects `feat_nid` in a real, live 'feat_choice' screen (FeatChoiceState)
    that is about to appear -- e.g. right after selecting 'Donate XP' in
    prep_main, which queues one feat_choice push per Merchant level gained.

    Deliberately does NOT use run_until's generic AUTO_SELECT_STATES
    auto-pilot for this: that pilot calls `choose(state)` and immediately
    sends SELECT on every frame whose top state is named 'feat_choice',
    including the very first frame after the state was merely PUSHED (via
    a queued state.change()) but before StateMachine.update() has actually
    run its start() -- FeatChoiceState.unit/.menu are still the class-level
    defaults (None) at that point (set for real only inside start()), so a
    choose() callback trying to branch on `state.unit` would see None and
    silently fall through to "confirm whatever's under the cursor" before
    ever getting a chance to steer the pick. Pumping plain (event=None)
    frames here until the state has genuinely started avoids that race,
    then selects for real and confirms with one explicit SELECT.
    """
    from app.engine.game_state import game
    from app.data.database.database import DB

    for _ in range(max_frames):
        cur = game.state.current_state()
        if cur is not None and cur.name == 'feat_choice' and cur.started:
            break
        frame(None)
    else:
        raise TimeoutError(
            "resolve_feat_choice_for: 'feat_choice' never started within %d frames" % max_frames)

    state = game.state.current_state()
    feats = DB.skills.get_feats()
    target = next((f for f in feats if f.nid == feat_nid), None)
    assert target is not None, "feat %r not found in DB.skills.get_feats()" % feat_nid
    state.menu.set_selection(target)
    frame('SELECT')


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


def back_out_of_prep_market(max_frames=20000, choose=None):
    """BACK from prep_market's top Buy/Sell menu (PrepMarketState's initial
    self.state == 'free') back to prep_manage_select."""
    frame('BACK')
    run_until(lambda g: top_name() == 'prep_manage_select', max_frames=max_frames, choose=choose)


def enter_prep_market(manage_select_state, max_frames=20000, choose=None):
    """From a live prep_manage_select state (as returned by
    enter_manage_and_select_unit): selects 'Market' in the real select_menu
    and drives forward into the real 'prep_market' state (PrepMarketState),
    returning that live instance so its buy_menu/sell_menu can be
    inspected."""
    from app.engine.game_state import game
    manage_select_state.select_menu.set_selection('Market')
    frame('SELECT')
    run_until(lambda g: top_name() == 'prep_market', max_frames=max_frames, choose=choose)
    return game.state.current_state()


def buy_menu_item_nids(prep_market_state):
    """The nids actually offered by the real, live PrepMarketState.buy_menu
    -- built in PrepMarketState.start() from game.market_items filtered by
    item.Tier vs skill_system.unlocked_market_tier(merchant) (see
    app/engine/prep.py), so this reflects what tier-gating actually leaves
    choosable, not the raw (unfiltered) game.market_items dict."""
    return [item.nid for item in prep_market_state.buy_menu.options]


def buy_item_in_prep_market(prep_market_state, item_nid):
    """Drives PrepMarketState's REAL Buy path end to end for one unit of
    `item_nid`: from the initial free Buy/Sell choice (if not already past
    it), positions the live Market menu's selection on the matching item,
    then sends the actual 'SELECT' event -- the exact take_input() branch
    (app/engine/prep.py) that computes item_funcs.buy_price /
    skill_system.modify_buy_price and calls game.set_money(). Nothing here
    reimplements that arithmetic; callers read game.get_money() before/after
    to observe the real effect.

    Returns True if `item_nid` was found in the live buy_menu and SELECT was
    sent, False if it wasn't found (nothing is pressed, nothing changes).
    """
    state = prep_market_state
    assert state.name == 'prep_market', "top state is %r, not prep_market" % state.name
    if state.state == 'free':
        state.menu.set_selection('Buy')
        frame('SELECT')
    assert state.state == 'buy', "expected PrepMarketState in 'buy' substate, got %r" % state.state
    market_menu = state.buy_menu
    for i, w_type in enumerate(market_menu.order):
        submenu = market_menu.menus[w_type]
        for idx, opt in enumerate(submenu.options):
            item = opt.get()
            if item is not None and getattr(item, 'nid', None) == item_nid:
                market_menu.selection_index = i + 1
                market_menu.menu_index = i
                submenu.current_index = idx
                frame('SELECT')
                return True
    return False


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


def _counterattack_could_kill(attacker, weapon, defender):
    """True if `defender` countering `attacker`'s strike (at the adjacent
    range this module always teleports attackers to before striking) could
    reduce a FULLY HEALED `attacker` to 0 HP or below.

    Uses the exact same forecast primitives the real pre-combat UI preview
    (app/engine/ui_view.py) and the AI's own attack scoring
    (app/engine/ai_controller.py) call to answer "can this defender counter,
    and for how much" -- combat_calcs.can_counterattack + compute_damage with
    mode='defense' -- rather than re-deriving might/defense by hand. Takes
    the worse of a normal hit and a critical hit, but ONLY treats a crit as
    possible when combat_calcs.compute_crit(...) actually returns a
    percentage rather than None -- compute_damage(..., crit=True) applies
    the crit multiplier/addition unconditionally regardless of whether the
    weapon has a Crit component at all, so calling it without this guard
    flags every non-critable weapon (e.g. S1 Draven's plain Iron Lance) as
    lethal on a hit that, in real combat, can never actually land as a crit
    -- and also accounts for the defender doubling the attacker on the
    counter (compute_attack_phases), since a single win_current_level_by_
    combat combat instance can still lose a healed-to-full attacker within
    that one exchange -- the existing heal-before-each-attacker's-own-strike
    only ever prevented an EARLIER round's chip damage from compounding into
    a later, otherwise-survivable hit; it does nothing against a single
    exchange that is lethal by itself.
    """
    from app.engine import combat_calcs

    def_weapon = defender.get_weapon()
    if not combat_calcs.can_counterattack(attacker, weapon, defender, def_weapon):
        return False
    normal = combat_calcs.compute_damage(defender, attacker, def_weapon, weapon, 'defense', (0, 0)) or 0
    worst = normal
    crit_chance = combat_calcs.compute_crit(defender, attacker, def_weapon, weapon, 'defense', (0, 0))
    if crit_chance:
        crit = combat_calcs.compute_damage(defender, attacker, def_weapon, weapon, 'defense', (0, 0), crit=True) or 0
        worst = max(worst, crit)
    phases = combat_calcs.compute_attack_phases(defender, attacker, def_weapon, weapon, 'defense', (0, 0))
    worst_case = worst * max(phases, 1)
    return worst_case >= attacker.get_max_hp()


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

    Rowan is special: every level's loss condition is his death (an
    `unit_death` event with unit.nid == 'Rowan', see events.json), so he's
    tried LAST against every target -- a fallback attacker, not the default
    one -- and _counterattack_could_kill guards every attacker (not just
    him) so a healed-to-full unit is never thrown at a matchup whose counter
    could kill it outright in one exchange. This still lets Rowan fight (and
    finish off) anything the rest of the squad genuinely cannot damage --
    the guard only ever skips a specific (attacker, target) pairing for this
    attempt, never the attacker or the target outright.
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
        # Rowan last: every other unit gets first crack at any target, so
        # Rowan (whose death alone ends the level) only ever attacks when
        # he's actually needed -- see _counterattack_could_kill above.
        deployed.sort(key=lambda u: u.nid == 'Rowan')

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
                if _counterattack_could_kill(attacker, weapon, enemy):
                    # This specific pairing is unsafe -- not the attacker or
                    # the target overall. Move on to the next attacker this
                    # pass; this attacker may still be safe against a
                    # different target, and a different attacker may be
                    # exactly who this target needed.
                    continue
                action.do(action.SetHP(attacker, attacker.get_max_hp()))
                adj = _find_adjacent_free_tile(enemy.position)
                if adj is None:
                    continue
                # Remember where this attacker came from so it can be sent
                # back there once this strike resolves (below) -- otherwise
                # every attacker that ever fought this enemy stays parked on
                # one of its (at most 4) orthogonal tiles forever, and a
                # tough enemy that outlives everyone's first attack attempt
                # eventually has every adjacent tile permanently occupied by
                # its own attackers, making _find_adjacent_free_tile return
                # None for everyone from then on -- a real deadlock this
                # loop can't tell apart from a genuinely un-damageable
                # matchup (both look like max_stale_passes consecutive
                # no-progress passes), even though every attacker's forecast
                # damage/hit here is perfectly healthy.
                origin = attacker.position
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

                # Free up the tile this attacker just occupied (see the
                # `origin` comment above) -- but only if it's still alive
                # and its old tile is actually empty (nothing else was
                # teleported there in the interim; only one unit ever moves
                # per attempt in this loop, so it always is).
                if not attacker.dead and origin and not game.board.get_unit(origin):
                    action.do(action.Teleport(attacker, origin))

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


def force_node_safety(level_nid, desired, max_attempts=200):
    """Pins the Safe/Unsafe outcome a revisit of `level_nid` will see, by
    repeatedly invoking the REAL production coin-flip -- OverworldManager.
    get_node_safety (see overworld/overworld_manager.py), the exact call
    OverworldFreeState.take_input makes the moment a re-entry is selected --
    after clearing any cached roll, until it lands on `desired` ('Safe' or
    'Unsafe'). This is the same brute-force-until-it-lands technique
    tools/test_alignment_d20_tier.py already uses for roll_d20 bands
    (`next(r for r in (...) if r['natural'] == 1)`): it drives the actual
    production RNG (game.get_random_weighted_choice, the turnwheel-safe
    other_random stream) over and over rather than writing the cached
    result by hand. get_node_safety's whole point is "never re-roll once
    cached" (app/engine/overworld/overworld_manager.py), so once this
    lands on `desired`, travel_to_level_node()'s subsequent real node-select
    -> get_node_safety() call for the same node reads back the exact same
    cached outcome, unchanged.
    """
    from app.engine.game_state import game
    for _ in range(max_attempts):
        game.game_vars.get('_node_safety', {}).pop(level_nid, None)
        # get_node_safety only ever SETS '_pending_unsafe_encounter' (on an
        # Unsafe outcome); it never clears it, because in real play a node
        # is only ever rolled once before the level consumes the flag. A
        # discarded retry that happened to land Unsafe would otherwise leak
        # a stale pending flag past a later retry that lands the desired
        # Safe outcome -- clear it before every real re-roll so the flag
        # only ever reflects the LAST (kept) roll, exactly as if that had
        # been the only roll made.
        if game.game_vars.get('_pending_unsafe_encounter') == level_nid:
            del game.game_vars['_pending_unsafe_encounter']
        outcome = game.overworld_controller.get_node_safety(level_nid)
        if outcome == desired:
            return
    raise RuntimeError(
        "force_node_safety: %r never landed on %r after %d real rolls" %
        (level_nid, desired, max_attempts))


# ---------------------------------------------------------------------------
# Skill check -- drives the REAL on-map ability menu (general_states.py's
# 'free' -> 'move' -> 'menu' -> 'targeting' state chain), not a direct call
# into abilities.SkillCheckAbility.
# ---------------------------------------------------------------------------

def attempt_skill_check(initiator_nid, target_nid, max_frames=2000):
    """From 'free': teleports `initiator_nid` adjacent to `target_nid` (real
    action.Teleport -- the same technique win_current_level_by_combat uses
    to position attackers; grid pathing is orthogonal to the bug under
    test), then drives the exact state chain a player clicking that unit
    and choosing "Skill Check" produces:

    - 'free' -> SELECT with the cursor already on the unit -> 'move'
      (FreeState.take_input's real unit-selection branch).
    - 'move' -> SELECT with the cursor still on the unit's own tile ->
      'menu' (MoveState.take_input's "confirm, don't move" branch), whose
      option list is the REAL live one MenuState.begin() builds from
      Ability.targets() (app/engine/abilities.py) -- asserted present here,
      not assumed.
    - 'menu' -> selecting "Skill Check" -> 'targeting' (MenuState.take_input's
      generic-ability branch).
    - 'targeting' -> SELECT invokes SkillCheckAbility.do() for real (the
      d20 roll via query_engine.roll_d20 plus the on_skill_check trigger
      dispatch) -- TargetingState.start() already parked the cursor on the
      only registered target for this initiator.

    SkillCheckAbility.do() pops 'targeting' back to 'menu' *before* firing
    the on_skill_check event (the identical shape TalkAbility.do() uses) --
    MenuState only special-cases clearing self.menu for the 'Talk'/'Support'
    selections, not 'Skill Check', so the same live menu is still there once
    the event (run on top of it as an ordinary 'event' state, auto-skipped
    like any other) resolves. A Skill Check, like a Talk, does not end the
    unit's turn by itself -- this drives the real 'Wait' option in that same
    menu afterward to return to 'free', exactly like a player would.
    """
    from app.engine.game_state import game
    from app.engine import action

    initiator = game.get_unit(initiator_nid)
    target = game.get_unit(target_nid)
    assert initiator and initiator.position, "%s not on the map" % initiator_nid
    assert target and target.position, "%s not on the map" % target_nid
    assert top_name() == 'free', "attempt_skill_check must start from 'free' (top=%r)" % top_name()

    adj = _find_adjacent_free_tile(target.position)
    assert adj is not None, "no free tile adjacent to %s" % target_nid
    action.do(action.Teleport(initiator, adj))

    game.cursor.set_pos(initiator.position)
    frame('SELECT')
    run_until(lambda g: top_name() == 'move', max_frames=max_frames)

    frame('SELECT')
    run_until(lambda g: top_name() == 'menu', max_frames=max_frames)

    menu_state = game.state.current_state()
    options = [opt.get() for opt in menu_state.menu.options]
    assert 'Skill Check' in options, (
        "'Skill Check' not in the real on-map ability menu: %r" % options)
    menu_state.menu.set_selection('Skill Check')
    frame('SELECT')
    run_until(lambda g: top_name() == 'targeting', max_frames=max_frames)

    frame('SELECT')  # invokes SkillCheckAbility.do() for real
    run_until(lambda g: top_name() == 'menu', max_frames=max_frames)

    menu_state = game.state.current_state()
    menu_state.menu.set_selection('Wait')
    frame('SELECT')
    run_until(lambda g: top_name() == 'free', max_frames=max_frames)
