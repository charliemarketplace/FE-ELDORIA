"""Enemy pool loader + squad generator.

Loads lion_throne.ltproj/game_data/enemy_pools.json (plain JSON via
app.utilities.serialization -- deliberately NOT one of DB.save_data_types;
this is generator-only data, never touched by the project editor) and,
given the live party's average effective level
(app.engine.power_band.effective_level), samples and instantiates a squad
of generic enemy units to fill "procedural" marked slots
(app.data.database.level_units.GenericUnit.procedural) in a level.

Grinding is an intended feature. There is no balance guard here: a party
whose average effective level is far past every declared band still gets a
squad -- pick_band() clamps to the nearest edge band instead of refusing.

Sampling always goes through game.get_random_weighted_choice /
game.get_random (the turnwheel-logged `other_random` stream), never
app.utilities.static_random.get_randint directly, which draws from the
combat stream and would desync turnwheel replay of real combat rolls.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Sequence

from app.engine.power_band import effective_level
from app.utilities.serialization import load_json
from app.utilities.typing import NID

# Single shared constant: how far (in effective levels) a generated squad's
# mean is allowed to drift from the party's average once a band has been
# picked. Grinding past a band's authored range is never blocked -- this
# only bounds how tightly the generator is expected to track the party
# within whichever band it lands in.
LEVEL_TOLERANCE = 2

_POOL_FILENAME = 'enemy_pools.json'


def _default_pool_path() -> Path:
    from app.data.database.database import DB
    if DB.current_proj_dir:
        return Path(DB.current_proj_dir) / 'game_data' / _POOL_FILENAME
    # Fallback for callers that need the pool before DB.load() has run.
    return Path(__file__).resolve().parents[2] / 'lion_throne.ltproj' / 'game_data' / _POOL_FILENAME


def load_pools(path: Optional[Path] = None) -> List[dict]:
    """Loads the list of power bands from disk."""
    path = path or _default_pool_path()
    return load_json(path)


def party_average_effective_level(units: Sequence) -> float:
    """Average effective level (power_band.effective_level) across a list
    of live units (anything with .level/.klass -- UnitObject in practice).
    An empty party has no meaningful average; 1 matches debug_jump's own
    fallback for a level with no determinable enemy levels."""
    levels = []
    for u in units:
        lvl = effective_level(getattr(u, 'level', None), getattr(u, 'klass', None))
        if lvl is not None:
            levels.append(lvl)
    if not levels:
        return 1.0
    return sum(levels) / len(levels)


def pick_band(avg: float, bands: List[dict]) -> dict:
    """Picks the band whose [min_avg_level, max_avg_level] contains avg.
    If avg falls outside every band, clamps to the nearest edge band
    instead of raising -- grinding past the authored ceiling (or a fresh
    party below the floor) still needs a squad."""
    if not bands:
        raise ValueError("pick_band: no bands to pick from")
    for band in bands:
        if band['min_avg_level'] <= avg <= band['max_avg_level']:
            return band
    # Bands are authored as INTEGER intervals ([1,4], [5,8], ...) but avg is a
    # float mean, so every fractional value between two bands -- 4.33, 8.5,
    # 12.4 -- matches none of them. Falling back to "the highest band" here
    # would hand a party averaging 4.33 the level-17+ endgame squad, which is
    # exactly the range a grinding party passes through. Pick the band whose
    # interval is nearest instead.
    def distance(band):
        if avg < band['min_avg_level']:
            return band['min_avg_level'] - avg
        return avg - band['max_avg_level']
    return min(bands, key=distance)


def _range_for_target(template: dict, target_level) -> tuple:
    """Narrows template['level_range'] to within LEVEL_TOLERANCE of
    target_level (the party's average effective level), instead of rolling
    uniformly across the template's whole declared range -- the band decides
    WHICH enemies show up, target_level decides how strong they are.

    The comparison happens in EFFECTIVE level terms (power_band adds a flat
    bonus for promoted classes), so a promoted template's range is offset
    back into raw-level terms before clamping -- otherwise a tier-2 class
    would be pushed to level 1 to hit a low-level party's effective average.
    """
    lo, hi = template['level_range']
    if target_level is None:
        return lo, hi
    promotion_offset = effective_level(0, template.get('klass'))
    target_raw = target_level - promotion_offset
    want_lo = int(round(target_raw)) - LEVEL_TOLERANCE
    want_hi = int(round(target_raw)) + LEVEL_TOLERANCE
    new_lo, new_hi = max(lo, want_lo), min(hi, want_hi)
    if new_lo > new_hi:
        # The template cannot reach the party's band at all; sit at whichever
        # end of its own range comes closest rather than inverting the range.
        return (lo, lo) if want_hi < lo else (hi, hi)
    return new_lo, new_hi


def sample_squad(band: dict, count: int, game, target_level=None) -> List[dict]:
    """Weighted-samples `count` templates from band['templates'], each
    filled in with a concrete level rolled from its declared level_range,
    narrowed toward `target_level` (the party's average effective level) so
    the squad actually scales to the party rather than to the band alone.
    Uses only game.get_random_weighted_choice / game.get_random -- the
    turnwheel-safe `other_random` stream."""
    templates = band['templates']
    if not templates:
        raise ValueError("sample_squad: band %r has no templates" % band.get('nid'))
    weights = [int(t.get('weight', 1)) for t in templates]
    picked = []
    for _ in range(count):
        template = game.get_random_weighted_choice(templates, weights)
        lo, hi = _range_for_target(template, target_level)
        level = lo if lo == hi else game.get_random(lo, hi)
        picked.append({
            'klass': template['klass'],
            'level': level,
            'faction': template['faction'],
            'ai': template.get('ai'),
            'starting_items': list(template.get('starting_items', [])),
        })
    return picked


def instantiate_squad(slots: Sequence, band: dict, game, target_level=None) -> List:
    """Fills each procedural slot (a level-prefab GenericUnit with
    procedural=True) with a freshly-sampled squad member. klass/level/
    faction/ai/starting_items come from the sampled template;
    position/team/ai_group are kept exactly as authored on the slot -- those
    encode where in the level design the enemy stands and which
    reinforcement/AI group it belongs to, only its identity and power are
    procedural. Returns unregistered UnitObjects; the caller (
    game_state._generate_enemy_squad) is responsible for placing them into
    LevelObject.units."""
    from app.engine.generic_unit import create_generic_unit

    templates = sample_squad(band, len(slots), game, target_level=target_level)
    units = []
    for slot, template in zip(slots, templates):
        unit = create_generic_unit(
            slot.nid,
            template['klass'],
            template['level'],
            slot.team,
            ai=template['ai'],
            faction=template['faction'],
            variant=slot.variant,
            starting_items=template['starting_items'],
            starting_skills=list(slot.starting_skills) if slot.starting_skills else None,
            current_mode=game.current_mode,
        )
        starting_position = tuple(slot.starting_position) if slot.starting_position else None
        unit.starting_position = starting_position
        unit.position = starting_position
        unit.ai_group = slot.ai_group
        units.append(unit)
    return units
