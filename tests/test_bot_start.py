# pyright: reportAttributeAccessIssue=false
"""A real Bot, as a run starts it: what the first look at the game reads must already be there.

The stand-ins in the other test files set these themselves, so they can't see one that Bot forgot
(a run stopped with AttributeError on 'load_seen' when the bag was 97-99% full at its first reading).
"""

from __future__ import annotations

import threading
from typing import Any, cast

import pytest

from unclefarmer.engine.bot import Bot


def fresh() -> Bot:
    def log(*_args: object, **_kwargs: object) -> None:
        pass

    return Bot(cast(Any, None), {}, log, threading.Event())


@pytest.mark.parametrize("load", [97, 98, 99])
def test_a_run_can_start_with_the_bag_nearly_full(load: int) -> None:
    bot = fresh()
    assert bot.bag_stalled({"load": load, "maxload": 100}, 100) is False
    assert [row[2] for row in bot.load_seen] == [load]


@pytest.mark.parametrize("name", ["load_seen", "potion_slots", "_attackers"])
def test_what_is_read_before_it_is_written_starts_empty(name: str) -> None:
    assert not getattr(fresh(), name)
