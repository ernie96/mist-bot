"""What this fork (Mist Bot) changes in Uncle Farmer, held in place: after a merge from upstream
(sync_upstream.py) a failure here says which of the fork's own changes the merge undid. FORK.md
lists them and how to settle each."""

from __future__ import annotations

import inspect
import os

import pytest

from unclefarmer import contact, control, settings, updater

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def source(path: str) -> str:
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return f.read()


def test_updates_come_signed_from_this_forks_releases() -> None:
    assert updater.REPO == "ernie96/mist-bot"
    assert updater.ASSET == "UncleFarmer.exe" and updater.SIGNATURE == "UncleFarmer.exe.sig"
    assert updater.PUBLIC_KEY == "9ZL7+zrOloMB3Odt9KwnvF/htqK4xjLZOHTSrlvX4fY="
    assert updater.DOMAIN == "MistBot-update-v1"


def test_releases_carry_the_install_zip_beside_the_exe() -> None:
    import release
    assert release.ZIP == "MistBot-%s.zip" and release.ZIP_FOLDER == "Mist Bot"
    assert "_publish(a, v, [zipped, exe, sig])" in source("release.py")


def test_the_contact_and_donation_details_are_ernestos() -> None:
    assert contact.EMAIL == "ernesto@melendez.land"
    assert contact.MASTODON == "ernie@someplace.social"
    assert contact.TELEGRAM == "https://t.me/+-SHI1xTKJugwMzQ5"
    assert contact.PAYPAL == "https://paypal.me/RefinnejLTD"
    assert contact.KOFI == "https://ko-fi.com/ernie96"
    assert contact.ISSUES == "https://github.com/ernie96/mist-bot/issues"


def test_the_help_menu_keeps_the_telegram_channel_and_donate() -> None:
    main = source("unclefarmer/gui/main.py")
    assert '_("&Telegram updates channel"), lambda e: self.join_telegram()' in main
    assert 'opens(_("D&onate")), lambda e: self.donate()' in main
    assert "Join the &Telegram group" not in main            # upstream's group, not this fork's channel


def test_the_update_check_also_runs_while_open() -> None:
    pytest.importorskip("wx")
    from unclefarmer.gui.mainparts import editing, updates
    assert updates.CHECK_EVERY_MS == 6 * 3600 * 1000
    first_run = inspect.getsource(editing.EditingMixin.first_run)
    assert "self.start_update_checks()" in first_run


def test_control_by_other_programs_is_wired_and_off_by_default() -> None:
    pytest.importorskip("wx")
    from unclefarmer.gui import remote
    from unclefarmer.gui.mainparts import editing
    assert settings.APP_DEFAULTS["mcp_control"] is False and settings.APP_DEFAULTS["mcp_raw_agent"] is False
    assert "remote.start()" in inspect.getsource(editing.EditingMixin.first_run)
    assert '"--mcp" in sys.argv' in source("unclefarmer/__main__.py")
    main = source("unclefarmer/gui/main.py")
    assert "self.remote = RemoteControl(self)" in main and "remote.stop()" in main
    logpane = source("unclefarmer/gui/mainparts/logpane.py")
    assert "self.events.append(" in logpane                   # read_log and wait_for_log see every line
    assert "def errand_on(" in source("unclefarmer/gui/mainparts/runs.py")
    assert "self.control_page(nb)" in source("unclefarmer/gui/setup.py")
    for t in control.TOOLS:
        assert callable(getattr(remote.RemoteControl, "t_" + t.name, None)), t.name


def test_the_one_exe_build_stays() -> None:
    build = source("build_exe.py")
    assert "--onefile" in build or "onefile" in build
    assert "--windows-console-mode=disable" in build


def test_the_fork_names_itself_in_the_readme() -> None:
    readme = source("README.md")
    assert "Mist Bot" in readme and "ernie96/mist-bot" in readme
    assert "MistBot-<version>.zip" in readme
