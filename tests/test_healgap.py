"""The player's gap between two casts of a Priest's Recover (engine/healgap.py)."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from unclefarmer.engine import combat, healgap

RECOVER: dict[str, Any] = {"name": "Recover", "role": "heal", "targets": 1, "cd": None, "cast": None}
HEAL: dict[str, Any] = {"name": "Heal", "role": "heal", "targets": 1, "cd": None, "cast": None}


def book(gap: Any) -> Any:
    """Just what SkillBook.ready reads: the profile, the casts done and nothing pending."""
    b: Any = object.__new__(combat.SkillBook)
    b.b = SimpleNamespace(p={"recover_every": gap})
    b.cls = "Priest"
    b.combos = None
    b.pending = {}
    b.refused = {}
    b.used = {"Recover": 100.0, "Heal": 100.0}
    return b


@pytest.mark.parametrize("value,expected", [(0, 0.0), (16, 16.0), ("16", 16.0), (-5, 0.0), (999, 120.0),
                                            (None, 0.0), ("fast", 0.0)])
def test_the_gap_is_read_within_its_bounds(value: Any, expected: float) -> None:
    assert healgap.recover_gap({"recover_every": value}) == expected


def test_without_a_gap_recover_is_ready_at_once_as_before() -> None:
    assert book(0).ready(RECOVER, 101.0)


def test_with_a_gap_recover_waits_for_it_and_other_heals_do_not() -> None:
    b = book(16)
    assert not b.ready(RECOVER, 110.0)            # 10 s after the last Recover: still waiting
    assert b.ready(HEAL, 101.0)                   # Heal has no gap
    assert b.ready(RECOVER, 116.5)                # the gap (and the usual 0.3 s margin) is over


def test_a_profile_without_the_setting_behaves_as_before() -> None:
    b = book(0)
    b.b.p = {}
    assert b.ready(RECOVER, 101.0)
