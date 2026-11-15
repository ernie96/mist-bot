"""message.py: the developer's message file (message.txt beside the web page)."""

from __future__ import annotations

import pytest

from unclefarmer import message


def test_a_message_is_its_number_and_its_text() -> None:
    assert message.parse("﻿3\r\nServers are down tonight.\r\nBack tomorrow.\r\n") == (
        3, "Servers are down tonight.\nBack tomorrow.")
    assert message.parse("12\nHello") == (12, "Hello")


@pytest.mark.parametrize("text", ["", "3\n", "3", "3\n  \n", "0\nHello", "-2\nHello", "<html>not found</html>\nx",
                                  "Hello\nthere"])
def test_nothing_to_show(text: str) -> None:
    assert message.parse(text) is None


def test_the_last_shown_number() -> None:
    assert message.seen({}) == 0
    assert message.seen({message.SEEN: 4}) == 4
    assert message.seen({message.SEEN: "4"}) == 0
    assert message.seen({message.SEEN: True}) == 0
