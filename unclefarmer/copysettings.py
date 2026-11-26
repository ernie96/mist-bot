"""Copying parts of one character's settings to another for other programs (MCP's
copy_character_settings): the same parts the character window and the bag window copy, done on
saved profiles. Uses upstream's engine/profilecopy.py and engine/bagcopy.py; nothing is saved here.
"""

from __future__ import annotations

import copy
from collections.abc import Sequence
from typing import Any, cast

from .control import COPY_PARTS as PARTS
from .engine import bagcopy, profilecopy, triggers


def copy_parts(mine: dict[str, Any], theirs: dict[str, Any], parts: Sequence[str],
               replace: bool) -> tuple[dict[str, Any], list[str]]:
    """(this character's profile after the copy, a line per part saying what changed).
    replace: lists become the other character's; otherwise their entries are added to this one's.
    Each skill's use is copied only between characters of one class."""
    unknown = [p for p in parts if p not in PARTS]
    if unknown:
        raise ValueError("Unknown parts: %s. Parts are: %s." % (", ".join(unknown), ", ".join(PARTS)))
    out = copy.deepcopy(mine)
    lines: list[str] = []
    for stage in triggers.STAGES:
        if stage not in parts:
            continue
        rows, added, same = profilecopy.steps(out, theirs, stage, replace)
        old: Any = out.get("trigger_sequences")
        seqs: dict[str, Any] = dict(cast("dict[str, Any]", old)) if isinstance(old, dict) else {}
        other = "after" if stage == "before" else "before"
        if other not in seqs:                 # the other list keeps what it had
            try:
                seqs[other] = triggers.sequence(out, other)
            except ValueError:
                pass
        seqs[stage] = {"steps": rows}
        out["trigger_sequences"] = seqs
        if stage == "before" and "skip_before_on_farm" in theirs:
            out["skip_before_on_farm"] = theirs["skip_before_on_farm"]
        lines.append("%s farming list: %d put in, %d already there" % (stage.capitalize(), added, same))
    if "fighting" in parts:
        with_skills = profilecopy.same_class(out, theirs)
        out.update(profilecopy.fighting(theirs, with_skills))
        lines.append("Fighting settings: set as theirs" if with_skills else
                     "Fighting settings: set as theirs, but not each skill's use (%s vs %s)"
                     % (profilecopy.class_of(theirs), profilecopy.class_of(mine)))
    if "team" in parts:
        out.update(profilecopy.team(theirs))
        lines.append("Team settings: set as theirs")
    lists = [a for a in bagcopy.LISTS if a in parts]
    if lists:
        rules, added_by, same_by = bagcopy.copy_rules(out.get("bag_rules") or {}, theirs.get("bag_rules") or {},
                                                      lists, replace)
        out["bag_rules"] = rules
        lines += ["%s list: %d put in, %d already there" % (a.capitalize(), added_by[a], same_by[a]) for a in lists]
    if "supplies" in parts:
        out["restock"], added, same = bagcopy.copy_supplies(out.get("restock") or [], theirs.get("restock") or [],
                                                            replace)
        lines.append("Supplies: %d put in, %d already there" % (added, same))
    if "full" in parts:
        out.update(bagcopy.full_settings(theirs))
        lines.append("Full bag and equipment by rarity: set as theirs")
    return out, lines
