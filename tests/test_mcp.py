"""Control by other programs: the MCP server (mcpserver.py) over the named pipe (control.py) to the
open window's end (gui/remote.py), with a pretend game behind it (simgame.py)."""

from __future__ import annotations

import collections
import io
import json
import os
import secrets
import threading
import time
from collections.abc import Callable, Generator
from pathlib import Path
from typing import Any

import pytest

from unclefarmer import control, mcpserver, settings

pytest.importorskip("wx")
from unclefarmer.gui import remote  # noqa: E402


class Window:
    """What RemoteControl reads of the main window, without a window."""

    def __init__(self, pid: int | None = None, character: str | None = None) -> None:
        self.s: dict[str, Any] = settings.load_app()
        self.games: list[tuple[int, str | None, str | None]] = [(pid, character, "Here")] if pid else []
        self.runs: dict[int, Any] = {}
        self.destroyed = False
        self.events: collections.deque[dict[str, Any]] = collections.deque(maxlen=100)
        self.event_lock = threading.Condition()
        self.event_seq = 0
        self.last_line: dict[int, str] = {}
        self.errands: list[tuple[int, str, str, bool]] = []
        self.listed: list[Any] = []

    def is_paused(self, pid: int) -> bool:
        return False

    def character(self, pid: int) -> str | None:
        return next((g[1] for g in self.games if g[0] == pid), None)

    def item_text(self, item: tuple[str, str]) -> str:
        return "farm\n"

    def fill_runs(self, select: Any = None) -> None:
        self.listed.append(select)

    def errand_on(self, pid: int, text: str, title: str, walk: bool = False) -> str | None:
        self.errands.append((pid, text, title, walk))
        return None

    def add_line(self, line: str, speak: bool = False, pid: int | None = None) -> None:
        with self.event_lock:
            self.event_seq += 1
            self.events.append({"n": self.event_seq, "time": time.time(), "line": line, "spoken": speak, "pid": pid})
            self.event_lock.notify_all()


