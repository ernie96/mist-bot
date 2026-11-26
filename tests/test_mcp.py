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

from unclefarmer import chat, control, mcpserver, settings
from unclefarmer.clock import CLOCK
from unclefarmer.engine import logout

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
        self.expected = []
        self.listed: list[Any] = []

    clock = CLOCK
    waiting: Any = None                  # the bot logged out for a while, if any

    def is_paused(self, pid: int) -> bool:
        return False

    def waiting_bot(self, pid: int | None) -> Any:
        return self.waiting

    def sync_pause(self) -> None:
        pass

    def character(self, pid: int) -> str | None:
        return next((g[1] for g in self.games if g[0] == pid), None)

    def item_text(self, item: tuple[str, str]) -> str:
        return "farm\n"

    def fill_runs(self, select: Any = None) -> None:
        self.listed.append(select)

    def errand_on(self, pid: int, text: str, title: str, walk: bool = False,
                  expect: str | None = None) -> str | None:
        self.errands.append((pid, text, title, walk))
        self.expected.append(expect)
        return None

    expected: list[str | None]

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
        if t.kind == control.RISKY and "confirm" in t.properties and t.name not in ("run_tool", "voice_message", "market"):
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
    assert state["data"]["character"] == "Simchar" and state["data"]["map"] and "xp_needed" in state["data"]
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

    def start(self, pid: int, item: Any = None, remote: bool = False, profile: str | None = None) -> str:
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


def test_run_tool_starts_only_for_the_character_whose_settings_it_read(
        piped: Callable[[Window], mcpserver.Bridge]) -> None:
    w = Window(pid=os.getpid(), character="Simchar")
    w.s["mcp_control"] = True
    b = piped(w)
    assert b.call("run_tool", {"tool": "survey"})["ok"] is True
    assert w.expected[-1] == "Simchar"


