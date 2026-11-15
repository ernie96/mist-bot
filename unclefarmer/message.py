"""A message from the developer, read from the web page's folder at start and shown once (the fork's
own, as in Ernesto's other apps: Squire, Tin Pan, TimePlayer).

message.txt is uploaded beside the web page. Its first line is a number, the lines after it the
message. A higher number than the last one shown is a new message; a missing file, no number, 0 or
no text is nothing to show, which is how a message is taken down. The number shown last is kept in
settings.json as "message_seen".
"""

from __future__ import annotations

import urllib.error
import urllib.request

from . import __version__, applog

URL = "https://www.kurnal.tech/mistbot/message.txt"
SEEN = "message_seen"       # the settings.json key: the number of the last message shown
TIMEOUT = 30


def parse(text: str) -> tuple[int, str] | None:
    """The number and the message from message.txt; None when there's no number or no message."""
    text = text.lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n").strip()
    first, sep, rest = text.partition("\n")
    if not sep:
        return None
    try:
        number = int(first.strip())
    except ValueError:
        return None
    message = rest.strip()
    return (number, message) if number > 0 and message else None


def fetch(timeout: float = TIMEOUT) -> tuple[int, str] | None:
    """The message on the web page, or None. A missing file is no message; any other failure is
    written to update.log and is no message either."""
    req = urllib.request.Request(URL, headers={"User-Agent": "MistBot/" + __version__})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw: bytes = r.read(64 * 1024)
    except urllib.error.HTTPError as e:
        if e.code != 404:
            applog.update("message check: %s" % e, "WARNING")
        return None
    except Exception as e:      # offline, a timeout, a bad certificate: only the log hears of it
        applog.update("message check: %r" % e, "WARNING")
        return None
    return parse(raw.decode("utf-8", "replace"))


def seen(s: dict[str, object]) -> int:
    """The number of the last message shown, 0 when none was or the setting is not a number."""
    v = s.get(SEEN, 0)
    return v if isinstance(v, int) and not isinstance(v, bool) else 0
