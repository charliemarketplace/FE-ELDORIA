"""Debug-mode chapter-jump bootstrap.

When the web build is booted with BOTH ?level=<nid> and ?debug=1 (see
main.py, where cf.SETTINGS['debug'] is set from the URL and
game_state.start_level(level_nid) is called), QA wants to land in that
chapter with the full previously-recruitable roster fielded and leveled
to the chapter's power band, instead of only whatever the level prefab
fields by default.

Rather than hand-rolling unit surgery, this builds a synthetic event
script out of the engine's own event commands (load_unit / add_unit /
autolevel_to / game_var) and injects it the same way the in-game debug
console does (EventManager._add_event_from_script), so it runs through
the normal event pipeline right after level start.

bootstrap_commands() is pure DB computation (no running game required),
so it's natively testable; install() is the thin runtime hook.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from app.data.database.database import DB


def _median(values: List[int]) -> float:
    # pygbag's wasm stdlib does not ship the `statistics` module.
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2


def _effective_level_and_tier(level_unit) -> Optional[Tuple[int, int]]:
    """(effective_level, tier) for a level-prefab unit entry, or None if
    it can't be determined. Effective level is level + 10 for tier-2
    (promoted) classes, else just level -- this keeps promoted units
    from skewing the power-band median down relative to their threat."""
    if level_unit.generic:
        level = level_unit.level
        klass_nid = level_unit.klass
    else:
        # Non-generic (unique) units don't carry their own level/klass in
        # the level prefab -- look them up in DB.units.
        unit_prefab = DB.units.get(level_unit.nid)
        if not unit_prefab:
            return None
        level = unit_prefab.level
        klass_nid = unit_prefab.klass
    if level is None or not klass_nid:
        return None
    klass = DB.classes.get(klass_nid)
    tier = klass.tier if klass else 1
    effective = level + 10 if tier == 2 else level
    return effective, tier


def _players_in(level_prefab) -> set:
    """nids of non-generic team=='player' units in a level prefab."""
    return {u.nid for u in level_prefab.units if u.team == 'player' and not u.generic}


def _collect_prior_roster(level_nid: str) -> set:
    """Walks backward through DB.levels (stored in campaign order),
    unioning in the player roster of each prior level as long as it
    shares at least one player-team unit with the level right after it.
    Stops at the first level that shares nothing (a different
    campaign/roster)."""
    level_nids = DB.levels.keys()
    idx = level_nids.index(level_nid)
    current_set = _players_in(DB.levels.get(level_nid))
    collected = set(current_set)
    j = idx
    while j > 0:
        prev_prefab = DB.levels[j - 1]
        prev_players = _players_in(prev_prefab)
        if current_set & prev_players:
            collected |= prev_players
            current_set = prev_players
            j -= 1
        else:
            break
    return collected


def _target_level(level_prefab) -> int:
    """Median of effective enemy levels in the level prefab -- the
    chapter's power band."""
    effective_levels = []
    for u in level_prefab.units:
        if u.team != 'enemy':
            continue
        result = _effective_level_and_tier(u)
        if result is None:
            continue
        effective_levels.append(result[0])
    if not effective_levels:
        return 1
    return int(_median(effective_levels))


def bootstrap_commands(level_nid: str) -> List[str]:
    """Pure computation: the list of "command;arg;arg" event-script
    lines needed to bootstrap a debug jump directly into `level_nid` --
    add every previously-recruitable character not already fielded there,
    and autolevel the whole collected party up to the chapter's power
    band (never down). Only reads DB; safe to call without a running
    game."""
    level_prefab = DB.levels.get(level_nid)
    if not level_prefab:
        return []

    collected = _collect_prior_roster(level_nid)

    units_by_nid = {u.nid: u for u in level_prefab.units}
    order_index = {u.nid: i for i, u in enumerate(level_prefab.units)}

    # Anchor for placement: first player-team unit in the target level
    # that already has a valid starting position.
    anchor = None
    for u in level_prefab.units:
        if u.team == 'player' and u.starting_position:
            anchor = u.starting_position
            break

    # "Not already fielded" == no valid starting_position in the target
    # level (so it wouldn't otherwise arrive on the map automatically).
    to_add = [nid for nid in collected
              if not (units_by_nid.get(nid) and units_by_nid[nid].starting_position)]
    to_add.sort(key=lambda nid: order_index.get(nid, len(order_index)))

    commands: List[str] = []
    for nid in to_add:
        commands.append('load_unit;%s' % nid)
    for nid in to_add:
        if anchor:
            commands.append('add_unit;%s;%d,%d;immediate;closest' % (nid, anchor[0], anchor[1]))
        else:
            commands.append('add_unit;%s;;immediate;closest' % nid)
    for nid in to_add:
        commands.append('game_var;%s_joined;True' % nid.lower())

    target_lv = _target_level(level_prefab)
    ordered_collected = sorted(collected, key=lambda nid: order_index.get(nid, len(order_index)))
    for nid in ordered_collected:
        unit_prefab = DB.units.get(nid)
        if not unit_prefab:
            continue
        current_level = unit_prefab.level
        if current_level is None or current_level >= target_lv:
            continue
        klass = DB.classes.get(unit_prefab.klass)
        max_level = klass.max_level if klass else target_lv
        new_level = min(target_lv, max_level)
        if new_level > current_level:
            commands.append('autolevel_to;%s;%d' % (nid, new_level))

    return commands


def install(game, level_nid: str) -> bool:
    """Injects the synthetic bootstrap event so it runs through the
    normal event pipeline right after level start (same mechanism the
    in-game debug console uses for typed commands). Returns True if an
    event was queued."""
    commands = bootstrap_commands(level_nid)
    if not commands:
        return False
    from app.events.triggers import GenericTrigger
    script = '\n'.join(commands)
    game.events._add_event_from_script('debug_jump_bootstrap', script, GenericTrigger())
    return True
