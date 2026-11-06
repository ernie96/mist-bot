"""Build the shareable Uncle Farmer: one file, dist\\Uncle Farmer\\UncleFarmer.exe.

    python build_exe.py
    python build_exe.py --full     every core at normal priority (faster; CI builds this way)

Needs Nuitka (uv sync installs it) and a JDK (the game agent is built from source). UPX isn't used:
Nuitka compresses the single file itself, and it warns that compressing it twice makes it bigger
and slower. Builds its own copy of the game agent every time, never over the one a running game
has loaded. The result needs nothing installed: share the exe. Everything that ships is inside it:
it unpacks to a cache folder (paths.BUNDLE) and starts from there, at once from the second start
on. It puts the game agent beside itself at its first start (the game loads it by path), and what
the player saves goes there too. Character settings, plans, scripts, settings and logs are NOT
built in, so your own setup never ends up in someone else's copy. What goes in, and the finished
exe, are checked (verify) before the build counts as done.
"""

from __future__ import annotations

import glob
import os
import shutil
import subprocess
import sys
import time

from docs_html import build as build_docs
from unclefarmer import __version__, native

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, "dist")
OUT = os.path.join(DIST, "Uncle Farmer")
# The release's jar is built here, never over agent/unclefarmer-agent.jar: a running game has that
# one loaded, and a release can be built while you play.
JAR = os.path.join(DIST, "unclefarmer-agent.jar")
# What goes into the exe, gathered here first (the libraries Nuitka finds itself).
PAYLOAD = os.path.join(DIST, "payload")
# What the finished folder must hold: the one exe.
REQUIRED = ("UncleFarmer.exe",)
# What the payload must hold (verify): the game agent, the data, the translations and the guides.
PAYLOAD_REQUIRED = ("agent/unclefarmer-agent.jar", "data/knowledge.json", "data/atlas.json", "data/skills.json",
                    "lang/unclefarmer.pot", "lang/ur/LC_MESSAGES/unclefarmer.mo", "docs/USER_GUIDE.md",
                    "README.html", "LICENSE")


def windows_version(version: str) -> str:
    """Nuitka's version resource wants up to four numbers: 0.3.1 -> 0.3.1.0."""
    return ".".join((version.split(".") + ["0", "0", "0"])[:4])


def gather_payload(jar: str) -> None:
    """Everything that ships but isn't compiled, in PAYLOAD, laid out as it unpacks."""
    if os.path.exists(PAYLOAD):
        shutil.rmtree(PAYLOAD)
    os.makedirs(os.path.join(PAYLOAD, "agent"))
    # game_texts.json is built from the player's own game folder on first use, never shipped
    shutil.copytree(os.path.join(ROOT, "data"), os.path.join(PAYLOAD, "data"),
                    ignore=shutil.ignore_patterns("game_texts.json"))
    shutil.copytree(os.path.join(ROOT, "lang"), os.path.join(PAYLOAD, "lang"))
    shutil.copytree(os.path.join(ROOT, "docs"), os.path.join(PAYLOAD, "docs"))
    shutil.copy2(jar, os.path.join(PAYLOAD, "agent"))
    # the guides as web pages too (headings to move by), and the user guide as README.html
    pages = build_docs(os.path.join(PAYLOAD, "docs"))
    shutil.copy2(pages["USER_GUIDE.md"], os.path.join(PAYLOAD, "README.html"))
    for name in ("LICENSE", "THIRD_PARTY_NOTICES.md"):
        if os.path.exists(os.path.join(ROOT, name)):
            shutil.copy2(os.path.join(ROOT, name), PAYLOAD)
    verify(PAYLOAD, PAYLOAD_REQUIRED)


def dll_flags() -> list[str]:
    """Nuitka leaves DLLs out of a data folder, so each one is named. The screen reader bridge, and
    the C map searches: loaded with ctypes from beside the compiled unclefarmer.native module, which
    Nuitka doesn't know to carry. Without it the app runs the slower Python searches. The Visual C++
    runtime isn't here: --include-windows-runtime-dlls=yes carries it, on PCs without it too."""
    searches = native.dll_path()
    if not searches or not os.path.exists(searches):
        # the DLL is committed (build_native.py makes it): a build without it is a mistake
        sys.exit("no DLL for routing.c (python build_native.py): a build without it routes in Python")
    pairs = [(os.path.join(ROOT, "nvdaControllerClient64.dll"), "nvdaControllerClient64.dll"),
             (searches, "unclefarmer/native/" + os.path.basename(searches))]
    return ["--include-data-files=%s=%s" % pair for pair in pairs]


def main(full: bool = False) -> None:
    """full: every core at normal priority (faster, but the PC is busy meanwhile)."""
    sys.path.insert(0, ROOT)
    # The jar is rebuilt every time: it is gitignored, so "it exists" says nothing about whether
    # it matches the sources (a stale jar ships the previous agent version and missing commands).
    os.makedirs(DIST, exist_ok=True)
    subprocess.check_call([sys.executable, os.path.join(ROOT, "agent", "build_agent.py"), JAR])
    gather_payload(JAR)
    os.remove(JAR)
    flags = dll_flags()       # before the half-hour compile, not after it
    single = os.path.join(DIST, "UncleFarmer.exe")
    # Each build unpacks to its own folder: a later build of the same version must never start
    # from an earlier one's files.
    unpack = "{CACHE_DIR}/UncleFarmer/%s-%s" % (__version__, time.strftime("%Y%m%d%H%M%S"))
    # The C compile takes half an hour or more and every core it is given: it gets half of them, and
    # it runs (with every compiler it starts) below normal priority, so the PC stays usable meanwhile.
    # full: all of them, at normal priority.
    jobs = (os.cpu_count() or 4) if full else max(1, (os.cpu_count() or 4) // 2)
    priority = 0 if full else getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0)
    subprocess.check_call([
        sys.executable, "-m", "nuitka", os.path.join(ROOT, "UncleFarmer.pyw"),
        "--onefile", "--onefile-tempdir-spec=" + unpack,
        "--include-data-dir=%s=." % PAYLOAD, *flags, "--include-windows-runtime-dlls=yes",
        "--windows-console-mode=disable", "--assume-yes-for-downloads",
        "--output-filename=UncleFarmer.exe", "--output-dir=" + DIST, "--remove-output",
        "--windows-product-name=Uncle Farmer",
        "--windows-product-version=" + windows_version(__version__),
        "--jobs=%d" % jobs, "--lto=auto", "--python-flag=-OO",
        "--include-package=unclefarmer",
    ], creationflags=priority)
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    os.replace(single, os.path.join(OUT, "UncleFarmer.exe"))
    shutil.rmtree(PAYLOAD)
    verify(OUT)
    print("built:", OUT)


def verify(folder: str, required: tuple[str, ...] = REQUIRED) -> None:
    """Stop the build when a folder lacks something it must hold: a missing jar or data file is
    only found by a player otherwise. What the exe itself carries, its self-test checks."""
    missing = [p for p in required if not glob.glob(os.path.join(folder, *p.split("/")))]
    if missing:
        sys.exit("the built folder %s lacks: %s" % (folder, ", ".join(missing)))


if __name__ == "__main__":
    main(full="--full" in sys.argv[1:])
