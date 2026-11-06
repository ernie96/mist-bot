"""Where everything lives. The app is portable: what it keeps sits in one folder next to the exe.

The built exe is a single file: Nuitka unpacks the program, its data and its translations to a
cache folder (BUNDLE) and runs it there. Whatever has to be a real file at a lasting place stays
beside the exe (APP): the game agent, which the game loads by its path, and everything the app
writes. From source, the two are the same folder.
"""

from __future__ import annotations

import os
import sys


def frozen() -> bool:
    """Running as the built UncleFarmer.exe, not from the source: the one answer every module asks.
    build_exe.py builds with Nuitka, which sets no sys.frozen; it puts __compiled__ in the globals
    of every module it compiles, this one too. sys.frozen still counts, for another tool's build."""
    return "__compiled__" in globals() or bool(getattr(sys, "frozen", False))


def exe_folder() -> str:
    """The folder of the exe the player started. Nuitka says so itself; a single-file build's
    sys.executable is a python.exe in the unpacked copy, never beside the real exe."""
    where: str | None = getattr(globals().get("__compiled__"), "containing_dir", None)
    return where or os.path.dirname(os.path.abspath(sys.executable))


def app_folder() -> str:
    """The folder that holds what the app keeps: in a build the exe's own, from source the
    checkout's. Never the working folder."""
    if frozen():
        return exe_folder()
    return BUNDLE


BUNDLE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # what ships: read only in a build
APP = app_folder()

DATA = os.path.join(BUNDLE, "data")
LANG = os.path.join(BUNDLE, "lang")
DOCS = os.path.join(BUNDLE, "docs")
AGENT_SHIPPED = os.path.join(BUNDLE, "agent", "unclefarmer-agent.jar")
AGENT_DIR = os.path.join(APP, "agent")
AGENT_JAR = os.path.join(AGENT_DIR, "unclefarmer-agent.jar")
AGENT_RUN = os.path.join(AGENT_DIR, "run")        # the agent's port file and log
PROFILES = os.path.join(APP, "profiles")
PLANS = os.path.join(APP, "plans")
SCRIPTS = os.path.join(APP, "scripts")
SETTINGS = os.path.join(APP, "settings.json")
LOGS = os.path.join(APP, "logs")

for _d in (PROFILES, PLANS, SCRIPTS, LOGS):
    os.makedirs(_d, exist_ok=True)


def one_exe() -> bool:
    """Running as the single-file build: what ships is unpacked away from the exe's own folder."""
    return os.path.normcase(os.path.abspath(APP)) != os.path.normcase(os.path.abspath(BUNDLE))


def learned_file(name: str) -> str:
    """Where a file the app writes into data/ goes: beside the exe in the single-file build (what
    ships is replaced by every new version), the checkout's data/ from source."""
    return os.path.join(APP, "data", name) if one_exe() else os.path.join(DATA, name)


def data_file(name: str) -> str:
    """A data file the app may have rewritten: the learned copy if there is one, else what ships."""
    learned = learned_file(name)
    return learned if os.path.isfile(learned) else os.path.join(DATA, name)


def place_agent() -> None:
    """Put the shipped agent at AGENT_JAR, unless the same bytes are there. The game loads it by its
    path, also while the app is closed, so it can't stay in the unpacked copy. A game holding the
    old one keeps it: the check at start says so, and installing again comes back here."""
    if not one_exe():
        return
    try:
        with open(AGENT_SHIPPED, "rb") as f:
            shipped = f.read()
        try:
            with open(AGENT_JAR, "rb") as f:
                if f.read() == shipped:
                    return
        except OSError:
            pass
        os.makedirs(AGENT_DIR, exist_ok=True)
        with open(AGENT_JAR + ".tmp", "wb") as f:
            f.write(shipped)
        os.replace(AGENT_JAR + ".tmp", AGENT_JAR)
    except OSError:
        pass


place_agent()


def safe_name(name: str) -> str:
    """A file name from a character or plan name; keeps letters, digits, space, - and _."""
    keep = "".join(c if c.isalnum() or c in " -_" else "_" for c in name).strip()
    return keep or "unnamed"
