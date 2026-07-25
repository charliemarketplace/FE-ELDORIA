"""Shared "effective level" rule for power-band computations.

A unit's raw `level` alone understates the threat of a promoted (tier-2)
class -- a level-1 General is not remotely comparable to a level-1 Soldier.
`debug_jump.py` (the chapter-jump QA bootstrap) and `enemy_pool.py` (the
procedural squad generator) both need this "promoted units count as +10
levels" rule, and they must never be allowed to drift apart, so it lives
here as the single source of truth. `debug_jump._effective_level_and_tier`
delegates to `effective_level()` below instead of recomputing it.
"""
from __future__ import annotations

from typing import Optional

from app.utilities.typing import NID

# How many levels a tier-2 (promoted) class's threat is worth beyond its
# raw `level`, for power-band purposes only (this is not a gameplay stat
# bonus -- it never touches an actual unit's stats).
TIER_PROMOTION_BONUS = 10


def effective_level(level: Optional[int], klass_nid: Optional[NID]) -> Optional[int]:
    """Effective level for power-band purposes: `level + TIER_PROMOTION_BONUS`
    if `klass_nid` names a tier-2 class, else just `level`. Unknown/missing
    class nids are treated as tier 1 (no bonus). Returns None if `level` is
    None, so callers can filter out units they couldn't determine a level
    for without special-casing this function.
    """
    if level is None:
        return None
    from app.data.database.database import DB
    klass = DB.classes.get(klass_nid) if klass_nid else None
    tier = klass.tier if klass else 1
    return level + TIER_PROMOTION_BONUS if tier == 2 else level