def test_results_are_read_by_the_characters_settings_key(piped: Callable[[Window], mcpserver.Bridge],
                                                        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Upstream keeps results per settings key (Bob--S2--99.jsonl), so two Bobs never share a file."""
    from unclefarmer import stats
    key = settings.character_profile("Bob", 99, "S2")
    w = FullWindow(12, key, str(tmp_path / "schedules.json"))
    w.s["mcp_control"] = True
    asked: list[str] = []
    def runs(who: str, *_a: Any, **_k: Any) -> list[dict[str, Any]]:
        asked.append(who)
        return []
    monkeypatch.setattr(stats, "runs", runs)
    b = piped(w)
    got = b.call("results", {"period": "all"})
    assert got["ok"] is True and asked == [key]
    assert settings.profile_display(key) in got["text"]
    b.call("result_days", {})
    assert asked[-1] == key


def test_copy_character_settings_copies_the_parts_asked_for(piped: Callable[[Window], mcpserver.Bridge]) -> None:
    w = Window(pid=os.getpid(), character="Simchar")
    w.s["mcp_control"] = True
    mine = settings.load_profile("Simchar")
    settings.save_profile("Simchar", dict(mine, attack_gap=0.4, bag_rules={"Wolf Fang": {"action": "sell", "keep": 0}}))
    theirs = settings.load_profile("Other")
    settings.save_profile("Other", dict(theirs, attack_gap=0.9, team_heal=True,
                                        bag_rules={"Bear Claw": {"action": "throw", "keep": 0}}))
    b = piped(w)
    assert b.call("copy_character_settings", {"from": "Simchar", "parts": ["fighting"]})["ok"] is False  # itself
    assert b.call("copy_character_settings", {"from": "Other", "parts": ["nonsense"]})["ok"] is False
    assert settings.load_profile("Simchar")["attack_gap"] == 0.4                    # nothing saved
    got = b.call("copy_character_settings", {"from": "Other", "parts": ["fighting", "team", "throw"]})
    assert got["ok"] is True, got["text"]
    p = settings.load_profile("Simchar")
    assert p["attack_gap"] == 0.9 and p["team_heal"] is True
    assert p["bag_rules"]["Bear Claw"]["action"] == "throw"
    assert p["bag_rules"]["Wolf Fang"]["action"] == "sell"                          # added, not replaced


def test_run_tool_knows_every_job_the_triggers_know() -> None:
    from unclefarmer.engine import triggers
    assert {job.split()[0] for job, _w in triggers.TOOLS} <= set(control.TOOL_NAMES)


@pytest.mark.parametrize("args", [
    {"action": "scan"}, {"action": "scan", "count_sellers": True},
    {"action": "search", "item": "Lesser Blood | Worthless Blood", "cheapest": True, "max": 50, "pages": 3},
    {"action": "search", "category": "materials"}, {"action": "seller", "sellers": [1234, 5678]},
    {"action": "buy", "item": "Lesser Blood", "count": 10, "max": 50, "cap": 500, "check": True},
    {"action": "buy", "item": "Lesser Blood", "count": 10, "max": 50, "confirm": True},
])
def test_every_market_line_the_tool_builds_passes_the_script_check(args: dict[str, Any]) -> None:
    from unclefarmer.engine import script
    line = remote.RemoteControl.market_line(args["action"], args)
    assert script.check(line) is None, line


def test_market_buying_and_publishing_need_confirm(piped: Callable[[Window], mcpserver.Bridge]) -> None:
    w = Window(pid=os.getpid(), character="Simchar")
    w.s["mcp_control"] = True
    b = piped(w)
    no = b.call("market", {"action": "buy", "item": "Lesser Blood", "count": 5, "max": 40})
    assert no["ok"] is False and "confirm=true" in no["text"] and w.errands == []
    look = b.call("market", {"action": "buy", "item": "Lesser Blood", "count": 5, "max": 40, "check": True})
    assert look["ok"] is True and w.errands[-1][1].startswith("market buy check ")
    assert b.call("market", {"action": "seller"})["ok"] is False
    assert b.call("market", {"action": "search", "category": "nonsense"})["ok"] is False
    no = b.call("run_tool", {"tool": "construction_scan", "publish": "broadcast"})
    assert no["ok"] is False and "confirm=true" in no["text"]
    yes = b.call("run_tool", {"tool": "construction_scan", "publish": "broadcast", "confirm": True})
    assert yes["ok"] is True and w.errands[-1][1] == "construction_scan auto=broadcast\n"
    assert b.call("run_tool", {"tool": "gem_breaker"})["ok"] is False          # breaking can't be undone
    assert b.call("run_tool", {"tool": "gem_breaker", "check_only": True})["ok"] is True
    assert b.call("run_tool", {"tool": "bounties"})["ok"] is True
    empty = b.call("market_results", {})
    assert empty["ok"] is True and "materials" in empty["data"]["categories"]


def test_trigger_lists_chat_filters_and_tool_schedules(piped: Callable[[Window], mcpserver.Bridge],
                                                       tmp_path: Path) -> None:
    w = FullWindow(os.getpid(), "Simchar", str(tmp_path / "schedules.json"))
    w.s["mcp_control"] = True
    settings.save_profile("Simchar", settings.load_profile("Simchar"))
    b = piped(w)
    got = b.call("get_triggers", {})
    assert got["ok"] is True and set(got["data"]) == {"before", "after"}
    bad = b.call("set_triggers", {"stage": "before", "steps": [{"action": "no_such_job"}]})
    assert bad["ok"] is False
    steps = [{"action": "clean_bag", "delay": 600}, {"action": "chores", "deterministic": True}]
    assert b.call("set_triggers", {"stage": "before", "steps": steps})["ok"] is True
    saved = b.call("get_triggers", {})["data"]["before"]
    assert [(s["action"], s["delay"], s["deterministic"]) for s in saved] == [("clean_bag", 600.0, False),
                                                                               ("chores", 0.0, True)]
    assert b.call("set_chat_filters", {"rules": [{"mode": "regex", "text": "x"}]})["ok"] is False
    dupe = [{"mode": "contains", "text": "gold"}, {"mode": "contains", "text": "gold"}]
    assert b.call("set_chat_filters", {"rules": dupe})["ok"] is False
    ok = b.call("set_chat_filters", {"rules": [{"mode": "wildcard", "text": "*selling*", "case_sensitive": False}]})
    assert ok["ok"] is True and w.s["chat_filters"][0]["mode"] == "wildcard"
    assert len(b.call("get_chat_filters", {})["data"]) == 1
    tool = b.call("add_schedule", {"character": "Simchar", "name": "chores", "type": "tool", "repeat": "daily",
                                   "time": "04:00"})
    assert tool["ok"] is True and tool["data"]["item"] == "tool:chores"
    trig = b.call("add_schedule", {"character": "Simchar", "name": "after", "type": "trigger", "repeat": "daily",
                                   "time": "04:30"})
    assert trig["ok"] is True and trig["data"]["item"] == "trigger:after"
    assert b.call("start_plan", {"type": "tool", "name": "store_items"})["ok"] is False      # the stub never runs
    assert w.started[-1] == (os.getpid(), ("tool", "store_items"))


def test_potion_maker_keyboard_profiles_and_autopilot(piped: Callable[[Window], mcpserver.Bridge],
                                                      tmp_path: Path) -> None:
    w = FullWindow(os.getpid(), "Simchar", str(tmp_path / "schedules.json"))
    w.s["mcp_control"] = True
    p = settings.load_profile("Simchar")
    settings.save_profile("Simchar", dict(p, keyboard_profiles={"Night farm": {}}, autopilot_farm="plan",
                                          autopilot_how="lists", autopilot_plan="plan:Wolves"))
    b = piped(w)
    assert b.call("run_tool", {"tool": "potion_maker"})["ok"] is False                  # it spends: confirm
    assert b.call("run_tool", {"tool": "potion_maker", "check_only": True})["ok"] is True
    assert w.errands[-1][1] == "potion_maker check\n"
    assert b.call("run_tool", {"tool": "manage_team"})["ok"] is True
    assert b.call("keyboard_profiles", {})["data"]["names"] == ["Night farm"]
    assert b.call("apply_keyboard_profile", {"name": "Day"})["ok"] is False
    assert b.call("apply_keyboard_profile", {"name": "Night farm"})["ok"] is True
    assert w.errands[-1][1] == "keyboard_profile 'Night farm'\n"
    b.call("start_autopilot", {"character": "Simchar"})          # the stub window never runs it
    assert w.started[-1] == (os.getpid(), ("plan", "Wolves"))


class RoomSender:
    lines: list[str] = []

    def __init__(self, **_kw: object) -> None:
        pass

    def send(self, line: str) -> str:
        if line != "arm":
            RoomSender.lines.append(line)
        return "armed" if line == "arm" else "sent"

    def close(self) -> None:
        pass


def test_chat_rooms_are_listed_read_and_written_to(piped: Callable[[Window], mcpserver.Bridge],
                                                   tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(chat, "AgentLink", RoomSender)
    RoomSender.lines = []
    w = FullWindow(os.getpid(), "Simchar", str(tmp_path / "schedules.json"))
    w.s["mcp_control"] = True
    feed = chat.Feed(os.getpid())
    feed.note_rooms([{"channel": 5, "id": 30, "name": "French", "current": False},
                     {"channel": 5, "id": 10, "name": None, "current": True}])
    feed.add("5", "Ali", "salut", room=30)
    feed.add("5", "Bob", "hello", room=10)
    w.chats[os.getpid()] = feed
    b = piped(w)
    rooms = b.call("chat_rooms", {})
    assert [(r["key"], r["name"], r["up_in_game"]) for r in rooms["data"]] == [
        ("5@30", "International: French", False), ("5@10", "International: room 10", True)]
    french = b.call("read_chat", {"channel": "5@30"})
    assert [r["text"] for r in french["data"]] == ["salut"] and "International: French Ali: salut" in french["text"]
    assert len(b.call("read_chat", {"channel": "international"})["data"]) == 2
    assert b.call("send_chat", {"room": "5@30", "text": "bonjour", "confirm": True})["ok"] is True
    assert b.call("send_chat", {"channel": "global", "text": "hi", "confirm": True})["ok"] is True
    assert b.call("send_chat", {"room": "2@4", "text": "hi", "confirm": True})["ok"] is False
    assert RoomSender.lines == ["sayin 5 30 bonjour", "say 0 hi"]


class WaitingBot:
    def __init__(self) -> None:
        import queue
        self.requests: queue.Queue[Any] = queue.Queue()
        self.waiting_until: float | None = None
        self.wait_cut = threading.Event()

    def log(self, line: str, speak: bool = False) -> None:
        pass


def test_log_out_for_waits_inside_a_run_and_log_back_in_now_ends_it(
        piped: Callable[[Window], mcpserver.Bridge], tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    w = FullWindow(os.getpid(), "Simchar", str(tmp_path / "schedules.json"))
    w.s["mcp_control"] = True
    b = piped(w)
    assert b.call("log_out_for", {"minutes": 5, "confirm": True})["ok"] is False        # no run
    bot = WaitingBot()
    w.runs[os.getpid()] = type("Run", (), {"bot": bot, "title": "Wolves", "kind": "plan"})()
    assert b.call("log_out_for", {"minutes": 5})["ok"] is False                         # confirm
    assert b.call("log_out_for", {"minutes": 0, "confirm": True})["ok"] is False
    assert b.call("log_out_for", {"minutes": 1000, "confirm": True})["ok"] is False
    done: list[tuple[int, str]] = []
    def wait_out(_bot: Any, minutes: int, who: str, _tell: Any) -> None:
        done.append((minutes, who))
    monkeypatch.setattr(logout, "wait_out", wait_out)
    assert b.call("log_out_for", {"minutes": 45, "confirm": True})["ok"] is True
    bot.requests.get_nowait()(bot)                    # the run does it at its next safe moment
    assert done == [(45, "the AI assistant")]
    assert b.call("log_back_in_now", {})["ok"] is False                                 # not waiting
    bot.waiting_until = CLOCK.time() + 12 * 60
    w.waiting = bot
    assert b.call("list_games", {})["data"][0]["logged_out_minutes_left"] == 12
    assert b.call("log_out_for", {"minutes": 5, "confirm": True})["ok"] is False        # already out
    assert b.call("log_back_in_now", {})["ok"] is True and bot.wait_cut.is_set()
