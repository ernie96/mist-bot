"""Updates (updater.py): after one, checking, offering and installing."""

from __future__ import annotations

import threading

import wx

from ... import __version__, applog, settings, updater
from ...i18n import _
from .. import agentfix
from ..common import ask, ask_ok, error, info, save_file
from .base import FrameParts

CHECK_EVERY_MS = 6 * 3600 * 1000   # while the window is open: a fix reaches a copy left open the same day
OFFER_RETRY_MS = 60 * 1000         # a found update waits this long between tries while a bot runs or a dialog is up


class UpdatesMixin(FrameParts):
    update_timer: wx.Timer
    update_waiting: updater.Release | None    # found while busy: offered once nothing is in the way
    update_offered: set[str]                  # versions offered by the periodic check this session
    update_retry: bool                        # an OFFER_RETRY_MS wait is already set

    def start_update_checks(self) -> None:
        """Look again every CHECK_EVERY_MS while the window is open (the start check is after_update's).
        Each tick reads the settings, so turning the check on or off in Settings counts at once."""
        self.update_waiting, self.update_offered, self.update_retry = None, set(), False
        self.update_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, lambda e: self.update_tick(), self.update_timer)
        self.update_timer.Start(CHECK_EVERY_MS)
        applog.bootup.note("update check while open: every %d h" % (CHECK_EVERY_MS // 3_600_000))

    def update_tick(self) -> None:
        """The periodic check. Quiet: nothing is said when there is no new version or GitHub can't
        be reached (update.log has it); a new version is offered as the start check offers it."""
        if self.destroyed or self.updating or not updater.frozen() or not self.s.get("check_updates", True):
            return
        if self.update_waiting is not None:          # already found: no need to ask GitHub again
            self._offer_waiting()
            return
        ch = updater.channel(self.s.get("update_channel"))

        def look() -> None:
            rel = updater.check(update_channel=ch)
            if rel is not None:
                try:
                    wx.CallAfter(self._periodic_found, rel)
                except RuntimeError:                 # the window went away meanwhile
                    pass
        threading.Thread(target=look, daemon=True).start()

    def _periodic_found(self, rel: updater.Release) -> None:
        if self.destroyed or rel["version"] in (self.s.get("skip_version"), *self.update_offered):
            return
        self.update_waiting = rel
        self._offer_waiting()

    def _ui_busy(self) -> bool:
        """A modal window is up (a dialog the player is in): the offer would land on top of it."""
        return any(w is not self and isinstance(w, wx.Dialog) and w.IsShown() and w.IsModal()
                   for w in wx.GetTopLevelWindows())

    def _offer_waiting(self) -> None:
        """Offer the waiting update unless a bot runs, an update is under way or a dialog is open;
        then try again in OFFER_RETRY_MS. An update needs every bot stopped, so a farming run is
        never interrupted: the offer comes when it ends."""
        rel = self.update_waiting
        if rel is None or self.destroyed:
            return
        if self.updating or self.runs or self._ui_busy():
            if not self.update_retry:
                self.update_retry = True
                wx.CallLater(OFFER_RETRY_MS, self._retry_offer)
            return
        self.update_waiting = None
        self.update_offered.add(rel["version"])
        updater.log("update check while open: %s offered" % rel["version"])
        self.offer_update(rel, True)

    def _retry_offer(self) -> None:
        self.update_retry = False
        self._offer_waiting()
    # ------------------------------------------------------------ updates (updater.py)
    def after_update(self) -> None:
        """Say how an update went, empty the staging folder, and look for a newer one in the background."""
        result = updater.take_result()
        updater.tidy()
        mine = updater.installed_version()
        # In the background: the update helper may still be closing, and the cleanup waits for it.
        threading.Thread(target=updater.clean, kwargs={"wait": 60}, daemon=True).start()
        if result is not None and result.get("ok"):
            applog.bootup.note("the update to %s finished" % mine)
            info(self, _("Uncle Farmer is updated to {v}.", v=mine))
        elif result is not None:
            applog.bootup.note("the update to %s didn't finish: %s" % (result.get("version"), result.get("error")),
                               "WARNING")
            error(self, _("The update to {v} didn't finish: {why}\nUncle Farmer {cur} still works. The details are "
                          "in {log}.", v=result.get("version"), why=result.get("error"), cur=mine,
                          log=updater.LOG))
        ch = updater.channel(self.s.get("update_channel"))
        if not updater.frozen():
            applog.bootup.note("no update check: this copy runs from source")
        elif not self.s.get("check_updates", True):
            applog.bootup.note("no update check: it is off in Settings")
        else:
            def look() -> None:
                rel = updater.check(update_channel=ch)
                if rel and rel["version"] != self.s.get("skip_version"):
                    wx.CallAfter(self.offer_update, rel, True)
            threading.Thread(target=look, daemon=True).start()
            applog.bootup.note("update check (%s channel) running in the background" % ch)

    def check_updates(self) -> None:
        """Help, Check for updates. The request goes to a worker: GitHub can take its time and the
        window must not freeze (a BusyCursor only hid that)."""
        if self.destroyed:
            return
        self._append(_("Looking for a new version"), False)
        ch = updater.channel(self.s.get("update_channel"))

        def work() -> None:
            rel: updater.Release | None = None
            err: updater.UpdateError | None = None
            try:
                rel = updater.latest(update_channel=ch)
            except updater.UpdateError as e:
                err = e
                updater.log("update check (%s) failed: %s" % (ch, e), "WARNING")
            else:
                updater.log("update check (%s), asked from the Help menu: newest %s" % (
                    ch, rel["version"] if rel else "none to see"))
            try:
                wx.CallAfter(self._checked_updates, rel, err)
            except RuntimeError:          # the window went away meanwhile
                pass
        threading.Thread(target=work, daemon=True).start()

    def _checked_updates(self, rel: updater.Release | None, err: updater.UpdateError | None) -> None:
        if self.destroyed:
            return
        self.SetStatusText("")
        dev = updater.channel(self.s.get("update_channel")) == "dev"
        mine = updater.installed_version()
        if err is not None:
            error(self, _("Couldn't reach GitHub to look for updates: {why}", why=err))
        elif rel is None and not updater.REPO:
            info(self, _("Uncle Farmer {v} doesn't look for updates online. Download the new "
                         "UncleFarmer.exe and put it in place of this one.", v=__version__))
        elif rel is None and dev:
            info(self, _("No development build of Uncle Farmer can be seen on GitHub yet."))
        elif rel is None:
            info(self, _("No release of Uncle Farmer can be seen on GitHub yet."))
        elif not updater.is_newer(rel["version"], mine) and updater.is_dev(mine) and not dev:
            # switched back to master: a stable release is offered once one is newer than this build
            info(self, _("You have the development build {v}. The newest stable release, {stable}, is older; "
                         "the next stable release newer than your build will be offered.", v=mine,
                         stable=rel["version"]))
        elif not updater.is_newer(rel["version"], mine):
            info(self, _("Uncle Farmer {v} is the newest version.", v=mine))
        else:
            self.offer_update(rel, False)

    def offer_update(self, rel: updater.Release, at_start: bool) -> None:
        if self.destroyed:
            return
        notes = rel.get("notes") or _("(no notes)")
        if len(notes) > 1500:
            notes = notes[:1500].rstrip() + " ..."
        if updater.is_dev(rel["version"]):
            notes = _("This is a development build from the dev branch: the newest changes, not yet a stable "
                      "release, and it can break.") + "\n" + notes
        if not ask(self, _("Uncle Farmer {v} is out (you have {cur}).\n\nWhat's new:\n{notes}\n\n"
                           "Update now? Uncle Farmer closes, updates and starts again; your characters, plans, "
                           "scripts and settings stay as they are.", v=rel["version"],
                           cur=updater.installed_version(), notes=notes),
                   _("Update")):
            if at_start:                      # not asked again at start for this one; the Help menu still offers it
                self.s["skip_version"] = rel["version"]
                save_file(self, settings.save_app, self.s)
            return
        self.install_update(rel)

    def install_update(self, rel: updater.Release) -> None:
        if not updater.frozen():
            info(self, _("This copy runs from its source code: update it with git pull."))
            return
        if self.updating:
            return
        if self.runs:
            error(self, _("Stop every running bot first, then update."))
            return
        games = agentfix.running_pids()
        if games:
            # An open game holds the agent file, which the update replaces: the games close first.
            if not ask_ok(self, _("The update reinstalls Uncle Farmer's agent, which the open games have loaded, "
                                  "so every Mist World window must close first.\n\nPress OK to close them ({n} "
                                  "open) and update. Start Mist World again after the update.", n=len(games)),
                          _("Update")):
                return
            self.updating = True
            self.say(_("Closing every Mist World window for the update"))
            agentfix.close_then(games, lambda left: self._games_closed_for_update(rel, left))
            return
        self._download_update(rel)

    def _games_closed_for_update(self, rel: updater.Release, left: list[int]) -> None:
        self.updating = False
        if self.destroyed:
            return
        if left:
            error(self, _("Mist World windows that didn't close: {n}. Close them, then update.", n=len(left)))
            return
        self._download_update(rel)

    def _download_update(self, rel: updater.Release) -> None:
        self.updating = True
        dlg = wx.ProgressDialog(_("Update"), _("Downloading Uncle Farmer {v}", v=rel["version"]), 100, self,
                                wx.PD_APP_MODAL | wx.PD_CAN_ABORT | wx.PD_AUTO_HIDE | wx.PD_ELAPSED_TIME)
        state = {"cancel": False}       # the worker asks this; the window's thread sets it

        def progress(done: int, total: int) -> bool:
            if self.destroyed:
                return False
            try:
                wx.CallAfter(self._update_progress, dlg, state, done, total)
            except RuntimeError:
                return False
            return not state["cancel"]

        def work() -> None:
            folder: str | None = None
            err: Exception | None = None
            try:
                with updater.claimed("update"):
                    folder = updater.download(rel, progress)
            except Exception as e:      # whatever goes wrong, the window must hear of it and close
                err = e
                updater.log("the update to %s stopped: %r" % (rel["version"], e),
                            "INFO" if str(e) == "cancelled" else "WARNING")
            try:
                wx.CallAfter(self._update_done, dlg, rel, folder, err)
            except RuntimeError:
                pass
        threading.Thread(target=work, daemon=True).start()

    def _update_progress(self, dlg: wx.ProgressDialog, state: dict[str, bool], done: int, total: int,
                         message: str | None = None) -> None:
        if self.destroyed:
            state["cancel"] = True
            return
        value = min(99, done * 100 // max(1, total))
        keep = dlg.Update(value, message)[0] if message else dlg.Update(value)[0]
        if not keep:
            state["cancel"] = True

    def _update_done(self, dlg: wx.ProgressDialog, rel: updater.Release, folder: str | None,
                     err: Exception | None) -> None:
        self.updating = False
        if self.destroyed:
            return
        dlg.Destroy()
        if err is not None or folder is None:        # (no folder comes only with an error)
            if str(err) != "cancelled":
                error(self, _("The update didn't download: {why}", why=err))
            updater.clean()
            return
        try:
            updater.start_install(folder, rel["version"])
        except OSError as e:
            error(self, _("The update couldn't start: {why}", why=e))
            return
        self.close_reason = "the update to %s is ready: the updater takes over" % rel["version"]
        self.Close()
