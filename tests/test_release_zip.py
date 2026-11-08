"""release.py's first-install zip: the exe inside a "Mist Bot" folder, without the update signature."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest
from conftest import returning

import release


def test_install_zip_holds_the_exe_in_its_own_folder(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    out = tmp_path / "dist" / "Uncle Farmer"
    out.mkdir(parents=True)
    (out / "UncleFarmer.exe").write_bytes(b"exe")
    (out / "UncleFarmer.exe.sig").write_text("sig", encoding="ascii")
    monkeypatch.setattr(release, "OUT", str(out))
    monkeypatch.setattr(release, "ROOT", str(tmp_path))
    path = release.install_zip("9.9.9")
    assert Path(path).name == "MistBot-9.9.9.zip"
    with zipfile.ZipFile(path) as z:
        assert z.namelist() == ["Mist Bot/UncleFarmer.exe"]


def test_the_updater_still_takes_the_exe_not_the_zip(monkeypatch: pytest.MonkeyPatch) -> None:
    from unclefarmer import updater
    asset = {"state": "uploaded", "size": 3, "browser_download_url": "https://github.com/x"}
    rel = {"tag_name": "v9.9.9", "draft": False, "prerelease": False, "body": "",
           "assets": [{**asset, "name": "MistBot-9.9.9.zip"}, {**asset, "name": updater.ASSET},
                      {**asset, "name": updater.SIGNATURE}]}
    monkeypatch.setattr(updater, "_ask", returning(rel))
    monkeypatch.delenv("UNCLEFARMER_GITHUB_TOKEN", raising=False)
    found = updater.latest()
    assert found is not None and found["asset"] == updater.ASSET
