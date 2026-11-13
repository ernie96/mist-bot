"""The open window's end of control by other programs (control.py; `UncleFarmer.exe --mcp` is the
other end). A thread listens on the named pipe; each connection gets a thread that reads requests and
answers them. A tool that touches the window or the runs is done on the window's thread, as if the
player had done it, and never opens a message box: what a box would have asked, the tool's own
arguments say (confirm, replace). Settings, Control turns it on; it is off by default.

The answers are for the program calling the tools, so they are English only.
"""

from __future__ import annotations

import datetime as dt
import os
import threading
import time
from collections.abc import Callable
from multiprocessing import AuthenticationError
from multiprocessing.connection import Connection, Listener
from typing import TYPE_CHECKING, Any, TypeVar

import wx
from pydantic import ValidationError

from .. import (__version__, applog, chat, control, gameinstall, jsonio, messages, nearby, paths, schedule, settings,
                silencer, speech, stats, updater)
from ..engine import dungeon, plan as plans, script
from ..errors import carry_on
from ..link import AgentError, AgentLink, server_name
from . import agentfix

if TYPE_CHECKING:
    from .main import MainFrame

T = TypeVar("T")
UI_WAIT = 30.0                      # seconds a tool waits for the window's thread
CONFIRMED = {"gem_maker", "enhance", "chores", "gather", "dungeon", "lose_xp", "restock", "sell_collection",
             "sell_shards", "clean_bag"}        # jobs that spend, sell or throw away: confirm must be true
CHECKABLE = {"gem_maker", "enhance", "chores", "gather", "dungeon", "lose_xp"}
CHANNEL_NUMBERS = {"global": 0, "map": 1, "nearby": 2, "gang": 3, "team": 4, "international": 5,
                   "private_channel": 6}
OFF_LIMITS = {"mcp_control", "mcp_raw_agent"}     # only the player changes who may control the bot


class ToolError(Exception):
    """What went wrong, said to the calling program."""


Result = tuple[str, Any]            # (text for the caller, data or None)