@pytest.fixture
def piped(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[Callable[[Window], mcpserver.Bridge], None, None]:
    """A RemoteControl listening on a pipe of the test's own, and the MCP server's end of it."""
    monkeypatch.setenv("UNCLEFARMER_CONTROL_PIPE", r"\\.\pipe\UncleFarmer-test-%s" % secrets.token_hex(6))
    monkeypatch.setenv("UNCLEFARMER_CONTROL_NO_START", "1")
    monkeypatch.setattr(control, "SECRET_FILE", str(tmp_path / "control.key"))
    def direct(self: remote.RemoteControl, fn: Callable[..., Any], *args: Any) -> Any:
        return fn(*args)                 # no window thread here
    monkeypatch.setattr(remote.RemoteControl, "ui", direct)
    started: list[remote.RemoteControl] = []
    bridges: list[mcpserver.Bridge] = []

    def make(w: Window) -> mcpserver.Bridge:
        rc = remote.RemoteControl(w)  # pyright: ignore[reportArgumentType]
        rc.start()
        started.append(rc)
        end = time.monotonic() + 5
        while rc.listener is None and time.monotonic() < end:
            time.sleep(0.05)
        b = mcpserver.Bridge()
        bridges.append(b)
        return b
    yield make
    for b in bridges:
        b.close()
    for rc in started:
        rc.stop()


# ---------------------------------------------------------------------------- the tool table
def test_every_tool_has_its_handler_and_a_clean_schema() -> None:
    for t in control.TOOLS:
        assert callable(getattr(remote.RemoteControl, "t_" + t.name, None)), t.name
        schema = t.schema()
        assert schema["type"] == "object"
        assert set(t.required) <= set(schema["properties"]), t.name
        if t.kind == control.RISKY and "confirm" in t.properties and t.name not in ("run_tool", "voice_message"):
            assert "confirm" in t.required, t.name
    assert len({t.name for t in control.TOOLS}) == len(control.TOOLS)


def test_the_setup_prompt_carries_the_path_and_the_claude_code_command() -> None:
    text = control.setup_prompt(r"C:\Bots\Mist Bot\UncleFarmer.exe")
    assert 'claude mcp add uncle-farmer -- "C:\\Bots\\Mist Bot\\UncleFarmer.exe" --mcp' in text
    assert '"args": [\n        "--mcp"\n      ]' in text


# ---------------------------------------------------------------------------- the stdio server
class FakeBridge(mcpserver.Bridge):
    def __init__(self) -> None:
        super().__init__()
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def call(self, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        self.calls.append((tool, args))
        return {"ok": tool != "stop", "text": "said %s" % tool, "data": {"n": 1}}


def talk(*messages: Any, bridge: mcpserver.Bridge | None = None) -> list[Any]:
    inp = io.BytesIO(b"".join(json.dumps(m).encode() + b"\n" for m in messages))
    out = io.BytesIO()
    mcpserver.serve(inp, out, bridge or FakeBridge())
    return [json.loads(line) for line in out.getvalue().splitlines()]


def test_initialize_lists_and_calls_tools_over_stdio() -> None:
    b = FakeBridge()
    got = talk({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-03-26"}},
               {"jsonrpc": "2.0", "method": "notifications/initialized"},
               {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
               {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "status", "arguments": {}}},
               {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "stop", "arguments": {"game": 7}}},
               {"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "nope"}},
               {"jsonrpc": "2.0", "id": 6, "method": "nonsense"}, bridge=b)
    assert [r["id"] for r in got] == [1, 2, 3, 4, 5, 6]          # the notification got no answer
    assert got[0]["result"]["protocolVersion"] == "2025-03-26"
    assert got[0]["result"]["serverInfo"]["name"] == "uncle-farmer"
    names = [t["name"] for t in got[1]["result"]["tools"]]
    assert names == [t.name for t in control.TOOLS]
    risky = next(t for t in got[1]["result"]["tools"] if t["name"] == "delete_plan")
    assert risky["annotations"]["destructiveHint"] is True
    assert got[2]["result"]["isError"] is False and got[2]["result"]["content"][0]["text"] == "said status"
    assert got[3]["result"]["isError"] is True
    assert got[4]["error"]["code"] == -32602 and got[5]["error"]["code"] == -32601
    assert b.calls == [("status", {}), ("stop", {"game": 7})]


def test_an_unknown_protocol_version_gets_the_newest_and_bad_json_an_error() -> None:
    got = talk({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "1999-01-01"}})
    assert got[0]["result"]["protocolVersion"] == mcpserver.VERSIONS[0]
    out = io.BytesIO()
    mcpserver.serve(io.BytesIO(b"{not json\n"), out, FakeBridge())
    assert json.loads(out.getvalue())["error"]["code"] == -32700


# ---------------------------------------------------------------------------- over the pipe
def test_nothing_is_done_while_the_player_hasnt_allowed_it(piped: Callable[[Window], mcpserver.Bridge]) -> None:
    w = Window()
    b = piped(w)
    answer = b.call("status", {})
    assert answer["ok"] is False and "doesn't allow control" in answer["text"]
    w.s["mcp_control"] = True                           # the player ticks it: the next call works
    assert b.call("status", {})["ok"] is True


def test_a_program_without_the_secret_is_turned_away(piped: Callable[[Window], mcpserver.Bridge],
                                                     tmp_path: Path) -> None:
    w = Window()
    w.s["mcp_control"] = True
    piped(w)
    (tmp_path / "control.key").write_text("not-the-secret", encoding="ascii")
    answer = mcpserver.Bridge().call("status", {})
    assert answer["ok"] is False and "isn't answering" in answer["text"]


def test_no_server_open_says_so_without_starting_anything(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("UNCLEFARMER_CONTROL_PIPE", r"\\.\pipe\UncleFarmer-test-none-%s" % secrets.token_hex(6))
    monkeypatch.setenv("UNCLEFARMER_CONTROL_NO_START", "1")
    monkeypatch.setattr(control, "SECRET_FILE", str(tmp_path / "missing.key"))
    answer = mcpserver.Bridge().call("status", {})
    assert answer["ok"] is False and "isn't answering" in answer["text"]


def test_risky_tools_need_confirm_and_the_control_switches_stay_the_players(
        piped: Callable[[Window], mcpserver.Bridge]) -> None:
    w = Window(pid=os.getpid(), character="Simchar")
    w.s["mcp_control"] = True
    b = piped(w)
    no = b.call("delete_plan", {"name": "x", "type": "plan"})
    assert no["ok"] is False and "confirm=true" in no["text"]
    no = b.call("run_tool", {"tool": "sell_shards"})
    assert no["ok"] is False and "confirm=true" in no["text"]
    assert w.errands == []
    yes = b.call("run_tool", {"tool": "sell_shards", "confirm": True})
    assert yes["ok"] is True and w.errands == [(os.getpid(), "sell_shards\n", "sell shards", False)]
    look = b.call("run_tool", {"tool": "gem_maker", "check_only": True, "game": "Simchar"})
    assert look["ok"] is True and w.errands[-1][1] == "gem_maker check\n"
    no = b.call("set_app_settings", {"values": {"mcp_raw_agent": True}})
    assert no["ok"] is False and "Only the player" in no["text"] and not w.s.get("mcp_raw_agent")


def test_scripts_are_checked_saved_and_run(piped: Callable[[Window], mcpserver.Bridge]) -> None:
    w = Window(pid=os.getpid(), character="Simchar")
    w.s["mcp_control"] = True
    b = piped(w)
    bad = b.call("check_script", {"text": "frobnicate\n"})
    assert bad["ok"] is True and bad["data"]["ok"] is False
    assert b.call("save_script", {"name": "bad", "text": "frobnicate\n"})["ok"] is False
    assert b.call("save_script", {"name": "Wait a bit", "text": "wait 1"})["ok"] is True
    again = b.call("save_script", {"name": "wait a bit", "text": "wait 2"})
    assert again["ok"] is False and "replace=true" in again["text"]
    assert b.call("read_script", {"name": "wait a bit"})["data"]["text"] == "wait 1\n"
    assert b.call("run_script", {"text": "wait 1", "mode": "errand"})["ok"] is True
    assert w.errands[-1] == (os.getpid(), "wait 1\n", "script from another program", True)
    gone = b.call("delete_plan", {"name": "Wait a bit", "type": "script", "confirm": True})
    assert gone["ok"] is True and b.call("read_script", {"name": "Wait a bit"})["ok"] is False


def test_character_settings_are_checked_before_saving(piped: Callable[[Window], mcpserver.Bridge]) -> None:
    w = Window(pid=os.getpid(), character="Simchar")
    w.s["mcp_control"] = True
    settings.save_profile("Simchar", settings.load_profile("Simchar"))
    b = piped(w)
    got = b.call("get_character_settings", {"keys": ["attack_gap"], "schema": True})
    assert got["ok"] is True and "attack_gap" in got["data"]["settings"] and "properties" in got["data"]["schema"]
    wrong = b.call("set_character_settings", {"values": {"attack_gap": "fast"}})
    assert wrong["ok"] is False and "Not saved" in wrong["text"]
    unknown = b.call("set_character_settings", {"values": {"no_such_thing": 1}})
    assert unknown["ok"] is False
    assert b.call("set_character_settings", {"values": {"attack_gap": 0.5}})["ok"] is True
    assert settings.load_profile("Simchar")["attack_gap"] == 0.5


def test_the_log_is_read_by_number_and_waited_for(piped: Callable[[Window], mcpserver.Bridge]) -> None:
    w = Window()
    w.s["mcp_control"] = True
    b = piped(w)
    w.add_line("12:00:00  Walking to the farm")
    w.add_line("12:00:05  Killed a wolf", speak=True)
    got = b.call("read_log", {})
    assert [e["n"] for e in got["data"]] == [1, 2]
    assert [e["line"] for e in b.call("read_log", {"important_only": True})["data"]] == ["12:00:05  Killed a wolf"]
    threading.Timer(0.3, w.add_line, ("12:00:09  Bag full",)).start()
    waited = b.call("wait_for_log", {"after": 2, "contains": "bag", "timeout": 5})
    assert waited["ok"] is True and waited["data"][-1]["line"] == "12:00:09  Bag full"
    quiet = b.call("wait_for_log", {"after": 3, "timeout": 1})
    assert quiet["data"] == []


def test_several_games_need_one_named(piped: Callable[[Window], mcpserver.Bridge]) -> None:
    w = Window()
    w.games = [(11, "Ann", "A"), (12, settings.character_profile("Bob", 99, "S2"), "B")]
    w.s["mcp_control"] = True
    b = piped(w)
    no = b.call("run_tool", {"tool": "survey"})
    assert no["ok"] is False and "Several games" in no["text"]
    assert b.call("run_tool", {"tool": "survey", "game": "bob - s2"})["ok"] is True
    assert w.errands[-1][0] == 12
    assert b.call("run_tool", {"tool": "survey", "game": 11})["ok"] is True and w.errands[-1][0] == 11


# ---------------------------------------------------------------------------- with a pretend game
def test_game_state_and_raw_agent_commands_read_the_game(piped: Callable[[Window], mcpserver.Bridge],
                                                         sim_env: Callable[..., Any]) -> None:
    sim_env()
    w = Window(pid=os.getpid(), character="Simchar")
    w.s["mcp_control"] = True
    b = piped(w)
    state = b.call("game_state", {})
    assert state["ok"] is True, state["text"]
    assert state["data"]["character"] == "Simchar" and state["data"]["map"]
    raw = b.call("game_state", {"part": "self"})
    assert raw["ok"] is True and raw["data"]
    off = b.call("agent_command", {"command": "mem self", "confirm": True})
    assert off["ok"] is False and "Raw agent commands are off" in off["text"]
    w.s["mcp_raw_agent"] = True
    on = b.call("agent_command", {"command": "ping", "confirm": True})
    assert on["ok"] is True


class FullWindow(Window):
    """Window with what the rest of the tools read: schedules, results, chat and runs."""

    def __init__(self, pid: int, character: str, schedules: str) -> None:
        super().__init__(pid, character)
        from unclefarmer import schedule
        self.scheduler = schedule.Scheduler(schedules)
        self.chats: dict[int, Any] = {}
        self.messengers: dict[int, Any] = {}
        self.started: list[Any] = []
        self.stopped: list[Any] = []

    @staticmethod
    def now() -> Any:
        import datetime as dt
        return dt.datetime.now()

    def live_tally(self, character: str) -> None:
        return None

    def refresh_games(self) -> None:
        pass

    def start(self, pid: int, item: Any = None, remote: bool = False) -> str:
        self.started.append((pid, item))
        return "Starting %s." % (item[1] if item else "?")

    def start_bot(self, pid: int, plan: str | None) -> str:
        return "Which plan? Send: start <plan name>"

    def stop(self, pid: int) -> None:
        self.stopped.append(pid)

    def stop_all(self) -> None:
        self.stopped.append("all")

    def forget_answered(self) -> None:
        pass

    def follow_for(self, pid: int, leader: str, tell: Any = None) -> str:
        return "Following you."

    def unfollow(self, pid: int) -> str:
        return "I'm not following anyone."

    def toggle_pause(self, pid: int | None = None) -> None:
        pass

    def set_game_speech(self, talk: bool, every: bool = False) -> None:
        pass


def test_every_tool_answers_without_crashing(piped: Callable[[Window], mcpserver.Bridge],
                                             sim_env: Callable[..., Any], tmp_path: Path) -> None:
    """Each tool once, against the pretend game: an answer every time (done, or why not), never a
    crash that ends the connection."""
    sim_env()
    me = os.getpid()
    w = FullWindow(me, "Simchar", str(tmp_path / "schedules.json"))
    w.s["mcp_control"] = True
    settings.save_profile("Simchar", settings.load_profile("Simchar"))
    b = piped(w)
    assert b.call("save_script", {"name": "Hold", "text": "wait 1"})["ok"] is True
    plan = {"name": "Wolves", "spots": [{"map": 1503, "minutes": 30}], "end": {"how": "start"}}
    saved = b.call("save_plan", {"plan": plan})
    assert saved["ok"] is True, saved["text"]
    added = b.call("add_schedule", {"character": "Simchar", "name": "Hold", "repeat": "daily", "time": "05:30"})
    assert added["ok"] is True, added["text"]
    sid = added["data"]["id"]
    export = str(tmp_path / "wolves.unclefarmer-plan.json")
    calls: list[tuple[str, dict[str, Any]]] = [
        ("status", {}), ("list_games", {"refresh": True}), ("game_state", {}), ("game_state", {"part": "bag"}),
        ("read_log", {}), ("wait_for_log", {"after": 0, "timeout": 1}), ("list_plans", {}),
        ("read_plan", {"name": "wolves"}), ("read_script", {"name": "hold"}), ("script_reference", {}),
        ("check_script", {"text": "wait 1"}), ("list_characters", {}), ("get_character_settings", {}),
        ("get_app_settings", {"schema": True}), ("list_schedules", {"history": True}),
        ("results", {"period": "today"}), ("results", {"period": "run", "kind": "tools"}),
        ("results", {"period": "day", "day": "2026-01-01"}), ("results", {"period": "all"}), ("result_days", {}),
        ("read_chat", {}), ("read_conversations", {}), ("get_messages_settings", {}), ("get_sound_silencer", {}),
        ("agent_status", {}),
        ("start_plan", {"name": "Wolves"}), ("start_plan", {}), ("stop", {}), ("stop_all", {}),
        ("pause", {}), ("resume", {}), ("run_tool", {"tool": "dungeon", "confirm": True}),
        ("run_tool", {"tool": "survey"}), ("follow_player", {"player": "Kim"}), ("unfollow_player", {}),
        ("follow_buffs", {"on": True}), ("team", {"action": "leave"}), ("voice_message", {"action": "record"}),
        ("wait_for_run", {"timeout": 1}), ("export_plan", {"name": "Wolves", "path": export}),
        ("import_plan", {"path": export, "replace": True}), ("set_app_settings", {"values": {"speak": False}}),
        ("set_app_settings", {"values": {"speak": "loud"}}),
        ("export_character_settings", {"path": str(tmp_path / "me.json")}),
        ("import_character_settings", {"path": str(tmp_path / "me.json"), "confirm": True}),
        ("update_schedule", {"id": sid, "fields": {"time": "06:00"}}),
        ("set_schedule_enabled", {"id": sid, "enabled": False}),
        ("send_chat", {"channel": "team", "text": "hi", "confirm": True}),
        ("send_private_message", {"to": "Kim", "text": "hi", "confirm": True}),
        ("set_messages_settings", {"trusted": ["Kim"], "replies": ["Away"], "values": {"pm_away_note": False}}),
        ("forget_answered", {}), ("set_game_speech", {"talk": False}), ("set_sound_silencer", {"rows": []}),
        ("open_game_window", {}), ("remove_agent", {"folder": str(tmp_path), "confirm": True}),
        ("install_agent", {"folder": str(tmp_path), "confirm": True}),
        ("delete_schedule", {"id": sid, "confirm": True}), ("delete_plan", {"name": "Wolves", "type": "plan",
                                                                            "confirm": True}),
    ]
    for name, args in calls:
        answer = b.call(name, args)
        assert "Lost the connection" not in answer["text"] and " failed: " not in answer["text"], (name, answer)
    assert w.started and w.stopped
    assert settings.load_app()["pm_trusted"] == ["Kim"]
    assert b.call("list_schedules", {})["data"] == []
