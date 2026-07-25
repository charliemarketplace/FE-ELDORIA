"""Runtime generic-unit creation, extracted from
`app.events.event_functions.make_generic` (843-870 as of the BACKLOG_AUDIT
pass) so it's reachable outside an `Event` instance -- the enemy-pool
generator (app/engine/enemy_pool.py) needs the exact same construction path
(GenericUnit prefab -> UnitObject.from_prefab) at level-start time, well
before any event runs.

`make_generic` is now a thin wrapper around `create_generic_unit` that keeps
its event-specific bits (nid auto-assignment, error logging via
self.logger, registering the unit via action.RegisterUnit, and stashing
self.created_unit for the event script).
"""
from __future__ import annotations

from typing import List, Optional

from app.utilities.typing import NID


def create_generic_unit(
    nid: NID,
    klass: NID,
    level: int,
    team: str,
    ai: Optional[NID] = None,
    faction: Optional[NID] = None,
    variant: Optional[str] = None,
    starting_items: Optional[List] = None,
    starting_skills: Optional[List[NID]] = None,
    current_mode=None,
):
    """Builds a GenericUnit prefab and turns it into a real (but unregistered)
    UnitObject -- generic-unit stats/levels come from DB.classes and are
    filled in by `UnitObject.from_prefab`'s call to `unit_funcs.auto_level`,
    which only runs when `current_mode` is passed in (see
    app/engine/objects/unit.py); omit it and the unit comes out at its
    class's raw level-1 base stats.

    The caller is responsible for registering the returned unit
    (action.do(action.RegisterUnit(unit)) for a mid-event spawn, or
    appending it to LevelObject.units before level_setup() for a
    level-start squad -- see game_state._generate_enemy_squad).

    Raises ValueError if `klass` isn't in DB.classes, since (unlike
    make_generic, which has an Event/self.logger to report through) this
    function has no logger of its own to report through.
    """
    from app.data.database.database import DB
    from app.data.database.level_units import GenericUnit
    from app.engine.objects.unit import UnitObject

    if klass not in DB.classes:
        raise ValueError("create_generic_unit: Class %s doesn't exist in database" % klass)
    if not ai:
        ai = 'None'
    if not faction:
        faction = DB.factions[0].nid
    starting_items = starting_items or []
    starting_skills = starting_skills or []

    level_unit_prefab = GenericUnit(
        nid, variant, level, klass, faction, starting_items, starting_skills, team, ai)
    new_unit = UnitObject.from_prefab(level_unit_prefab, current_mode)
    return new_unit