class RemoteControl:
    def __init__(self, window: MainFrame) -> None:
        self.w = window
        self.halt = threading.Event()
        self.listener: Listener | None = None

    # ---------------------------------------------------------------------------- the pipe
    def start(self) -> None:
        try:
            secret = control.new_secret()
        except OSError as e:
            applog.bootup.problem("control by other programs: couldn't write the secret: %s" % e)
            return
        threading.Thread(target=self._listen, args=(secret,), daemon=True, name="unclefarmer-control").start()

    def stop(self) -> None:
        self.halt.set()

    def _listen(self, secret: bytes) -> None:
        try:
            self.listener = Listener(control.pipe_name(), family="AF_PIPE", authkey=secret)
        except OSError as e:
            applog.write("control by other programs: the pipe couldn't be opened: %s" % e)
            return
        while not self.halt.is_set():
            try:
                conn = self.listener.accept()
            except (AuthenticationError, OSError, EOFError):
                self.halt.wait(0.2)         # a program without the secret, or one that went away;
                continue                    # never a busy loop if the pipe keeps failing
            threading.Thread(target=self._serve, args=(conn,), daemon=True, name="unclefarmer-control-client").start()

    def _serve(self, conn: Connection) -> None:
        with conn:
            while not self.halt.is_set():
                try:
                    req = control.receive(conn)
                except (EOFError, OSError, ValueError):
                    return
                try:
                    control.send(conn, self.handle(req))
                except (OSError, ValueError):
                    return

    def handle(self, req: Any) -> dict[str, Any]:
        """One request {"tool", "args"} -> {"ok", "text", "data"}."""
        if not jsonio.is_object(req) or not isinstance(req.get("tool"), str):
            return {"ok": False, "text": "A request is {\"tool\": name, \"args\": {...}}."}
        if req["tool"] == "hello":
            return {"ok": bool(self.w.s.get("mcp_control")), "text": "" if self.w.s.get("mcp_control")
                    else control.NOT_ALLOWED, "data": {"version": __version__}}
        if not self.w.s.get("mcp_control"):
            return {"ok": False, "text": control.NOT_ALLOWED}
        if self.w.destroyed:
            return {"ok": False, "text": "Uncle Farmer is closing."}
        tool = control.BY_NAME.get(req["tool"])
        if tool is None:
            return {"ok": False, "text": "There is no tool called %s." % req["tool"]}
        raw_args = req.get("args")
        args: dict[str, Any] = raw_args if jsonio.is_object(raw_args) else {}
        if tool.kind == control.RISKY and "confirm" in tool.properties and args.get("confirm") is not True \
                and "confirm" in tool.required:
            return {"ok": False, "text": "%s needs confirm=true. Ask the player first." % tool.name}
        missing = [r for r in tool.required if args.get(r) in (None, "")]
        if missing:
            return {"ok": False, "text": "%s needs: %s." % (tool.name, ", ".join(missing))}
        try:
            text, data = getattr(self, "t_" + tool.name)(args)
        except ToolError as e:
            return {"ok": False, "text": str(e)}
        except Exception as e:          # a tool's bug must not end the connection
            carry_on(e, "a control tool (%s)" % tool.name)
            return {"ok": False, "text": "%s failed: %s" % (tool.name, e)}
        applog.write("control by another program: %s" % tool.name)
        return {"ok": True, "text": text, "data": data}

    # ---------------------------------------------------------------------------- helpers
    def ui(self, fn: Callable[..., T], *args: Any) -> T:
        """fn on the window's thread, its result (or its exception) back here."""
        if threading.current_thread() is threading.main_thread():
            return fn(*args)
        box: list[Any] = []
        done = threading.Event()

        def go() -> None:
            try:
                box.append((True, fn(*args)))
            except BaseException as e:
                box.append((False, e))
            finally:
                done.set()
        wx.CallAfter(go)
        if not done.wait(UI_WAIT):
            raise ToolError("Uncle Farmer's window didn't answer within %d s (a window of its own may be open "
                            "and waiting for the player)." % UI_WAIT)
        ok, value = box[0]
        if not ok:
            raise value
        return value

    def games(self) -> list[tuple[int, str | None, str | None]]:
        return self.ui(lambda: list(self.w.games))

    def pid(self, args: dict[str, Any]) -> int:
        """The game asked for: a pid, a character's name, or the only open game."""
        games = self.games()
        want = args.get("game")
        if want is None or want == "":
            if len(games) == 1:
                return games[0][0]
            if not games:
                raise ToolError("No game with the agent is open. Start Mist World (see agent_status).")
            raise ToolError("Several games are open: name one (game = pid or character). %s" % self.games_text(games))
        if isinstance(want, int) or (isinstance(want, str) and want.strip().isdigit()):
            pid = int(want)
            if any(g[0] == pid for g in games):
                return pid
            raise ToolError("No open game has pid %d. %s" % (pid, self.games_text(games)))
        text = str(want).strip().lower()
        for pid, name, _where in games:
            if name and text in (name.lower(), settings.profile_display(name).lower(),
                                 settings.profile_name(name).lower()):
                return pid
        raise ToolError("No open game is logged in as %s. %s" % (want, self.games_text(games)))

    @staticmethod
    def games_text(games: list[tuple[int, str | None, str | None]]) -> str:
        if not games:
            return "No game is open."
        return "Open games: " + "; ".join("%d (%s)" % (pid, settings.profile_display(name) if name else "not logged in")
                                          for pid, name, _w in games)

    def character(self, args: dict[str, Any], need: bool = True) -> str:
        """A character's profile key: named (profile, display or plain name) or the given/only game's."""
        want = args.get("character")
        if want:
            text = str(want).strip().lower()
            for key in settings.profiles():
                if text in (key.lower(), settings.profile_display(key).lower(), settings.profile_name(key).lower()):
                    return key
            raise ToolError("No character called %s has settings. list_characters names them." % want)
        pid = self.pid(args)
        name = self.ui(self.w.character, pid)
        if not name:
            raise ToolError("Game %d has no character logged in yet." % pid)
        return name

    def run_on(self, pid: int) -> Any:
        return self.ui(lambda: self.w.runs.get(pid))

    def need_idle(self, pid: int) -> None:
        if self.run_on(pid) is not None:
            raise ToolError("A bot is running on game %d: stop it first." % pid)

    def item(self, name: str, kind: str | None) -> tuple[str, str]:
        items: list[tuple[str, str]] = [("plan", n) for n in plans.names()] + \
                                       [("script", n) for n in plans.script_names()]
        found = [it for it in items if it[1].lower() == name.strip().lower() and (kind is None or it[0] == kind)]
        if not found:
            raise ToolError("No %s called %s. list_plans names them." % (kind or "plan or script", name))
        return found[0]

    def events(self, after: int, pid: int | None = None, important: bool = False) -> list[dict[str, Any]]:
        with self.w.event_lock:
            rows = [e for e in self.w.events if e["n"] > after]
        if pid is not None:
            rows = [e for e in rows if e.get("pid") in (pid, None)]
        if important:
            rows = [e for e in rows if e["spoken"]]
        return rows

    # ---------------------------------------------------------------------------- looking
    def t_status(self, args: dict[str, Any]) -> Result:
        games = self.t_list_games({})[1]
        folder = self.w.s.get("game_folder", "")
        data = {"version": __version__, "games": games, "plans": len(plans.names()),
                "scripts": len(plans.script_names()), "agent": gameinstall.status(folder),
                "game_folder": folder, "raw_agent_commands": bool(self.w.s.get("mcp_raw_agent")),
                "last_log_line": self.w.event_seq}
        lines = ["Uncle Farmer %s. Agent: %s." % (__version__, data["agent"]), self.games_text(
            [(g["pid"], g["profile"], g["map"]) for g in games])]
        for g in games:
            if g["running"]:
                lines.append("%s: %s%s - %s" % (g["character"], g["running"], " (paused)" if g["paused"] else "",
                                                 g["activity"]))
        return "\n".join(lines), data

    def t_list_games(self, args: dict[str, Any]) -> Result:
        def read() -> list[dict[str, Any]]:
            if args.get("refresh"):
                self.w.refresh_games()
            out: list[dict[str, Any]] = []
            for pid, name, where in self.w.games:
                run = self.w.runs.get(pid)
                out.append({"pid": pid, "profile": name, "character": settings.profile_display(name) if name else None,
                            "server": settings.profile_server(name) if name else None, "map": where,
                            "running": run.title if run else None, "kind": getattr(run, "kind", None) if run else None,
                            "paused": self.w.is_paused(pid), "activity": self.w.last_line.get(pid, "")})
            return out
        games = self.ui(read)
        return self.games_text([(g["pid"], g["profile"], g["map"]) for g in games]), games

    def t_game_state(self, args: dict[str, Any]) -> Result:
        pid = self.pid(args)
        part = str(args.get("part") or "summary")
        if part not in ("summary", *control.MEM_PARTS):
            raise ToolError("part is summary or one of: %s" % ", ".join(control.MEM_PARTS))
        try:
            with AgentLink(pid=pid, timeout=10) as a:
                s = a.json("mem" if part in ("summary", "all") else "mem " + part)
                server = server_name(a)
        except (AgentError, OSError, ValueError) as e:
            raise ToolError("The game didn't answer: %s" % e) from e
        if s is None or (part == "summary" and not jsonio.is_object(s)):
            raise ToolError("The game's answer wasn't a reading.")
        if part != "summary":
            return "Game %d, %s." % (pid, part), s
        return self.summary(pid, s, server)

    @staticmethod
    def summary(pid: int, s: dict[str, Any], server: str) -> Result:
        raw_me, raw_map, raw_ents = s.get("self"), s.get("map"), s.get("entities")
        me: dict[str, Any] = raw_me if jsonio.is_object(raw_me) else {}
        where: dict[str, Any] = raw_map if jsonio.is_object(raw_map) else {}
        if not me.get("name"):
            return "Game %d: no character is logged in." % pid, {"pid": pid, "logged_in": False}
        sheet: dict[str, Any] = me.get("sheet") or {}
        vit: dict[str, Any] = me.get("vitals") or {}
        x, y = float(me.get("x", 0)), float(me.get("y", 0))
        ents: list[Any] = raw_ents if jsonio.is_array(raw_ents) else []
        monsters: list[dict[str, Any]] = []
        for e in ents:
            if jsonio.is_object(e) and e.get("kind") == "monster":
                d = ((float(e.get("x", 0)) - x) ** 2 + (float(e.get("y", 0)) - y) ** 2) ** 0.5
                monsters.append({"id": e.get("id"), "name": e.get("name"), "distance": round(d, 1),
                                 "hp": e.get("hp"), "maxhp": e.get("maxhp")})
        monsters.sort(key=lambda m: m["distance"])
        data = {"pid": pid, "logged_in": True, "character": me.get("name"), "server": server,
                "map": where.get("name"), "map_id": where.get("id"), "x": round(x, 1), "y": round(y, 1),
                "hp": me.get("hp"), "maxhp": me.get("maxhp"),
                "mp": vit.get("mp") if vit.get("mp", -1) >= 0 else sheet.get("mp"), "maxmp": sheet.get("maxmp"),
                "level": sheet.get("level"), "bag_load": sheet.get("load"), "bag_max": sheet.get("maxload"),
                "drop_seconds_left": sheet.get("drop_seconds"), "pet": nearby.pet_text(s),
                "players": nearby.players_text(s), "monsters": monsters[:25]}
        text = "%s on %s at %d, %d. HP %s/%s. Pet: %s. Players: %s. Monsters in view: %d." % (
            data["character"], data["map"], int(x), int(y), data["hp"], data["maxhp"], data["pet"], data["players"],
            len(monsters))
        return text, data

    def t_read_log(self, args: dict[str, Any]) -> Result:
        limit = max(1, min(500, int(args.get("limit") or 100)))
        pid = self.pid(args) if args.get("game") not in (None, "") else None
        rows = self.events(int(args.get("after") or 0), pid, bool(args.get("important_only")))[-limit:]
        return "\n".join("%d  %s" % (e["n"], e["line"]) for e in rows) or "No new lines.", rows

    def t_wait_for_log(self, args: dict[str, Any]) -> Result:
        after = int(args.get("after") or 0)
        want = str(args.get("contains") or "").lower()
        pid = self.pid(args) if args.get("game") not in (None, "") else None
        end = time.monotonic() + max(1, min(control.LONGEST_WAIT, int(args.get("timeout") or 30)))
        while True:
            rows = self.events(after, pid)
            hit = [e for e in rows if not want or want in e["line"].lower()]
            if hit or time.monotonic() >= end:
                break
            with self.w.event_lock:
                self.w.event_lock.wait(min(1.0, max(0.0, end - time.monotonic())))
        if not hit:
            return "Nothing new within the time given.", []
        return "\n".join("%d  %s" % (e["n"], e["line"]) for e in rows[-200:]), rows[-200:]

    def t_list_plans(self, args: dict[str, Any]) -> Result:
        out: list[dict[str, Any]] = []
        for name in plans.names():
            try:
                summary = self.w.item_text(("plan", name)).strip().splitlines()
            except (OSError, ValueError):
                summary = []
            out.append({"type": "plan", "name": name, "script": "\n".join(summary)})
        out += [{"type": "script", "name": n} for n in plans.script_names()]
        return "Plans: %s. Scripts: %s." % (", ".join(plans.names()) or "none",
                                            ", ".join(plans.script_names()) or "none"), out

    def t_read_plan(self, args: dict[str, Any]) -> Result:
        name = self.item(str(args["name"]), "plan")[1]
        p = plans.load(name)
        return plans.to_script(p), p

    def t_read_script(self, args: dict[str, Any]) -> Result:
        name = self.item(str(args["name"]), "script")[1]
        with open(plans.script_path(name), encoding="utf-8") as f:
            text = f.read()
        return text, {"name": name, "text": text}

    def t_script_reference(self, args: dict[str, Any]) -> Result:
        guide = os.path.join(paths.DOCS, "SCRIPTING.md")
        try:
            with open(guide, encoding="utf-8") as f:
                more = f.read()
        except OSError:
            more = ""
        text = "SCRIPT COMMANDS\n%s\n\nTRUSTED PLAYERS' PRIVATE-MESSAGE COMMANDS\n%s\n\nSCRIPT GUIDE\n%s" % (
            script.__doc__ or "", messages.__doc__ or "", more)
        return text, {"commands": list(script.COMMANDS)}

    def t_check_script(self, args: dict[str, Any]) -> Result:
        problem = script.check(str(args.get("text") or ""))
        return problem or "No problems found.", {"ok": problem is None, "problem": problem}

    def t_list_characters(self, args: dict[str, Any]) -> Result:
        rows = [{"profile": k, "character": settings.profile_display(k), "name": settings.profile_name(k),
                 "server": settings.profile_server(k)} for k in settings.profiles()]
        return ", ".join(r["character"] for r in rows) or "No character has settings yet.", rows

    def t_get_character_settings(self, args: dict[str, Any]) -> Result:
        key = self.character(args)
        data = settings.load_profile(key)
        keys = args.get("keys")
        if jsonio.is_array(keys):
            data = {k: data.get(k) for k in keys if isinstance(k, str)}
        out: dict[str, Any] = {"character": settings.profile_display(key), "profile": key, "settings": data}
        if args.get("schema"):
            out["schema"] = settings.Profile.model_json_schema()
            out["defaults"] = settings.PROFILE_DEFAULTS
        return "Settings of %s (%d values)." % (settings.profile_display(key), len(data)), out

    def t_get_app_settings(self, args: dict[str, Any]) -> Result:
        data = dict(self.ui(lambda: dict(self.w.s)))
        keys = args.get("keys")
        if jsonio.is_array(keys):
            data = {k: data.get(k) for k in keys if isinstance(k, str)}
        out: dict[str, Any] = {"settings": data}
        if args.get("schema"):
            out["schema"] = settings.AppSettings.model_json_schema()
            out["defaults"] = settings.APP_DEFAULTS
        return "Uncle Farmer's settings (%d values)." % len(data), out

    def t_list_schedules(self, args: dict[str, Any]) -> Result:
        def read() -> list[dict[str, Any]]:
            now = self.w.now()
            out: list[dict[str, Any]] = []
            for s in self.w.scheduler.items:
                due = schedule.next_due(s, now)
                row = {k: v for k, v in s.items() if k != "history" or args.get("history")}
                row["next"] = schedule.stamp(due) if due else None
                row["when"] = schedule.describe_when(s)
                out.append(row)
            return out
        rows = self.ui(read)
        return "\n".join("%s: %s for %s, %s, %s" % (r["id"], r["item"], r["character"], r["when"],
                                                     "on" if r["enabled"] else "off") for r in rows) \
            or "No schedules.", rows

    def t_results(self, args: dict[str, Any]) -> Result:
        name = settings.profile_name(self.character(args)) or self.character(args)
        period = str(args.get("period") or "run")
        kind = stats.FARMING if (args.get("kind") or "farming") == "farming" else stats.TOOL
        if period not in control.PERIODS:
            raise ToolError("period is one of: %s" % ", ".join(control.PERIODS))
        tally = self.ui(self.w.live_tally, name)
        live: list[dict[str, Any]] = [r for r in tally.results() if r["kind"] == kind] if tally else []
        now = time.time()
        until: float | None = None
        if period == "run":
            if live:
                return self.report(kind, live[-1:], "%s, this run (running)" % name)
            past = stats.runs(name, kind=kind)
            if not past:
                return "%s: no runs yet." % name, []
            return self.report(kind, [r for r in past if r["start"] == past[-1]["start"]], "%s, last run" % name)
        if period in ("today", "yesterday", "day"):
            today = dt.date.fromtimestamp(now).isoformat()
            day = {"today": today, "yesterday": (dt.date.fromtimestamp(now) - dt.timedelta(days=1)).isoformat()}.get(
                period) or str(args.get("day") or "")
            try:
                since, until = stats.day_bounds(day)
            except (ValueError, TypeError) as e:
                raise ToolError("day is YYYY-MM-DD (result_days lists them).") from e
            if day != today:
                live = []
            label = day
        else:
            since = {"week": now - 7 * 86400, "month": now - 30 * 86400, "all": None}[period]
            label = period
        results = stats.runs(name, since, kind=kind, until=until) + live
        if not results:
            return "%s, %s: no runs." % (name, label), []
        return self.report(kind, results, "%s, %s" % (name, label))

    @staticmethod
    def report(kind: str, results: list[dict[str, Any]], title: str) -> Result:
        if kind == stats.FARMING:
            r = stats.add_up(results) if len(results) > 1 else results[-1]
            return stats.report(r, title), r
        return stats.report_tools(results, title), results

    def t_result_days(self, args: dict[str, Any]) -> Result:
        name = settings.profile_name(self.character(args)) or self.character(args)
        days = stats.days(name, kind=None)
        return ", ".join(days) or "No results yet.", days

    def feed(self, pid: int) -> chat.Feed:
        f = self.ui(lambda: self.w.chats.get(pid))
        if f is None or f.unsupported:
            raise ToolError("Chat isn't ready in game %d (a game needs the newer agent: restart it)." % pid)
        return f

    def t_read_chat(self, args: dict[str, Any]) -> Result:
        f = self.feed(self.pid(args))
        channel = str(args.get("channel") or "all").lower()
        limit = max(1, min(500, int(args.get("limit") or 100)))
        if channel == "all":
            rows = list(f.lines)
        elif channel in ("private", "notice"):
            rows = list(f.buffer(chat.PRIVATE if channel == "private" else chat.NOTICE))
        elif channel in CHANNEL_NUMBERS:
            rows = list(f.buffer(str(CHANNEL_NUMBERS[channel])))
        else:
            raise ToolError("channel is all, private, notice or one of: %s" % ", ".join(CHANNEL_NUMBERS))
        rows = rows[-limit:]
        return "\n".join("%s %s: %s" % (chat.channel_name(str(r.get("channel"))), r.get("name"), r.get("text"))
                         for r in rows) or "No chat lines.", rows

    def t_read_conversations(self, args: dict[str, Any]) -> Result:
        rows = self.feed(self.pid(args)).conversations()
        return ", ".join(str(r.get("name")) for r in rows) or "No private conversations.", rows

    def t_get_messages_settings(self, args: dict[str, Any]) -> Result:
        cfg = messages.config()
        data = {"trusted": list(self.w.s.get("pm_trusted", [])), "replies": messages.replies(),
                "goodbyes": messages.goodbyes(), "settings": cfg}
        return "Trusted: %s." % (", ".join(map(str, data["trusted"])) or "nobody"), data

    def t_get_sound_silencer(self, args: dict[str, Any]) -> Result:
        rows = silencer.load()
        return "%d sounds, %d muted." % (len(rows), sum(1 for r in rows if r.get("muted"))), rows

    def t_agent_status(self, args: dict[str, Any]) -> Result:
        folder = self.w.s.get("game_folder", "")
        stale = gameinstall.stale_games()
        data = {"folder": folder, "is_game_folder": gameinstall.is_game_folder(folder),
                "status": gameinstall.status(folder), "games_without_this_agent": [p for p, _v in stale]}
        return "Agent %s in %s; games without this version's agent: %d." % (
            data["status"], folder or "(no folder set)", len(stale)), data

    def t_check_for_updates(self, args: dict[str, Any]) -> Result:
        ch = updater.channel(self.w.s.get("update_channel"))
        try:
            rel = updater.latest(update_channel=ch)
        except updater.UpdateError as e:
            raise ToolError("Couldn't reach GitHub: %s" % e) from e
        mine = updater.installed_version()
        if rel is None:
            return "No release to see on the %s channel. This copy is %s." % (ch, mine), None
        newer = updater.is_newer(rel["version"], mine)
        return ("%s is out (this copy is %s)." % (rel["version"], mine) if newer else
                "%s is the newest; this copy is %s." % (rel["version"], mine)), {
            "newest": rel["version"], "installed": mine, "newer": newer, "notes": rel.get("notes")}

    # ---------------------------------------------------------------------------- doing
    def t_select_game(self, args: dict[str, Any]) -> Result:
        pid = self.pid(args)

        def pick() -> None:
            from .common import select_row
            pids = [g[0] for g in self.w.games]
            select_row(self.w.game_list, pids.index(pid))
            self.w.game_changed()
        self.ui(pick)
        return "Game %d is selected." % pid, None

    def t_start_plan(self, args: dict[str, Any]) -> Result:
        pid = self.pid(args)
        kind = args.get("type") if args.get("type") in ("plan", "script") else None
        if args.get("name"):
            item = self.item(str(args["name"]), kind)
            answer = self.ui(lambda: self.w.start(pid, item, remote=True))
        else:
            answer = self.ui(lambda: self.w.start_bot(pid, None))
        run = self.run_on(pid)
        if run is None:
            raise ToolError(answer or "It didn't start.")
        return answer or "Started.", {"pid": pid, "running": run.title}

    def t_stop(self, args: dict[str, Any]) -> Result:
        pid = self.pid(args)
        if self.run_on(pid) is None:
            return "No bot is running on game %d." % pid, None
        self.ui(self.w.stop, pid)
        return "Stopping game %d's run (it ends the safe way; wait_for_run waits for it)." % pid, None

    def t_stop_all(self, args: dict[str, Any]) -> Result:
        self.ui(self.w.stop_all)
        return "Stopping every bot.", None

    def pause_to(self, args: dict[str, Any], paused: bool) -> Result:
        pid = self.pid(args)
        run = self.run_on(pid)
        if run is None or run.bot is None:
            raise ToolError("No bot is running on game %d." % pid)
        if run.bot.paused.is_set() != paused:
            self.ui(self.w.toggle_pause, pid)
        return ("Paused." if paused else "Going on."), None

    def t_pause(self, args: dict[str, Any]) -> Result:
        return self.pause_to(args, True)

    def t_resume(self, args: dict[str, Any]) -> Result:
        return self.pause_to(args, False)

    def errand(self, pid: int, text: str, title: str, walk: bool) -> None:
        problem = script.check(text)
        if problem:
            raise ToolError(problem)
        self.need_idle(pid)
        answer = self.ui(lambda: self.w.errand_on(pid, text, title, walk=walk))
        if answer:
            raise ToolError(answer)

    def t_run_script(self, args: dict[str, Any]) -> Result:
        pid = self.pid(args)
        text = str(args.get("text") or "")
        if not text.endswith("\n"):
            text += "\n"
        title = str(args.get("title") or "script from another program")
        self.errand(pid, text, title, walk=args.get("mode") == "errand")
        return "Started %s on game %d. read_log or wait_for_run follow it." % (title, pid), {"pid": pid}

    def t_run_tool(self, args: dict[str, Any]) -> Result:
        pid = self.pid(args)
        tool = str(args.get("tool") or "")
        if tool not in control.TOOL_NAMES:
            raise ToolError("tool is one of: %s" % ", ".join(control.TOOL_NAMES))
        check = bool(args.get("check_only"))
        if check and tool not in CHECKABLE:
            raise ToolError("%s has no check_only." % tool)
        if tool in CONFIRMED and not check and args.get("confirm") is not True:
            raise ToolError("%s spends, sells or throws away: it needs confirm=true. Ask the player first." % tool)
        name = self.ui(self.w.character, pid)
        if tool == "dungeon" and not check:
            text = dungeon.script((settings.load_profile(name) if name else {}).get("dungeon") or {})
        else:
            text = tool + (" check" if check else "") + "\n"
        self.errand(pid, text, "%s%s" % (tool.replace("_", " "), " check" if check else ""), walk=False)
        return "Started %s on game %d." % (text.strip().splitlines()[-1], pid), {"pid": pid}

    def t_follow_player(self, args: dict[str, Any]) -> Result:
        pid = self.pid(args)
        answer = self.ui(lambda: self.w.follow_for(pid, str(args["player"])))
        return answer or "Following.", None

    def t_unfollow_player(self, args: dict[str, Any]) -> Result:
        pid = self.pid(args)
        return self.ui(self.w.unfollow, pid) or "Stopped following.", None

    def t_follow_buffs(self, args: dict[str, Any]) -> Result:
        pid = self.pid(args)
        run = self.run_on(pid)
        bot = getattr(run, "bot", None) if run else None
        if not run or not getattr(run, "follows", None) or bot is None:
            raise ToolError("Game %d isn't following anyone (follow_player first)." % pid)
        bot.follow_buffs = bool(args.get("on"))
        return ("Buffs on." if bot.follow_buffs else "Buffs off."), None

    def t_team(self, args: dict[str, Any]) -> Result:
        from ..engine import team
        pid = self.pid(args)
        action = str(args.get("action") or "")
        player = str(args.get("player") or "").strip()
        if action in ("accept", "leader") and not player:
            raise ToolError("%s needs the player's name." % action)
        jobs: dict[str, Callable[[Any], Any]] = {
            "accept": lambda bot: team.accept_application(bot, player),
            "leader": lambda bot: team.make_leader(bot, player),
            "leave": lambda bot: team.leave(bot)}
        if action not in jobs:
            raise ToolError("action is accept, leader or leave.")
        run = self.run_on(pid)
        if run is not None and run.bot is not None:
            done: list[Any] = []
            finished = threading.Event()

            def job(bot: Any) -> None:
                try:
                    done.append(jobs[action](bot))
                finally:
                    finished.set()
            run.bot.requests.put(job)       # the run does it between two of its steps
            if not finished.wait(60):
                return "Asked the run to do it; it hasn't got to it within a minute.", None
            ok, text = done[0] if done else (False, "no answer")
        else:
            m = self.ui(lambda: self.w.messengers.get(pid))
            bot = m.idle_bot() if m is not None else None
            if bot is None:
                raise ToolError("Game %d isn't logged in, or its messages aren't ready yet." % pid)
            ok, text = jobs[action](bot)
        text = text if isinstance(text, str) else "; ".join(map(str, text))
        if not ok:
            raise ToolError(text)
        return text, None

    def t_voice_message(self, args: dict[str, Any]) -> Result:
        pid = self.pid(args)
        f = self.feed(pid)
        why = f.voice_ready()
        if why:
            raise ToolError(why)
        action = str(args.get("action") or "")
        if action == "play":
            why = f.play_voice(str(args.get("voice") or ""))
        elif action == "record":
            why = f.record_voice()
        elif action == "cancel":
            f.cancel_voice()
        elif action == "send":
            if args.get("confirm") is not True:
                raise ToolError("Sending a voice message needs confirm=true. Ask the player first.")
            if args.get("to"):
                to = f.id_of(str(args["to"]))
                if not to:
                    raise ToolError("%s's id isn't known yet: give their id." % args["to"])
                why = f.send_voice(to=to)
            else:
                key = {"team": "4", "gang": "3"}.get(str(args.get("channel") or "").lower())
                if key is None:
                    raise ToolError("Send to channel team or gang, or to a player.")
                why = f.send_voice(channel=key)
        else:
            raise ToolError("action is play, record, send or cancel.")
        if why:
            raise ToolError(why)
        return {"play": "Playing.", "record": "Recording.", "cancel": "Cancelled.",
                "send": "Sent in %d part(s)." % max(1, f.voice_parts)}[action], None

    def t_scan_character(self, args: dict[str, Any]) -> Result:
        pid = self.pid(args)
        self.need_idle(pid)
        name = self.ui(self.w.character, pid)
        if not name:
            raise ToolError("No character is logged in on game %d." % pid)

        def scan() -> None:
            self.w.scanned = getattr(self.w, "scanned", {})
            self.w.scanned.pop(name, None)
            self.w.auto_scan(name, pid)
        self.ui(scan)
        return "Scanned %s." % settings.profile_display(name), None

    def t_wait_for_run(self, args: dict[str, Any]) -> Result:
        pid = self.pid(args)
        start = self.w.event_seq
        end = time.monotonic() + max(1, min(control.LONGEST_WAIT, int(args.get("timeout") or 60)))
        while self.run_on(pid) is not None and time.monotonic() < end:
            time.sleep(0.5)
        ended = self.run_on(pid) is None
        rows = self.events(start, pid)[-30:]
        return ("The run ended." if ended else "Still running."), {"ended": ended, "lines": rows}

    def refresh_items(self, select: tuple[str, str] | None = None) -> None:
        self.ui(self.w.fill_runs, select)

    def t_save_plan(self, args: dict[str, Any]) -> Result:
        p = args.get("plan")
        if not jsonio.is_object(p) or not isinstance(p.get("name"), str) or not p["name"].strip():
            raise ToolError("plan is an object with a name (read_plan shows the format).")
        existing = next((n for n in plans.names() if n.casefold() == p["name"].strip().casefold()), None)
        if existing and not args.get("replace"):
            raise ToolError("A plan called %s exists: replace=true replaces it." % existing)
        try:
            p = plans.upgrade(dict(p, name=existing or p["name"].strip()))
            problem = script.check(plans.to_script(p))
            if problem:
                raise ToolError(problem)
            plans.save(p)
        except (ValidationError, ValueError, KeyError, TypeError) as e:
            raise ToolError("The plan isn't valid: %s" % e) from e
        self.refresh_items(("plan", p["name"]))
        return "Saved plan %s." % p["name"], None

    def t_save_script(self, args: dict[str, Any]) -> Result:
        name = str(args.get("name") or "").strip()
        text = str(args.get("text") or "")
        if not name or paths.safe_name(name) != name:
            raise ToolError("A script's name can't be empty or hold characters a file name can't.")
        existing = next((n for n in plans.script_names() if n.casefold() == name.casefold()), None)
        if existing and not args.get("replace"):
            raise ToolError("A script called %s exists: replace=true replaces it." % existing)
        problem = script.check(text)
        if problem:
            raise ToolError(problem)
        jsonio.save_text(plans.script_path(existing or name), text if text.endswith("\n") else text + "\n")
        self.refresh_items(("script", existing or name))
        return "Saved script %s." % (existing or name), None

    def t_delete_plan(self, args: dict[str, Any]) -> Result:
        kind, name = self.item(str(args["name"]), str(args.get("type")))
        if kind == "plan":
            plans.delete(name)
        else:
            from .. import filelock
            filelock.delete(plans.script_path(name))
        self.refresh_items()
        return "Deleted %s %s." % (kind, name), None

    def t_export_plan(self, args: dict[str, Any]) -> Result:
        name = self.item(str(args["name"]), "plan")[1]
        try:
            plans.export(name, str(args["path"]))
        except (OSError, ValueError) as e:
            raise ToolError("Couldn't export it: %s" % e) from e
        return "Exported %s to %s." % (name, args["path"]), None

    def t_import_plan(self, args: dict[str, Any]) -> Result:
        try:
            p = plans.read_import(str(args["path"]))
        except (OSError, ValueError) as e:
            raise ToolError("Couldn't import it: %s" % e) from e
        existing = next((n for n in plans.names() if n.casefold() == p["name"].casefold()), None)
        if existing and not args.get("replace"):
            raise ToolError("A plan called %s exists: replace=true replaces it." % existing)
        p["name"] = existing or p["name"]
        plans.save(p)
        self.refresh_items(("plan", p["name"]))
        return "Imported plan %s." % p["name"], None

    def t_set_character_settings(self, args: dict[str, Any]) -> Result:
        values = args.get("values")
        if not jsonio.is_object(values) or not values:
            raise ToolError("values maps setting names to new values.")
        key = self.character(args)
        current = settings.load_profile(key)
        unknown = [k for k in values if k not in settings.PROFILE_DEFAULTS and k not in current]
        if unknown:
            raise ToolError("No such character settings: %s (get_character_settings with schema=true lists them)."
                            % ", ".join(unknown))
        merged = {**current, **values}
        try:
            settings.Profile.model_validate(merged)
        except ValidationError as e:
            raise ToolError("Not saved: %s" % e) from e
        settings.save_profile(key, merged)
        return "Saved %d settings of %s. A run going reads them when it next starts." % (
            len(values), settings.profile_display(key)), None

    def t_set_app_settings(self, args: dict[str, Any]) -> Result:
        values = args.get("values")
        if not jsonio.is_object(values) or not values:
            raise ToolError("values maps setting names to new values.")
        banned = [k for k in values if k in OFF_LIMITS]
        if banned:
            raise ToolError("Only the player can change %s, in Uncle Farmer's Settings." % ", ".join(banned))

        def apply() -> str:
            unknown = [k for k in values if k not in settings.APP_DEFAULTS and k not in self.w.s]
            if unknown:
                raise ToolError("No such settings: %s." % ", ".join(unknown))
            merged = {**self.w.s, **values}
            try:
                settings.AppSettings.model_validate(merged)
            except ValidationError as e:
                raise ToolError("Not saved: %s" % e) from e
            old_lang = self.w.s.get("language")
            self.w.s.update(values)
            settings.save_app(self.w.s)
            return " Restart Uncle Farmer for the new language." if self.w.s.get("language") != old_lang else ""
        more = self.ui(apply)
        return "Saved %d settings.%s" % (len(values), more), None

    def t_export_character_settings(self, args: dict[str, Any]) -> Result:
        key = self.character(args)
        try:
            settings.export_profile(key, str(args["path"]))
        except (OSError, ValueError) as e:
            raise ToolError("Couldn't export them: %s" % e) from e
        return "Exported %s's settings to %s." % (settings.profile_display(key), args["path"]), None

    def t_import_character_settings(self, args: dict[str, Any]) -> Result:
        key = self.character(args)
        try:
            _source, imported = settings.read_profile_export(str(args["path"]))
            settings.import_profile(key, imported)
        except (OSError, ValueError) as e:
            raise ToolError("Couldn't import them: %s" % e) from e
        return "Imported the settings into %s. Scan it before farming if its skills or keys changed." % (
            settings.profile_display(key)), None

    def schedule_fields(self, raw: dict[str, Any], base: dict[str, Any] | None = None) -> dict[str, Any]:
        out = dict(base or {})
        if raw.get("character"):
            out["character"] = settings.profile_name(self.character({"character": raw["character"]}))
        if raw.get("name"):
            out["item"] = "%s:%s" % self.item(str(raw["name"]), raw.get("type") if raw.get("type") in
                                                ("plan", "script") else None)
        for k in ("repeat", "time", "date", "days", "enabled"):
            if k in raw:
                out[k] = raw[k]
        out.setdefault("enabled", True)
        return out

    def t_add_schedule(self, args: dict[str, Any]) -> Result:
        fields = self.schedule_fields(args)

        def add() -> dict[str, Any]:
            return self.w.scheduler.add(fields, self.w.now())
        try:
            s = self.ui(add)
        except ValueError as e:
            raise ToolError(str(e)) from e
        return "Added schedule %s: %s." % (s["id"], schedule.describe_when(s)), s

    def t_update_schedule(self, args: dict[str, Any]) -> Result:
        sid = str(args["id"])
        given = args.get("fields")
        raw: dict[str, Any] = given if jsonio.is_object(given) else {}
        s0 = self.ui(self.w.scheduler.get, sid)
        if s0 is None:
            raise ToolError("No schedule has id %s." % sid)
        fields = self.schedule_fields(raw, {k: v for k, v in s0.items() if k not in ("id", "history", "handled")})
        try:
            s = self.ui(lambda: self.w.scheduler.update(sid, fields, self.w.now()))
        except ValueError as e:
            raise ToolError(str(e)) from e
        return "Changed schedule %s." % sid, s

    def t_set_schedule_enabled(self, args: dict[str, Any]) -> Result:
        sid = str(args["id"])
        if self.ui(self.w.scheduler.get, sid) is None:
            raise ToolError("No schedule has id %s." % sid)
        self.ui(lambda: self.w.scheduler.set_enabled(sid, bool(args["enabled"]), self.w.now()))
        return "Schedule %s is %s." % (sid, "on" if args["enabled"] else "off"), None

    def t_delete_schedule(self, args: dict[str, Any]) -> Result:
        sid = str(args["id"])
        if self.ui(self.w.scheduler.get, sid) is None:
            raise ToolError("No schedule has id %s." % sid)
        self.ui(self.w.scheduler.remove, sid)
        return "Deleted schedule %s." % sid, None

    def t_send_chat(self, args: dict[str, Any]) -> Result:
        channel = str(args.get("channel") or "").lower()
        if channel not in CHANNEL_NUMBERS:
            raise ToolError("channel is one of: %s" % ", ".join(CHANNEL_NUMBERS))
        why = self.feed(self.pid(args)).say(CHANNEL_NUMBERS[channel], str(args["text"]))
        if why:
            raise ToolError(why)
        return "Sent.", None

    def t_send_private_message(self, args: dict[str, Any]) -> Result:
        pid = self.pid(args)
        f = self.feed(pid)
        who = str(args["to"]).strip()
        to = f.id_of(who)
        if not to:
            raise ToolError("The game hasn't shown %s yet, so their id isn't known: give their id instead." % who)
        m = self.ui(lambda: self.w.messengers.get(pid))
        if m is None or not m.ready:
            raise ToolError("Private messages aren't ready in this game yet.")
        m.send(to, who, str(args["text"]), first=True)
        return "Sent to %s." % who, None

    def t_set_messages_settings(self, args: dict[str, Any]) -> Result:
        values: dict[str, Any] = dict(args.get("values") or {}) if jsonio.is_object(args.get("values")) else {}
        bad = [k for k in values if k not in messages.DEFAULTS]
        if bad:
            raise ToolError("Not private-message settings: %s." % ", ".join(bad))
        if jsonio.is_array(args.get("trusted")):
            values["pm_trusted"] = [str(x).strip() for x in args["trusted"] if str(x).strip()]
        if values:
            def apply() -> None:            # the pm_ settings live in settings.json beside the others
                self.w.s.update(values)
                settings.save_app(self.w.s)
            self.ui(apply)
        for key, path in (("replies", messages.REPLIES_FILE), ("goodbyes", messages.GOODBYES_FILE)):
            if jsonio.is_array(args.get(key)):
                messages.save_lines(path, [str(x) for x in args[key]])
        return "Saved.", None

    def t_forget_answered(self, args: dict[str, Any]) -> Result:
        self.ui(self.w.forget_answered)
        return "Everyone can get replies again.", None

    def t_set_game_speech(self, args: dict[str, Any]) -> Result:
        talk = bool(args.get("talk"))
        if args.get("every"):
            self.ui(self.w.set_game_speech, talk, True)
            return ("Every game talks." if talk else "Every game is muted."), None
        pid = self.pid(args)
        try:
            with AgentLink(pid=pid, timeout=3) as a:
                now = a.send("speech " + ("on" if talk else "off"))
        except (AgentError, OSError) as e:
            raise ToolError("The game didn't answer: %s" % e) from e
        return "Game %d's speech is %s." % (pid, now), None

    def t_speak_results(self, args: dict[str, Any]) -> Result:
        name = settings.profile_name(self.character(args))
        text, _data = self.t_results({**args, "period": "run"})
        line = text.splitlines()[0] if text else name
        self.ui(speech.speak, line)
        return "Spoke: %s" % line, None

    def t_set_sound_silencer(self, args: dict[str, Any]) -> Result:
        try:
            rows = silencer.validate(args.get("rows"))
        except ValueError as e:
            raise ToolError(str(e)) from e
        app = settings.load_app()
        app[silencer.KEY] = rows
        settings.save_app(app)
        self.ui(lambda: self.w.s.__setitem__(silencer.KEY, rows))
        applied, failed = 0, 0
        for pid, _n, _w in self.games():
            try:
                with AgentLink(pid=pid, timeout=5) as a:
                    silencer.apply_saved(a)
                    applied += 1
            except (AgentError, OSError, ValueError):
                failed += 1
        return "Saved %d sounds; muting applied in %d games%s." % (
            len(rows), applied, ", not confirmed in %d" % failed if failed else ""), None

    def t_open_game_window(self, args: dict[str, Any]) -> Result:
        folder = self.w.s.get("game_folder", "")
        if not gameinstall.is_game_folder(folder) or gameinstall.status(folder) != "installed":
            raise ToolError("The agent isn't installed in the game yet (install_agent).")
        import subprocess
        subprocess.Popen([os.path.join(folder, "mw.exe")], cwd=folder, close_fds=True,
                         creationflags=getattr(subprocess, "DETACHED_PROCESS", 0x8))
        self.ui(lambda: wx.CallLater(8000, self.w.refresh_games))
        return "Opening another game window. The player logs in; list_games(refresh=true) sees it.", None

    def t_close_game(self, args: dict[str, Any]) -> Result:
        pid = self.pid(args)
        if self.run_on(pid) is not None:
            self.ui(self.w.stop, pid)
            end = time.monotonic() + 60
            while self.run_on(pid) is not None and time.monotonic() < end:
                time.sleep(0.5)
        left = gameinstall.close_games([pid])
        return ("Game %d is closed." % pid) if not left else "Game %d didn't close." % pid, None

    def t_install_agent(self, args: dict[str, Any]) -> Result:
        folder = str(args.get("folder") or self.w.s.get("game_folder", ""))
        if not gameinstall.is_game_folder(folder):
            raise ToolError("%s isn't a Mist World folder (the one with mw.exe)." % (folder or "No folder"))
        if self.ui(lambda: bool(self.w.runs)):
            raise ToolError("Stop every running bot first.")
        games = agentfix.running_pids()
        left = gameinstall.close_games(games) if games else []
        if left:
            raise ToolError("Mist World windows that didn't close: %d." % len(left))
        try:
            gameinstall.install(folder)
        except OSError as e:
            raise ToolError("Couldn't change the game's settings: %s" % e) from e

        def remember() -> None:
            if self.w.s.get("game_folder") != folder:
                self.w.s["game_folder"] = folder
                settings.save_app(self.w.s)
        self.ui(remember)
        return "The agent is installed. Start Mist World again: it loads the agent as it starts.", None

    def t_remove_agent(self, args: dict[str, Any]) -> Result:
        folder = str(args.get("folder") or self.w.s.get("game_folder", ""))
        if not gameinstall.is_game_folder(folder):
            raise ToolError("%s isn't a Mist World folder." % (folder or "No folder"))
        try:
            gameinstall.uninstall(folder)
        except OSError as e:
            raise ToolError("Couldn't change the game's settings: %s" % e) from e
        return "The agent is removed from the game's settings.", None

    def t_install_update(self, args: dict[str, Any]) -> Result:
        if not updater.frozen():
            raise ToolError("This copy runs from source: it updates with git pull.")
        if self.ui(lambda: bool(self.w.runs)):
            raise ToolError("Stop every running bot first.")
        try:
            rel = updater.latest(update_channel=updater.channel(self.w.s.get("update_channel")))
        except updater.UpdateError as e:
            raise ToolError("Couldn't reach GitHub: %s" % e) from e
        if rel is None or not updater.is_newer(rel["version"], updater.installed_version()):
            return "There is no newer version.", None
        games = agentfix.running_pids()
        if games and gameinstall.close_games(games):
            raise ToolError("Some Mist World windows didn't close.")
        self.ui(self.w._download_update, rel)     # pyright: ignore[reportPrivateUsage]
        return "Downloading %s; Uncle Farmer closes and starts again as it." % rel["version"], None

    def t_clear_log(self, args: dict[str, Any]) -> Result:
        def clear() -> None:
            self.w.log_lines.clear()
            self.w.log_box.Clear()
        self.ui(clear)
        return "The log is empty.", None

    def t_quit(self, args: dict[str, Any]) -> Result:
        def close_when_stopped(tries: int = 0) -> None:
            if self.w.destroyed:
                return
            if self.w.runs and tries < 240:          # a run can take a while to end safely
                wx.CallLater(500, close_when_stopped, tries + 1)
                return
            self.w.close_reason = "another program asked (control)"
            if not self.w.runs:
                self.w.Close()

        def close() -> None:
            for run in list(self.w.runs.values()):
                run.stop()
            close_when_stopped()
        self.ui(close)
        return "Uncle Farmer is stopping its bots and closing.", None

    def t_agent_command(self, args: dict[str, Any]) -> Result:
        if not self.w.s.get("mcp_raw_agent"):
            raise ToolError("Raw agent commands are off. The player can allow them in Uncle Farmer: File, Settings, "
                            "Control, \"Also let them send raw commands to the game agent\".")
        pid = self.pid(args)
        line = str(args.get("command") or "").strip()
        if not line or "\n" in line:
            raise ToolError("command is one line.")
        if line.split()[0].lower() == "auth":
            raise ToolError("The connection is already authenticated.")
        try:
            with AgentLink(pid=pid, timeout=15) as a:
                if line.split()[0].lower() in ("key", "keydown", "type", "typeenter", "slot", "use", "select"):
                    a.send("arm")
                answer = a.send(line)
        except (AgentError, OSError) as e:
            raise ToolError("The game didn't answer: %s" % e) from e
        data: Any = answer
        try:
            data = jsonio.loads(answer)
        except (ValueError, AttributeError):
            pass
        return answer[:4000], data
