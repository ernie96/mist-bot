"""The player's own gap between two casts of a Priest's Recover (the fork's; see FORK.md).

Recover has no cooldown in the game's skill data, so while HP stayed under the heal mark the bot
cast it at every global cooldown, the whole fight. Character, Advanced, Low HP, "Cast Recover at
most every (seconds)" sets a gap: 0 keeps the old way. SkillBook._cooldown takes the longer of the
skill's own cooldown and this gap, so every heal path (our HP, the pet, the team) waits for it.
"""

from __future__ import annotations

from typing import Any

RECOVER = "Recover"
MOST = 120          # seconds: the longest gap the window offers


def recover_gap(p: dict[str, Any]) -> float:
    """The gap in seconds from the profile, kept within 0..MOST (a bad value counts as 0)."""
    try:
        gap = float(p.get("recover_every", 0) or 0)
    except (TypeError, ValueError):
        return 0.0
    return min(float(MOST), max(0.0, gap))


def cooldown(name: str, cd: float, p: dict[str, Any]) -> float:
    """The cooldown to wait for this skill: Recover's at least the player's gap."""
    return max(cd, recover_gap(p)) if name == RECOVER else cd
