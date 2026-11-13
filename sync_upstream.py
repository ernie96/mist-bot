"""Bring Uncle Farmer's own dev branch (the `upstream` remote) into this fork's dev.

    uv run python sync_upstream.py            what's new upstream, and which files would conflict
    uv run python sync_upstream.py merge      merge it, settle the conflicts that always go the same way,
                                              rebuild the generated files, and say what is left

Nothing is committed and nothing is pushed: look at what's left, finish it, run check.py, commit.
Upstream's tags are never fetched (it has its own v1.0.1, not this fork's).

The files settled here, and how (FORK.md says why):
  - the version (pyproject.toml, unclefarmer/__init__.py, uv.lock): this fork's numbers
  - requirements*.txt: exported again from the merged uv.lock
  - lang/*.pot, lang/*.po, lang/*/LC_MESSAGES/*.mo: upstream's, then this fork's own translations
    put back where upstream's file has none, then rebuilt with `python -m unclefarmer --strings`
  - README.md and CONTRIBUTING.md: this fork's (upstream rewrites them in its own style; new facts
    are carried over by hand, which this says)
Everything else that conflicts is listed for a person to settle: CHANGELOG.md (upstream's new
entries go under "Unreleased", above this fork's released versions), docs/USER_GUIDE.md and code.
Then tests/test_fork.py says whether the merge undid anything this fork depends on.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
REMOTE, BRANCH = "upstream", "dev"
OURS = ("pyproject.toml", "unclefarmer/__init__.py", "README.md", "CONTRIBUTING.md")
REGENERATED = re.compile(r"^(lang/.*\.(pot|po|mo)|requirements(-dev)?\.txt|uv\.lock)$")


def git(*args: str, check: bool = True) -> str:
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    if check and r.returncode != 0:
        sys.exit("git %s failed:\n%s" % (" ".join(args), r.stderr.strip()))
    return r.stdout


def run(*cmd: str) -> None:
    print("$", " ".join(cmd))
    if subprocess.call(list(cmd), cwd=ROOT) != 0:
        sys.exit("that failed: fix it, then go on by hand")


def fetch() -> str:
    git("fetch", REMOTE, "--no-tags", "--prune")
    return "%s/%s" % (REMOTE, BRANCH)


def report(theirs: str) -> list[str]:
    new = git("log", "--no-merges", "--format=%h %cs %an: %s", "HEAD.." + theirs).strip()
    print("New on %s:\n%s\n" % (theirs, new or "(nothing)"))
    for b in git("branch", "-r", "--format=%(refname:short)").split():
        if b.startswith(REMOTE + "/") and not b.endswith("/HEAD") and b != theirs:
            ahead = git("rev-list", "--count", theirs + ".." + b).strip()
            if ahead != "0":
                print("%s has %s commit(s) not in %s yet" % (b, ahead, theirs))
    agent = re.findall(r"static final int VERSION = (\d+)", git("diff", "HEAD..." + theirs, "--", "agent/src"))
    if agent:
        print("Game agent version: %s" % " -> ".join(agent))
    trial = git("merge-tree", "--write-tree", "--name-only", "HEAD", theirs, check=False)
    conflicts = re.findall(r"CONFLICT \([^)]*\): Merge conflict in (.+)", trial)
    print("Would conflict: %s" % (", ".join(conflicts) or "nothing"))
    return conflicts


def conflicted() -> list[str]:
    return [p for p in git("diff", "--name-only", "--diff-filter=U").split("\n") if p]


def restore_translations(before: dict[str, str]) -> int:
    """Put this fork's own translations back where the merged .po has none (upstream's file lacks
    the fork's own texts, such as Donate)."""
    sys.path.insert(0, ROOT)
    from unclefarmer import catalog
    filled = 0
    for path, old_text in before.items():
        full = os.path.join(ROOT, path)
        if not os.path.exists(full):
            continue
        _h, old_entries, _o = catalog._parse(old_text)  # pyright: ignore[reportPrivateUsage]
        old = {k: v for k, v in old_entries if v}
        with open(full, encoding="utf-8") as f:
            header, entries, obsolete = catalog._parse(f.read())  # pyright: ignore[reportPrivateUsage]
        out: list[tuple[str, str]] = []
        for k, v in entries:
            if not v and old.get(k):
                v, filled = old[k], filled + 1
            out.append((k, v))
        with open(full, "w", encoding="utf-8", newline="\n") as f:
            f.write(catalog.render_po(header, out, obsolete))
    return filled


def merge(theirs: str) -> None:
    if git("status", "--porcelain").strip():
        sys.exit("There are uncommitted changes: commit or stash them first.")
    report(theirs)
    po_files = [p for p in git("ls-files", "lang").split() if p.endswith(".po")]
    before = {p: git("show", "HEAD:" + p) for p in po_files}
    r = subprocess.run(["git", "merge", "--no-ff", "--no-commit", theirs], cwd=ROOT, capture_output=True, text=True)
    print(r.stdout.strip())
    left = conflicted()
    for path in left:
        if path in OURS or path == "uv.lock":
            git("checkout", "--ours", "--", path)
        elif REGENERATED.match(path):
            git("checkout", "--theirs", "--", path)
        else:
            continue
        git("add", "--", path)
    if "uv.lock" in left or "pyproject.toml" in left:
        run("uv", "lock")
    run("uv", "run", "python", "export_requirements.py")
    print("Fork translations put back: %d" % restore_translations(before))
    run("uv", "run", "python", "-m", "unclefarmer", "--strings")
    git("add", "lang", "requirements.txt", "requirements-dev.txt", "uv.lock")
    still = conflicted()
    settled = sorted(set(left) - set(still))
    print("\nSettled: %s" % (", ".join(settled) or "nothing"))
    for path in ("README.md", "CONTRIBUTING.md"):
        if path in settled:
            print("  %s kept as this fork has it: carry over any new facts from %s's version by hand"
                  % (path, theirs))
    print("Still to settle by hand: %s" % (", ".join(still) or "nothing"))
    print("\nThen: uv run pytest tests/test_fork.py, uv run python check.py, and commit.")


def main() -> None:
    theirs = fetch()
    if sys.argv[1:] == ["merge"]:
        merge(theirs)
    elif not sys.argv[1:]:
        report(theirs)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
