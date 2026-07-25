"""
The Merchant: a persistent, non-roster unit that banks donated experience
and levels up over the campaign, granting feats that discount the
prep-menu market.

Key facts this module relies on (see BACKLOG_AUDIT.md):
- `UnitObject.from_prefab` silently skips items/skills and forces
  `team='player'` when given a raw `UnitPrefab`. The Merchant is
  constructed the same way `event_functions.load_unit` builds a
  non-level unit: wrap the prefab nid in a `UniqueUnit(nid, team, ai,
  None)` before calling `from_prefab`.
- `team='other'` is allied to the player (see `teams.json`) but is
  filtered out of `get_units_in_party`/`get_all_units_in_party`, which
  only return `team == 'player'` units. That's what keeps the Merchant
  out of the roster, Pick Units, Formation, etc.
- Registering the Merchant via `action.do(action.RegisterUnit(...))`
  is reversible (turnwheel-safe) and, because `game.save()` serializes
  every unit in `unit_registry` and `clean_up(full=True)` only strips
  non-`persistent` units, the Merchant persists across saves and
  chapter transitions with no additional save-format code.
"""
from typing import List, Tuple

from app.data.database.database import DB
from app.data.database.level_units import UniqueUnit

from app.engine import action
from app.engine.game_state import game
from app.engine.objects.unit import UnitObject

MERCHANT_NID = 'Merchant'


def get_merchant() -> UnitObject:
    """
    Returns the persistent Merchant unit, lazily creating and registering
    it if this save has never needed one before (either because it
    predates the Merchant entirely, or because the player has not yet
    donated XP or visited a market that checks for one).

    Safe to call repeatedly -- returns the same UnitObject once created.
    """
    merchant = game.get_unit(MERCHANT_NID)
    if merchant:
        return merchant

    # Same construction path as app/events/event_functions.py:load_unit --
    # wrap the raw UnitPrefab in a UniqueUnit so from_prefab takes the
    # is_level_unit branch and actually resolves items/skills, rather than
    # silently skipping that block.
    unique_unit = UniqueUnit(MERCHANT_NID, 'other', 'None', None)
    merchant = UnitObject.from_prefab(unique_unit, game.current_mode)
    merchant.party = None
    action.do(action.RegisterUnit(merchant))
    return merchant


def donate_xp() -> Tuple[List[action.Action], int]:
    """
    Pools exp from every unit currently in the player's roster (plus
    whatever the Merchant has already banked) into the Merchant.

    Every full 100 pooled exp becomes one Merchant level, clamped to the
    Merchant's class's max_level; the leftover (`total % 100`) is carried
    into the Merchant's exp bar. Every donor's exp is zeroed. A
    `feat_choice` screen is queued once per level gained, with
    `game.memory['current_unit']` pointed at the Merchant.

    Returns (actions, levels_gained) where `actions` is the ordered list
    of `action.Action` objects performed via `action.do()` -- callers
    (including tests) can reverse a donation turnwheel-style by calling
    `.reverse()` on each, in reverse order.
    """
    merchant = get_merchant()
    donors = game.get_units_in_party()

    total = merchant.exp + sum(unit.exp for unit in donors)

    performed: List[action.Action] = []
    for donor in donors:
        zero_act = action.SetExp(donor, 0)
        action.do(zero_act)
        performed.append(zero_act)

    klass = DB.classes.get(merchant.klass)
    raw_levels = total // 100
    remainder = total % 100
    room_to_grow = max(0, klass.max_level - merchant.level)
    levels_gained = min(raw_levels, room_to_grow)

    if levels_gained > 0:
        level_act = action.SetLevel(merchant, merchant.level + levels_gained)
        action.do(level_act)
        performed.append(level_act)

    exp_act = action.SetExp(merchant, remainder)
    action.do(exp_act)
    performed.append(exp_act)

    if levels_gained > 0:
        game.memory['current_unit'] = merchant
        for _ in range(levels_gained):
            game.state.change('feat_choice')

    return performed, levels_gained
