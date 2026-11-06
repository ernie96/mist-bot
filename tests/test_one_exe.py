"""The single-file build: what ships is unpacked away from the exe (paths.BUNDLE), and whatever has
to stay at a lasting place is beside the exe (paths.APP). Nothing is built here: the two folders are
pointed at tmp_path, the way the built exe has them."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from unclefarmer import gameinstall, paths


@pytest.fixture
def one_exe(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> tuple[Path, Path]:
    """(the exe's folder, the unpacked copy) with a shipped agent and data file."""
    app, bundle = tmp_path / "app", tmp_path / "bundle"
    (bundle / "agent").mkdir(parents=True)
    (bundle / "data").mkdir()
    app.mkdir()
    (bundle / "agent" / "unclefarmer-agent.jar").write_bytes(b"agent 2")
    (bundle / "data" / "shards.json").write_text("shipped", encoding="utf-8")
    monkeypatch.setattr(paths, "APP", str(app))
    monkeypatch.setattr(paths, "BUNDLE", str(bundle))
    monkeypatch.setattr(paths, "DATA", str(bundle / "data"))
    monkeypatch.setattr(paths, "AGENT_SHIPPED", str(bundle / "agent" / "unclefarmer-agent.jar"))
    monkeypatch.setattr(paths, "AGENT_DIR", str(app / "agent"))
    monkeypatch.setattr(paths, "AGENT_JAR", str(app / "agent" / "unclefarmer-agent.jar"))
    return app, bundle


def test_from_source_nothing_is_split() -> None:
    assert not paths.one_exe()
    assert paths.learned_file("shards.json") == os.path.join(paths.DATA, "shards.json")


def test_the_exe_folder_is_the_one_nuitka_names(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(vars(paths), "__compiled__", SimpleNamespace(containing_dir="C:\\Games\\Bot"))
    monkeypatch.setattr(sys, "executable", "C:\\cache\\unpacked\\python.exe")
    assert paths.exe_folder() == "C:\\Games\\Bot"
    assert paths.app_folder() == "C:\\Games\\Bot"


def test_the_agent_is_put_beside_the_exe(one_exe: tuple[Path, Path]) -> None:
    app, _ = one_exe
    paths.place_agent()
    assert (app / "agent" / "unclefarmer-agent.jar").read_bytes() == b"agent 2"
    assert not (app / "agent" / "unclefarmer-agent.jar.tmp").exists()


def test_a_new_agent_replaces_the_old_one(one_exe: tuple[Path, Path]) -> None:
    app, _ = one_exe
    (app / "agent").mkdir()
    (app / "agent" / "unclefarmer-agent.jar").write_bytes(b"agent 1")
    paths.place_agent()
    assert (app / "agent" / "unclefarmer-agent.jar").read_bytes() == b"agent 2"


def test_an_agent_held_by_a_game_stays_and_nothing_breaks(one_exe: tuple[Path, Path],
                                                         monkeypatch: pytest.MonkeyPatch) -> None:
    app, _ = one_exe
    (app / "agent").mkdir()
    (app / "agent" / "unclefarmer-agent.jar").write_bytes(b"agent 1")

    def in_use(*_args: object) -> None:
        raise PermissionError("in use")

    monkeypatch.setattr(paths.os, "replace", in_use)
    paths.place_agent()
    assert (app / "agent" / "unclefarmer-agent.jar").read_bytes() == b"agent 1"


def test_installing_puts_the_agent_back(one_exe: tuple[Path, Path], tmp_path: Path,
                                        monkeypatch: pytest.MonkeyPatch) -> None:
    app, _ = one_exe
    game = tmp_path / "game"
    game.mkdir()
    (game / gameinstall.VMOPTIONS).write_text("-Xmx1g\n", encoding="utf-8")
    monkeypatch.setattr(paths, "AGENT_RUN", str(app / "agent" / "run"))
    gameinstall.install(str(game))
    assert (app / "agent" / "unclefarmer-agent.jar").exists()
    assert str(app / "agent" / "unclefarmer-agent.jar") in (game / gameinstall.VMOPTIONS).read_text(encoding="utf-8")


def test_data_reads_what_ships_until_the_app_learns_better(one_exe: tuple[Path, Path]) -> None:
    app, bundle = one_exe
    assert paths.data_file("shards.json") == str(bundle / "data" / "shards.json")
    learned = Path(paths.learned_file("shards.json"))
    assert learned == app / "data" / "shards.json"
    learned.parent.mkdir()
    learned.write_text("learned", encoding="utf-8")
    assert paths.data_file("shards.json") == str(learned)
