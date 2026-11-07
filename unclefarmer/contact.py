"""How to reach the developer: Help, Contact the developer, Help, Join the Telegram group, and the
README's Contact section.

The addresses and the group's invite link are the developer's public contacts, there on purpose,
and kept in this one place; the translations only carry "{email}", "{mastodon}" and "{link}",
never the contacts themselves.
"""

from __future__ import annotations

EMAIL = "ernesto@melendez.land"
MASTODON = "ernie@someplace.social"
ISSUES = "https://github.com/ernie96/mist-bot/issues"
TELEGRAM = "https://t.me/+-SHI1xTKJugwMzQ5"   # the project's Telegram invite link


def mailto(subject: str = "") -> str:
    """A mailto: link to the developer, with a subject when one is given."""
    from urllib.parse import quote
    return "mailto:%s" % EMAIL + ("?subject=%s" % quote(subject) if subject else "")
